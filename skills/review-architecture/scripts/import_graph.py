#!/usr/bin/env python3
"""Internal import graph for a Python or JS/TS source tree.

Prints, for the modules under ROOT: fan-in and fan-out per module (internal
edges only), external imports per module, line counts, import cycles
(strongly connected components), and hub modules imported by more than 70%
of the other modules. Standard library only; reads files, writes nothing.

Usage:
  python3 import_graph.py ROOT [--include-tests] [--json]

Edges marked "deferred" are imports inside a function body or an
`if TYPE_CHECKING:` block. They still couple the modules, but a cycle made
only of deferred edges will not fail at import time.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
    ".mypy_cache", ".pytest_cache", ".tox", ".next", "coverage", ".cache",
}
PY_EXT = {".py"}
JS_EXT = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]
HUB_SHARE = 0.70  # checklist.md: no module imported by more than 70% of the codebase


def is_test(path: Path) -> bool:
    name = path.name
    if any(part in {"tests", "test", "__tests__", "spec"} for part in path.parts[:-1]):
        return True
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or name == "conftest.py"
        or re.search(r"\.(test|spec)\.[cm]?[jt]sx?$", name) is not None
    )


def collect(root: Path, include_tests: bool) -> tuple[list[Path], int]:
    files, skipped_tests = [], 0
    for p in sorted(root.rglob("*")):
        if not p.is_file() or any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if p.suffix not in PY_EXT and p.suffix not in JS_EXT:
            continue
        if p.name.endswith(".d.ts"):
            continue
        if not include_tests and is_test(p.relative_to(root)):
            skipped_tests += 1
            continue
        files.append(p)
    return files, skipped_tests


# ---------------------------------------------------------------- Python ----

def py_name(rel: Path) -> str:
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) or "__init__"


def py_imports(path: Path):
    """Yield (node, deferred) for every import statement in the file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        print(f"warning: cannot parse {path}: {exc}", file=sys.stderr)
        return
    deferred_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            deferred_nodes.update(id(n) for n in ast.walk(node) if n is not node)
        if isinstance(node, ast.If) and "TYPE_CHECKING" in ast.unparse(node.test):
            for stmt in node.body:
                deferred_nodes.update(id(n) for n in ast.walk(stmt))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node, id(node) in deferred_nodes


def lookup(dotted: str, names: dict[str, Path], absolute: bool) -> str | None:
    """Match a dotted name to an internal module. Absolute imports may carry
    leading package components above ROOT (`from pkg.mod import x` when ROOT
    is pkg/), so try each suffix."""
    if not dotted:
        return None
    parts = dotted.split(".")
    options = [".".join(parts[i:]) for i in range(len(parts))] if absolute else [dotted]
    return next((o for o in options if o in names), None)


def resolve_py(node, here: str, is_pkg: bool, names: dict[str, Path]):
    """Return (internal hits, external top-level names) for one import node."""
    hits, ext = set(), set()
    if isinstance(node, ast.Import):
        for a in node.names:
            h = lookup(a.name, names, True)
            (hits.add(h) if h else ext.add(a.name.split(".")[0]))
        return hits, ext
    if node.level:
        pkg = [] if here == "__init__" else (here.split(".") if is_pkg else here.split(".")[:-1])
        pkg = pkg[: len(pkg) - (node.level - 1)] if node.level > 1 else pkg
        base = ".".join([*pkg, *( [node.module] if node.module else [] )])
        absolute = False
    else:
        base, absolute = node.module or "", True
    for a in node.names:
        sub = f"{base}.{a.name}" if base else a.name
        h = lookup(sub, names, absolute) or lookup(base, names, absolute)
        if not h and not base and node.level:
            h = "__init__" if "__init__" in names else None
        if h:
            hits.add(h)
        elif not node.level:
            ext.add(base.split(".")[0])
    return hits, ext


# ------------------------------------------------------------------- JS ----

JS_RE = re.compile(
    r"""(?:import\s[^'"]*?from\s*|import\s*\(?\s*|export\s[^'"]*?from\s*|require\s*\(\s*)['"]([^'"]+)['"]""",
    re.S,
)


def resolve_js(spec: str, src: Path, root: Path) -> Path | None:
    base = (src.parent / spec).resolve()
    cands = [base] + [Path(str(base) + e) for e in JS_EXT] + [base / f"index{e}" for e in JS_EXT]
    if base.suffix in {".js", ".jsx", ".mjs", ".cjs"}:  # TS sources imported as .js
        cands += [base.with_suffix(e) for e in (".ts", ".tsx")]
    for c in cands:
        if c.is_file():
            try:
                c.relative_to(root)
            except ValueError:
                return None
            return c
    return None


# ----------------------------------------------------------------- graph ----

