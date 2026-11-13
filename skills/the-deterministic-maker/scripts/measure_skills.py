#!/usr/bin/env python3
"""Measure what each skill costs to load and to run, before and after a change.

snapshot  Static load cost per skill (description, body, references, scripts)
          plus use cost mined from Claude Code transcripts: runs, API calls,
          output tokens, tool-result volume, subagent tokens, and the shell
          commands the model ran by hand instead of calling a bundled script.
compare   Diff a saved snapshot against the skills as they are now (or against
          a second snapshot). Use cost after the change counts only runs that
          started after the first snapshot, so every number is either measured
          or marked as not measured yet.

A run starts when a skill is invoked (Skill tool, slash command, or a subagent
reading its SKILL.md) and ends at the next user prompt or skill invocation.
A subagent that reads a SKILL.md and then edits that skill is not counted.
Subagents a run starts are charged to it, found by the Agent call's id or by
the harness's `attributionSkill` tag, so a skill that fans out shows its real
cost. A skill invoked inside such a subagent is also counted as its own run.
Plugin prefixes are ignored, so `plugin:name` counts as `name`.

Prints counts, paths, and short command heads only; never tool output.

Usage:
  measure_skills.py snapshot [skill ...] [--skills-dir DIR] [--out FILE]
                    [--project PATH ...] [--days 30] [--since ISO] [--json]
  measure_skills.py compare BEFORE.json [AFTER.json] [--out FILE] [--json]
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import os
import re
import sys
import time
from pathlib import Path

SCHEMA = 1
CHARS_PER_TOKEN = 4
RECIPE_MIN_COMMANDS = 3
MAX_HINTS = 12
SHELL_LANGS = {"bash", "sh", "shell", "zsh", "console"}
EMPTY_BLOCK_SCALARS = {"", ">", "|", ">-", "|-", ">+", "|+"}
# Price weights relative to one uncached input token.
COST = {"input_tokens": 1.0, "cache_creation_input_tokens": 1.25, "cache_read_input_tokens": 0.1, "output_tokens": 5.0}

DATA_STEP = re.compile(
    r"\b(count|tally|sum|total|average|calculate|compute|percentage|ratio|weighted|tabulate|"
    r"list (?:all|every|each)|for (?:each|every)|"
    r"(?:each|every|all) (?:files?|lines?|functions?|imports?|commits?|modules?|tests?)|"
    r"parse|extract|grep|scan|search for|find (?:all|every)|look for)\b",
    re.I,
)
INLINE_CODE = re.compile(r"^((python3?|node|ruby|perl|deno|bun) (-c|-e|-)$|awk\b|jq\b)")
COMMAND_NAME = re.compile(r"<command-name>\s*/?([^<\s]+)\s*</command-name>")
RUN_OPENER = re.compile(r'"Skill"|<command-name>|SKILL\.md')
SECRETISH = re.compile(r"(?i)(token|secret|password|passwd|api[_-]?key|bearer)\S*\s*[=:]\s*\S+")


# ---------- static: what a skill costs to load ----------

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def tokens(text: str) -> int:
    return round(len(text) / CHARS_PER_TOKEN)


def split_frontmatter(lines: list[str]) -> tuple[list[str], int]:
    """Return the frontmatter lines and the 1-based line where the body starts."""
    if not lines or lines[0].strip() != "---":
        return [], 1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], i + 2
    return [], 1


def fm_field(fm: list[str], key: str) -> str:
    """Read one top-level frontmatter value, folded block scalars included."""
    for i, line in enumerate(fm):
        if not line.startswith(key + ":"):
            continue
        val = line[len(key) + 1:].strip()
        if val in EMPTY_BLOCK_SCALARS:
            block = []
            for nxt in fm[i + 1:]:
                if nxt and not nxt[0].isspace():
                    break
                block.append(nxt.strip())
            val = " ".join(b for b in block if b)
        return val.strip("\"'")
    return ""


def fm_version(fm: list[str]) -> str:
    for line in fm:
        m = re.match(r"\s+version:\s*[\"']?([^\"'\s]+)", line)
        if m:
            return m.group(1)
    return ""


def mentions_script(text: str, script_names: list[str]) -> bool:
    return "scripts/" in text or any(n in text for n in script_names)


def scan_body(lines: list[str], body_start: int, script_names: list[str]) -> tuple[list[dict], list[dict]]:
    """Find prose lines that describe data work, and shell blocks with no script behind them."""
    hints, recipes = [], []
    fence = None  # [lang, start line, commands, calls a script]
    for no, line in enumerate(lines, 1):
        if no < body_start:
            continue
        s = line.strip()
        if s.startswith("```"):
            if fence is None:
                fence = [s[3:].strip().lower(), no, 0, False]
            else:
                if fence[0] in SHELL_LANGS and fence[2] >= RECIPE_MIN_COMMANDS and not fence[3]:
                    recipes.append({"line": fence[1], "commands": fence[2]})
                fence = None
        elif fence is not None:
            if s and not s.startswith("#"):
                fence[2] += 1
                fence[3] = fence[3] or mentions_script(s, script_names)
        elif DATA_STEP.search(s) and not mentions_script(s, script_names):
            hints.append({"line": no, "text": s[:110]})
    return hints, recipes


def files_under(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")


def static_metrics(skill_dir: Path) -> dict:
    text = read_text(skill_dir / "SKILL.md")
    lines = text.splitlines()
    fm, body_start = split_frontmatter(lines)
    ref_texts = [read_text(p) for p in files_under(skill_dir / "references")]
    scripts = [p.name for p in files_under(skill_dir / "scripts")]
    docs = text + "".join(ref_texts)
    hints, recipes = scan_body(lines, body_start, scripts)
    return {
        "name": fm_field(fm, "name") or skill_dir.name,
        "version": fm_version(fm),
        "description_tokens": tokens(fm_field(fm, "description")),
        "body_tokens": tokens("\n".join(lines[body_start - 1:])),
        "body_lines": max(len(lines) - body_start + 1, 0),
        "reference_files": len(ref_texts),
        "reference_tokens": sum(tokens(t) for t in ref_texts),
        "scripts": scripts,
        "unreferenced_scripts": [n for n in scripts if n not in docs],
        "recipe_blocks": recipes,
        "data_step_hint_count": len(hints),
        "data_step_hints": hints[:MAX_HINTS],
    }


# ---------- usage: what a skill costs to run ----------

def slug_for(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(os.path.expanduser(path)))


def head_of(cmd: str) -> str:
    """Normalize a shell command to a stable, non-sensitive head."""
    cmd = SECRETISH.sub(r"\1=<redacted>", cmd.strip())
    words: list[str] = []
    for seg in re.split(r"\s*(?:&&|\|\||;|\||\n)\s*", cmd):
        words = [w for w in seg.split() if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w)]
        if words and words[0] not in ("cd", "export", "set", "source", "."):
            break
        words = []
    if words and "/" in words[0]:
        words[0] = words[0].rstrip("/").rsplit("/", 1)[-1]
    keep: list[str] = []
    for w in words:
        if len(keep) >= 3 or w.startswith(("/", "~", "'", '"', "<", "$(")) or "/" in w[1:]:
            break
        keep.append(w)
    return " ".join(keep) or (words[0] if words else "")


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def result_len(content) -> int:
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(b.get("text", "")) for b in content if isinstance(b, dict))
    return 0


class Catalog:
    """The skills being measured: how to recognize an invocation and a bundled script."""

    def __init__(self, skills: dict[str, dict]):
        self.aliases = {}
        self.scripts = {}
        for dirname, static in skills.items():
            self.aliases[dirname] = dirname
            self.aliases[static["name"]] = dirname
            self.scripts[dirname] = static["scripts"]

    def resolve(self, raw: str) -> str | None:
        name = raw.strip().lstrip("/").split()[0] if raw.strip() else ""
        return self.aliases.get(name.rsplit(":", 1)[-1])

    def calls_own_script(self, skill: str, cmd: str) -> bool:
        return f"/{skill}/scripts/" in cmd or any(n in cmd for n in self.scripts[skill])

    def is_reference(self, skill: str, path: str) -> bool:
        return f"/{skill}/references/" in path

    def needles(self) -> list[bytes]:
        return [a.encode() for a in self.aliases]


class Run:
    def __init__(self, skill: str, kind: str, session: str, ts: str, is_sub: bool = False):
        self.skill, self.kind, self.session, self.ts, self.is_sub = skill, kind, session, ts or "", is_sub
        self.calls = 0
        self.output = 0
        self.processed = 0
        self.cost = 0.0
        self.result_chars = 0
        self.failures = 0
        self.own_script_calls = 0
        self.inline_code = 0
        self.ref_reads = 0
        self.agent_calls = 0
        self.agent_ids: list[str] = []
        self.edits_skill = False
        self.adhoc: collections.Counter = collections.Counter()


class FileMiner:
    """Walks one transcript and attributes the work after a skill invocation to that skill."""

    def __init__(self, catalog: Catalog, session: str, is_sub: bool):
        self.cat, self.session, self.is_sub = catalog, session, is_sub
        self.cur: Run | None = None
        self.pending: dict = {}
        self.seen: set = set()
        self.runs: list[Run] = []

    def mine(self, path: Path) -> list[Run]:
        try:
            fh = path.open(encoding="utf-8", errors="replace")
        except OSError:
            return []
        with fh:
            for line in fh:
                # Outside a run, only a line that can open one is worth parsing.
                if self.cur is None and not RUN_OPENER.search(line):
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                msg = rec.get("message")
                if isinstance(msg, dict) and rec.get("type") == "assistant":
                    self.assistant(rec, msg)
                elif isinstance(msg, dict) and rec.get("type") == "user":
                    self.user(rec, msg)
        return self.runs

    def invoke(self, raw: str, kind: str, ts: str):
        skill = self.cat.resolve(raw)
        self.cur = None
        if skill:
            self.cur = Run(skill, kind, self.session, ts, self.is_sub)
            self.runs.append(self.cur)

    def assistant(self, rec: dict, msg: dict):
        usage, mid = msg.get("usage"), msg.get("id") or rec.get("requestId")
        if usage and mid not in self.seen:
            self.seen.add(mid)
            if self.cur is not None:
                self.count_usage(self.cur, usage)
        for b in msg.get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                self.tool_use(b, rec.get("timestamp"))

    @staticmethod
    def count_usage(run: Run, usage: dict):
        run.calls += 1
        run.output += usage.get("output_tokens") or 0
        for key, weight in COST.items():
            n = usage.get(key) or 0
            run.cost += n * weight
            if key != "output_tokens":
                run.processed += n

    def tool_use(self, b: dict, ts: str):
        name, inp = b.get("name", "?"), b.get("input") or {}
        if name == "Skill":
            self.invoke(str(inp.get("skill") or inp.get("command") or ""), "skill-tool", ts)
            return
        path = str(inp.get("file_path") or "")
        if name == "Read" and self.is_sub and path.endswith("/SKILL.md"):
            skill = self.cat.resolve(path.rsplit("/", 2)[-2])
            if skill and (self.cur is None or self.cur.skill != skill):
                self.invoke(skill, "read-in-subagent", ts)
        run = self.cur
        self.pending[b.get("id")] = (name, run)
        if run is None:
            return
        if name in ("Edit", "Write") and f"/{run.skill}/" in path:
            run.edits_skill = True
        if name == "Bash":
            self.bash(run, str(inp.get("command", "")))
        elif name == "Read" and self.cat.is_reference(run.skill, path):
            run.ref_reads += 1
        elif name in ("Agent", "Task"):
            run.agent_calls += 1

    def bash(self, run: Run, cmd: str):
        if self.cat.calls_own_script(run.skill, cmd):
            run.own_script_calls += 1
            return
        head = head_of(cmd) or "?"
        run.adhoc[head] += 1
        if INLINE_CODE.match(head):
            run.inline_code += 1

    def user(self, rec: dict, msg: dict):
        content = msg.get("content")
        results = [b for b in content if isinstance(b, dict) and b.get("type") == "tool_result"] if isinstance(content, list) else []
        if results:
            for b in results:
                self.tool_result(b, rec)
            return
        text = text_of(content).strip()
        m = COMMAND_NAME.search(text)
        if m:
            self.invoke(m.group(1), "slash", rec.get("timestamp"))
        elif not self.is_sub and not rec.get("isMeta") and text and not text.startswith("<"):
            self.cur = None  # a new user prompt ends the run

    def tool_result(self, b: dict, rec: dict):
        name, run = self.pending.pop(b.get("tool_use_id"), ("?", None))
        if run is None:
            return
        run.result_chars += result_len(b.get("content"))
        if b.get("is_error") is True:
            run.failures += 1
        tr = rec.get("toolUseResult")
        if name in ("Agent", "Task") and isinstance(tr, dict) and tr.get("agentId"):
            run.agent_ids.append(str(tr["agentId"]))


def project_dirs(projects_dir: Path, projects: list[str]) -> list[Path]:
    dirs = [d for d in sorted(projects_dir.iterdir()) if d.is_dir()] if projects_dir.is_dir() else []
    if not projects:
        return dirs
    slugs = [slug_for(p) for p in projects]
    return [d for d in dirs if any(d.name == s or d.name.startswith(s + "--claude-worktrees-") for s in slugs)]


def transcripts(dirs: list[Path], cutoff: float):
    """Yield (path, session id, is subagent) for sessions touched since the cutoff."""
    for d in dirs:
        for f in sorted(d.glob("*.jsonl")):
            try:
                if f.stat().st_mtime < cutoff:
                    continue
            except OSError:
                continue
            yield f, f.stem, False
            for s in sorted((d / f.stem / "subagents").rglob("agent-*.jsonl")):
                yield s, f.stem, True


def mentions(path: Path, needles: list[bytes]) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    return any(n in data for n in needles)


def subagent_info(path: Path) -> dict:
    """Tokens and price-weighted cost of one subagent transcript, its start time, and the skill it is tagged with."""
    info = {"tokens": 0, "cost": 0.0, "ts": "", "tag": ""}
    seen = set()
    try:
        fh = path.open(encoding="utf-8", errors="replace")
    except OSError:
        return info
    with fh:
        for line in fh:
            if '"usage"' not in line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
            usage, mid = msg.get("usage"), msg.get("id") or rec.get("requestId")
            if usage and mid not in seen:
                seen.add(mid)
                info["tokens"] += sum(usage.get(k) or 0 for k in COST)
                info["cost"] += sum((usage.get(k) or 0) * w for k, w in COST.items())
                info["ts"] = info["ts"] or rec.get("timestamp") or ""
                info["tag"] = info["tag"] or rec.get("attributionSkill") or ""
    return info


def link_tagged_subagents(runs: list[Run], tagged: list[tuple[str, str, dict]], catalog: Catalog):
    """Charge each tagged subagent transcript to the latest main-thread run of that skill in its session."""
    for session, agent_id, info in tagged:
        skill = catalog.resolve(info["tag"])
        owners = [r for r in runs if not r.is_sub and r.session == session and r.skill == skill and r.ts <= info["ts"]]
        if owners and agent_id not in owners[-1].agent_ids:
            owners[-1].agent_ids.append(agent_id)


def mine_usage(catalog: Catalog, dirs: list[Path], cutoff: float, since: str) -> tuple[list[Run], dict, dict]:
    runs: list[Run] = []
    agent_files: dict[str, Path] = {}
    infos: dict[str, dict] = {}
    tagged = []
    scanned = {"sessions": 0, "transcripts": 0, "mentioning": 0}
    needles = catalog.needles()
    for path, session, is_sub in transcripts(dirs, cutoff):
        scanned["transcripts"] += 1
        scanned["sessions"] += 0 if is_sub else 1
        if is_sub:
            agent_files[path.stem[len("agent-"):]] = path
        if mentions(path, needles):
            scanned["mentioning"] += 1
            runs += FileMiner(catalog, session, is_sub).mine(path)
            if is_sub:
                agent_id = path.stem[len("agent-"):]
                infos[agent_id] = subagent_info(path)
                if catalog.resolve(infos[agent_id]["tag"]):
                    tagged.append((session, agent_id, infos[agent_id]))
    # A subagent that reads a SKILL.md and then edits that skill is developing it, not using it.
    runs = [r for r in runs if not (r.kind == "read-in-subagent" and r.edits_skill)]
    runs = [r for r in runs if not since or r.ts >= since]
    link_tagged_subagents(runs, tagged, catalog)
    for a in {a for r in runs for a in r.agent_ids}:
        if a not in infos and a in agent_files:
            infos[a] = subagent_info(agent_files[a])
    return runs, infos, scanned


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 1) if values else 0.0


def summarize(runs: list[Run], infos: dict, window_days: float) -> dict:
    heads: collections.Counter = collections.Counter()
    head_runs: collections.Counter = collections.Counter()
    for r in runs:
        heads.update(r.adhoc)
        head_runs.update(r.adhoc.keys())
    sub = [sum(infos[a]["tokens"] for a in r.agent_ids if a in infos) for r in runs]
    sub_cost = [sum(infos[a]["cost"] for a in r.agent_ids if a in infos) for r in runs]
    return {
        "runs": len(runs),
        "sessions": len({r.session for r in runs}),
        "kinds": dict(collections.Counter(r.kind for r in runs)),
        "runs_per_30d": round(len(runs) / max(window_days, 1) * 30, 1),
        "per_run": {
            "api_calls": mean([r.calls for r in runs]),
            "output_tokens": mean([r.output for r in runs]),
            "tool_result_tokens": mean([r.result_chars / CHARS_PER_TOKEN for r in runs]),
            "processed_tokens": mean([r.processed for r in runs]),
            "cost_eq_tokens": mean([r.cost for r in runs]),
            "subagent_tokens": mean(sub),
            "subagent_cost_eq_tokens": mean(sub_cost),
            "total_cost_eq_tokens": mean([r.cost + c for r, c in zip(runs, sub_cost)]),
            "adhoc_bash_calls": mean([sum(r.adhoc.values()) for r in runs]),
        },
        "total_cost_eq_tokens": round(sum(r.cost for r in runs) + sum(sub_cost)),
        "subagents": sum(len(r.agent_ids) for r in runs),
        "own_script_calls": sum(r.own_script_calls for r in runs),
        "adhoc_bash_calls": sum(heads.values()),
        "inline_code_calls": sum(r.inline_code for r in runs),
        "failures": sum(r.failures for r in runs),
        "reference_reads": sum(r.ref_reads for r in runs),
        "agent_calls": sum(r.agent_calls for r in runs),
        "top_adhoc": [{"head": h, "calls": c, "runs": head_runs[h]} for h, c in heads.most_common(8)],
    }


# ---------- snapshot ----------

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def days_since(iso: str) -> float:
    try:
        then = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        sys.exit(f"measure_skills: --since needs an ISO date or time (2026-01-31 or 2026-01-31T12:00:00Z), not '{iso}'")
    if then.tzinfo is None:
        then = then.replace(tzinfo=datetime.timezone.utc)
    return (datetime.datetime.now(datetime.timezone.utc) - then).total_seconds() / 86400


def find_skills(skills_dir: str, names: list[str], missing_ok: bool = False) -> tuple[Path, dict[str, Path]]:
    base = Path(skills_dir) if skills_dir else next((Path(c) for c in ("skills", ".claude/skills") if Path(c).is_dir()), None)
    if base is None or not base.is_dir():
        sys.exit("measure_skills: no skills directory found; pass --skills-dir")
    if not names:
        found = {d.name: d for d in sorted(base.iterdir()) if (d / "SKILL.md").is_file()}
    else:
        found = {}
        for n in names:
            d = Path(n) if (Path(n) / "SKILL.md").is_file() else base / n
            if not (d / "SKILL.md").is_file():
                if missing_ok:
                    continue
                sys.exit(f"measure_skills: no SKILL.md for '{n}' under {base}")
            found[d.name] = d
    if not found:
        sys.exit(f"measure_skills: no skills with a SKILL.md under {base}")
    return base, found


def take_snapshot(skills_dir: str, names: list[str], projects: list[str], projects_dir: str, days: int, since: str,
                  missing_ok: bool = False) -> dict:
    base, found = find_skills(skills_dir, names, missing_ok)
    static = {name: static_metrics(path) for name, path in found.items()}
    catalog = Catalog(static)
    window_days = min(days, days_since(since)) if since else days
    cutoff = time.time() - window_days * 86400
    dirs = project_dirs(Path(os.path.expanduser(projects_dir)), projects)
    runs, infos, scanned = mine_usage(catalog, dirs, cutoff, since)
    by_skill = collections.defaultdict(list)
    for r in runs:
        by_skill[r.skill].append(r)
    return {
        "schema": SCHEMA,
        "taken_at": now_iso(),
        "skills_dir": str(base),
        "args": {"projects": projects, "projects_dir": projects_dir, "days": days, "since": since},
        "window_days": round(window_days, 2),
        "scanned": scanned,
        "skills": {name: {"static": static[name], "usage": summarize(by_skill[name], infos, window_days)} for name in found},
    }


def fmt(n: float) -> str:
    return f"{n:,.0f}" if abs(n) >= 100 or float(n).is_integer() else f"{n:,.1f}"


def table(header: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    return out + ["| " + " | ".join(r) + " |" for r in rows]


def scope_line(snap: dict) -> str:
    a, s = snap["args"], snap["scanned"]
    where = ", ".join(a["projects"]) if a["projects"] else "all projects"
    window = f"since {a['since']}" if a["since"] else f"last {a['days']} days"
    return f"Transcripts: {where}, {window}; {s['sessions']} sessions, {s['mentioning']} of {s['transcripts']} transcripts name a measured skill."


def render_snapshot(snap: dict) -> str:
    skills = snap["skills"]
    out = ["# Skill measurements", "", f"Skills: {len(skills)} under `{snap['skills_dir']}`. Taken {snap['taken_at']}.", scope_line(snap),
           "Tokens are estimates (chars / 4). Cost-eq weights one API call's tokens by price: input 1, cache write 1.25, cache read 0.1, output 5.",
           "API calls, output, tool results, and Cost-eq cover the skill's own thread; Subagent cost-eq is what its subagents added.",
           "", "## Load cost", ""]
    rows = []
    for name, s in sorted(skills.items(), key=lambda kv: -kv[1]["static"]["body_tokens"]):
        st = s["static"]
        rows.append([name, fmt(st["description_tokens"]), fmt(st["body_tokens"]), f"{fmt(st['reference_tokens'])} in {st['reference_files']}",
                     str(len(st["scripts"])), str(len(st["recipe_blocks"])), str(st["data_step_hint_count"])])
    out += table(["Skill", "Description (every session)", "Body (every run)", "References (on demand)", "Scripts", "Recipe blocks", "Data-step hints"], rows)

    used = sorted(((n, s["usage"]) for n, s in skills.items() if s["usage"]["runs"]), key=lambda kv: -kv[1]["total_cost_eq_tokens"])
    out += ["", "## Use cost (mean per run, highest total first)", ""]
    if used:
        rows = []
        for name, u in used:
            p = u["per_run"]
            rows.append([name, str(u["runs"]), fmt(p["api_calls"]), fmt(p["output_tokens"]), fmt(p["tool_result_tokens"]), fmt(p["cost_eq_tokens"]),
                         fmt(p["subagent_cost_eq_tokens"]), fmt(u["total_cost_eq_tokens"]), str(u["own_script_calls"]), str(u["adhoc_bash_calls"]),
                         str(u["inline_code_calls"]), str(u["failures"])])
        out += table(["Skill", "Runs", "API calls", "Output tok", "Tool-result tok", "Cost-eq tok", "Subagent cost-eq", "Total cost-eq (all runs)",
                      "Own-script calls", "Ad hoc Bash", "Inline code", "Failed calls"], rows)
    unused = [n for n, s in skills.items() if not s["usage"]["runs"]]
    if unused:
        out += ["", f"No runs in the window ({len(unused)}): {', '.join(sorted(unused))}."]

    out += ["", "## Commands run by hand (per skill, most frequent)", ""]
    for name, u in used:
        if u["top_adhoc"]:
            out.append(f"- **{name}**: " + "; ".join(f"{h['calls']} × `{h['head']}` in {h['runs']} run(s)" for h in u["top_adhoc"][:6]))

    out += ["", "## Where to look in each SKILL.md", "", "Hints are word matches, not findings. Read the line before you call it a candidate.", ""]
    for name, s in sorted(skills.items()):
        st = s["static"]
        notes = [f"recipe block at SKILL.md:{r['line']} ({r['commands']} commands, no script)" for r in st["recipe_blocks"]]
        notes += [f"unreferenced script `{n}`" for n in st["unreferenced_scripts"]]
        notes += [f"SKILL.md:{h['line']} {h['text']}" for h in st["data_step_hints"][:5]]
        if notes:
            out.append(f"### {name}")
            out += [f"- {n}" for n in notes]
    return "\n".join(out) + "\n"


# ---------- compare ----------

def arrow(before: float, after: float) -> str:
    if before == after:
        return fmt(before)
    return f"{fmt(before)} → {fmt(after)} ({after - before:+,.0f})"


def compare(before: dict, after: dict) -> dict:
    """Pair each skill's numbers and say which ones are measured."""
    skills = {}
    for name in sorted(set(before["skills"]) | set(after["skills"])):
        b, a = before["skills"].get(name), after["skills"].get(name)
        if b is None or a is None:
            skills[name] = {"status": "added" if b is None else "removed"}
            continue
        bs, as_ = b["static"], a["static"]
        static = {k: [bs[k], as_[k]] for k in ("description_tokens", "body_tokens", "reference_tokens", "data_step_hint_count")}
        static["scripts"] = [len(bs["scripts"]), len(as_["scripts"])]
        static["recipe_blocks"] = [len(bs["recipe_blocks"]), len(as_["recipe_blocks"])]
        body_delta = as_["body_tokens"] - bs["body_tokens"]
        runs_after = a["usage"]["runs"]
        skills[name] = {
            "status": "changed" if any(x != y for x, y in static.values()) or bs["version"] != as_["version"] else "unchanged",
            "version": [bs["version"], as_["version"]],
            "static": static,
            "projected_body_tokens_per_30d": round(body_delta * b["usage"]["runs_per_30d"]),
            "runs": [b["usage"]["runs"], runs_after],
            "use_measured": runs_after > 0,
            "per_run": {k: [v, a["usage"]["per_run"][k] if runs_after else None] for k, v in b["usage"]["per_run"].items()},
        }
    return {"before": before["taken_at"], "after": after["taken_at"], "skills": skills}


