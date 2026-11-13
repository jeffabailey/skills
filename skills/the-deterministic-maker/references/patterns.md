# Patterns: what to move from the model to a script

## Contents

1. The test
2. Steps to move
3. Steps to leave with the model
4. Writing a script that removes cost
5. Rewriting the SKILL.md step
6. Estimating savings
7. When not to bother

## 1. The test

Ask of each step: **would two careful runs have to give the same answer?**

If yes, the answer is a fact about files, history, or numbers, and a script should produce it. If two good reviewers could reasonably differ, the step needs meaning, and it stays with the model.

Most real steps are both. "Find the functions over 50 lines and decide which ones hurt" is a fact followed by a judgment. Split it: the script lists the functions, the model judges the list.

## 2. Steps to move

| Pattern | In SKILL.md it reads like | In transcripts it shows as | The script |
|---------|---------------------------|----------------------------|------------|
| Inventory | "find every instruction file", "list all workflows" | `find`, `ls`, `for f in`, `git ls-files`, Reads made only to learn a size | prints each path with the attributes the step needs |
| Counting and arithmetic | "count", "total", "weighted average", "`wc -c` ÷ 4", a scoring formula | `wc`, `python3 -c`, sums written out in the reply | computes and prints the numbers and their inputs |
| Parsing | frontmatter, JSON, lockfiles, coverage XML, JUnit | `jq`, `python3 -`, `grep -A` | prints only the fields the step uses |
| Pattern scan | a fixed list of regexes or banned phrases | one `grep -nE` call per pattern | runs the whole list once and prints `file:line rule` hits, capped |
| History query | churn, authors, commit shape | several `git log` variants | prints one summary |
| Gate | "check that every…", "done when…" | re-reading files to confirm | exits 0 or 1 with one line per failure |
| Fixed edit | version bumps, renames, filling a template | the same Edit repeated across files | makes the edit, and is safe to run twice |
| Recipe | a shell block of three or more commands | the same command sequence in every run | one entry point that runs them |
| Run-time program | none, which is the problem | `python3 -`, `cat > x.py` then `python3 x.py`, a high "Inline code" count | that program, written once and tested |

The last row is the strongest signal. When the model writes a program in most runs of a skill, it has shown you the script that is missing.

## 3. Steps to leave with the model

- Judging quality, severity, risk, or intent.
- Deciding whether a hit is a real finding. The script finds hits; the model rules on them.
- Ranking when the trade-offs depend on the project.
- Explaining, summarizing, and writing prose.
- Choosing between approaches.
- Anything whose input is open-ended natural language.

Don't script these to make a number go down. A skill that is cheap and wrong has not improved.

## 4. Writing a script that removes cost

The script's output goes into the model's context on every run. A script that prints 20,000 characters has moved the cost, not removed it.

- **Print the decision's inputs and nothing else.** Counts, `file:line`, short labels. Cap lists ("top 10, and 37 more") and offer `--all` or `--json` for the rare run that needs everything. Aim for under about 500 tokens on a typical input and 2,000 at worst.
- **One call does the whole step.** Take every input as an argument. If the model must call it five times, wrap the loop inside.
- **Same input, same output.** Sort everything. Leave out timestamps, durations, and absolute temp paths unless the step is about them.
- **Fail in one line.** Exit non-zero with a message that says what to fix. A traceback for an expected error costs tokens and starts a retry loop.
- **Use the standard library** unless the repo already carries the dependency. A missing import is a failed call and a second try.
- **No secrets and no file contents.** Print where something is, not what it says.
- **`--help` and the docstring carry the usage**, so SKILL.md doesn't have to list flags.
- **Match the repo**: its language, its lint rules, its test layout.
- **Extend before you add.** If the skill has a script that covers half the step, give it a subcommand.

Test with a small fixture that has a known answer, including an empty and a malformed input.

## 5. Rewriting the SKILL.md step

Replace the prose; don't add a script call above it.

Before:

```markdown
2. Find every instruction file (CLAUDE.md, AGENTS.md, .cursor/rules/*). For each one record the
   path, tier, line count, and a token estimate (`wc -c` ÷ 4), then sum the always-loaded total.
```

After:

```markdown
2. Run `python3 "${CLAUDE_SKILL_DIR}/scripts/inventory.py" <target>`. It prints one row per
   instruction file (path, tier, lines, tokens) and the always-loaded total. Use the rows as they are.
```

- Say what the output means and which decision it feeds.
- Tell the model to trust it: "open a file only when a finding depends on its wording."
- Don't keep the old prose as a fallback. That doubles the body. If the script can fail, one sentence says what to do then.
- Keep the judgment step that follows, and make it start from the script's output.

## 6. Estimating savings

Use the baseline numbers and show the arithmetic. Estimate per run first, then per 30 days.

Per run, a moved step saves:

1. **API calls removed.** The by-hand calls the step makes now, minus one for the script. Take the count from "Commands run by hand" divided by the runs. Commands sent in parallel share one API call, so count turns, not commands; when you can't tell, halve the number.
2. **The cost of those calls.** Each call rereads the conversation. Price it at the skill's own mean: `cost-eq per run ÷ API calls per run`, times the calls removed.
3. **Tool-result tokens removed.** What the by-hand calls returned, minus what the script prints. Measure the script's output once it exists.
4. **Output tokens removed.** The commands and programs the model no longer writes: about 30 to 80 tokens for a plain command, 200 to 600 for an inline program, more if it also wrote the table or the sums by hand.

Items 3 and 4 are already inside item 2 when you price whole calls. Use item 2 for the headline and give 3 and 4 as the breakdown, not as additions.

Per 30 days: per-run saving × `runs_per_30d` from the baseline JSON. The body change is separate and measured: `compare` prints the body delta times the run rate.

Confidence:

- **8 to 10**: the by-hand commands appear in three or more runs.
- **5 to 7**: one or two runs, or the evidence is a memory.
- **Below 5**: static hints only. Give the per-run estimate and write "no usage data" in place of a 30-day number.

Failed calls and retries count as interruptions. List them as a count; don't turn them into tokens.

## 7. When not to bother

- The skill has no runs in the window and the step is small.
- The saving is under about 5,000 cost-eq per 30 days, unless the step produces wrong numbers today. Then correctness is the reason, and say so.
- The step changes shape with every project and can't be given clean arguments.
- A tool the repo already has does it (a make target, a linter, another skill's script). Call that.
- The script would need a network call, credentials, or a heavy dependency that the skill doesn't have now.
