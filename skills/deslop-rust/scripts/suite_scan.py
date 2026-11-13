#!/usr/bin/env python3
"""Static facts about a Rust test suite, and the numbers for the audit report.

Usage:
  suite_scan.py scan [PATH] [--all] [--json]
  suite_scan.py totals <junit.xml> [--mutants-out DIR] [--root PATH]
                       [--remove TEST ...] [--shorten TEST=SECONDS ...] [--merge TEST ...]

scan reads every .rs file under PATH (not target/ or hidden directories) and
prints, sorted: each test that has a label (file:line, name, assert count,
body lines), groups of tests with identical bodies, groups of 3 or more tests
with the same first 3 lines, and each #[allow(dead_code)] item with the
number of other mentions of its name. --all lists tests without labels too.

Labels (text matches, not judgments; read the test before you classify it):
  no-assert     no assert/panic macro in the body (a helper may assert)
  is_ok is_err  the body calls .is_ok() / .is_err()
  let_          `let _ = ...`
  bound         assert!(x > 0)-style comparison with a number
  sleep         a sleep( call
  ignore should_panic snapshot proptest   attributes and macros of that kind
  cites-issue   name or comment mentions an issue, bug, CVE, or incident

totals reads the JUnit report (and cargo-mutants outcomes.json) and prints the
baseline line, one row per named test (seconds saved per run, per mutation
run, body lines), and the sums. TEST is "<binary-id> <test name>" or the test
name. --shorten gives the seconds a test will lose; --merge counts a test
that folds into another (0s, lines not counted).
"""
import argparse
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

SKIP_DIRS = {"target", "node_modules"}
TEST_ATTRS = {"test", "rstest", "test_case", "quickcheck"}
RAW = re.compile(r'r(#*)"')
CHAR = re.compile(r"'(?:\\(?:[^u]|u\{[0-9a-fA-F_]+\})|[^\\'\n])'")
ITEM = re.compile(
    r"\s*(pub(?:\s*\([^)]*\))?\s+)?"
    r"(?:(?:const|async|unsafe|default)\s+|extern\s*(?:\"[^\"]*\"\s*)?)*"
    r"(fn|struct|enum|union|trait|mod|static|const|type|impl|use)\b\s*(?:mut\s+)?(\w+)?")
FIELD = re.compile(r"\s*(pub(?:\s*\([^)]*\))?\s+)?(\w+)")
ASSERT = re.compile(r"\b(?:\w*assert\w*|panic|unreachable)!")
PLAIN_ASSERT = re.compile(r"\bassert!\s*\(")
BOUND = re.compile(r"[^-=<>](?:>=?|<=?)\s*-?\d")
CITES = re.compile(r"(?i)\b(?:issue|bug|cve|incident|regression)\b|\bgh-\d+|#\d{2,}")
DEAD = re.compile(r"\b(?:allow|expect)\s*\([^)]*\bdead_code\b")
MAX_ROWS, MAX_GROUPS, MAX_NAMES = 40, 10, 5


def die(msg):
    print(f"suite_scan: {msg}", file=sys.stderr)
    sys.exit(2)


