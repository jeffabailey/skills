---
name: review-agent-memory
description: "Reads what coding agents have learned and suffered in a project — Claude Code auto-memory, CLAUDE.md/AGENTS.md/GEMINI.md and Cursor/Copilot rules, session transcripts, and context stores such as CONTEXT.md, dual-graph, CodeGraph, and graphify — and turns it into a ranked list of software architecture and harness improvements that cut token usage and agent churn. Mines transcripts with bundled scripts for repeated reads, oversized reads, search loops, failing and retried commands, permission denials, subagent fan-out, and hook-injected context, treats every gotcha memory as a gap the code should close, ranks fixes by estimated tokens saved, writes a report, and applies only what the user picks. Works on one repo or a workspace of several. Use when the user says /review-agent-memory, asks why agents burn so many tokens or keep going in circles in a repo, wants to reduce token usage, agent churn, or context bloat, asks what the agent's memory says about the codebase, wants to turn memories or lessons learned into code or tooling fixes, or asks how to make a project cheaper or easier for agents to work in, even if they don't say 'memory'."
user-invocable: true
argument-hint: '[path ...] [--sessions N] - repo(s) to review; several paths = a workspace. Defaults to the current repo.'
metadata:
  version: "1.0.0"
---

# Agent Memory Review

Agent memory is a record of where the project made agents work too hard. A memory that says "lint X is a false positive" or "the eval script needs this exact layout" is a trap every future session pays to step around. A file read in twenty sessions, or a command that fails the same way every week, is the same story told by the transcripts. This skill collects that evidence and proposes **structural** fixes — in code, tooling, layout, and harness config — ranked by how many tokens and interruptions they would save. It does not edit anything until the user picks.

The strongest fix makes the problem stop happening (delete the trap, or encode it in a script, test, or config). Adding a line to an instruction file is the weakest fix: it costs tokens every session and still relies on the agent obeying it. `references/catalog.md` spells out that order; read it before you rank anything.

## Inputs

- **Targets**: the paths the user named, or the current repo. Several paths make a workspace review: findings that repeat across repos become one workspace-level item.
- **Window**: the last 30 sessions per repo by default (`--sessions N`, `--days N`). Say what window you used.

## Workflow

### 1. Collect sources (cheap, structured)

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/collect_sources.py" <path> [<path> ...]
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; if your agent doesn't expand it, use the directory holding this SKILL.md.

It lists, per repo: always-loaded instruction files with token estimates (including ancestor CLAUDE.md files and MEMORY.md), rules and skills for every harness it knows, hooks (which inject hidden context), context stores and their size, auto-memory entries by name and description, and memory hygiene problems: dangling index links, unindexed files, stale absolute paths, and relative paths it couldn't resolve. It also notes global files and whether cross-harness copies are symlinks or drifting copies.

Only open a memory or instruction file when a finding depends on its exact wording. The descriptions are usually enough to triage.

