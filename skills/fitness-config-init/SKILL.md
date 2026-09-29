---
name: fitness-config-init
description: Creates a fitness-config.json for a project with review weights that fit what the project is for. Scans the folder (or runs a full review first, if asked), classifies its purpose, proposes weights starting from a matching purpose profile, explains every change, and saves only the proposal the user approved. Use when the user says /fitness-config-init, asks to "create a fitness config", "set up fitness-config.json", "initialize fitness config", "tune review weights for this project", "weight the review for this repo", or wants the fitness review to reflect a project's purpose instead of the defaults.
argument-hint: '[fast|full] [path] - evidence mode and target folder (defaults: ask, current folder)'
---

# Fitness Config Init

Create `fitness-config.json` for a project so the review skills weigh what matters for it. A database backend should count reliability and data heavily and accessibility barely at all. A public website should count accessibility first. This skill works out which kind of project it is looking at, proposes weights from a matching profile, and saves them only after the user has seen the proposal.

The weights themselves live in `references/purpose-profiles.md` and in the resolver. This file never states a weight. Always take numbers from the resolver output or the profile table.

## References

- `references/purpose-signals.md`: what to read in the fast scan, the 40-file budget, signals per archetype, and what high, medium and low confidence mean.
- `references/purpose-profiles.md`: the six archetype profiles, the rules for adjusting them, and typical rationale for each.

Read both before step 3.

## Resolver

Every config read and write goes through the resolver CLI. Never load `fitness-config.json` yourself and never write it with a file tool.

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py" <command>
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; the resolver ships two levels up in the plugin's `scripts/`. If your agent does not expand the variable, substitute the directory containing this `SKILL.md`.

Run every resolver command from the **anchor**: the git top-level of the target (`git -C <target> rev-parse --show-toplevel`), or the target itself when it is not in a git repository. Pass the target relative to the anchor.

| Purpose | Command |
|---|---|
| Starting config (baseline) | `init --path <target> --dry-run` |
| Check a proposal, get its fingerprint | `init --path <target> --from - --dry-run` (proposal JSON on stdin) |
| Save a reviewed proposal | `init --path <target> --from - --expect <fingerprint>` (same JSON on stdin) |
| Confirm what applies after saving | `show --path <target>` |

## Workflow

### Step 0: Target and probe

1. The target is the path argument, or the current folder. Print it as the first line of output: `Target: <absolute path>`.
2. Find the anchor. If there is no git repository, say "No repository found; ancestor configs not considered."
3. Run `init --path <target> --dry-run`. It writes nothing. Relay its header lines verbatim (`STATUS:`, `Baseline-Source:` and any chain lines) and keep the canonical JSON block as the **baseline**. The baseline is the built-in starting config at the repository root, or the merged parent configs for a subfolder.
4. If the command fails (no `python3`, the path did not expand, the resolver errors), switch to **degraded mode**: read `${CLAUDE_SKILL_DIR}/../../fitness-config.example.json` as the baseline, label it "example file (degraded)", and continue through step 5 printing the proposal for manual use. Degraded mode never saves. If the example file is also unreachable, stop and say why.

### Step 1: Evidence mode

- **fast** (default): a read-only scan of at most 40 files.
- **full**: runs `review-full` on the target first, then the fast scan.

Take the mode from the argument only if it is exactly `fast` or `full`. Otherwise use the request text: it means full only if it says "full review", "full mode" or "run review-full" and does not also say "fast" or "quick"; it means fast if it says "fast" or "quick" and nothing about full. In every other case, ask `Evidence mode: fast scan or full review? [fast]` and treat Enter as fast. Never upgrade to full on your own.

Before a full review, warn and wait for a yes: "A full review runs every review skill and writes `docs/fitness-report.md` into the project. Continue? [y/N]". Anything other than `y` or `yes` falls back to fast.

### Step 2: Gather evidence

- **Fast:** follow the scan order in `references/purpose-signals.md`. Stay within 40 file reads. Do not run project code or use the network. Do not change any file.
- **Full:** run the `review-full` skill with its scope set explicitly to the target folder (never the default of pending changes), then do the fast scan as well. Read `docs/fitness-report.md` afterwards:
  - If its `**Scope:**` line shows that only pending changes were reviewed (not the target folder), drop all full review evidence and tell the user: "The full review only covered pending changes, so its results were not used."
  - If a domain failed or has no parsable row, use fast scan evidence for that domain only and say so. The other domains keep their full review evidence.

Each evidence item is a path that a read or list tool returned, a short note on what it shows, and its source (`fast` or `review-full`).