def render_compare(diff: dict) -> str:
    out = ["# Before and after", "", f"Before: {diff['before']}. After: {diff['after']}.", "", "## Load cost (measured)", ""]
    changed = {n: s for n, s in diff["skills"].items() if s["status"] == "changed"}
    rows = []
    for name, s in changed.items():
        st = s["static"]
        version = s["version"][0] if s["version"][0] == s["version"][1] else f"{s['version'][0]} → {s['version'][1]}"
        rows.append([name, version, arrow(*st["description_tokens"]), arrow(*st["body_tokens"]), arrow(*st["reference_tokens"]),
                     arrow(*st["scripts"]), arrow(*st["recipe_blocks"]), arrow(*st["data_step_hint_count"]),
                     f"{s['projected_body_tokens_per_30d']:+,}"])
    if rows:
        out += table(["Skill", "Version", "Description", "Body", "References", "Scripts", "Recipe blocks", "Data-step hints",
                      "Body tokens / 30 days (projected)"], rows)
        out += ["", "The projection is the body change times the run rate before the change."]
    other = collections.Counter(s["status"] for s in diff["skills"].values() if s["status"] != "changed")
    out += ["", "Other skills: " + (", ".join(f"{n} {k}" for k, n in sorted(other.items())) or "none") + "."]

    out += ["", "## Use cost per run", ""]
    rows = []
    for name, s in changed.items():
        if not s["runs"][0] and not s["runs"][1]:
            rows.append([name, "0", "0", "-", "-", "-", "-", "-", "no runs before or after"])
            continue
        p = s["per_run"]
        cell = (lambda k: arrow(p[k][0], p[k][1])) if s["use_measured"] else (lambda k: f"{fmt(p[k][0])} → not measured")
        rows.append([name, str(s["runs"][0]), str(s["runs"][1]), cell("api_calls"), cell("output_tokens"), cell("tool_result_tokens"),
                     cell("total_cost_eq_tokens"), cell("adhoc_bash_calls"), "measured" if s["use_measured"] else "not measured yet"])
    if rows:
        out += table(["Skill", "Runs before", "Runs since", "API calls", "Output tok", "Tool-result tok", "Cost-eq tok (with subagents)", "Ad hoc Bash", "Status"], rows)
    if any(not s["use_measured"] for s in changed.values()):
        out += ["", "\"Not measured yet\" means no run started after the first snapshot. Report an estimate for those skills, "
                    "and run `compare` again after they have been used."]
    if not changed:
        out.append("No measured skill changed.")
    return "\n".join(out) + "\n"


