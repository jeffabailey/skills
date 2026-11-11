#!/usr/bin/env python3
"""Per-test mutation kill matrix on top of a finished `mutmut run`.

Usage (from the project root, after `mutmut run`):
  kill_matrix.py --cache <file.json> [-j N] [--timeout S] [--pytest-arg ARG ...]
  kill_matrix.py --cache <file.json> --remove TEST [TEST ...] [--json]

mutmut runs pytest with -x, so it stops at the first failing test and its
results credit a killed mutant to one test at most. This script reruns every
killed mutant against the tests that cover its function (mutmut's own
mutants/mutmut-stats.json) without -x, and records *every* test that fails.
The first call builds the cache; later calls (for example with --remove)
read it and run nothing. Delete the cache to rebuild.

Reports, per test: mutants it kills and how many no other test kills;
groups of tests with identical kill sets; tests whose kills are a strict
subset of another test's; tests that kill nothing.

--remove TEST ... answers "what do we lose if these tests go?": it lists
every mutant that only the removed tests kill. TEST is a pytest node id
(tests/test_x.py::test_name) or just the test name. Exit code 1 when the
removal loses at least one kill.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

KILLED = {1, 3}
FAILED_LINE = re.compile(r"^(FAILED|ERROR) (.+?)(?: - .*)?$")


def load_mutmut(mutants: Path):
    stats_path = mutants / "mutmut-stats.json"
    if not stats_path.exists():
        sys.exit(f"{stats_path} not found: run `mutmut run` first, from the project root")
    stats = json.loads(stats_path.read_text())
    codes = {}
    for meta in mutants.rglob("*.meta"):
        codes.update(json.loads(meta.read_text()).get("exit_code_by_key", {}))
    return stats, codes


def function_of(key: str) -> str:
    return key.rsplit("__mutmut_", 1)[0]


def run_one(key, tests, mutants, pythonpath, timeout, extra):
    env = dict(os.environ, MUTANT_UNDER_TEST=key, PYTHONPATH=pythonpath,
               PY_IGNORE_IMPORTMISMATCH="1")
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [sys.executable, "-m", "pytest", "--rootdir=.", "-q", "-rfE", "--no-header",
               "-p", "no:cacheprovider", "-p", "no:randomly", "-p", "no:random-order",
               "--basetemp", tmp, *extra, *tests]
        try:
            out = subprocess.run(cmd, cwd=mutants, env=env, capture_output=True, text=True,
                                 timeout=timeout).stdout
        except subprocess.TimeoutExpired:
            return key, None
    killers = sorted({m.group(2) for line in out.splitlines() if (m := FAILED_LINE.match(line))})
    return key, killers


def build(args, cache: Path):
    mutants = Path("mutants")
    stats, codes = load_mutmut(mutants)
    by_fn = stats.get("tests_by_mangled_function_name", {})
    all_tests = sorted(set(stats.get("duration_by_test", {})) | {t for ts in by_fn.values() for t in ts})
    roots = [str((mutants / p).resolve()) for p in (".", "src", "source") if (mutants / p).is_dir()]
    pythonpath = os.pathsep.join(roots + ([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else []))

    todo = [(k, sorted(by_fn.get(function_of(k), []))) for k, c in codes.items() if c in KILLED]
    todo = [(k, ts) for k, ts in todo if ts]
    print(f"rerunning {len(todo)} killed mutants without -x ({args.jobs} jobs)", file=sys.stderr)
    result = {"tests": all_tests, "mutants": {}}
    for k, c in codes.items():
        result["mutants"][k] = {"exit_code": c, "killers": []}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_one, k, ts, mutants, pythonpath, args.timeout, args.pytest_arg)
                   for k, ts in todo]
        for f in futures:
            key, killers = f.result()
            if killers is None:
                result["mutants"][key]["rerun_timeout"] = True
            else:
                result["mutants"][key]["killers"] = killers
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(result, indent=1))
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("-j", "--jobs", type=int, default=4)
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--pytest-arg", action="append", default=[],
                    help="extra argument for pytest, repeatable (for example the project's -m filter)")
    ap.add_argument("--remove", nargs="+", default=[])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cache = Path(args.cache)
    data = json.loads(cache.read_text()) if cache.exists() else build(args, cache)

    all_tests = set(data["tests"])
    kills = defaultdict(set)
    caught_without_test, rerun_timeouts = [], []
    for key, m in data["mutants"].items():
        if m["exit_code"] not in KILLED and m["exit_code"] != 37:
            continue
        if m.get("rerun_timeout"):
            rerun_timeouts.append(key)
        elif not m["killers"]:
            caught_without_test.append(key)  # type-check kill, collection error, or flaky
        for t in m["killers"]:
            kills[t].add(key)
            all_tests.add(t)

    by_mutant = defaultdict(set)
    for t, ms in kills.items():
        for k in ms:
            by_mutant[k].add(t)
    unique = {t: sorted(k for k in kills.get(t, ()) if len(by_mutant[k]) == 1) for t in all_tests}

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
            return t == name or t.split("::")[-1] == name or t.endswith("::" + name)
        removed = {t for t in all_tests if any(matches(t, n) for n in args.remove)}
        unknown = [n for n in args.remove if not any(matches(t, n) for t in all_tests)]
        if unknown:
            sys.exit(f"unknown test(s): {', '.join(unknown)}")
        lost = sorted(k for k, ts in by_mutant.items() if ts and ts <= removed)

    result = {
        "tests": len(all_tests),
        "mutants_credited": len(by_mutant),
        "per_test": {t: {"kills": len(kills.get(t, ())), "unique_kills": unique[t]} for t in sorted(all_tests)},
        "identical_kill_sets": identical,
        "strict_subsets": subsets,
        "zero_kill_tests": sorted(t for t in all_tests if not kills.get(t)),
        "caught_without_a_failing_test": caught_without_test,
        "rerun_timeouts": rerun_timeouts,
        "removal": {"tests": args.remove, "lost_kills": lost} if args.remove else None,
    }
    if args.json:
        json.dump(result, sys.stdout, indent=2)
        print()
    else:
        print(f"{len(all_tests)} tests, {len(by_mutant)} killed mutants credited to tests")
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
            print(f"\nkilled with no failing test to credit (type check, collection error, flaky): {len(caught_without_test)}")
        if rerun_timeouts:
            print(f"\ntimed out on rerun, not credited: {len(rerun_timeouts)}")
        if args.remove:
            print(f"\nremoving {len(args.remove)} test(s) loses {len(lost)} kill(s):")
            for k in lost:
                print(f"  LOST  {k}  (only: {', '.join(sorted(by_mutant[k]))})  see: mutmut show {k}")
    return 1 if lost else 0


if __name__ == "__main__":
    sys.exit(main())
