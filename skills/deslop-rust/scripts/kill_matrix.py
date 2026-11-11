#!/usr/bin/env python3
"""Per-test mutation kill matrix from one cargo-mutants run.

Usage:
  kill_matrix.py <mutants.out> [--remove TEST ...] [--json]

Needs a run where every test runs against every mutant:
  cargo mutants --test-tool nextest -j 4 -o <dir> -- --no-fail-fast
With fail-fast on (the default), nextest stops at the first failing test, so
a mutant is credited to one test only and the matrix is wrong. The script
checks the logs and refuses to report in that case.

Reports, per test: mutants it kills and how many no other test kills;
groups of tests with identical kill sets; tests whose kills are a strict
subset of another test's; mutants killed by exactly one test.

--remove TEST ... answers "what do we lose if these tests go?" without
another mutation run: it lists every mutant that only the removed tests
kill. TEST is "<binary-id> <test name>" or just the test name. Exit code 1
when the removal loses at least one kill.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

FAIL = re.compile(r"^\s+(FAIL|TIMEOUT|SIGSEGV|SIGABRT|SIGBUS|SIGILL|ABORT)\s+\[[^\]]*\]\s+(?:\(\s*\d+/\d+\)\s+)?(\S+)\s+(\S+)\s*$")
PASS = re.compile(r"^\s+PASS\s+\[[^\]]*\]\s+(?:\(\s*\d+/\d+\)\s+)?(\S+)\s+(\S+)\s*$")


def mutant_label(sc):
    m = sc["Mutant"]
    fn = (m.get("function") or {}).get("function_name", "")
    st = (m.get("span") or {}).get("start", {})
    return f"{m.get('file')}:{st.get('line')}:{st.get('column')} {fn} -> {m.get('replacement', '')} ({m.get('genre', '')})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mutants_out")
    ap.add_argument("--remove", nargs="+", default=[])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = args.mutants_out
    if not os.path.exists(os.path.join(root, "outcomes.json")) and os.path.exists(os.path.join(root, "mutants.out", "outcomes.json")):
        root = os.path.join(root, "mutants.out")
    data = json.load(open(os.path.join(root, "outcomes.json")))

    all_tests, kills, fail_fast_seen = set(), defaultdict(set), False
    caught_without_test = []
    for o in data.get("outcomes", []):
        sc, log = o.get("scenario"), o.get("log_path")
        if not log:
            continue
        text = open(os.path.join(root, log), encoding="utf-8", errors="replace").read()
        if sc == "Baseline":
            for line in text.splitlines():
                m = PASS.match(line)
                if m:
                    all_tests.add(f"{m.group(1)} {m.group(2)}")
            continue
        if not isinstance(sc, dict) or "Mutant" not in sc:
            continue
        if o.get("summary") not in ("CaughtMutant", "Timeout"):
            continue
        if "--no-fail-fast" not in text:
            fail_fast_seen = True
        label = mutant_label(sc)
        killers = set()
        for line in text.splitlines():
            m = FAIL.match(line)
            if m:
                killers.add(f"{m.group(2)} {m.group(3)}")
        if not killers:
            caught_without_test.append(label)  # build failure or doctest; no single test to credit
        for t in killers:
            kills[t].add(label)
            all_tests.add(t)

    if fail_fast_seen:
        sys.exit("this run used fail-fast: rerun cargo mutants with `-- --no-fail-fast` so every test runs against every mutant")

    by_mutant = defaultdict(set)
    for t, ms in kills.items():
        for m in ms:
            by_mutant[m].add(t)
    unique = {t: sorted(m for m in kills.get(t, ()) if len(by_mutant[m]) == 1) for t in all_tests}

    groups = defaultdict(list)
    for t in all_tests:
        groups[frozenset(kills.get(t, ()))].append(t)
    identical = [sorted(ts) for ks, ts in groups.items() if len(ts) > 1 and ks]
    subsets = []
    for t in sorted(all_tests):
        mine = kills.get(t, set())
        for u in sorted(all_tests):
            if t != u and mine and mine < kills.get(u, set()):
                subsets.append({"test": t, "kills": len(mine), "within": u, "within_kills": len(kills[u])})
                break

    lost = []
    if args.remove:
        def matches(t, name):
            return t == name or t.split(" ", 1)[-1] == name
        removed = {t for t in all_tests if any(matches(t, n) for n in args.remove)}
        unknown = [n for n in args.remove if not any(matches(t, n) for t in all_tests)]
        if unknown:
            sys.exit(f"unknown test(s): {', '.join(unknown)}")
        lost = sorted(m for m, ts in by_mutant.items() if ts and ts <= removed)

    result = {
        "tests": len(all_tests),
        "mutants_credited": len(by_mutant),
        "per_test": {t: {"kills": len(kills.get(t, ())), "unique_kills": unique[t]} for t in sorted(all_tests)},
        "identical_kill_sets": identical,
        "strict_subsets": subsets,
        "zero_kill_tests": sorted(t for t in all_tests if not kills.get(t)),
        "caught_without_a_failing_test": caught_without_test,
        "removal": {"tests": args.remove, "lost_kills": lost} if args.remove else None,
    }
    if args.json:
        json.dump(result, sys.stdout, indent=2)
        print()
    else:
        print(f"{len(all_tests)} tests, {len(by_mutant)} caught mutants credited to tests")
        print(f"\n{'kills':>5} {'unique':>6}  test")
        for t in sorted(all_tests, key=lambda t: (len(unique[t]), len(kills.get(t, ()))), reverse=True):
            print(f"{len(kills.get(t, ())):5} {len(unique[t]):6}  {t}")
        print("\nidentical kill sets:")
        for g in identical:
            print("  - " + "  ==  ".join(g))
        print("\nkills are a strict subset of another test:")
        for s in subsets:
            print(f"  - {s['test']} ({s['kills']}) within {s['within']} ({s['within_kills']})")
        print("\ntests that kill nothing:")
        for t in result["zero_kill_tests"]:
            print(f"  - {t}")
        if caught_without_test:
            print(f"\ncaught with no failing test to credit (build error, doctest): {len(caught_without_test)}")
        if args.remove:
            print(f"\nremoving {len(args.remove)} test(s) loses {len(lost)} kill(s):")
            for m in lost:
                print(f"  LOST  {m}  (only: {', '.join(sorted(by_mutant[m]))})")
    return 1 if lost else 0


if __name__ == "__main__":
    sys.exit(main())