def mask(src):
    """Return (code, nocomment, comments), each the same length as src.

    code has comments, strings, and chars blanked; nocomment has comments
    blanked; comments keeps only the comment text. Newlines always stay.
    """
    n = len(src)
    code, noc, com = list(src), list(src), [c if c == "\n" else " " for c in src]

    def blank(buf, a, b):
        for k in range(a, min(b, n)):
            if buf[k] != "\n":
                buf[k] = " "

    def comment(a, b):
        com[a:b] = src[a:b]
        blank(code, a, b)
        blank(noc, a, b)

    i = 0
    while i < n:
        c = src[i]
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            comment(i, j)
            i = j
        elif src.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if src.startswith("/*", j):
                    depth, j = depth + 1, j + 2
                elif src.startswith("*/", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            comment(i, j)
            i = j
        elif c == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            blank(code, i + 1, j)
            i = j + 1
        elif c == "r" and RAW.match(src, i):
            m = RAW.match(src, i)
            end = src.find('"' + m.group(1), m.end())
            end = n if end < 0 else end
            blank(code, m.end(), end)
            i = end + 1 + len(m.group(1))
        elif c == "'":
            m = CHAR.match(src, i)
            if m:
                blank(code, i + 1, m.end() - 1)
                i = m.end()
            else:
                i += 1
        else:
            i += 1
    return "".join(code), "".join(noc), "".join(com)


def close(code, start, opener, closer):
    """Index after the bracket that closes the one at start, or -1."""
    depth = 0
    for k in range(start, len(code)):
        ch = code[k]
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return k + 1
    return -1


def attr_runs(code):
    """Yield (start, end, [(text, inner)]) for each run of attributes."""
    i, n = 0, len(code)
    while True:
        i = code.find("#", i)
        if i < 0:
            return
        start, attrs, j = i, [], i
        while True:
            m = re.compile(r"\s*#(!?)\[").match(code, j)
            if not m:
                break
            end = close(code, m.end() - 1, "[", "]")
            if end < 0:
                break
            attrs.append((code[m.end():end - 1].strip(), bool(m.group(1))))
            j = end
        if attrs:
            yield start, j, attrs
            i = j
        else:
            i += 1
        if i >= n:
            return


def attr_name(text):
    return re.split(r"[(=\s]", text, maxsplit=1)[0].split("::")[-1]


def scan_file(path, rel):
    src = path.read_text(encoding="utf-8", errors="replace")
    code, noc, com = mask(src)
    line_of = lambda pos: src.count("\n", 0, pos) + 1  # noqa: E731
    tests, dead, broken = [], [], False
    for start, end, attrs in attr_runs(code):
        names = {attr_name(t) for t, _ in attrs}
        for text, inner in attrs:
            if inner and DEAD.search(text):
                dead.append({"file": rel, "line": line_of(start), "kind": "file", "name": None, "pub": False})
        item = ITEM.match(code, end)
        if any(DEAD.search(t) for t, inner in attrs if not inner):
            m = item or FIELD.match(code, end)
            dead.append({
                "file": rel, "line": line_of(m.start(2) if m else end),
                "kind": item.group(2) if item else "field",
                "name": (item.group(3) if item else m.group(2) if m else None),
                "pub": bool(m and m.group(1)),
            })
        if not (names & TEST_ATTRS and item and item.group(2) == "fn" and item.group(3)):
            continue
        paren = code.find("(", item.end())
        args_end = close(code, paren, "(", ")") if paren >= 0 else -1
        brace = code.find("{", args_end) if args_end >= 0 else -1
        body_end = close(code, brace, "{", "}") if brace >= 0 else -1
        if body_end < 0:
            broken = True
            continue
        body, body_noc = code[brace + 1:body_end - 1], noc[brace + 1:body_end - 1]
        lead = src.rfind("\n", 0, start) + 1
        while lead:  # comment lines directly above the attributes belong to the test
            prev = src.rfind("\n", 0, lead - 1) + 1
            if not com[prev:lead].strip() or code[prev:lead].strip():
                break
            lead = prev
        labels = set()
        asserts = len(ASSERT.findall(body))
        if re.search(r"\bassert_\w*snapshot!", body):
            labels.add("snapshot")
        if " in " in code[paren:args_end] or "prop_assert" in body or "quickcheck" in names:
            labels.add("proptest")
        labels |= names & {"ignore", "should_panic"}
        if not asserts and not labels & {"should_panic"}:
            labels.add("no-assert")
        if re.search(r"\.is_ok\s*\(\s*\)", body):
            labels.add("is_ok")
        if re.search(r"\.is_err\s*\(\s*\)", body):
            labels.add("is_err")
        if re.search(r"\blet\s+_\s*=", body):
            labels.add("let_")
        if re.search(r"\bsleep\s*\(", body):
            labels.add("sleep")
        for m in PLAIN_ASSERT.finditer(body):
            stop = close(body, m.end() - 1, "(", ")")
            if stop > 0 and BOUND.search(body[m.end():stop - 1]):
                labels.add("bound")
        if CITES.search(item.group(3).replace("_", " ")) or CITES.search(com[lead:body_end]):
            labels.add("cites-issue")
        norm = re.sub(r"\s+", " ", body_noc).strip()
        lines = [ln.strip() for ln in body_noc.splitlines() if ln.strip()]
        tests.append({
            "file": rel, "line": line_of(item.start(2)), "name": item.group(3),
            "asserts": asserts, "lines": line_of(body_end - 1) - line_of(start) + 1,
            "labels": labels,
            "hash": hashlib.sha1(norm.encode()).hexdigest()[:8] if norm else "",
            "setup": tuple(lines[:3]) if len(lines) > 3 else None,
        })
    return code, tests, dead, broken


def rust_files(root):
    out = []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        out += [Path(base) / f for f in sorted(files) if f.endswith(".rs")]
    return out


def scan(root):
    root = Path(root)
    if not root.is_dir():
        die(f"{root} is not a directory; pass the crate or workspace root")
    files = rust_files(root)
    if not files:
        die(f"no .rs files under {root}; pass the crate or workspace root")
    codes, tests, dead, broken, binaries = [], [], [], [], 0
    for f in files:
        rel = f.relative_to(root).as_posix()
        code, t, d, bad = scan_file(f, rel)
        codes.append(code)
        tests += t
        dead += d
        if bad:
            broken.append(rel)
        if f.parent.name == "tests" and (f.parent.parent == root or (f.parent.parent / "Cargo.toml").exists()):
            binaries += 1
    key = lambda t: (t["file"], t["line"])  # noqa: E731
    tests.sort(key=key)
    by_hash, by_setup = defaultdict(list), defaultdict(list)
    for t in tests:
        if t["hash"]:
            by_hash[t["hash"]].append(t)
        if t["setup"]:
            by_setup[t["setup"]].append(t)
    dups = sorted((g for g in by_hash.values() if len(g) > 1), key=lambda g: key(g[0]))
    setups = sorted((g for g in by_setup.values() if len(g) >= 3 and len({t["hash"] for t in g}) > 1),
                    key=lambda g: (-len(g), key(g[0])))
    blob = "\n".join(codes)
    for d in dead:
        d["refs"] = len(re.findall(rf"\b{re.escape(d['name'])}\b", blob)) - 1 if d["name"] else None
    dead.sort(key=key)
    return {"files": len(files), "integration_binaries": binaries, "tests": tests, "identical_bodies": dups,
            "same_first_lines": setups, "dead_code": dead, "unparsed": sorted(broken)}


def where(t):
    return f"{t['file']}:{t['line']} {t['name']}"


def cmd_scan(args):
    r = scan(args.path)
    tests = r["tests"]
    if args.json:
        json.dump({
            **r,
            "tests": [{k: (sorted(v) if k == "labels" else v) for k, v in t.items() if k != "setup"} for t in tests],
            "identical_bodies": [[where(t) for t in g] for g in r["identical_bodies"]],
            "same_first_lines": [[where(t) for t in g] for g in r["same_first_lines"]],
        }, sys.stdout, indent=2)
        print()
        return 0
    counts = Counter(lb for t in tests for lb in t["labels"])
    print(f"{len(tests)} tests in {r['files']} .rs files; {r['integration_binaries']} integration binaries (tests/*.rs); "
          f"{sum(t['asserts'] for t in tests)} assert macros")
    print("labels: " + (", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "none"))
    rows = tests if args.all else [t for t in tests if t["labels"]]
    shown = rows if args.all else rows[:MAX_ROWS]
    if shown:
        print(f"\n{'tests' if args.all else 'tests with a label'} (line name: asserts, body lines, labels):")
        current = None
        for t in shown:
            if t["file"] != current:
                current = t["file"]
                print(f"  {current}")
            print(f"    {t['line']} {t['name']}: {t['asserts']}, {t['lines']}, {' '.join(sorted(t['labels']))}".rstrip(" ,"))
        if len(rows) > len(shown):
            print(f"  ... and {len(rows) - len(shown)} more (--all)")
    for title, groups, sep in (("identical bodies", r["identical_bodies"], "  ==  "),
                               ("same first 3 lines", r["same_first_lines"], ", ")):
        if not groups:
            continue
        print(f"\n{title}:")
        cap = len(groups) if args.all else MAX_GROUPS
        for g in groups[:cap]:
            names = [where(t) for t in (g if args.all else g[:MAX_NAMES])]
            more = f" and {len(g) - len(names)} more" if len(g) > len(names) else ""
            print(f"  - {len(g)} tests: {sep.join(names)}{more}")
        if len(groups) > cap:
            print(f"  ... and {len(groups) - cap} more groups (--all)")
    if r["dead_code"]:
        print("\n#[allow(dead_code)] (refs = other mentions of the name in .rs files):")
        for d in r["dead_code"]:
            what = "whole file or module" if d["kind"] == "file" else f"{'pub ' if d['pub'] else ''}{d['kind']} {d['name'] or ''}".rstrip()
            refs = "" if d["refs"] is None else f"  refs {d['refs']}"
            print(f"  {d['file']}:{d['line']} {what}{refs}")
    if r["unparsed"]:
        print(f"\nunbalanced braces, tests not listed: {', '.join(r['unparsed'])}")
    return 0


def load_junit(path):
    try:
        root = ET.parse(path).getroot()
    except OSError as e:
        die(f"cannot read {path}: {e.strerror}")
    except ET.ParseError as e:
        die(f"{path} is not a JUnit XML report: {e}")
    rows = {}
    for case in root.iter("testcase"):
        try:
            seconds = float(case.get("time") or 0)
        except ValueError:
            die(f"{path}: testcase {case.get('name')!r} has time {case.get('time')!r}, not a number")
        rows[f"{case.get('classname', '')} {case.get('name', '')}"] = seconds
    wall = root.get("time") if root.tag == "testsuites" else None
    try:
        wall = float(wall) if wall else None
    except ValueError:
        wall = None
    return rows, wall


def load_mutants(path):
    root = Path(path)
    if not (root / "outcomes.json").exists() and (root / "mutants.out" / "outcomes.json").exists():
        root = root / "mutants.out"
    try:
        data = json.loads((root / "outcomes.json").read_text())
        outcomes = data["outcomes"]
    except OSError as e:
        die(f"cannot read {root / 'outcomes.json'}: {e.strerror}")
    except (ValueError, KeyError, TypeError):
        die(f"{root / 'outcomes.json'} is not a cargo-mutants outcomes file")
    return Counter(o.get("summary") for o in outcomes
                   if isinstance(o, dict) and isinstance(o.get("scenario"), dict) and "Mutant" in o["scenario"])


def resolve(spec, rows):
    hits = [k for k in rows if k == spec or k.split(" ", 1)[-1] == spec]
    if not hits:
        die(f"unknown test: {spec} (use a name from the JUnit report)")
    if len(hits) > 1:
        die(f"{spec} matches {len(hits)} tests; use \"<binary-id> <test name>\": {', '.join(sorted(hits))}")
    return hits[0]


def source_lines(key, tests):
    """Body lines of the one source test that matches a JUnit key, else None."""
    binary, name = key.split(" ", 1)
    hits = [t for t in tests if t["name"] == name.split("::")[-1]]
    if len(hits) > 1:
        in_tests = lambda t: Path(t["file"]).parent.name == "tests"  # noqa: E731
        stem = binary.split("::")[-1]
        hits = ([t for t in hits if in_tests(t) and Path(t["file"]).stem == stem] if "::" in binary
                else [t for t in hits if not in_tests(t)])
    return hits[0] if len(hits) == 1 else None


def cmd_totals(args):
    rows, wall = load_junit(args.junit)
    summed = sum(rows.values())
    line = f"baseline: {len(rows)} tests, {summed:.3f}s summed test time"
    if wall is not None:
        line += f", {wall:.3f}s wall time"
    tested = None
    if args.mutants_out:
        c = load_mutants(args.mutants_out)
        tested = c["CaughtMutant"] + c["MissedMutant"] + c["Timeout"]
        line += (f"; mutants {c['CaughtMutant']}/{tested} caught ({c['MissedMutant']} missed, "
                 f"{c['Timeout']} timeout; {c['Unviable']} unviable not counted)")
    print(line)

    items, seen = [], {}
    for spec in args.remove:
        items.append((resolve(spec, rows), "remove", None))
    for spec in args.shorten:
        name, sep, secs = spec.rpartition("=")
        try:
            saved = float(secs)
        except ValueError:
            saved = -1
        if not sep or saved < 0:
            die(f"--shorten takes TEST=SECONDS, got {spec}")
        key = resolve(name, rows)
        if saved > rows[key] + 1e-9:
            die(f"--shorten {name}={secs}: the test takes only {rows[key]:.3f}s")
        items.append((key, "shorten", saved))
    for spec in args.merge:
        items.append((resolve(spec, rows), "merge", 0.0))
    for key, action, _ in items:
        if seen.setdefault(key, action) != action or [k for k, _, _ in items].count(key) > 1:
            die(f"{key} is named more than once")
    if not items:
        return 0

    root = Path(args.root)
    tests = scan(root)["tests"] if root.is_dir() and rust_files(root) else []
    out, lines_removed, unknown = [], 0, 0
    for key, action, saved in items:
        saved = rows[key] if saved is None else saved
        src = source_lines(key, tests)
        if action == "remove":
            if src:
                lines_removed += src["lines"]
            else:
                unknown += 1
        out.append((-saved, key, action, saved, src))
    out.sort(key=lambda r: r[:2])
    width = max(len(r[1]) for r in out)
    mut_head = "  s/mutation run" if tested is not None else ""
    print(f"\n{'test':<{width}}  action   s/run{mut_head}  lines  source")
    for _, key, action, saved, src in out:
        mut = f"  {saved * tested:14.1f}" if tested is not None else ""
        print(f"{key:<{width}}  {action:<7} {saved:6.3f}{mut}  {src['lines'] if src else '?':>5}  "
              f"{src['file'] + ':' + str(src['line']) if src else '?'}")
    n = Counter(action for _, action, _ in items)
    total = sum(r[3] for r in out)
    share = f" ({total / summed * 100:.0f}% of summed test time)" if summed else ""
    line = f"\ntotals: {n['remove']} removed, {n['shorten']} shortened, {n['merge']} merged; {total:.3f}s saved per run{share}"
    if tested is not None:
        line += f"; {total * tested:.1f}s per mutation run ({tested} mutants tested)"
    line += f"; {lines_removed} lines in removed tests"
    if unknown:
        line += f" ({unknown} not found in the source, count by hand)"
    print(line)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="static facts about the tests and dead-code markers")
    s.add_argument("path", nargs="?", default=".")
    s.add_argument("--all", action="store_true", help="list every test and every group")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_scan)
    t = sub.add_parser("totals", help="baseline line and savings for the report")
    t.add_argument("junit")
    t.add_argument("--mutants-out")
    t.add_argument("--root", default=".", help="crate root, to count the lines of removed tests")
    t.add_argument("--remove", nargs="+", default=[], metavar="TEST")
    t.add_argument("--shorten", nargs="+", default=[], metavar="TEST=SECONDS")
    t.add_argument("--merge", nargs="+", default=[], metavar="TEST")
    t.set_defaults(func=cmd_totals)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
