---
name: agent-hygiene
description: "Cleans up the instruction files agents read in a repo (AGENTS.md, CLAUDE.md, GEMINI.md, nested agent files, Cursor and Copilot rules, skills, subagent definitions). Audits every line for no-ops, duplication, stale claims, restated config, negation, and sprawl, then runs three subagents that each propose a restructuring, each more radical than the last: prune, progressive disclosure, rebuild. Compares them by always-loaded size and lost instructions, and applies only the one the user picks. Use when the user says /agent-hygiene, says their AGENTS.md or CLAUDE.md is a mess, bloated, or contradictory, asks to remove no-ops, use progressive disclosure, move rules into CODING_STANDARDS.md, or slim down agent instructions."
user-invocable: true
argument-hint: '[path or focus] - Optional subtree to audit and extra goals, e.g. "move style rules to CODING_STANDARDS.md"'
---

# Agent Hygiene

Agent instruction files collect **sediment**: lines get added because adding feels safe and never removed because removing feels risky. This skill digs the live instructions out, proposes three restructurings of rising radicalness, and applies the one the user chooses.

**Mode**: read-only until Step 5. Proposals are written to a scratch directory outside the repo. Nothing in the repo changes until the user picks a proposal.

**Goals**: the user's own goals (the argument, or the message that invoked this skill) bind every step and every subagent. With no goals given, use the defaults: remove no-ops, apply progressive disclosure, and move coding rules into `CODING_STANDARDS.md`.

## Workflow

### Step 1: Inventory

Find every file an agent reads in the target (repo root, or the path argument):

- **Always-loaded**: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` at every level, `.github/copilot-instructions.md`, `.cursor/rules/*`, `.cursorrules`, `.windsurfrules`, and every skill or subagent `description` (`SKILL.md` and `.claude/agents/*.md` frontmatter).
- **Disclosed**: any file one of those points at (`CODING_STANDARDS.md`, `CONTRIBUTING.md`, `docs/…`, skill bodies and `references/`).
- **Imports**: `@path` includes in `CLAUDE.md` load their target too, so count the target as always-loaded.
- **Ancestors**: `CLAUDE.md` and `AGENTS.md` in directories above the repo root load too. Count them as always-loaded and flag what they duplicate, but propose changes to them only if the user asks, since other repos share them.

Record, for each file: path, tier, line count, and a token estimate (`wc -c` ÷ 4). Also record which files are symlinks or copies of each other.

**Done when** the table lists every file and the always-loaded total is summed.

### Step 2: Audit

Invoke `mattpocock-skills:writing-for-agents` for the principles behind the audit. It is a soft dependency: if that skill is not installed, tell the user the audit will be rougher without it (install with `/plugin install mattpocock-skills@claude-plugins-official`) and continue. Then read [`references/rubric.md`](references/rubric.md), which turns those principles into ledger actions, and classify **every line** of every always-loaded file, and every disclosed file a pointer reaches, as one of: keep, cut, move (with destination), rewrite (with reason). Each non-keep line carries a finding with `file:line`, the rubric category, and the evidence (for stale claims: the command you ran or the path that does not exist).

Verify, don't assume: run `ls`, `--help`, `cat package.json`, `git log -S` to test each concrete claim a line makes about the repo.

Save the result as the **ledger** at `$TMPDIR/agent-hygiene/<repo-name>/ledger.md`.

**Done when** every line of every always-loaded file appears in the ledger exactly once.

### Step 3: Three proposals

Dispatch three subagents in one message so they run in parallel. Brief each one with [`references/proposal-brief.md`](references/proposal-brief.md), filling in its tier, the ledger path, the user's goals, and its output directory:

| Tier | Name | Moves allowed |
|---|---|---|
| 1 | **Prune** | Delete no-ops, duplicates, and stale lines; tighten wording. File layout stays as it is. |
| 2 | **Disclose** | Tier 1, plus move reference material out of always-loaded files into disclosed files behind sharp pointers (`CODING_STANDARDS.md`, `docs/agents/…`). |
| 3 | **Rebuild** | Start from an empty always-loaded file. Readmit only what the agent needs on every turn and cannot find by looking. Everything else is disclosed, merged, or deleted. May merge, rename, or delete instruction files and convert duplicated `CLAUDE.md`/`AGENTS.md` pairs to one file plus an import or symlink. |

Each subagent writes complete replacement files under `$TMPDIR/agent-hygiene/<repo-name>/tier-<n>/`, mirroring repo paths, plus a `PLAN.md`.

If the harness has no subagent tool, write the three proposals yourself, one after another, finishing each before starting the next.

**Done when** all three tier directories exist and each has a `PLAN.md`.

### Step 4: Verify and compare

For each tier, check:

1. **Nothing lost**: every ledger line marked keep, move, or rewrite is present in that tier's files (verbatim or rewritten). A missing line is a defect: send it back to that subagent or fix it yourself, and note it.
2. **Pointers resolve**: every path a proposed file names exists in the repo or in the proposal.
3. **Size**: always-loaded lines and tokens, before and after.

Then show the user one table and a short verdict:

| | Always-loaded lines | Tokens | Files added / removed | Risk |
|---|---|---|---|---|
| Today | | | | |
| Tier 1 Prune | | | | |
| Tier 2 Disclose | | | | |
| Tier 3 Rebuild | | | | |

Under the table, give each tier two or three lines: what it does and the biggest risk (for example, "a rule moved behind a pointer the agent may not follow"). Recommend one tier, and say why. Offer `diff -ru` against the repo for any tier the user wants to read in full.

**Done when** the user has the table, the verdicts, and a recommendation, and you have asked which tier to apply (a tier, a mix such as "tier 2 but keep the testing section inline", or none).

### Step 5: Apply

Copy the chosen proposal into the repo, apply any mix the user asked for, and delete files the plan removes only after showing their paths. Then:

- Re-run the Step 4 pointer check against the real repo.
- Run the repo's markdown lint, if it has one, on the changed files.
- Report the files changed and the final always-loaded size.

Leave committing to the user unless they ask; when they do, commit only the files this skill changed.

**Done when** the chosen proposal is in the repo, every pointer resolves, and lint passes or its failures are reported.
