# Signal → improvement catalog

Each row pairs something the evidence shows with the structural change that removes it. The fix should make the problem stop happening, not just remind the agent about it. An improvement that adds a line to CLAUDE.md is the weakest kind, because it costs tokens every session and still depends on the agent obeying it. Prefer, in order: **delete the need** (the code or tooling no longer has the trap) > **encode it** (script, test, lint, config, type) > **make it cheap to find** (index, split, entry point) > **document it** (one line in the right instruction file).

## Contents

1. Memory-derived signals
2. Reading and navigation churn
3. Command and tooling churn
4. Subagent churn
5. Always-loaded context
6. Context-tool sprawl
7. Estimating savings

## 1. Memory-derived signals

| Signal | What it means | Improvement |
| --- | --- | --- |
| A `project` or `reference` memory describes a gotcha ("X silently fails unless Y", "tool A needs flag B", "these warnings are false positives") | The project has a trap that every agent has to learn. The memory is a patch over an architecture gap. | Remove the trap: fix the default, add a wrapper script or make target with the right flags, add a test or check that fails loudly, or suppress the false positive in the tool's config. Then delete the memory. |
| A memory says which command, file, or config to use ("run markdownlint-cli2, not markdownlint") | There are two ways to do something and one is wrong. | Make the right way the only easy way: one `make lint` / `scripts/lint.sh` / package script, and remove or alias the wrong entry point. |
| A memory records a layout or schema the code demands ("needs `eval-N/<config>/run-1/`") | A contract the code doesn't enforce. | Validate the contract in code with a clear error, or accept both shapes. |
| A `feedback` memory about agent behavior (tone, asking, pacing) | Not an architecture issue. | Leave it unless it is duplicated, contradicted, or stale. Don't turn behavior preferences into code. |
| Memory points at a file, flag, or command that no longer exists | Stale memory: it now misleads. | Delete or update it. Only call it stale after checking the path yourself; relative paths may belong to another tool. |
| Two memories, or a memory and CLAUDE.md, say the same thing | Duplication: double tokens, and they drift. | Keep one source. Memory for personal or ephemeral facts; checked-in instruction files for project facts every contributor's agent needs. |
| A memory holds a project fact that teammates' agents would also need | Knowledge stuck on one machine. | Move it into the repo (instruction file, `docs/`, or better, code), then delete the memory. |
| MEMORY.md index links with no file, or memory files missing from the index | The index is broken; the memory is invisible or noisy. | Fix the index. |
| CONTEXT.md, a context store, or nWave state with a "next step" that git history shows is done | Stale handoff state sends the next session down a finished path. | Update or clear it. If it keeps going stale, propose a wrap-up step or hook that rewrites it. |

## 2. Reading and navigation churn

| Signal | What it means | Improvement |
| --- | --- | --- |
| The same repo file is read in many sessions | A hub that every task needs. | If it's large: split it along change reasons, or put a short index/summary at the top. If it's small and central: fine, but check whether instruction files tell agents to read it when a smaller entry point would do. |
| Same file read several times in one session | The agent lost it to compaction, or read it in slices hunting for something. | Add a table of contents or anchors; split by section; give the agent a script that answers the question it was hunting for. |
| Reads returning > 20k chars (≈5k tokens) | Whole-file reads of big files. | Split the file; move rarely needed parts to referenced files; for data or docs, a script or `grep -n '^#'` heading index. |
| Many searches with reads right after | The agent has to hunt to find where things live. | A short map (where the entry points, layers, and tests live) in the instruction file or a `docs/ARCHITECTURE.md`; consistent naming so one grep finds it; co-locate code that changes together. |
| Reads of `tool-results/` overflow files | A command printed more than the harness inlines, so the agent paid to re-read it. | Make the command quieter: a `--quiet` / summary mode, log to a file and print the tail, a script that prints only counts. |
| A small set of files edited in most sessions | Change hotspots. | Check cohesion: a file that changes for many reasons should be split. Cross-check with `git log` churn. |

## 3. Command and tooling churn

