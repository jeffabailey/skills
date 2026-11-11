#!/usr/bin/env python3
"""Rank tests by time from a pytest JUnit report.

Usage: pytest_timings.py <junit.xml> [--top N] [--json]

Produce the JUnit file with `pytest --junitxml=<file>`. A test's time is
setup + call + teardown, so an expensive fixture shows up in every test that
uses it; run `pytest --durations=25 --durations-min=0.05` to split the phases.
"""
import argparse
import json
import sys
import xml.etree.ElementTree as ET


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("junit")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = ET.parse(args.junit).getroot()
    rows = []
    for case in root.iter("testcase"):
        status = "pass"
        if case.find("failure") is not None or case.find("error") is not None:
            status = "fail"
        elif case.find("skipped") is not None:
            status = "skip"
        cls = case.get("classname", "")
        rows.append({
            "node": f"{cls.replace('.', '/')}.py::{case.get('name', '')}" if cls else case.get("name", ""),
            "classname": cls,
            "test": case.get("name", ""),
            "seconds": float(case.get("time", "0") or 0),
            "status": status,
        })
    rows.sort(key=lambda r: r["seconds"], reverse=True)
    total = sum(r["seconds"] for r in rows)
    suites = list(root.iter("testsuite"))
    wall = sum(float(s.get("time", "0") or 0) for s in suites)

    if args.json:
        json.dump({"total_seconds": total, "wall_seconds": wall, "count": len(rows), "tests": rows}, sys.stdout, indent=2)
        print()
        return 0

    print(f"{len(rows)} tests, {total:.3f}s summed test time, {wall:.3f}s session time")
    print(f"{'seconds':>9}  {'share':>6}  status  classname :: test")
    for r in rows[: args.top]:
        share = (r["seconds"] / total * 100) if total else 0
        print(f"{r['seconds']:9.3f}  {share:5.1f}%  {r['status']:<6}  {r['classname']} :: {r['test']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