### Step 3: Classify the purpose

Classify as one archetype from `references/purpose-profiles.md`, `mixed`, or `unknown`, with a confidence level from `references/purpose-signals.md`. Show the purpose in plain words, the archetype, the confidence and the evidence list.

- **high:** go on to step 4.
- **medium or mixed:** ask "What is the primary purpose of this project?" and offer the archetypes. For a mixed repository, add that a subfolder can get its own config later by running this skill on that folder. Do not create one.
- **low or unknown:** ask the same question once. With no answer, say "Kept baseline: not enough evidence to tune." and propose the baseline unchanged, with no reasons.

If the user corrects the classification, use their answer without argument.

### Step 4: Propose

1. Start from the archetype's row in `references/purpose-profiles.md`.
2. Adjust using this project's evidence, following the rules in that file: no more than 4 points per domain from the profile, a cited reason for every move, whole numbers of at least 1, total of 100. Full review results only lower domains that do not apply; a low score never raises a weight.
3. Build the complete proposal: the baseline JSON with the `weights` section replaced. Keep `statusThresholds`, `security` and `scoring` from the baseline unless the evidence shows higher stakes (payments, credentials, personal data). Change a threshold only with a stated reason citing that evidence, and add a row for it to the table below. For an ordinary project, keep the starting thresholds and say there is no stakes signal to change them. The status bands must cover every score from 1 to 10 once, with no gap or overlap; the security cutoff stays between 1 and 10.
4. Print the rationale table, one row per weight in resolver order, then one row per changed threshold:

   | key | baseline | proposed | reason |
   |---|---|---|---|
   | `weights.<domain>` | from baseline | from proposal | one line citing an evidence path, or `(unchanged)` |

   There is exactly one reason for each value that differs from the baseline. Keep each reason under about 100 characters.
5. Show the total. Apply any change the user asks for ("raise X, take it from Y"), rebalance to 100, and print the table again.

The rationale is printed only. It is never written into the config file.

### Step 5: Check the proposal

Pipe the proposal JSON to `init --path <target> --from - --dry-run`. This writes nothing.

- Relay the `STATUS:` and `Proposal:` lines verbatim and show the canonical JSON block exactly as printed. The `Proposal:` value is the fingerprint.
- `STATUS: invalid`: show each error line, fix the proposal, and run the check again.
- `STATUS: would-create`: ask "Save this as `<target>/fitness-config.json`? [y/N]".
- `STATUS: would-replace`: a config already exists. Show every diff line the resolver printed (`path old -> new`, then `(N values unchanged)`), then ask "Overwrite `<target>/fitness-config.json`? [y/N]".
- `STATUS: existing-malformed`: the current file is not valid JSON, so there is no diff. Say so, show the proposal, and ask the same overwrite question.
- `STATUS: unchanged`: the current config already equals the proposal. Say there is nothing to save and skip to step 7.

### Step 6: Save

Only an answer of `y` or `yes` (any case) is a go-ahead. Anything else, including an empty answer, means No: say nothing was written and stop.

- After a go-ahead for `would-create`, pipe the **same** JSON to `init --path <target> --from - --expect <fingerprint>` with the fingerprint from step 5.
- After a go-ahead to overwrite (`would-replace` or `existing-malformed`), pipe the **same** JSON to `init --path <target> --from - --expect <fingerprint> --force`. The resolver replaces the file atomically and puts the old bytes back if the check after writing fails.

- `STATUS: created` or `replaced`: go to step 7.
- `STATUS: unchanged`: the file already held this config and was not touched. Go to step 7.
- `STATUS: fingerprint-mismatch`: the JSON changed since the check. Run step 5 again and ask again.
- `STATUS: refused-exists`: a config appeared since the check. Stop; nothing was written.
- `STATUS: verify-failed-rolled-back` or any other failure: report "not written" with the resolver's message.

Pass `--force` only after the user said yes to the overwrite question for this fingerprint. Never save a proposal the user has not seen and approved.

### Step 7: Summarize

1. Run `show --path <target>` and relay its `Config:` line verbatim.
2. If that line names more than one file, say: "This config applies to `<target>` and below. Parent configs still apply where this file does not set a value."
3. Repeat the rationale table from step 4 exactly as shown.
4. Suggest the next step: run `review-full` to get a fitness report with the new weights.

## Rules

- Nothing in the project changes before step 6, except `docs/fitness-report.md` in full mode after the user agreed.
- Every weight shown comes from the resolver output or `references/purpose-profiles.md`.
- Every reason cites evidence that exists in the target.
- Never create per-folder configs the user did not ask for.
