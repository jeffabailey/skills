#!/usr/bin/env python3
"""Per-test coverage overlap from one pytest-cov run with test contexts.

Usage (run with the project's Python, for example `uv run python`):
  coverage_overlap.py <coverage data file> [--tests-glob PATTERN ...] [--json]

Produce the data file with:
  COVERAGE_FILE=<file> pytest --cov=<package> --cov-context=test --cov-branch --cov-report=
--cov-context=test records which test executed each line, so one run gives
per-test coverage for the whole suite.

Reports: groups of tests with identical production coverage, tests whose
coverage is a strict subset of another test's, unique lines per test, and
production lines no test executes. Test code (tests/, test_*.py, *_test.py,
conftest.py) is left out, so a test's own body never counts as coverage.
"""
import argparse
import fnmatch
import json
import os
import sys
from collections import defaultdict

DEFAULT_TEST_GLOBS = ["*/tests/*", "*/test/*", "*/test_*.py", "*_test.py", "*/conftest.py"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data_file")
    ap.add_argument("--tests-glob", action="append", default=[],
                    help="extra glob for files that are test code (repeatable)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        import coverage
    except ImportError:
        sys.exit("coverage is not importable: run this script with the project's Python (uv run python ...)")

    cov = coverage.Coverage(data_file=args.data_file)
    cov.load()
    data = cov.get_data()
    contexts = [c for c in data.measured_contexts() if c]
    if not contexts:
        sys.exit("no test contexts in the data file: rerun pytest with --cov-context=test")

    globs = DEFAULT_TEST_GLOBS + args.tests_glob
    cwd = os.getcwd()

    def rel(p):
        return os.path.relpath(p, cwd)

    lines_by_test = defaultdict(set)
    uncovered = {}
    for f in sorted(data.measured_files()):
        if any(fnmatch.fnmatch(f, g) for g in globs):
            continue
        for lineno, ctxs in (data.contexts_by_lineno(f) or {}).items():
            for c in ctxs:
                if c:
                    test = c.rsplit("|", 1)[0]
                    lines_by_test[test].add((rel(f), lineno))
        try:
            _, statements, _, missing, _ = cov.analysis2(f)
            if missing:
                uncovered[rel(f)] = {"missing": len(missing), "statements": len(statements),
                                     "lines": coverage.numbits.numbits_to_nums(coverage.numbits.nums_to_numbits(missing))}
        except Exception:  # noqa: BLE001 - source file gone or not Python
            pass

    tests = sorted({c.rsplit("|", 1)[0] for c in contexts})
    owners = defaultdict(set)
    for t, ls in lines_by_test.items():
        for ln in ls:
            owners[ln].add(t)
    unique = {t: sorted(ln for ln in lines_by_test.get(t, ()) if len(owners[ln]) == 1) for t in tests}

    groups = defaultdict(list)
    for t in tests:
        groups[frozenset(lines_by_test.get(t, ()))].append(t)
    identical = [sorted(ts) for ls, ts in groups.items() if len(ts) > 1 and ls]
    subsets = []
    for t in tests:
        mine = lines_by_test.get(t, set())
        for u in tests:
            if t != u and mine and mine < lines_by_test.get(u, set()):
                subsets.append({"test": t, "lines": len(mine), "within": u})
                break

    result = {
        "tests": len(tests),
        "per_test": {t: {"lines": len(lines_by_test.get(t, ())), "unique_lines": len(unique[t])} for t in tests},
        "identical_coverage": identical,
        "strict_subsets": subsets,
        "no_production_coverage": sorted(t for t in tests if not lines_by_test.get(t)),
        "uncovered_production_lines": uncovered,
    }
    if args.json:
        json.dump(result, sys.stdout, indent=2)
        print()
        return 0

    print(f"{len(tests)} tests with coverage contexts")
    print(f"\n{'lines':>5} {'unique':>6}  test")
    for t in sorted(tests, key=lambda t: (len(unique[t]), len(lines_by_test.get(t, ()))), reverse=True):
        print(f"{len(lines_by_test.get(t, ())):5} {len(unique[t]):6}  {t}")
    print("\nidentical production coverage:")
    for g in identical:
        print("  - " + "  ==  ".join(g))
    print("\ncoverage is a strict subset of another test:")
    for s in subsets:
        print(f"  - {s['test']} ({s['lines']} lines) within {s['within']}")
    if result["no_production_coverage"]:
        print("\ntests that execute no production line:")
        for t in result["no_production_coverage"]:
            print(f"  - {t}")
    print("\nproduction lines no test executes:")
    for f, u in uncovered.items():
        print(f"  {f}: {u['missing']}/{u['statements']} statements, lines {u['lines']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
