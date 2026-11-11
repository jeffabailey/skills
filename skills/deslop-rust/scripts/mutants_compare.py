#!/usr/bin/env python3
"""Compare two cargo-mutants runs and flag lost mutation kills.

Usage: mutants_compare.py <baseline mutants.out> <after mutants.out> [--json]

Mutants are matched by package, file, function, genre, replacement, and the
mutated source text position *relative to the function start*, so edits that
shift line numbers (for example, removing an inline test module above a
function) do not break the match.

Exit code 1 when a mutant the baseline caught is no longer caught (missed or
timed out). Exit code 0 otherwise. Mutants that exist only on one side (code
that was added or deleted) are listed separately and do not fail the check.
"""
import argparse
import collections
import json
import os
import sys

CAUGHT = {"CaughtMutant"}


def load(dir_path):
    path = os.path.join(dir_path, "outcomes.json")
    if not os.path.exists(path):
        path = os.path.join(dir_path, "mutants.out", "outcomes.json")
    if not os.path.exists(path):
        sys.exit(f"no outcomes.json under {dir_path}: did the cargo mutants run finish, and was -o pointed there?")
    with open(path) as fh:
        data = json.load(fh)
    out = collections.defaultdict(list)
    for o in data.get("outcomes", []):
        sc = o.get("scenario")
        if not isinstance(sc, dict) or "Mutant" not in sc:
            continue
        m = sc["Mutant"]
        fn = m.get("function") or {}
        fstart = (fn.get("span") or {}).get("start", {}).get("line", 0)
        start = (m.get("span") or {}).get("start", {})
        rel = (start.get("line", 0) - fstart, start.get("column", 0))
        key = (
            m.get("package", ""), m.get("file", ""), fn.get("function_name", ""),
            m.get("genre", ""), m.get("replacement", ""), rel,
        )
        label = f"{m.get('file')}:{start.get('line')}:{start.get('column')} {fn.get('function_name','')} -> {m.get('replacement','')} ({m.get('genre','')})"
        out[key].append((o.get("summary"), label))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline")
    ap.add_argument("after")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    base, after = load(args.baseline), load(args.after)
    lost, gained, only_base, only_after = [], [], [], []
    for key, outs in base.items():
        if key not in after:
            only_base.extend(f"{lbl} [{s}]" for s, lbl in outs)
            continue
        for (b_sum, b_lbl), (a_sum, a_lbl) in zip(outs, after[key]):
            if b_sum in CAUGHT and a_sum not in CAUGHT and a_sum != "Unviable":
                lost.append({"mutant": a_lbl, "before": b_sum, "after": a_sum})
            elif b_sum not in CAUGHT and a_sum in CAUGHT:
                gained.append({"mutant": a_lbl, "before": b_sum, "after": a_sum})
    for key, outs in after.items():
        if key not in base:
            only_after.extend(f"{lbl} [{s}]" for s, lbl in outs)

    def count(d, s):
        return sum(1 for outs in d.values() for x, _ in outs if x == s)

    summary = {
        "baseline": {"caught": count(base, "CaughtMutant"), "missed": count(base, "MissedMutant"), "timeout": count(base, "Timeout")},
        "after": {"caught": count(after, "CaughtMutant"), "missed": count(after, "MissedMutant"), "timeout": count(after, "Timeout")},
        "lost_kills": lost,
        "new_kills": gained,
        "only_in_baseline": only_base,
        "only_in_after": only_after,
    }
    if args.json:
        json.dump(summary, sys.stdout, indent=2)
        print()
    else:
        b, a = summary["baseline"], summary["after"]
        print(f"baseline: {b['caught']} caught, {b['missed']} missed, {b['timeout']} timeout")
        print(f"after:    {a['caught']} caught, {a['missed']} missed, {a['timeout']} timeout")
        print(f"lost kills (caught before, not now): {len(lost)}")
        for x in lost:
            print(f"  LOST  {x['mutant']}  {x['before']} -> {x['after']}")
        print(f"new kills: {len(gained)}")
        for x in gained:
            print(f"  NEW   {x['mutant']}")
        if only_base:
            print(f"mutants only in baseline (code removed): {len(only_base)}")
            for x in only_base:
                print(f"  GONE  {x}")
        if only_after:
            print(f"mutants only in after (code added): {len(only_after)}")
            for x in only_after:
                print(f"  ADDED {x}")
    return 1 if lost else 0


if __name__ == "__main__":
    sys.exit(main())
