#!/usr/bin/env python3
"""Rank tests by wall time from a cargo-nextest JUnit report.

Usage: nextest_timings.py <junit.xml> [--top N] [--json]

Produce the JUnit file with:
  cargo nextest run --tool-config-file deslop-rust:<scratch>/nextest.toml
where nextest.toml holds:
  [profile.default.junit]
  path = "junit.xml"
The report lands in target/nextest/default/junit.xml.
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
        rows.append({
            "binary": case.get("classname", ""),
            "test": case.get("name", ""),
            "seconds": float(case.get("time", "0") or 0),
            "status": status,
        })
    rows.sort(key=lambda r: r["seconds"], reverse=True)
    total = sum(r["seconds"] for r in rows)

    if args.json:
        json.dump({"total_seconds": total, "count": len(rows), "tests": rows}, sys.stdout, indent=2)
        print()
        return 0

    print(f"{len(rows)} tests, {total:.3f}s summed test time (wall time is lower under parallelism)")
    print(f"{'seconds':>9}  {'share':>6}  status  binary :: test")
    for r in rows[: args.top]:
        share = (r["seconds"] / total * 100) if total else 0
        print(f"{r['seconds']:9.3f}  {share:5.1f}%  {r['status']:<6}  {r['binary']} :: {r['test']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
