#!/usr/bin/env python3
"""Per-test coverage with cargo-llvm-cov + nextest, then overlap analysis.

Usage:
  coverage_overlap.py --out <scratch dir> [--filter '<nextest filterset>']
                      [--manifest-path Cargo.toml] [--json] [-- <extra llvm-cov args>]

Runs `cargo llvm-cov nextest --lcov` once per test (narrow with --filter for
big suites; each run reuses the instrumented build, so the cost is roughly
test runtime plus report export), keeps only production lines (drops
tests/, benches/, examples/, and lines inside `#[cfg(test)]` modules), and
reports:

  * identical:  groups of tests whose production coverage is exactly the same
  * subsumed:   tests whose covered lines are a strict subset of one other test
  * unique:     per test, lines no other test covers
  * uncovered:  production lines no test covers (dead-code candidates)

Coverage overlap is a lead, not a verdict: two tests can cover the same lines
and assert different things. Confirm with assertions read and mutation runs.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

NON_PROD = re.compile(r"(^|/)(tests|benches|examples)/")


def list_tests(manifest, filt):
    cmd = ["cargo", "nextest", "list", "--message-format", "json"]
    if manifest:
        cmd += ["--manifest-path", manifest]
    if filt:
        cmd += ["-E", filt]
    data = json.loads(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout)
    tests = []
    for suite in data["rust-suites"].values():
        for name, tc in suite["testcases"].items():
            if tc.get("filter-match", {}).get("status", "matches") != "matches":
                continue
            if tc.get("ignored"):
                continue
            tests.append((suite["binary-id"], name))
    return tests


def cfg_test_ranges(path, cache={}):
    """Line ranges (1-based, inclusive) of #[cfg(test)] modules in a file."""
    if path in cache:
        return cache[path]
    ranges = []
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        cache[path] = ranges
        return ranges
    i = 0
    while i < len(lines):
        if re.match(r"\s*#\[cfg\(test\)\]", lines[i]):
            j = i + 1
            while j < len(lines) and not re.match(r"\s*(pub(\(.*\))?\s+)?mod\s+\w+", lines[j]):
                if lines[j].strip() and not lines[j].strip().startswith("#["):
                    break
                j += 1
            if j < len(lines) and re.match(r"\s*(pub(\(.*\))?\s+)?mod\s+\w+", lines[j]):
                depth, k, opened = 0, j, False
                while k < len(lines):
                    depth += lines[k].count("{") - lines[k].count("}")
                    opened = opened or "{" in lines[k]
                    if opened and depth <= 0:
                        break
                    k += 1
                ranges.append((i + 1, k + 1))
                i = k
        i += 1
    cache[path] = ranges
    return ranges


def parse_lcov(path, root):
    covered, instrumented = set(), set()
    sf = None
    for line in open(path):
        line = line.strip()
        if line.startswith("SF:"):
            sf = line[3:]
        elif line.startswith("DA:") and sf:
            ln, hits = line[3:].split(",")[:2]
            ln = int(ln)
            rel = os.path.relpath(sf, root)
            if NON_PROD.search(rel) or any(a <= ln <= b for a, b in cfg_test_ranges(sf)):
                continue
            instrumented.add((rel, ln))
            if int(hits) > 0:
                covered.add((rel, ln))
    return covered, instrumented


def main() -> int:
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:
        idx = argv.index("--")
        argv, extra = argv[:idx], argv[idx + 1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--filter")
    ap.add_argument("--manifest-path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    root = os.path.dirname(os.path.abspath(args.manifest_path)) if args.manifest_path else os.getcwd()
    tests = list_tests(args.manifest_path, args.filter)
    cov, all_lines = {}, set()
    for i, (binary, name) in enumerate(tests, 1):
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{binary}__{name}")
        lcov = os.path.join(args.out, safe + ".lcov")
        cmd = ["cargo", "llvm-cov", "nextest", "--lcov", "--output-path", lcov,
               "-E", f"binary_id({binary}) & test(={name})"]
        if args.manifest_path:
            cmd += ["--manifest-path", args.manifest_path]
        cmd += extra
        print(f"[{i}/{len(tests)}] {binary} :: {name}", file=sys.stderr)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-2000:], file=sys.stderr)
            continue
        covered, instrumented = parse_lcov(lcov, root)
        cov[(binary, name)] = covered
        all_lines |= instrumented

    counts = defaultdict(int)
    for lines in cov.values():
        for ln in lines:
            counts[ln] += 1

    groups = defaultdict(list)
    for t, lines in cov.items():
        groups[frozenset(lines)].append(t)
    identical = [sorted(f"{b} :: {n}" for b, n in ts) for ts in groups.values() if len(ts) > 1]

    subsumed = []
    items = list(cov.items())
    for t, lines in items:
        for u, other in items:
            if t != u and lines < other:
                subsumed.append({"test": f"{t[0]} :: {t[1]}", "by": f"{u[0]} :: {u[1]}",
                                 "lines": len(lines), "by_lines": len(other)})
                break

    unique = {f"{b} :: {n}": sum(1 for ln in lines if counts[ln] == 1) for (b, n), lines in cov.items()}
    union = set().union(*cov.values()) if cov else set()
    uncovered = sorted(all_lines - union)
    by_file = defaultdict(list)
    for f, ln in uncovered:
        by_file[f].append(ln)

    result = {
        "tests_measured": len(cov),
        "identical_coverage_groups": identical,
        "subsumed": subsumed,
        "unique_lines_per_test": unique,
        "uncovered_production_lines": {f: lns for f, lns in by_file.items()},
    }
    with open(os.path.join(args.out, "overlap.json"), "w") as fh:
        json.dump(result, fh, indent=2)
    if args.json:
        json.dump(result, sys.stdout, indent=2)
        print()
        return 0
    print(f"measured {len(cov)} tests; full result in {os.path.join(args.out, 'overlap.json')}")
    print("\nidentical production coverage:")
    for g in identical:
        print("  - " + "  ==  ".join(g))
    print("\nstrict subset of another test:")
    for s in subsumed:
        print(f"  - {s['test']} ({s['lines']} lines) within {s['by']} ({s['by_lines']} lines)")
    print("\ntests with zero unique lines:")
    for t, n in sorted(unique.items()):
        if n == 0:
            print(f"  - {t}")
    print("\nuncovered production lines (dead-code or gap candidates):")
    for f, lns in by_file.items():
        print(f"  - {f}: {compress(lns)}")
    return 0


def compress(nums):
    nums = sorted(nums)
    out, start, prev = [], None, None
    for n in nums:
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append(f"{start}-{prev}" if start != prev else str(start))
            start = prev = n
    if start is not None:
        out.append(f"{start}-{prev}" if start != prev else str(start))
    return ", ".join(out)


if __name__ == "__main__":
    sys.exit(main())