### 2. Mine transcripts (never read raw transcripts)

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/mine_transcripts.py" <path> [<path> ...] --sessions 30
```

Transcripts run to hundreds of megabytes and contain secrets and tool output, so never `cat`, `grep`, or Read them. The miner prints counts, paths, and short command heads only: token totals (main and subagent), tool-result volume per tool, files read across the most sessions, same-session re-reads, oversized reads, harness overflow re-reads, search-then-read churn, Bash heads and repeated 3-step sequences, failures and same-session retry failures, permission denials, skills and MCP servers used, hook-injected chars, compactions, and user-correction lines. Add `--json` if you need to compute something it doesn't print. Add `--no-snippets` if the user doesn't want their own messages quoted in the report.

The miner reads Claude Code transcripts only. If `collect_sources.py` shows other harnesses in active use (Codex sessions, Cursor rules), say their transcripts weren't mined, and base those findings on their instruction files alone.

If a repo has no transcripts, say so and continue with memory and instruction files. The report is thinner, not invalid.

### 3. Turn signals into candidate findings

Walk `references/catalog.md` section by section against the two outputs. For each candidate, write down the signal (with numbers), what it means, and the improvement. Things worth knowing when you read the numbers:

- **Separate the project from the work done there.** A repo where people do skill evals or blog writing will show scratchpad reads and scripts that aren't the repo's fault. The miner splits repo paths from temp paths; findings about the repo's architecture should rest on repo paths. Workflow-level churn (for example, a skill that fans out too many subagents) is still a finding, but name the workflow, not the repo's code.
- **Generic command heads are noise** (`ls`, `cat`, `python3 -`) unless one is failing a lot. Forty failing `cat` calls means agents guess paths. That's a navigation finding.
- **Verify before you report.** For each candidate, check the cited file, memory, or command yourself: confirm the path exists, the memory says what you claim, and `git log` doesn't show it already fixed. Drop what you can't verify, and count the drops.
- **Check what the repo already does.** Before recommending a script, look for an existing make target or script that does the job. If one exists, the finding is "agents don't know it exists", which calls for a discoverability fix.
- **Defer instead of duplicating.** Line-by-line CLAUDE.md/AGENTS.md restructuring belongs to `agent-hygiene`; permission allowlists to `fewer-permission-prompts`; a deep code-structure audit to `review-architecture`. Recommend those skills by name when a finding is really theirs, but only if they're installed (check the skill list).

### 4. Rank

Estimate savings per catalog section 7 and show the arithmetic. Then sort by estimated monthly savings × confidence, with effort as the tiebreaker. Keep the top 10 at most; a short list the user acts on beats a long one they skim. Interruptions (corrections, denials, failed attempts) rank alongside tokens. Don't convert them into made-up token numbers.

### 5. Write the report

Write the report to `docs/agent-memory-review.md` in the target repo. For a workspace review, write it to `agent-memory-review.md` in the common parent directory, or to the path the user gives. If the file exists and isn't an earlier report from this skill (first line `# Agent Memory Review`), pick a new name and say so. Never put secrets, tokens, or raw tool output in the report. Cite file:line, memory filenames, session-ID prefixes, and counts.

```markdown
# Agent Memory Review

**Target:** <repo(s)>  ·  **Window:** <N sessions, date range>  ·  **Harnesses seen:** <claude, codex, ...>

## Where the tokens go
<3-6 bullets: main vs subagent tokens per session, top tool-result volume, always-loaded estimate, hook injection, compactions. Numbers from the scripts.>

## Ranked improvements

| # | Improvement | Kind | Evidence | Est. savings / month | Effort | Confidence |
|---|-------------|------|----------|----------------------|--------|------------|
| 1 | Wrap lint in `make lint` with the cli2 config | code: tooling | memory `x.md`; 12 failed `markdownlint` runs in 5 sessions | ~40k tok + 5 interruptions | S | 8/10 |

Kind is one of: code: structure / code: tooling / code: tests / harness: instructions / harness: memory / harness: hooks / harness: context tools / workflow.

### 1. <Improvement>
- **Signal:** what the evidence shows, with numbers and where it came from
- **Why it costs:** the mechanism (what the agent keeps doing, and why)
- **Change:** the concrete edit, file by file; what to delete afterwards (often the memory itself)
- **Savings estimate:** the arithmetic
- **Verify:** how to tell it worked (for example, re-run the miner after a few sessions)

(repeat per item)

## Memory hygiene
<stale, duplicate, misplaced memories, and index fixes: a short list, each with the action>

## Not mined / limits
<harnesses not mined, thin windows, candidates dropped and why>
```

### 6. Offer to apply

After the report, list the items by number and ask which to apply. Group them so the user can choose quickly: harness-only items (memory and index fixes, hook trims), which are low risk, and code or tooling items, which change the repo. Apply only the picked items, smallest first. After code changes, run the repo's own checks. Delete or update a memory only as part of the item that made it unnecessary. Don't commit unless the user asks.

## Privacy

Transcripts and memory can hold credentials, customer data, and private messages. The scripts are built to emit counts and paths only, and the miner redacts `key=value` secrets in command heads. Keep it that way: don't paste tool output or transcript text into the report, and quote user-correction snippets only when they explain a finding (`--no-snippets` drops them entirely).
