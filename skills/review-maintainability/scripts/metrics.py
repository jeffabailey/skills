#!/usr/bin/env python3
"""Maintainability metrics for review-maintainability (stdlib only).

Usage:
    python3 metrics.py <path> [<path> ...] [--top N] [--json] [--include-vendored] [--exclude GLOB ...]

Per function: LOC, cyclomatic complexity (CC), max nesting depth, parameter
count, with file:line. Per file: LOC. Also lists TODO/FIXME/HACK/XXX markers
and lint/type suppressions with file:line.

Method by language:
  - Python: ast (exact). Files that do not parse fall back to indentation.
  - Brace languages (JS/TS/Java/C#/Go/C/C++/Rust/Kotlin/Swift/PHP/Scala):
    brace matching with strings and comments skipped. CC counts branch
    keywords and && / || / ?. Nesting counts brace depth inside the function,
    so object literals can inflate it; treat brace results as approximate.
  - Other files: file LOC and markers only.

Thresholds come from references/rubric.md (the single threshold table).
Rows over the finding threshold are marked with '!'.
"""
import argparse
import ast
import fnmatch
import json
import os
import re
import sys

# Finding thresholds: keep in sync with references/rubric.md "Threshold table".
FINDING = {"loc": 50, "cc": 15, "nest": 4, "params": 5, "class_loc": 500, "file_loc": 1000}

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "env", "dist", "build",
             "out", "target", ".next", ".tox", ".mypy_cache", ".pytest_cache", "coverage"}
VENDOR_DIRS = {"vendor", "vendored", "third_party", "third-party", "external", "deps"}
BRACE_EXT = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".java", ".cs", ".go", ".c", ".h",
             ".cc", ".cpp", ".hpp", ".rs", ".kt", ".kts", ".swift", ".php", ".scala", ".dart"}
OTHER_EXT = {".rb", ".sh", ".bash", ".zsh", ".lua", ".ex", ".exs", ".pl", ".r", ".jl", ".vue", ".svelte"}
GENERATED_RE = re.compile(r"\.(min|bundle|generated|pb)\.|_pb2\.py$|\.d\.ts$")

MARKER_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
SUPPRESS_RE = re.compile(
    r"(#\s*noqa|#\s*type:\s*ignore|pylint:\s*disable|eslint-disable|@ts-ignore|@ts-expect-error|"
    r"@ts-nocheck|//\s*nolint|#\[allow\(|@SuppressWarnings|rubocop:disable|shellcheck\s+disable|"
    r"NOSONAR|istanbul\s+ignore|c8\s+ignore|pragma:\s*no\s*cover|#\s*nosec)")


# ---------------------------------------------------------------- Python (AST)
class _PyVisitor(ast.NodeVisitor):
    NEST = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.AsyncWith)
    BRANCH = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp,
              ast.comprehension, ast.Assert)

    def __init__(self, rel):
        self.rel, self.funcs, self.classes = rel, [], []

    def _nest(self, node, d=0):
        best = d
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            step = 1 if isinstance(child, self.NEST) or type(child).__name__ in ("TryStar", "Match") else 0
            best = max(best, self._nest(child, d + step))
        return best

    def _cc(self, node):
        cc = 1
        stack = list(ast.iter_child_nodes(node))
        while stack:
            n = stack.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue  # nested defs are measured on their own
            if isinstance(n, self.BRANCH):
                cc += 1
            elif isinstance(n, ast.BoolOp):
                cc += len(n.values) - 1
            elif type(n).__name__ == "match_case":
                cc += 1
            stack.extend(ast.iter_child_nodes(n))
        return cc

    def _func(self, node):
        a = node.args
        params = [p.arg for p in a.posonlyargs + a.args + a.kwonlyargs]
        if params and params[0] in ("self", "cls"):
            params = params[1:]
        params += [x.arg for x in (a.vararg, a.kwarg) if x]
        self.funcs.append({"loc": node.end_lineno - node.lineno + 1, "cc": self._cc(node),
                           "nest": self._nest(node), "params": len(params),
                           "where": f"{self.rel}:{node.lineno}", "name": node.name})
        self.generic_visit(node)

    visit_FunctionDef = visit_AsyncFunctionDef = _func

    def visit_ClassDef(self, node):
        self.classes.append({"loc": node.end_lineno - node.lineno + 1,
                             "where": f"{self.rel}:{node.lineno}", "name": node.name})
        self.generic_visit(node)


def python_metrics(rel, text):
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return indent_metrics(rel, text) + ("indent (parse failed)",)
    v = _PyVisitor(rel)
    v.visit(tree)
    return v.funcs, v.classes, "ast"


