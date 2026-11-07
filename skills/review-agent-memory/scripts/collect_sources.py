#!/usr/bin/env python3
"""Inventory every harness memory and instruction source for a project or workspace.

For each target path it finds what agents load (always or on demand) across
Claude Code, Codex, Gemini, Cursor, Copilot, Windsurf, Cline, and common
third-party context stores, estimates the always-loaded token cost, and checks
memories for staleness (paths they mention that no longer exist, index entries
with no file, files missing from the index).

It prints paths, sizes, and memory names/descriptions — not file bodies — so
the agent reads only the files the findings point at.

Usage:
  collect_sources.py <path> [<path> ...] [--home ~] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))

# (relative glob, harness, load) — load is "always" when the harness injects it every session
PROJECT_FILES = [
    ("CLAUDE.md", "claude", "always"),
    ("CLAUDE.local.md", "claude", "always"),
    (".claude/CLAUDE.md", "claude", "always"),
    ("AGENTS.md", "codex/opencode/cursor", "always"),
    ("AGENTS.override.md", "codex", "always"),
    ("GEMINI.md", "gemini", "always"),
    (".cursorrules", "cursor", "always"),
    (".cursor/rules/*.mdc", "cursor", "rule"),
    (".cursor/rules/*.md", "cursor", "rule"),
    (".github/copilot-instructions.md", "copilot", "always"),
    (".github/instructions/*.instructions.md", "copilot", "rule"),
    (".windsurfrules", "windsurf", "always"),
    (".windsurf/rules/*.md", "windsurf", "rule"),
    (".clinerules", "cline", "always"),
    (".clinerules/*.md", "cline", "always"),
    (".claude/settings.json", "claude", "config"),
    (".claude/settings.local.json", "claude", "config"),
    (".mcp.json", "claude", "config"),
    (".claude/skills/*/SKILL.md", "claude", "skill"),
    (".claude/agents/*.md", "claude", "subagent"),
    (".claude/commands/*.md", "claude", "command"),
    (".agents/skills/*/SKILL.md", "agents", "skill"),
]
CONTEXT_STORES = [
    ("CONTEXT.md", "session handoff"),
    (".dual-graph", "dual-graph MCP"),
    ("context-store.json", "dual-graph MCP"),
    (".codegraph", "CodeGraph index"),
    ("graphify-out", "graphify graph"),
    (".serena/memories", "Serena memories"),
    (".nwave", "nWave state"),
    ("docs/feature", "nWave feature waves"),
    (".aider.conf.yml", "aider"),
    (".continue", "continue.dev"),
    ("memory-bank", "Cline memory bank"),
    (".kiro/steering", "Kiro steering"),
]
GLOBAL_FILES = [
    (HOME / ".claude/CLAUDE.md", "claude", "always"),
    (HOME / ".claude/settings.json", "claude", "config"),
    (HOME / ".codex/AGENTS.md", "codex", "always"),
    (HOME / ".codex/config.toml", "codex", "config"),
    (HOME / ".gemini/GEMINI.md", "gemini", "always"),
    (HOME / ".config/opencode/AGENTS.md", "opencode", "always"),
]
PATHISH = re.compile(r"`([^`\s]+\.[A-Za-z0-9]{1,6}|[^`\s]*/[^`\s]+)`")


def tok(n_chars: int) -> int:
    return round(n_chars / 4)


def size(p: Path) -> int:
    try:
        return p.stat().st_size if p.is_file() else sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
    except OSError:
        return 0


def git_root(p: Path) -> Path:
    try:
        out = subprocess.run(["git", "-C", str(p), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=10)
        if out.returncode == 0:
            return Path(out.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    return p


def nested_instruction_files(root: Path) -> list[Path]:
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard",
                              "*CLAUDE.md", "*AGENTS.md", "*GEMINI.md"],
                             capture_output=True, text=True, timeout=20)
        files = [root / line for line in out.stdout.splitlines() if "/" in line]
    except (OSError, subprocess.TimeoutExpired):
        files = []
    return [f for f in files if "node_modules" not in f.parts and ".agents" not in f.parts][:200]


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            if v.strip():
                out[k.strip()] = v.strip().strip("\"'")
    return out


def hooks_summary(settings: Path) -> list[str]:
    try:
        data = json.loads(settings.read_text())
    except (OSError, ValueError):
        return []
    out = []
    for event, groups in (data.get("hooks") or {}).items():
        for g in groups or []:
            for h in g.get("hooks", []):
                out.append(f"{event}[{g.get('matcher', '*')}]: {str(h.get('command', h.get('type')))[:90]}")
    return out


def memory_dir_report(mem: Path, repo: Path) -> dict:
    rep = {"dir": str(mem), "files": [], "index_lines": 0, "index_tokens": 0,
           "dangling_index": [], "unindexed": [], "stale_refs": [], "unresolved_refs": []}
    index = mem / "MEMORY.md"
    linked = set()
    if index.is_file():
        txt = index.read_text(errors="replace")
        rep["index_lines"] = txt.count("\n") + 1
        rep["index_tokens"] = tok(len(txt))
        linked = set(re.findall(r"\]\(([^)]+\.md)\)", txt))
        rep["dangling_index"] = sorted(link for link in linked if not (mem / link).is_file())
    for f in sorted(mem.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        txt = f.read_text(errors="replace")
        fm = frontmatter(txt)
        typ = fm.get("type") or re.search(r"type:\s*(\w+)", txt[:400] or "") and re.search(r"type:\s*(\w+)", txt[:400]).group(1)
        rep["files"].append({"file": f.name, "name": fm.get("name", f.stem), "type": typ,
                             "description": fm.get("description", "")[:160], "tokens": tok(len(txt))})
        if f.name not in linked:
            rep["unindexed"].append(f.name)
        for ref in sorted(set(PATHISH.findall(txt))):
            if (ref.startswith(("http", "$", "<")) or "*" in ref or "..." in ref or "<" in ref
                    or re.fullmatch(r"/[\w-]+(:[\w-]+)?", ref)):  # slash commands, placeholders
                continue
            if ref.startswith(("/", "~")):
                if not Path(os.path.expanduser(ref)).exists():
                    rep["stale_refs"].append(f"{f.name}: `{ref}`")
            elif "/" in ref and not (repo / ref).exists():
                rep["unresolved_refs"].append(f"{f.name}: `{ref}`")
    return rep


def ancestors_claude_md(root: Path) -> list[Path]:
    out = []
    for d in [root, *root.parents]:
        if d == HOME or HOME not in [d, *d.parents]:
            break
        if d != root and (d / "CLAUDE.md").is_file():
            out.append(d / "CLAUDE.md")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    result = {"global": [], "targets": []}
    for p, harness, load in GLOBAL_FILES:
        if p.exists():
            entry = {"path": str(p), "harness": harness, "load": load, "tokens": tok(size(p))}
            if p.name == "settings.json":
                entry["hooks"] = hooks_summary(p)
            result["global"].append(entry)
    seen = {}
    for e in result["global"]:
        p = Path(e["path"])
        if p.is_file() and e["load"] == "always":
            h = hash(p.read_bytes())
            if h in seen:
                e["note"] = f"same content as {seen[h]}" + (" (symlink)" if p.is_symlink() else " (copy: will drift)")
            else:
                seen[h] = e["path"]
    codex_sessions = HOME / ".codex/sessions"
    if codex_sessions.is_dir():
        result["global"].append({"path": str(codex_sessions), "harness": "codex", "load": "transcripts",
                                 "tokens": None, "note": "not mined by mine_transcripts.py; sample by hand if Codex is used here"})

    for raw in a.paths:
        root = git_root(Path(os.path.expanduser(raw)).resolve())
        t = {"root": str(root), "files": [], "nested": [], "stores": [], "ancestors": [], "memory": None,
             "always_tokens": 0}
        for pattern, harness, load in PROJECT_FILES:
            for f in sorted(root.glob(pattern)):
                e = {"path": str(f.relative_to(root)), "harness": harness, "load": load, "tokens": tok(size(f))}
                if f.name.startswith("settings"):
                    e["hooks"] = hooks_summary(f)
                if f.is_symlink():
                    e["symlink_to"] = os.readlink(f)
                t["files"].append(e)
                if load == "always":
                    t["always_tokens"] += e["tokens"]
        t["nested"] = [{"path": str(f.relative_to(root)), "tokens": tok(size(f))} for f in nested_instruction_files(root)]
        for anc in ancestors_claude_md(root):
            t["ancestors"].append({"path": str(anc), "tokens": tok(size(anc))})
            t["always_tokens"] += tok(size(anc))
        for name, kind in CONTEXT_STORES:
            for f in [root / name, *root.glob(f"*/{name}")][:5]:
                if f.exists():
                    t["stores"].append({"path": str(f.relative_to(root)), "kind": kind, "tokens": tok(size(f)),
                                        "bytes": size(f), "is_file": f.is_file(),
                                        "tracked": not subprocess.run(["git", "-C", str(root), "check-ignore", "-q", str(f)]).returncode == 0})
        slug = re.sub(r"[^A-Za-z0-9]", "-", str(root))
        mem = HOME / ".claude/projects" / slug / "memory"
        if mem.is_dir():
            t["memory"] = memory_dir_report(mem, root)
            t["always_tokens"] += t["memory"]["index_tokens"]
        transcripts = HOME / ".claude/projects" / slug
        t["transcript_sessions"] = len(list(transcripts.glob("*.jsonl"))) if transcripts.is_dir() else 0
        result["targets"].append(t)
    g_always = sum(e["tokens"] or 0 for e in result["global"] if e["load"] == "always" and "claude" in e["harness"])
    result["global_claude_always_tokens"] = g_always

    if a.json:
        json.dump(result, sys.stdout, indent=1)
        return

    print("# Harness memory sources\n\n## Global (every project)")
    for e in result["global"]:
        tk = f" ~{e['tokens']} tok" if e["tokens"] is not None else ""
        print(f"- {e['path']} [{e['harness']}, {e['load']}]{tk} {e.get('note', '')}".rstrip())
        for h in e.get("hooks", []):
            print(f"  - hook {h}")
    for t in result["targets"]:
        print(f"\n## {t['root']}")
        print(f"- Always-loaded estimate (Claude Code): ~{t['always_tokens'] + g_always:,} tokens "
              f"(project ~{t['always_tokens']:,} + global ~{g_always:,}); excludes skill/MCP/tool listings and hook output")
        print(f"- Transcripts: {t['transcript_sessions']} sessions")
        for e in t["files"]:
            extra = f" -> {e['symlink_to']}" if "symlink_to" in e else ""
            print(f"- {e['path']}{extra} [{e['harness']}, {e['load']}] ~{e['tokens']} tok")
            for h in e.get("hooks", []):
                print(f"  - hook {h}")
        for e in t["ancestors"]:
            print(f"- ancestor {e['path']} [claude, always] ~{e['tokens']} tok")
        if t["nested"]:
            print(f"- nested instruction files: {len(t['nested'])} (" +
                  ", ".join(f"{n['path']} ~{n['tokens']}" for n in t["nested"][:8]) + (" …" if len(t["nested"]) > 8 else "") + ")")
        for s in t["stores"]:
            sz = f"~{s['tokens']:,} tok" if s["is_file"] else f"{s['bytes'] / 1e6:.1f} MB on disk"
            print(f"- store {s['path']} [{s['kind']}] {sz}{'' if s['tracked'] else ' (git-ignored)'}")
        m = t["memory"]
        if m:
            print(f"\n### Auto-memory {m['dir']}\n- MEMORY.md: {m['index_lines']} lines ~{m['index_tokens']} tok (always loaded)")
            for f in m["files"]:
                print(f"- {f['file']} [{f['type']}] ~{f['tokens']} tok — {f['description']}")
            for k, label in (("dangling_index", "index links with no file"), ("unindexed", "files missing from index"),
                             ("stale_refs", "absolute paths mentioned that no longer exist (stale)"),
                             ("unresolved_refs", "relative paths not found in this repo (may belong to another tool; check before calling stale)")):
                if m[k]:
                    print(f"- {label}: " + "; ".join(m[k][:15]))
        else:
            print("- Auto-memory: none")


if __name__ == "__main__":
    main()
