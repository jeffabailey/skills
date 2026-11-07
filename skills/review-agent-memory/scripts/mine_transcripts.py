#!/usr/bin/env python3
"""Mine Claude Code session transcripts for token waste and agent churn.

Reads ~/.claude/projects/<slug>/*.jsonl (plus subagents/*.jsonl) for one or
more project paths and prints counts, paths, and short command heads only.
It never prints tool output, file contents, or thinking, so the report is
safe to read into context and cheap to read.

Usage:
  mine_transcripts.py <project-path> [<project-path> ...] [--sessions 30]
                      [--days N] [--projects-dir DIR] [--top 12] [--json]
                      [--no-snippets]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys
import time
from pathlib import Path

CORRECTION_RE = re.compile(
    r"^\s*(no\b|nope|don'?t|do not|stop|wrong|that'?s not|not what|"
    r"why did you|you (didn'?t|forgot|missed|ignored)|undo|revert|again\b)",
    re.I,
)
GENERIC_HEADS = re.compile(r"^(ls|cat|echo|sed|head|tail|grep|wc|for|cd|mkdir|python3? -|printf|true|sleep)\b")
TEMP_PATH = re.compile(r"^(/private)?/(tmp|var/folders)/|/scratchpad/|/tool-results/|/\.claude/projects/")
BIG_RESULT_CHARS = 20_000  # ~5k tokens: a read this size is worth questioning
SECRETISH = re.compile(r"(?i)(token|secret|password|passwd|api[_-]?key|bearer)\S*\s*[=:]\s*\S+")


def slug_for(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(os.path.expanduser(path)))


def slug_dirs(projects_dir: Path, path: str) -> list[Path]:
    slug = slug_for(path)
    out = []
    for d in projects_dir.iterdir() if projects_dir.is_dir() else []:
        # exact match, or a Claude Code worktree of this repo
        if d.is_dir() and (d.name == slug or d.name.startswith(slug + "--claude-worktrees-")):
            out.append(d)
    return out


def head_of(cmd: str) -> str:
    """Normalize a shell command to a stable, non-sensitive head."""
    cmd = SECRETISH.sub(r"\1=<redacted>", cmd.strip())
    words = []
    for seg in re.split(r"\s*(?:&&|\|\||;|\||\n)\s*", cmd):
        words = [w for w in seg.split() if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w)]
        if words and words[0] not in ("cd", "export", "set", "source", "."):
            break
        words = []
    if words and "/" in words[0]:
        words[0] = words[0].rstrip("/").rsplit("/", 1)[-1]  # /usr/bin/python3 -> python3
    keep = []
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


def norm_path(p: str, root: str) -> str:
    """Show repo files relative to the repo root; leave others absolute."""
    if not p:
        return p
    ap = os.path.normpath(os.path.join(root, os.path.expanduser(p)))
    for r in ROOTS:
        if ap == r or ap.startswith(r + os.sep):
            rel = os.path.relpath(ap, r)
            return rel if len(ROOTS) == 1 else f"{os.path.basename(r)}/{rel}"
    return ap


ROOTS: list[str] = []


class Stats:
    def __init__(self):
        self.root = os.getcwd()
        self.temp_reads = 0
        self.overflow_reads = 0
        self.sessions = 0
        self.subagent_files = 0
        self.tokens = collections.Counter()  # input, cache_create, cache_read, output
        self.subagent_tokens = 0
        self.tools = collections.Counter()
        self.result_chars = collections.Counter()  # by tool
        self.reads = collections.Counter()  # path -> reads
        self.read_sessions = collections.defaultdict(set)
        self.same_session_rereads = collections.Counter()  # path -> extra reads within a session
        self.big_reads = collections.Counter()  # path -> reads returning > BIG_RESULT_CHARS
        self.edits = collections.Counter()
        self.bash_heads = collections.Counter()
        self.bash_head_sessions = collections.defaultdict(set)
        self.bash_seqs = collections.defaultdict(set)  # (h1,h2,h3) -> sessions
        self.failures = collections.Counter()  # tool or bash head
        self.repeat_failures = collections.Counter()  # same exact input failed >1 in a session
        self.denials = collections.Counter()
        self.search_then_read = 0
        self.searches = 0
        self.agent_calls = 0
        self.agent_types = collections.Counter()
        self.skills = collections.Counter()
        self.mcp = collections.Counter()
        self.compactions = 0
        self.hook_chars = collections.Counter()  # hook name -> chars injected
        self.corrections = []
        self.user_turns = 0
        self.first_ts = None
        self.last_ts = None

    def to_dict(self):
        d = {}
        for k, v in self.__dict__.items():
            if isinstance(v, collections.defaultdict):
                d[k] = {(" > ".join(kk) if isinstance(kk, tuple) else kk): len(vv) for kk, vv in v.items()}
            elif isinstance(v, collections.Counter):
                d[k] = dict(v.most_common())
            else:
                d[k] = v
        return d


def mine_file(path: Path, st: Stats, session_id: str, is_sub: bool, snippets: bool):
    pending = {}  # tool_use_id -> (name, input)
    seen_msg = set()
    session_reads = collections.Counter()
    session_fail_inputs = collections.Counter()
    heads_seq = []
    last_was_search = False
    try:
        fh = path.open(encoding="utf-8", errors="replace")
    except OSError:
        return
    with fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            ts = d.get("timestamp")
            if ts:
                st.first_ts = min(st.first_ts or ts, ts)
                st.last_ts = max(st.last_ts or ts, ts)
            typ = d.get("type")
            if d.get("isCompactSummary"):
                st.compactions += 1
            if typ == "attachment":
                a = d.get("attachment") or {}
                if a.get("type") in ("hook_success", "hook_additional_context"):
                    n = len(str(a.get("content") or "")) + len(str(a.get("stdout") or ""))
                    if n:
                        st.hook_chars[str(a.get("hookName") or a.get("hookEvent") or "?")] += n
                continue
            msg = d.get("message")
            if not isinstance(msg, dict):
                continue
            if typ == "assistant":
                mid = msg.get("id") or d.get("requestId")
                u = msg.get("usage")
                if u and mid not in seen_msg:
                    seen_msg.add(mid)
                    tot = 0
                    for k, name in (("input_tokens", "input"), ("cache_creation_input_tokens", "cache_create"),
                                    ("cache_read_input_tokens", "cache_read"), ("output_tokens", "output")):
                        v = u.get(k) or 0
                        tot += v
                        if not is_sub:
                            st.tokens[name] += v
                    if is_sub:
                        st.subagent_tokens += tot
                for b in msg.get("content") or []:
                    if not isinstance(b, dict) or b.get("type") != "tool_use":
                        continue
                    name, inp = b.get("name", "?"), b.get("input") or {}
                    pending[b.get("id")] = (name, inp)
                    st.tools[name] += 1
                    if name.startswith("mcp__"):
                        st.mcp[name.split("__")[1]] += 1
                    if name in ("Read", "mcp__dual-graph__graph_read") or name.endswith("__read_file"):
                        p = str(inp.get("file_path") or inp.get("file") or inp.get("path") or "")
                        p = norm_path(p.split("::")[0], st.root)
                        if p and TEMP_PATH.search(p):
                            st.temp_reads += 1
                            if "/tool-results/" in p:
                                st.overflow_reads += 1
                        elif p:
                            st.reads[p] += 1
                            st.read_sessions[p].add(session_id)
                            session_reads[p] += 1
                            if session_reads[p] > 1:
                                st.same_session_rereads[p] += 1
                        if last_was_search:
                            st.search_then_read += 1
                    elif name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
                        p = str(inp.get("file_path") or inp.get("notebook_path") or "")
                        if p:
                            st.edits[norm_path(p, st.root)] += 1
                    elif name == "Bash":
                        h = head_of(str(inp.get("command", "")))
                        if h:
                            st.bash_heads[h] += 1
                            st.bash_head_sessions[h].add(session_id)
                            heads_seq.append(h)
                    elif name in ("Agent", "Task"):
                        st.agent_calls += 1
                        st.agent_types[str(inp.get("subagent_type") or "general-purpose")] += 1
                    elif name == "Skill":
                        st.skills[str(inp.get("skill") or inp.get("command") or "?")] += 1
                    last_was_search = name in ("Grep", "Glob", "mcp__dual-graph__fallback_rg") or (
                        name == "Bash" and re.match(r"(rg|grep|find|fd|ag)\b", head_of(str(inp.get("command", "")))))
                    if last_was_search:
                        st.searches += 1
            elif typ == "user":
                content = msg.get("content")
                if d.get("toolDenialKind"):
                    st.denials[d["toolDenialKind"]] += 1
                if isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
                    for b in content:
                        if not isinstance(b, dict) or b.get("type") != "tool_result":
                            continue
                        name, inp = pending.get(b.get("tool_use_id"), ("?", {}))
                        n = result_len(b.get("content"))
                        st.result_chars[name] += n
                        if name == "Read" and n > BIG_RESULT_CHARS:
                            bp = norm_path(str(inp.get("file_path", "?")), st.root)
                            if not TEMP_PATH.search(bp):
                                st.big_reads[bp] += 1
                        if b.get("is_error") is True:
                            key = f"Bash: {head_of(str(inp.get('command', '')))}" if name == "Bash" else name
                            st.failures[key] += 1
                            sig = json.dumps(inp, sort_keys=True)[:500]
                            session_fail_inputs[sig] += 1
                            if session_fail_inputs[sig] > 1:
                                st.repeat_failures[key] += 1
                elif not is_sub and not d.get("isMeta"):
                    t = text_of(content).strip()
                    if t and not t.startswith("<"):  # skip command/system wrappers
                        st.user_turns += 1
                        if CORRECTION_RE.match(t):
                            st.corrections.append(
                                {"session": session_id[:8], "text": (SECRETISH.sub("<redacted>", t)[:140] if snippets else "")})
    for i in range(len(heads_seq) - 2):
        st.bash_seqs[tuple(heads_seq[i:i + 3])].add(session_id)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projects", nargs="+", help="project or repo paths (a workspace = several paths)")
    ap.add_argument("--sessions", type=int, default=30, help="most recent N sessions per project (default 30)")
    ap.add_argument("--days", type=int, default=0, help="only sessions modified in the last N days")
    ap.add_argument("--projects-dir", default="~/.claude/projects")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-snippets", action="store_true", help="omit user correction text")
    a = ap.parse_args()

    pdir = Path(os.path.expanduser(a.projects_dir))
    st = Stats()
    found = {}
    cutoff = time.time() - a.days * 86400 if a.days else 0
    ROOTS.extend(os.path.realpath(os.path.expanduser(p)) for p in a.projects)
    for proj in a.projects:
        st.root = os.path.realpath(os.path.expanduser(proj))
        dirs = slug_dirs(pdir, proj)
        files = sorted((f for d in dirs for f in d.glob("*.jsonl") if f.stat().st_mtime >= cutoff),
                       key=lambda f: f.stat().st_mtime, reverse=True)[: a.sessions]
        found[proj] = {"transcript_dirs": [str(d) for d in dirs], "sessions": len(files)}
        for f in files:
            st.sessions += 1
            mine_file(f, st, f.stem, False, not a.no_snippets)
            for sub in (f.parent / f.stem / "subagents").glob("*.jsonl"):
                st.subagent_files += 1
                mine_file(sub, st, f.stem, True, False)

    if a.json:
        json.dump({"projects": found, "stats": st.to_dict()}, sys.stdout, indent=1, default=list)
        return

    T = a.top
    tot_in = st.tokens["input"] + st.tokens["cache_create"] + st.tokens["cache_read"]
    print("# Transcript mining summary\n")
    for p, info in found.items():
        print(f"- {p}: {info['sessions']} sessions from {len(info['transcript_dirs'])} transcript dir(s)")
    if not st.sessions:
        print("\nNo transcripts found. Check the path; the slug is", ", ".join(slug_for(p) for p in a.projects))
        return
    print(f"- Window: {st.first_ts} .. {st.last_ts}; user turns: {st.user_turns}")
    print(f"\n## Tokens (main threads)\n- input total {tot_in:,} (cache read {st.tokens['cache_read']:,}, "
          f"cache write {st.tokens['cache_create']:,}, uncached {st.tokens['input']:,}); output {st.tokens['output']:,}")
    print(f"- per session: ~{tot_in // st.sessions:,} input, ~{st.tokens['output'] // st.sessions:,} output")
    print(f"- subagents: {st.agent_calls} Agent calls, {st.subagent_files} subagent transcripts, "
          f"{st.subagent_tokens:,} tokens; types: {dict(st.agent_types.most_common(6))}")
    print(f"- compactions: {st.compactions}")

    def section(title, counter, fmt=lambda k, v: f"- {v} × {k}", n=T):
        items = [(k, v) for k, v in counter.most_common(n) if v]
        if items:
            print(f"\n## {title}")
            for k, v in items:
                print(fmt(k, v))

    print("\n## Tool result volume (chars ≈ 4 per token)")
    for k, v in st.result_chars.most_common(T):
        print(f"- {k}: {v:,} chars in {st.tools[k]} calls (avg {v // max(st.tools[k], 1):,})")
    section("Tool calls", st.tools)
    section("Files read in the most sessions",
            collections.Counter({k: len(v) * 10_000 + st.reads[k] for k, v in st.read_sessions.items()}),
            lambda k, v: f"- {v // 10_000} sessions / {st.reads[k]} reads: {k}")
    print(f"- outside-repo temp/scratch reads: {st.temp_reads} ({st.overflow_reads} of them re-read harness "
          f"tool-results overflow files, i.e. a command printed more than the harness would inline)")
    section("Same-session re-reads", st.same_session_rereads, lambda k, v: f"- +{v} extra reads: {k}")
    section(f"Reads returning > {BIG_RESULT_CHARS:,} chars", st.big_reads)
    section("Most-edited files", st.edits)
    print(f"\n## Search churn\n- {st.searches} searches; {st.search_then_read} reads directly after a search")
    section("Bash command heads used in the most sessions",
            collections.Counter({k: len(v) for k, v in st.bash_head_sessions.items()}),
            lambda k, v: f"- {v} sessions / {st.bash_heads[k]} runs: `{k}`")
    print("  (generic heads such as ls/cat/grep are noise unless the run count is extreme)")
    section("Bash 3-step sequences repeated across sessions (script candidates)",
            collections.Counter({k: len(v) for k, v in st.bash_seqs.items()
                                 if len(v) >= 2 and len(set(k)) > 1 and sum(bool(GENERIC_HEADS.match(h)) for h in k) <= 1}),
            lambda k, v: f"- {v} sessions: `{' → '.join(k)}`")
    section("Failed tool calls", st.failures)
    section("Same input failed again in the same session (retry churn)", st.repeat_failures)
    section("Permission denials", st.denials)
    section("Skills invoked", st.skills)
    section("MCP servers used", st.mcp)
    section("Hook-injected context (chars, all sessions)", st.hook_chars, lambda k, v: f"- {v:,} chars: {k}")
    if st.corrections:
        print(f"\n## User corrections ({len(st.corrections)} of {st.user_turns} user turns)")
        for c in st.corrections[: T * 2]:
            print(f"- [{c['session']}] {c['text']}")


if __name__ == "__main__":
    main()