def indent_metrics(rel, text):
    """Fallback for Python that does not parse: extent by indentation."""
    lines = text.split("\n")
    funcs, classes = [], []
    head = re.compile(r"^(\s*)(async\s+def|def|class)\s+(\w+)\s*(\(([^)]*)\)?)?")
    branch = re.compile(r"^\s*(if|elif|for|while|except|case)\b|\band\b|\bor\b")
    for i, line in enumerate(lines):
        m = head.match(line)
        if not m:
            continue
        ind = len(m.group(1).expandtabs())
        end, deepest = i, ind
        for j in range(i + 1, len(lines)):
            s = lines[j]
            if not s.strip() or s.lstrip().startswith("#"):
                continue
            k = len(s) - len(s.lstrip())
            if k <= ind:
                break
            end, deepest = j, max(deepest, k)
        loc = end - i + 1
        if m.group(2) == "class":
            classes.append({"loc": loc, "where": f"{rel}:{i + 1}", "name": m.group(3)})
            continue
        body = lines[i + 1:end + 1]
        cc = 1 + sum(len(branch.findall(b)) for b in body)
        params = [p for p in (m.group(5) or "").split(",") if p.strip() and p.strip() not in ("self", "cls")]
        funcs.append({"loc": loc, "cc": cc, "nest": max(0, (deepest - ind) // 4 - 1),
                      "params": len(params), "where": f"{rel}:{i + 1}", "name": m.group(3)})
    return funcs, classes


# ---------------------------------------------------------------- brace languages
def strip_code(text):
    """Blank out comments and string contents, keeping newlines and offsets."""
    out, i, n = [], 0, len(text)
    while i < n:
        c, nxt = text[i], text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt in "/*":
            close = "\n" if nxt == "/" else "*/"
            j = text.find(close, i + 2)
            j = n if j < 0 else j + (0 if nxt == "/" else 2)
            out.append(re.sub(r"[^\n]", " ", text[i:j]))
        elif c in "\"'`":
            j = _string_end(text, i, c)
            closed = j < n and text[j] == c
            out.append(c + re.sub(r"[^\n]", " ", text[i + 1:j]) + (c if closed else ""))
            j += 1 if closed else 0  # unterminated (or a regex literal): keep the newline
        else:
            out.append(c)
            j = i + 1
        i = j
    return "".join(out)


def _string_end(text, i, quote):
    j = i + 1
    while j < len(text) and text[j] != quote:
        if text[j] == "\\":
            j += 1
        elif text[j] == "\n" and quote != "`":
            break
        j += 1
    return j


def count_params(sig):
    """Top-level comma count, so a destructured {a, b} or a typed Map<K, V> is one parameter."""
    if not sig.strip():
        return 0
    depth, count = 0, 1
    for ch in sig:
        if ch in "{[(<":
            depth += 1
        elif ch in "}])>":
            depth -= 1
        elif ch == "," and depth == 0:
            count += 1
    return count - (1 if sig.rstrip().endswith(",") else 0)


FUNC_RES = [
    re.compile(r"\b(?:async\s+)?function\s*\*?\s*(\w*)\s*\(([^)]*)\)"),               # JS function
    re.compile(r"\b(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>\s*\{"),  # JS arrow
    re.compile(r"\b(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(\w+)\s*=>\s*\{"),       # x => {
    re.compile(r"()(?:\basync\s*)?\(([^()]*)\)\s*=>\s*\{"),                                 # anonymous / IIFE arrow
    re.compile(r"\bfunc\s+(?:\([^)]*\)\s*)?(\w+)\s*\(([^)]*)\)"),                       # Go
    re.compile(r"\bfn\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)"),                            # Rust
    re.compile(r"\bfun\s+(?:<[^>]*>\s*)?(?:\w+\.)?(\w+)\s*\(([^)]*)\)"),                 # Kotlin
    re.compile(r"^[ \t]*(?:(?:public|private|protected|static|final|override|virtual|async|"
               r"abstract|synchronized|internal|export)\s+)*[\w<>\[\],.?]+\s+(\w+)\s*\(([^)]*)\)\s*"
               r"(?:throws\s+[\w., ]+)?\{", re.M),                                       # Java/C#/C
    re.compile(r"^[ \t]*(?:(?:public|private|protected|static|async|get|set)\s+)*(\w+)\s*\(([^)]*)\)\s*(?::\s*[^{;=()]+)?\{", re.M),  # JS/TS method
]
NOT_FUNC = {"if", "for", "while", "switch", "catch", "return", "function", "with", "else", "do", "new", "typeof"}
BRACE_BRANCH = re.compile(r"\b(if|for|while|case|catch)\b|&&|\|\||\?\?|(?<![?.])\?(?![.?:])")
CLASS_RE = re.compile(r"\b(?:class|struct|interface|impl|object)\s+(\w+)[^{;]*\{")


def _block_end(code, open_idx):
    depth, deepest = 0, 0
    for k in range(open_idx, len(code)):
        ch = code[k]
        if ch == "{":
            depth += 1
            deepest = max(deepest, depth)
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return k, deepest
    return len(code) - 1, deepest


def brace_metrics(rel, text):
    code = strip_code(text)

    def line_of(idx):
        return code.count("\n", 0, idx) + 1

    funcs, classes, seen = [], [], set()
    for rx in FUNC_RES:
        for m in rx.finditer(code):
            name = m.group(1) or "<anonymous>"
            if name in NOT_FUNC:
                continue
            brace = code.find("{", m.end() - 1)
            gap = code[m.end():brace] if brace >= 0 else ""
            if brace < 0 or len(gap) > 120 or ";" in gap or "}" in gap:
                continue  # declaration only, or the brace belongs to something else
            if brace in seen:
                continue  # same function matched by another pattern
            seen.add(brace)
            start = line_of(m.start())
            end_idx, deepest = _block_end(code, brace)
            body = code[brace:end_idx + 1]
            funcs.append({"loc": line_of(end_idx) - start + 1, "cc": 1 + len(BRACE_BRANCH.findall(body)),
                          "nest": max(0, deepest - 1), "params": count_params(m.group(2) or ""),
                          "where": f"{rel}:{start}", "name": name})
    for m in CLASS_RE.finditer(code):
        brace = code.find("{", m.start())
        end_idx, _ = _block_end(code, brace)
        start = line_of(m.start())
        classes.append({"loc": line_of(end_idx) - start + 1, "where": f"{rel}:{start}", "name": m.group(1)})
    return funcs, classes, "brace (approximate)"


# ---------------------------------------------------------------- driver
def is_vendored(rel):
    parts = rel.replace("\\", "/").split("/")
    return any(p in VENDOR_DIRS for p in parts[:-1])


def iter_files(paths, include_vendored, excludes=()):
    for root in paths:
        if os.path.isfile(root):
            yield root, os.path.basename(root)
            continue
        for d, dirs, files in os.walk(root):
            dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not x.startswith("."))
            for f in sorted(files):
                full = os.path.join(d, f)
                rel = os.path.relpath(full, root)
                if any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(f, g) for g in excludes):
                    continue
                if not include_vendored and is_vendored(rel):
                    yield full, None
                    continue
                yield full, rel