# ---------- CLI ----------

def load(path: str) -> dict:
    try:
        snap = json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        sys.exit(f"measure_skills: cannot read snapshot {path}: {e}")
    if snap.get("schema") != SCHEMA:
        sys.exit(f"measure_skills: {path} is not a schema {SCHEMA} snapshot")
    return snap


def save(path: str, data: dict):
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(data, indent=1) + "\n")


def cmd_snapshot(args):
    snap = take_snapshot(args.skills_dir, args.skills, args.project, args.projects_dir, args.days, args.since)
    save(args.out, snap)
    print(json.dumps(snap, indent=1) if args.json else render_snapshot(snap), end="")


def cmd_compare(args):
    before = load(args.before)
    if args.after:
        after = load(args.after)
    else:
        a = before["args"]
        after = take_snapshot(args.skills_dir or before["skills_dir"], sorted(before["skills"]), a["projects"], a["projects_dir"],
                              a["days"], before["taken_at"], missing_ok=True)
        save(args.out, after)
    diff = compare(before, after)
    print(json.dumps(diff, indent=1) if args.json else render_compare(diff), end="")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot", help="measure skills now")
    s.add_argument("skills", nargs="*", help="skill names or directories (default: every skill in --skills-dir)")
    s.add_argument("--skills-dir", default="", help="default: ./skills, then ./.claude/skills")
    s.add_argument("--project", action="append", default=[], help="count only this project's transcripts (repeatable; default: all projects)")
    s.add_argument("--projects-dir", default="~/.claude/projects")
    s.add_argument("--days", type=int, default=30, help="transcript window (default 30)")
    s.add_argument("--since", default="", help="count only runs that started at or after this ISO time")
    s.add_argument("--out", default="", help="also save the snapshot as JSON here")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_snapshot)
    c = sub.add_parser("compare", help="diff a snapshot against now, or against a second snapshot")
    c.add_argument("before")
    c.add_argument("after", nargs="?")
    c.add_argument("--skills-dir", default="", help="default: the directory recorded in BEFORE")
    c.add_argument("--out", default="", help="save the new snapshot as JSON here")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_compare)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