| Signal | What it means | Improvement |
| --- | --- | --- |
| The same multi-step command sequence across sessions | A workflow the repo doesn't capture. | Bundle it: a make target, a script in `scripts/`, or a skill if it needs judgment. Name it in the instruction file in one line. |
| One command head fails often (`cat`, `ls` failing = guessed paths; a test or lint command failing = environment or flags) | Agents guess at paths or invocation. | Guessed paths: add the map from section 2. Invocation failures: a wrapper with correct flags and a clear error, pinned tool versions, a `make doctor`/setup check. |
| The same input fails again in the same session | Retry churn: the agent retries without new information. | Make the error message say what to do; fix the flaky tool; a timeout or skip rule in the instruction file only if code can't fix it. |
| Many permission denials or blocked calls | The agent keeps trying actions the harness forbids. | Allowlist the safe read-only ones (`fewer-permission-prompts` skill); for the rest, give a sanctioned alternative (a script) so the agent stops attempting them. |
| Heavy `python3 -` / heredoc use for the same kind of analysis | The agent writes the same throwaway script repeatedly. | Check it in as a script. |

## 4. Subagent churn

| Signal | What it means | Improvement |
| --- | --- | --- |
| Subagent tokens far above main-thread tokens | Fan-out is the main cost. | Check the workflows (skills, CLAUDE.md rules, nWave waves) that spawn them. Replace exploratory subagents with deterministic scripts; narrow briefs; cap fan-out; use cheaper models for review-only roles. |
| Failed or retried Agent calls | Briefs that are unclear, or work that times out. | Smaller units of work; pass file paths instead of pasted content; deterministic inputs. |
| Many subagents of one type doing similar work | Repeated discovery. | Precompute what they all rediscover (an index, a summary file) once and point them at it. |

## 5. Always-loaded context

| Signal | What it means | Improvement |
| --- | --- | --- |
| Always-loaded estimate is high (CLAUDE.md chain, MEMORY.md, AGENTS.md, rules) | Every turn pays for it, and long instructions get followed less. | Progressive disclosure: keep the always-loaded file to what every task needs and point to detail files. Line-level pruning and restructuring is `agent-hygiene`'s job; recommend it rather than doing it here. |
| SessionStart / UserPromptSubmit hooks inject a lot of text | Hidden always-loaded context. | Trim hook output to what changes decisions; show it once per session, not per prompt. |
| Instruction files copied (not symlinked) across harnesses | They drift. | One source, with symlinks or an `@AGENTS.md` import. |
| Instructions that restate what config or code already enforces | Paying tokens for something enforced anyway. | Delete the line. |

## 6. Context-tool sprawl

| Signal | What it means | Improvement |
| --- | --- | --- |
| Several code-context tools mandated at once (dual-graph, CodeGraph, graphify, Serena) with overlapping "call me first" rules | Each one injects listings, hooks, and rules, and they compete. The agent pays for all of them and follows none fully. | Measure which ones are actually used (MCP server counts in the miner) and against what. Pick one primary per repo; demote or remove the rest, including their hooks and instruction blocks. |
| A mandated tool that transcripts show is never or rarely called | Dead weight in context. | Remove its instructions or hooks, or make the instruction conditional. |
| Large git-ignored stores with no recent use | Disk only, but a sign of abandoned tooling still wired into hooks. | Check its hooks; remove the wiring if it's unused. |

## 7. Estimating savings

Rank by **estimated tokens saved per month**. The miner does the arithmetic (occurrences per session × sessions per month × tokens per occurrence) and prints it so the user can check it:

```bash
mine_transcripts.py --window <S:D> --estimate '<label>:<count>:<tokens>[:cached]' ...
```

- `--window`: copy it from the miner summary's "sessions per month" line.
- `count`: occurrences the fix removes in the whole window, as the miner printed them (failed runs, extra reads, calls).
- `tokens`: per occurrence. Tool results: the "avg ≈ tok" figure. Re-reads and big reads: the file's token size beside its path, or from `collect_sources.py --size`.
- Always-loaded context: `count` is the miner's "requests in the window", `tokens` is the size of the text to remove, and `:cached` weights it at a tenth, because it rides in every request as cache reads. It still fills the context window and brings compaction closer.
- Churn that isn't tokens (a user correction, a failed attempt, a permission prompt) costs human attention. Count it separately as "interruptions per month" rather than inventing a token figure.

Label every estimate as an estimate. When the evidence is thin (one session, one occurrence), give the item low confidence instead of a big number.