def analyze(paths, include_vendored=False, excludes=()):
    res = {"files": [], "functions": [], "classes": [], "markers": [], "suppressions": [],
           "skipped_generated": [], "skipped_vendored": 0, "methods": {}}
    for full, rel in iter_files(paths, include_vendored, excludes):
        if rel is None:
            res["skipped_vendored"] += 1
            continue
        ext = os.path.splitext(full)[1].lower()
        if ext not in BRACE_EXT and ext not in OTHER_EXT and ext != ".py":
            continue
        if GENERATED_RE.search(full):
            res["skipped_generated"].append(rel)
            continue
        try:
            with open(full, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        lines = text.split("\n")
        res["files"].append({"loc": len([x for x in lines if x.strip()]), "where": rel})
        for i, line in enumerate(lines, 1):
            if MARKER_RE.search(line):
                res["markers"].append({"where": f"{rel}:{i}", "kind": MARKER_RE.search(line).group(1),
                                       "text": line.strip()[:100]})
            if SUPPRESS_RE.search(line):
                res["suppressions"].append({"where": f"{rel}:{i}", "text": line.strip()[:100]})
        if ext == ".py":
            out = python_metrics(rel, text)
        elif ext in BRACE_EXT:
            out = brace_metrics(rel, text)
        else:
            continue
        funcs, classes, method = out[0], out[1], out[-1]
        res["functions"] += funcs
        res["classes"] += classes
        res["methods"][rel] = method
    return res


def summarize(res):
    def top(rows, key):
        return max(rows, key=lambda r: r[key]) if rows else None
    f = res["functions"]
    return {
        "files": len(res["files"]), "functions": len(f),
        "total_loc": sum(x["loc"] for x in res["files"]),
        "max_function_loc": top(f, "loc"), "max_cc": top(f, "cc"), "max_nesting": top(f, "nest"),
        "max_params": top(f, "params"), "max_class_loc": top(res["classes"], "loc"),
        "max_file_loc": top(res["files"], "loc"),
        "over_threshold": {
            "loc": sum(x["loc"] > FINDING["loc"] for x in f), "cc": sum(x["cc"] > FINDING["cc"] for x in f),
            "nest": sum(x["nest"] > FINDING["nest"] for x in f),
            "params": sum(x["params"] > FINDING["params"] for x in f),
            "class_loc": sum(x["loc"] > FINDING["class_loc"] for x in res["classes"]),
            "file_loc": sum(x["loc"] > FINDING["file_loc"] for x in res["files"]),
        },
        "markers": len(res["markers"]), "suppressions": len(res["suppressions"]),
    }


def flag(v, key):
    return "!" if v > FINDING[key] else " "


def print_text(res, s, top_n):
    print(f"files={s['files']} functions={s['functions']} nonblank_loc={s['total_loc']}")
    methods = sorted(set(res["methods"].values()))
    print("method: " + ", ".join(methods) if methods else "method: none (no supported source files)")
    print(f"finding thresholds: fn LOC>{FINDING['loc']} CC>{FINDING['cc']} nest>{FINDING['nest']} "
          f"params>{FINDING['params']} class LOC>{FINDING['class_loc']} file LOC>{FINDING['file_loc']}")
    print("\n## Max values")
    for label, key, field in (("function LOC", "max_function_loc", "loc"), ("cyclomatic complexity", "max_cc", "cc"),
                              ("nesting depth", "max_nesting", "nest"), ("parameters", "max_params", "params"),
                              ("class LOC", "max_class_loc", "loc"), ("file LOC (non-blank)", "max_file_loc", "loc")):
        r = s[key]
        print(f"  {label:24} " + (f"{r[field]:>5}  {r['where']} {r.get('name', '')}" if r else "    -  (none)"))
    print("  over finding threshold: " + ", ".join(f"{k}={v}" for k, v in s["over_threshold"].items()))
    print(f"\n## Top {top_n} functions by LOC  ('!' = over finding threshold)")
    print(f"  {'LOC':>5} {'CC':>4} {'NEST':>4} {'PRM':>3}  location  name")
    for r in sorted(res["functions"], key=lambda r: (-r["loc"], r["where"]))[:top_n]:
        print(f"  {r['loc']:>5}{flag(r['loc'], 'loc')}{r['cc']:>4}{flag(r['cc'], 'cc')}"
              f"{r['nest']:>4}{flag(r['nest'], 'nest')}{r['params']:>3}{flag(r['params'], 'params')}"
              f" {r['where']}  {r['name']}")
    print(f"\n## Top {top_n} functions by CC")
    for r in sorted(res["functions"], key=lambda r: (-r["cc"], r["where"]))[:top_n]:
        print(f"  {r['cc']:>4}  {r['where']}  {r['name']}")
    if res["classes"]:
        print("\n## Largest classes")
        for r in sorted(res["classes"], key=lambda r: -r["loc"])[:top_n]:
            print(f"  {r['loc']:>5}{flag(r['loc'], 'class_loc')} {r['where']}  {r['name']}")
    print("\n## Largest files (non-blank LOC)")
    for r in sorted(res["files"], key=lambda r: -r["loc"])[:top_n]:
        print(f"  {r['loc']:>5}{flag(r['loc'], 'file_loc')} {r['where']}")
    print(f"\n## Markers TODO/FIXME/HACK/XXX: {len(res['markers'])}")
    for m in res["markers"]:
        print(f"  {m['where']}  {m['kind']}")
    print(f"\n## Suppressions: {len(res['suppressions'])}")
    for m in res["suppressions"]:
        print(f"  {m['where']}")
    if res["skipped_vendored"]:
        print(f"\n## Skipped as vendored: {res['skipped_vendored']} files (rerun with --include-vendored "
              "if vendored code is the project)")
    if res["skipped_generated"]:
        print(f"\n## Skipped as generated: {len(res['skipped_generated'])}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--include-vendored", action="store_true",
                    help="also scan vendor/, third_party/ etc. (use when vendored code is the project)")
    ap.add_argument("--exclude", action="append", default=[], metavar="GLOB",
                    help="skip paths matching GLOB (relative path or file name); repeatable")
    a = ap.parse_args(argv)
    missing = [p for p in a.paths if not os.path.exists(p)]
    if missing:
        print(f"error: path not found: {', '.join(missing)}", file=sys.stderr)
        return 2
    res = analyze(a.paths, a.include_vendored, a.exclude)
    s = summarize(res)
    if a.json:
        json.dump({"summary": s, "thresholds": FINDING, **res}, sys.stdout, indent=1)
        print()
    else:
        print_text(res, s, a.top)
    return 0


if __name__ == "__main__":
    sys.exit(main())