def sccs(nodes, edges):
    index, low, stack, on, out, i = {}, {}, [], set(), [], [0]

    def strong(v):
        index[v] = low[v] = i[0]
        i[0] += 1
        stack.append(v)
        on.add(v)
        for w in edges.get(v, ()):
            if w not in index:
                strong(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1 or v in edges.get(v, ()):
                out.append(sorted(comp))

    sys.setrecursionlimit(max(10000, 4 * len(nodes)))
    for v in nodes:
        if v not in index:
            strong(v)
    return out


def build(root: Path, include_tests: bool) -> dict:
    files, skipped = collect(root, include_tests)
    py = {py_name(p.relative_to(root)): p for p in files if p.suffix in PY_EXT}
    js = {str(p.relative_to(root)): p for p in files if p.suffix in JS_EXT}
    nodes = sorted(py) + sorted(js)
    edges: dict[str, dict[str, dict]] = {n: {} for n in nodes}
    external: dict[str, set[str]] = {n: set() for n in nodes}
    loc = {}

    for name, path in py.items():
        loc[name] = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        is_pkg = path.name == "__init__.py"
        for node, deferred in py_imports(path):
            hits, ext = resolve_py(node, name, is_pkg, py)
            external[name] |= ext
            for h in hits - {name}:
                e = edges[name].setdefault(h, {"lines": [], "deferred": True})
                e["lines"].append(node.lineno)
                e["deferred"] = e["deferred"] and deferred

    for name, path in js.items():
        text = path.read_text(encoding="utf-8", errors="replace")
        loc[name] = len(text.splitlines())
        for m in JS_RE.finditer(text):
            spec = m.group(1)
            line = text.count("\n", 0, m.start()) + 1
            if not spec.startswith("."):
                external[name].add(spec.split("/")[0] if not spec.startswith("@") else "/".join(spec.split("/")[:2]))
                continue
            target = resolve_js(spec, path, root.resolve())
            if target is None:
                continue
            tname = str(target.relative_to(root.resolve()))
            if tname == name or tname not in edges:
                continue
            e = edges[name].setdefault(tname, {"lines": [], "deferred": False})
            e["lines"].append(line)

    fan_in = {n: 0 for n in nodes}
    for src, outs in edges.items():
        for dst in outs:
            fan_in[dst] += 1
    others = max(len(nodes) - 1, 1)
    hubs = [n for n in nodes if len(nodes) >= 5 and fan_in[n] / others > HUB_SHARE]
    plain = {s: set(d) for s, d in edges.items()}
    eager = {s: {d for d, e in outs.items() if not e["deferred"]} for s, outs in edges.items()}
    return {
        "root": str(root),
        "modules": len(nodes),
        "tests_excluded": skipped,
        "nodes": [
            {
                "module": n,
                "loc": loc.get(n, 0),
                "fan_in": fan_in[n],
                "fan_out": len(edges[n]),
                "imports": {d: e["lines"] for d, e in sorted(edges[n].items())},
                "deferred_imports": sorted(d for d, e in edges[n].items() if e["deferred"]),
                "imported_by": sorted(s for s in nodes if n in edges[s]),
                "external": sorted(external[n]),
            }
            for n in nodes
        ],
        "cycles": sccs(nodes, plain),
        "import_time_cycles": sccs(nodes, eager),
        "hubs_over_70pct": hubs,
    }


def render(g: dict) -> str:
    out = [
        f"root: {g['root']}",
        f"modules: {g['modules']}  (tests excluded: {g['tests_excluded']})",
        "",
        f"{'module':<40} {'loc':>5} {'in':>3} {'out':>3}  imports (module:lines)",
    ]
    for n in sorted(g["nodes"], key=lambda x: (-x["fan_in"], x["module"])):
        imps = ", ".join(
            f"{d}:{','.join(map(str, ls))}" + ("*" if d in n["deferred_imports"] else "")
            for d, ls in n["imports"].items()
        )
        out.append(f"{n['module']:<40} {n['loc']:>5} {n['fan_in']:>3} {n['fan_out']:>3}  {imps or '-'}")
    out += ["", "(* = deferred: inside a function or TYPE_CHECKING block)", ""]
    out.append("cycles: " + ("; ".join(" <-> ".join(c) for c in g["cycles"]) or "none"))
    out.append("import-time cycles: " + ("; ".join(" <-> ".join(c) for c in g["import_time_cycles"]) or "none"))
    out.append("hubs (fan-in > 70% of modules): " + (", ".join(g["hubs_over_70pct"]) or "none"))
    big = [f"{n['module']} ({n['loc']})" for n in g["nodes"] if n["loc"] > 500]
    out.append("files over 500 lines: " + (", ".join(big) or "none"))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", type=Path)
    ap.add_argument("--include-tests", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not a.root.is_dir():
        print(f"error: {a.root} is not a directory", file=sys.stderr)
        return 2
    g = build(a.root, a.include_tests)
    print(json.dumps(g, indent=1) if a.json else render(g))
    return 0


if __name__ == "__main__":
    sys.exit(main())
