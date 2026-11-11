#!/usr/bin/env python3
"""Snapshot mutmut results and compare two snapshots for lost kills.

Usage (from the project root):
  mutants_compare.py snapshot <dir>            copy mutants/**/*.meta and mutmut-stats.json to <dir>
  mutants_compare.py diff <baseline> <after> [--json]

mutmut keeps its results in mutants/, and the next `mutmut run` reuses or
overwrites them, so snapshot each run you want to keep. Delete mutants/
before the "after" run: mutmut reuses a result while the function's source
hash is unchanged, so deleting a test does not make it retest anything.

Mutants are matched by key (module, function, mutant number). A function
whose source hash changed between the snapshots is reported separately,
since its mutant numbers no longer line up; outside approved junk-code
deletions that means production code changed.

Exit code 1 when a mutant killed in the baseline is not killed after.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

KILLED = {1, 3, 37}
STATUS = {1: "killed", 3: "killed", 37: "caught by type check", 0: "survived", 5: "no tests",
          33: "no tests", 34: "skipped", 35: "suspicious", 36: "timeout", None: "not checked",
          24: "timeout", -24: "timeout", 152: "timeout", 255: "timeout", -9: "segfault", -11: "segfault"}


def snapshot(dest: Path) -> int:
    src = Path("mutants")
    if not (src / "mutmut-stats.json").exists():
        sys.exit("mutants/mutmut-stats.json not found: run `mutmut run` from the project root first")
    if dest.exists():
        shutil.rmtree(dest)
    for f in [src / "mutmut-stats.json", *src.rglob("*.meta")]:
        out = dest / f.relative_to(src)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, out)
    print(f"snapshot written to {dest}")
    return 0


def load(d: Path):
    if not d.exists():
        sys.exit(f"{d} not found: snapshot a finished `mutmut run` there first")
    codes, hashes = {}, {}
    for meta in d.rglob("*.meta"):
        data = json.loads(meta.read_text())
        file_codes = data.get("exit_code_by_key", {})
        file_hashes = data.get("hash_by_function_name", {})
        codes.update(file_codes)
        # Qualify each hash with its module, taken from this file's own mutant keys, so
        # same-named functions in different modules (main, run, parse) stay apart.
        for fn in {fn_of(k) for k in file_codes}:
            if short_fn(fn) in file_hashes:
                hashes[fn] = file_hashes[short_fn(fn)]
    return codes, hashes


def fn_of(key):
    return key.rsplit("__mutmut_", 1)[0]


def short_fn(fn):
    # meta hash keys are module-relative ("x_parse_qty"); mutant keys are dotted ("cartcalc.core.x_parse_qty")
    return fn.rsplit(".", 1)[-1]


def diff(base_dir: Path, after_dir: Path, as_json: bool) -> int:
    base, bh = load(base_dir)
    after, ah = load(after_dir)
    changed_fns = sorted({k for k in bh if k in ah and bh[k] != ah[k]})
    lost, gained, only_base, only_after, changed = [], [], [], [], []
    for k, b in base.items():
        if fn_of(k) in changed_fns:
            changed.append(k)
            continue
        if k not in after:
            only_base.append(f"{k} [{STATUS.get(b, b)}]")
            continue
        a = after[k]
        if b in KILLED and a not in KILLED:
            lost.append({"mutant": k, "before": STATUS.get(b, b), "after": STATUS.get(a, a)})
        elif b not in KILLED and a in KILLED:
            gained.append({"mutant": k, "before": STATUS.get(b, b), "after": STATUS.get(a, a)})
    only_after = [f"{k} [{STATUS.get(a, a)}]" for k, a in after.items() if k not in base and fn_of(k) not in changed_fns]

    def count(d):
        killed = sum(1 for c in d.values() if c in KILLED)
        return {"killed": killed, "survived": sum(1 for c in d.values() if c == 0),
                "no_tests": sum(1 for c in d.values() if c in (5, 33)), "total": len(d)}

    summary = {"baseline": count(base), "after": count(after), "lost_kills": lost, "new_kills": gained,
               "changed_functions": changed_fns, "only_in_baseline": only_base, "only_in_after": only_after}
    if as_json:
        json.dump(summary, sys.stdout, indent=2)
        print()
    else:
        for side in ("baseline", "after"):
            c = summary[side]
            print(f"{side:>8}: {c['killed']}/{c['total']} killed, {c['survived']} survived, {c['no_tests']} no tests")
        print(f"lost kills (killed before, not now): {len(lost)}")
        for x in lost:
            print(f"  LOST  {x['mutant']}  {x['before']} -> {x['after']}")
        print(f"new kills: {len(gained)}")
        for x in gained:
            print(f"  NEW   {x['mutant']}")
        if changed_fns:
            print(f"functions whose source changed (mutants not comparable): {len(changed_fns)}")
            for f in changed_fns:
                print(f"  CHANGED {f}")
        if only_base:
            print(f"mutants only in baseline (code removed): {len(only_base)}")
            for x in only_base:
                print(f"  GONE  {x}")
        if only_after:
            print(f"mutants only in after (code added): {len(only_after)}")
            for x in only_after:
                print(f"  ADDED {x}")
    return 1 if lost else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("dir")
    d = sub.add_parser("diff")
    d.add_argument("baseline")
    d.add_argument("after")
    d.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.cmd == "snapshot":
        return snapshot(Path(args.dir))
    return diff(Path(args.baseline), Path(args.after), args.json)


if __name__ == "__main__":
    sys.exit(main())
