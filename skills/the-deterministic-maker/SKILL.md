---
name: the-deterministic-maker
description: "Makes agent skills cheaper and more repeatable by moving work from the model to scripts. Measures what each skill costs to load and to run (tokens and API calls per run, commands the model types by hand, programs it writes at run time) with a bundled script, adds review-agent-memory's memory and transcript evidence, finds the steps where the model collects, counts, parses, or checks something a script could do, and reports the baseline with a ranked list of candidates. Then it makes the changes the user picks (a tested script plus a shorter SKILL.md step), measures again, and reports before and after with every number marked measured or estimated. Covers every skill in the skills folder by default, or only the skills named. Use when the user says /the-deterministic-maker, asks to make a skill or a skills project more deterministic, wants skills to burn fewer tokens, asks which skills cost the most to run, wants to replace LLM steps with scripts, or asks why a skill does by hand what a script could do, even if they don't say 'deterministic'."
user-invocable: true
argument-hint: '[skill ...] [--days N] [--project PATH] - skills to work on. Defaults to every skill in the skills folder.'
metadata:
  version: "1.0.0"
---

# The Deterministic Maker

A step the model does by reasoning costs tokens on every run and comes out a little different each time. The same step in a script costs one tool call, returns only what the model needs, and gives the same answer every time. This skill finds the steps that should be scripts, moves them, and shows the effect with numbers taken before and after.

The split is simple: the script gets the facts, the model keeps the judgment. `references/patterns.md` says which steps are which, how to write a script that removes cost instead of moving it, and how to estimate savings. Read it before step 3.

## Inputs

- **Targets**: the skills the user named, or every directory with a `SKILL.md` in `skills/` (then `.claude/skills/`). Edit only the targets. Skills vendored from elsewhere (for example under `.agents/`, or pinned in a lock file) are out of scope; if the user names one, say why you left it alone.
- **Window**: transcripts from the last 30 days across all projects, because a skill runs wherever it is installed. `--days N` changes the window and `--project PATH` counts one project only. Say which window you used.

## Workflow

### 1. Measure the baseline

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/measure_skills.py" snapshot [skill ...] --out docs/determinism-baseline.json
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; if your agent doesn't expand it, use the directory holding this SKILL.md. Run it from the project root. Keep the JSON: step 6 compares against it, and so does any later check.

The script prints four things. Use its numbers as they are; don't recount by hand.

- **Load cost**: tokens for each description (paid in every session), each body (paid in every run), and the references (paid when read).
- **Use cost**: per skill, the runs found in transcripts and the mean per run: API calls, output tokens, tool-result tokens, and a price-weighted total (cost-eq), plus the cost of the subagents each run started. The table is sorted by total cost with subagents, so the top rows are where the tokens go. When most of a skill's cost is in its subagents, look at what those subagents do by hand: a script inside the skill only helps if the subagents call it.
- **Commands run by hand**: the shell commands the model typed during runs instead of calling a bundled script. Many `grep`, `find`, `wc`, or `for f in` calls mean the model is collecting data itself. `python3 -`, `python3 -c`, or `cat >` followed by `python3` means it wrote a program at run time, which is the strongest sign that a script is missing.
- **Where to look**: lines in each SKILL.md that describe data work, and shell blocks with no script behind them. These are word matches. They tell you which lines to read, not what to conclude.

A skill with no runs in the window has static evidence only. Say so, and don't give it a per-month number.

### 2. Add project evidence from review-agent-memory

Run that skill's two collectors on the project. They sit beside this skill when both come from the same plugin or repo:

```bash
python3 "${CLAUDE_SKILL_DIR}/../review-agent-memory/scripts/collect_sources.py" .
python3 "${CLAUDE_SKILL_DIR}/../review-agent-memory/scripts/mine_transcripts.py" . --sessions 30
```

Take from them what bears on the target skills: memories that record a trap in a skill ("the eval script needs this exact layout"), three-step command sequences that repeat across sessions, commands that fail or get retried, and oversized reads of a skill's references. A memory that explains how to work around a skill is a step that skill should have scripted.

