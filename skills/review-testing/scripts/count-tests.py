#!/usr/bin/env python3
"""Count the tests under a target, per runner, level, and directory (stdlib only).

Usage:
    python3 count-tests.py <target> [--top N] [--all] [--no-collect] [--json]

For pytest and Go the count comes from the native collector when the toolchain
is installed (`pytest --collect-only -q`, `go test -list`), because a collector
sees parametrized cases. Both collectors import or compile the test code but
run no test; pytest runs without its cache and Go runs offline. Every other
runner, and any collector that is missing or fails, gets a pattern count of
test declarations, and the runner line says so. --no-collect forces the
pattern count everywhere.

The level (unit, integration, e2e) is a first guess from directory and file
names; "unlabelled" means the path does not say. Reads files, writes nothing.
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "env", "dist", "build", "out",
             "target", "_build", "deps", "bin", "obj", "vendor", "third_party", "coverage",
             ".next", ".tox", ".mypy_cache", ".pytest_cache"}
MAX_BYTES = 1_000_000
TIMEOUT = 120
JS_EXT = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")


def _js_test_file(rel, name):
    stem = name.rsplit(".", 1)[0]
    return name.endswith(JS_EXT) and (stem.endswith((".test", ".spec", ".cy", ".e2e")) or "__tests__/" in rel)


# runner: (is this a test file?, pattern for one test declaration)
RUNNERS = {
    "pytest": (lambda rel, name: name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py")),
               re.compile(r"^[ \t]*(?:async[ \t]+)?def[ \t]+test\w*[ \t]*\(", re.M)),
    "go test": (lambda rel, name: name.endswith("_test.go"),
                re.compile(r"^func[ \t]+(?:Test|Fuzz)\w*[ \t]*\(", re.M)),
    "js": (_js_test_file,
           re.compile(r"(?<![\w.$])(?:it|test)(?:\.(?:only|concurrent|each))?[ \t]*\(")),
    "dotnet test": (lambda rel, name: name.endswith(".cs"),
                    re.compile(r"^[ \t]*\[(?:Fact|Theory|Test|TestMethod|TestCase)\b", re.M)),
    "junit": (lambda rel, name: name.endswith((".java", ".kt")),
              re.compile(r"^[ \t]*@(?:Test|ParameterizedTest|RepeatedTest)\b", re.M)),
    "cargo test": (lambda rel, name: name.endswith(".rs"),
                   re.compile(r"^[ \t]*#\[(?:\w+::)*test\b", re.M)),
    "exunit": (lambda rel, name: name.endswith("_test.exs"),
               re.compile(r"^[ \t]*test[ \t]+\"", re.M)),
    "ruby": (lambda rel, name: name.endswith(("_spec.rb", "_test.rb")),
             re.compile(r"^[ \t]*(?:(?:it|specify|test)[ \t]+['\"(]|def[ \t]+test_)", re.M)),
    "phpunit": (lambda rel, name: name.endswith("Test.php"),
                re.compile(r"^[ \t]*(?:public[ \t]+)?function[ \t]+test\w*[ \t]*\(|^[ \t]*#\[Test\]", re.M)),
    "bats": (lambda rel, name: name.endswith(".bats"),
             re.compile(r"^@test[ \t]", re.M)),
    "gherkin": (lambda rel, name: name.endswith(".feature"),
                re.compile(r"^[ \t]*(?:Scenario|Scenario Outline|Scenario Template|Example):", re.M)),
}
LEVELS = (
    ("e2e", {"e2e", "end2end", "endtoend", "acceptance", "functional", "smoke", "browser",
             "playwright", "cypress", "cy", "selenium", "feature", "features"}),
    ("integration", {"integration", "integ", "contract"}),
    ("unit", {"unit", "units"}),
)


def guess_level(rel):
    tokens = set(re.split(r"[^a-z0-9]+", re.sub(r"end[_-]to[_-]end", "endtoend", rel.lower())))
    for level, words in LEVELS:
        if tokens & words:
            return level
    return "unlabelled"


def walk(root):
    if os.path.isfile(root):
        yield root, os.path.basename(root)
        return
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not x.startswith("."))
        for f in sorted(files):
            full = os.path.join(d, f)
            yield full, os.path.relpath(full, root).replace(os.sep, "/")


def pattern_counts(root):
    """{runner: {rel: declarations}} for every test file that has at least one."""
    found = {}
    for full, rel in walk(root):
        name = os.path.basename(rel)
        for runner, (is_test, rx) in RUNNERS.items():
            if not is_test(rel, name):
                continue
            try:
                if os.path.getsize(full) > MAX_BYTES:
                    break
                with open(full, encoding="utf-8", errors="replace") as fh:
                    n = len(rx.findall(fh.read()))
            except OSError:
                break
            if n:
                found.setdefault(runner, {})[rel] = n
            break
    return found


def _run(cmd, cwd, env):
    try:
        p = subprocess.run(cmd, cwd=cwd, env={**os.environ, **env}, capture_output=True, text=True,
                           timeout=TIMEOUT, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return None, f"collector timed out after {TIMEOUT}s"
    except OSError as e:
        return None, f"collector did not start: {e.strerror}"
    return p, None


def _pytest_command(cwd):
    venv = os.path.join(cwd, ".venv", "bin", "python")
    if os.path.exists(os.path.join(cwd, ".venv", "bin", "pytest")):
        return [venv, "-m", "pytest"]
    if shutil.which("pytest"):
        return ["pytest"]
    if importlib.util.find_spec("pytest"):
        return [sys.executable, "-m", "pytest"]
    return None


def collect_pytest(root):
    """({rel: collected tests}, None) or (None, reason the collector was not used)."""
    is_file = os.path.isfile(root)
    cwd = os.path.dirname(os.path.abspath(root)) if is_file else os.path.abspath(root)
    cmd = _pytest_command(cwd)
    if not cmd:
        return None, "pytest not installed"
    args = ["--collect-only", "-q", "-p", "no:cacheprovider"] + ([os.path.basename(root)] if is_file else [])
    p, err = _run(cmd + args, cwd, {"PYTHONDONTWRITEBYTECODE": "1"})
    if err:
        return None, err
    if p.returncode != 0:
        return None, f"collector exit {p.returncode}"
    counts, base = {}, None
    for line in p.stdout.splitlines():
        path, sep, _ = line.partition("::")
        if not sep or " " in path:
            continue
        if base is None:  # node ids are relative to pytest's rootdir, which can be above the target
            base = next((b for b in _ancestors(cwd) if os.path.exists(os.path.join(b, path))), cwd)
        rel = os.path.relpath(os.path.join(base, path), cwd).replace(os.sep, "/")
        rel = os.path.basename(rel) if is_file else rel
        counts[rel] = counts.get(rel, 0) + 1
    return (counts, None) if counts else (None, "collector listed no tests")


def _ancestors(path):
    while True:
        yield path
        parent = os.path.dirname(path)
        if parent == path:
            return
        path = parent


def collect_go(root):
    """(total tests, None) or (None, reason). Offline: modules are never downloaded."""
    if os.path.isfile(root):
        return None, "target is one file"
    if not shutil.which("go"):
        return None, "go not installed"
    p, err = _run(["go", "test", "-list", "^(Test|Fuzz)", "./..."], os.path.abspath(root),
                  {"GOPROXY": "off", "GOFLAGS": "-mod=readonly"})
    if err:
        return None, err
    if p.returncode != 0:
        return None, f"collector exit {p.returncode}"
    return len(re.findall(r"^(?:Test|Fuzz)\w*$", p.stdout, re.M)), None


def count(root, use_collectors=True):
    found = pattern_counts(root)
    runners = []
    for name in sorted(found):
        files = found[name]
        row = {"runner": name, "tests": sum(files.values()), "source": "pattern",
               "note": "no read-only collector", "files": files}
        if name in ("pytest", "go test"):
            row["note"] = "--no-collect"
        if name == "gherkin":
            row["note"] = "scenarios; a runner that executes them may count them again"
        if use_collectors and name == "pytest":
            counts, why = collect_pytest(root)
            if counts is None:
                row["note"] = why
            else:
                row.update(tests=sum(counts.values()), source="collector",
                           note="pytest --collect-only -q", files=counts)
        elif use_collectors and name == "go test":
            total, why = collect_go(root)
            if total is None:
                row["note"] = why
            else:
                note = "go test -list"
                if total != row["tests"]:
                    note += f"; level and directory rows use the pattern count, {row['tests']}"
                row.update(tests=total, source="collector", note=note)
        runners.append(row)
    levels, dirs = {}, {}
    for row in runners:
        for rel, n in row["files"].items():
            level = guess_level(rel)
            levels[level] = levels.get(level, 0) + n
            key = (os.path.dirname(rel) or ".", row["runner"], level)
            entry = dirs.setdefault(key, [0, 0])
            entry[0] += n
            entry[1] += 1
    return {
        "tests": sum(r["tests"] for r in runners),
        "files": sum(len(r["files"]) for r in runners),
        "runners": [{k: v for k, v in r.items() if k != "files"} | {"files": len(r["files"])} for r in runners],
        "levels": levels,
        "directories": [{"dir": d, "runner": r, "level": lv, "tests": n, "files": f}
                        for (d, r, lv), (n, f) in sorted(dirs.items(), key=lambda kv: (-kv[1][0], kv[0]))],
    }


def print_text(res, cap):
    print(f"tests={res['tests']} test_files={res['files']} runners={len(res['runners'])}")
    if not res["runners"]:
        print("no test declarations found (searched pytest, go, js/ts, dotnet, junit, cargo, exunit, "
              "ruby, phpunit, bats, gherkin patterns)")
        return
    print("\n## By runner (tests, files, runner, source)")
    for r in res["runners"]:
        print(f"  {r['tests']:>5} {r['files']:>4}  {r['runner']:<12} {r['source']} ({r['note']})")
    if any(r["source"] == "pattern" for r in res["runners"]):
        print("  pattern = declarations counted in test files; parametrized cases count once")
    print("\n## By level (guess from path names)")
    print("  " + "  ".join(f"{k}={res['levels'][k]}" for k in ("unit", "integration", "e2e", "unlabelled")
                           if k in res["levels"]))
    rows = res["directories"]
    shown = rows if cap is None else rows[:cap]
    print("\n## By directory (tests, files, level, runner, directory)")
    for d in shown:
        print(f"  {d['tests']:>5} {d['files']:>4}  {d['level']:<11} {d['runner']:<12} {d['dir']}")
    if len(rows) > len(shown):
        rest = rows[len(shown):]
        print(f"  ... and {len(rest)} more directories with {sum(d['tests'] for d in rest)} tests (--all lists them)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("target")
    ap.add_argument("--top", type=int, default=10, help="directory rows to print (default 10)")
    ap.add_argument("--all", action="store_true", help="print every directory row")
    ap.add_argument("--no-collect", action="store_true", help="never run a collector; pattern counts only")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.exists(a.target):
        print(f"error: path not found: {a.target}", file=sys.stderr)
        return 2
    res = count(a.target, use_collectors=not a.no_collect)
    if a.json:
        json.dump(res, sys.stdout, indent=1)
        print()
    else:
        print_text(res, None if a.all else a.top)
    return 0


if __name__ == "__main__":
    sys.exit(main())