If the scripts aren't there, say that review-agent-memory isn't installed and continue with step 1's evidence. Findings that aren't about a target skill (instruction files, hooks, the repo's own code) belong to a full `review-agent-memory` run: name them in one line and move on.

### 3. Find candidates

Start with the skills at the top of the use-cost table, then the ones with recipe blocks or many by-hand commands. Read a SKILL.md only when the numbers point at it; with twenty skills, most need no more than their row.

For each step you suspect, apply the test in `references/patterns.md`: would two careful runs have to give the same answer? If yes, it is a candidate. Write down the step (`SKILL.md:line`), the evidence with numbers, the script that would replace it (inputs, what it prints), and what stays with the model.

Before a candidate goes on the list:

- **Look for a script that already does it**, in the skill, a sibling skill, or the repo (`scripts/`, a make target). If one exists, the fix is to call it, and that is a smaller and better change.
- **Keep judgment out.** A script can find every hit; deciding which hits matter stays with the model. Most steps are mixed, so split them.
- **Check it would pay.** A long script for a step that runs twice a year isn't worth its upkeep unless the step gives wrong numbers today.

A skill that is already scripted, or is all judgment, has no candidates. Say that plainly; an empty result is a correct result.

### 4. Rank and report

Estimate savings per `references/patterns.md` section 6 and show the arithmetic. Sort by estimated tokens saved per 30 days × confidence, with effort as the tiebreaker, and keep at most ten.

Write the report to `docs/determinism-report.md` in the project (or the path the user gives). If that file exists and its first line isn't `# Determinism Report`, pick a new name and say so.

```markdown
# Determinism Report

**Skills:** <n measured, or the names>  ·  **Window:** <days, projects>  ·  **Baseline:** <taken_at>, `docs/determinism-baseline.json`

## Baseline
<the script's Load cost and Use cost rows for the targets; the top ten by total cost when there are more>
<2-4 bullets on where the tokens go>

## Candidates

| # | Skill | Step → script | Evidence | Est. savings / 30 days | Effort | Confidence |
|---|-------|---------------|----------|------------------------|--------|------------|
| 1 | review-process | git history queries → extend `git-evidence.sh` | 14 by-hand `git log` calls in 6 runs | ~90k cost-eq | S | 8/10 |

### 1. <skill>: <step>
- **Now:** what the model does by hand (`SKILL.md:line`), with the numbers
- **Script:** name, inputs, what it prints and about how much
- **Stays with the model:** the judgment that remains
- **Savings estimate:** the arithmetic
- **Verify:** the test for the script, and the number that should move in `compare`

## Not candidates
<steps you looked at and left alone, one line each with the reason; skills with no runs; skills out of scope>
```

Then list the candidates by number and ask which to apply. Stop there: the edits change how skills behave, so the user picks. Go straight on only when the user already said to apply (for example "fix everything you find"), and then only for what they approved.

### 5. Apply the picked items

Work smallest first, one candidate at a time:

1. **Write the script** in the skill's `scripts/`, following `references/patterns.md` section 4. Its output is what the model will read on every run, so keep it short.
2. **Test it.** Add a test where the repo keeps its tests, with a small fixture and a known answer. At minimum run it on a real input and on a broken one. The model will trust the script's numbers, so a wrong script is worse than the prose it replaced.
3. **Rewrite the step** in SKILL.md: call the script, say what the output means and what decision it feeds, and delete the prose the script replaces. If the body got longer, cut again.
4. **Measure the script's output** on a real input (`... | wc -c`, divided by 4). That is a measured number for the final report.
5. **Follow the repo's rules for a changed skill**: version bumps, checklists, linters, tests. Don't commit unless the user asks.

### 6. Measure again

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/measure_skills.py" compare docs/determinism-baseline.json
```

Load cost before and after is measured from the files. Use cost after the change counts only runs that started after the baseline, so straight after an edit it reads "not measured yet". That is the honest state: nobody has run the new version.

### 7. Report the result

Append `## After` to the report with the two `compare` tables, then one line per applied item:

| Item | Measured now | Estimated per run | Estimated per 30 days |
|------|--------------|-------------------|-----------------------|
| 1. inventory → `inventory.py` | body 1,453 → 1,210 tokens; script prints ~180 tokens | ~4 calls and ~6k tool-result tokens fewer | ~30k cost-eq |

Keep measured and estimated numbers in separate columns and never present an estimate as a measurement. End with the command that turns the estimates into measurements once the skills have been used again:

```bash
python3 <path to>/measure_skills.py compare docs/determinism-baseline.json
```

In the final message give the before-and-after table for the changed skills, what you skipped and why, and that command.

## Privacy

Transcripts hold credentials, customer data, and private messages. Both skills' scripts print counts, paths, and short command heads only. Keep it that way: never read a transcript directly, and don't paste tool output into the report.
