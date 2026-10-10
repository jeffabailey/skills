---
name: review-apply
description: Pulls a fitness report from a GitHub issue or from a local fitness report, addresses the action items by updating the codebase, and closes the issue when done. Use when the user says "apply review", "fix review issues", "address review feedback", "apply fitness report", "work through the action items", or provides a GitHub issue URL or number containing a fitness report, even if they don't say "fitness". Not for producing a new report (that's review-full).
---

# Apply Fitness Report

Pull a fitness report from a GitHub issue or a local file, address each action item by modifying the codebase, and close the issue when complete.

Reference: https://jeffbailey.us/blog/2026/02/14/what-is-fitness-review/

## Workflow

### Step 1: Locate the Report

Determine the report source from the user's input:

| Input | Source type |
|---|---|
| Starts with `https://`, or is a number with or without `#` (`17`, `#17`) | **GitHub issue** |
| A file path (contains `/` or ends in `.md`) | **Local file** |
| No input | **Auto-discover** |

#### GitHub issue

Pin down the repository first, because every later `gh` call must hit the same issue. A URL can point at a repo other than the one in the current directory, and a bare number resolves against the cwd's remote, which is wrong in that case.

- **URL** `https://github.com/<owner>/<repo>/issues/<n>`: take `<owner>/<repo>` and `<n>` from the path.
- **Number** (`17` or `#17`): strip the `#`, then get the repo with `gh repo view --json nameWithOwner -q .nameWithOwner`.

```bash
gh issue view <n> -R <owner>/<repo> --json title,body,state,labels,number,createdAt
```

Use the same `<n> -R <owner>/<repo>` pair for every `gh` call in Step 6. If `<owner>/<repo>` is not this checkout's remote (`git remote -v`), say so before going further: the edits will land in this checkout, so make sure that is what the user wants.

If the issue is already closed, inform the user and stop.

#### Local file

Read `docs/fitness-report.md` (or the user-specified path) directly. If the file does not exist, inform the user and stop.

#### Auto-discover (no input)

1. Look for the most recent open issue with the `fitness-review` label:

   ```bash
   gh issue list --label fitness-review --state open --limit 1 --json number,title,createdAt
   ```

2. Check whether `docs/fitness-report.md` exists and read its `**Date:**` line.
3. If only one source exists, use it. If both exist, use the newer one and tell the user which you picked and why, since a local run of review-full usually supersedes an older CI issue (and vice versa).
4. If neither source exists, inform the user and stop.

Record which source type was used — this determines behavior in Step 6.

#### Check the report is still current

Reports age. A local `docs/fitness-report.md` often stays in the repo after its items were already applied, and line numbers drift as code changes. Before parsing, list the commits that touched the files the report cites since it was written:

```bash
git log --oneline --since="<report date> 00:00" -- <cited paths>
```

Report dates are usually a day with no time, so this includes commits from earlier that same day; treat those as "possibly before the report", not proof. Judge commits by what they changed, not by their titles: an ordinary `fix:` commit resolves items as often as one titled "apply review". If cited files changed, say up front that some items may already be fixed. The Step 3 triage confirms item by item.

### Step 2: Parse Action Items

Extract the **Top 10 Action Items** section. Producers are not perfectly consistent, so parse tolerantly. All of these are the same item shape:

```
1. [HIGH] description - `path/file.py:60-63,123-139`, `other.yml:35`
1. [HIGH] description — path/file.py:60
1. **[HIGH]** description — path/file.py:60
```

For each item, capture:

- **Priority** — CRITICAL, HIGH, MEDIUM, or LOW (with or without bold)
- **Description** — the text between the priority and the final ` - ` or ` — ` separator
- **Locations** — every `path:lines` reference after the separator. There may be several, with ranges (`60-63`) and comma lists (`60-63,123-139`). Globs such as `skills/review-*/SKILL.md` mean "every matching file". Some items have no location at all; that is fine.

Build a work list ordered CRITICAL, HIGH, MEDIUM, LOW, keeping report order within a priority.

### Step 3: Triage Action Items

Look at the current code for every item before classifying it. Line numbers in the report point at the code as it was when the report was written, so find the cited code by its content (function name, config key, quoted string) rather than trusting the line number.

Classify each item as one of:

- **Actionable** — A concrete code or config change can be made now (e.g., "add trigger tests for review-maintainability", "add `--max-turns` flag")
- **Already resolved** — The current code no longer has the problem. Cite the evidence: the `file:line` showing the fix and, where you can, the commit that fixed it. To find that commit, search for when the cited snippet disappeared: `git log -S'<snippet from the report>' --oneline -- <file>` (the newest hit is usually the removal; `git show <hash>` confirms it)
- **Deferred** — Requires external decisions, new infrastructure, or is out of scope (e.g., "implement semantic versioning", "add external alerting")

Present the triage to the user:

```
## Action Items Triage

Source: issue #42 (opened YYYY-MM-DD) | docs/fitness-report.md (dated YYYY-MM-DD)

### Will Address Now
1. [HIGH] description — approach

### Already Resolved
2. [HIGH] description — evidence

### Deferred (requires discussion)
3. [MEDIUM] description — reason

When done: <comment on and close issue #42 | show summary only>
```

Ask the user to confirm before proceeding. Stating what happens in Step 6 here lets one confirmation cover the whole run, including the issue close. If the user wants to adjust which items are addressed, follow their guidance.

When nothing is actionable (every item is already resolved or deferred), still present the triage and still ask; skip only Step 4. The confirmation is what authorizes any issue action, and closing an issue on which this run did no work needs the user's agreement. For a GitHub source with deferred items, the "When done" line must say what happens to them, because the issue is often their only tracker. For example:

```
When done: comment on #17 and close it. Deferred item 3 has no other tracker:
open a follow-up issue for it, list it as unresolved in the closing comment,
or keep #17 open?
```

Then go to Step 5.

### Step 4: Address Each Actionable Item

For each actionable item, in priority order:

1. **Read the referenced code** to understand context
2. **Plan the change** — determine the minimal edit needed
3. **Make the change** using Edit, Write, or Bash tools
4. **Verify the change** — run the tests closest to the change

Follow these principles:
- Make the **minimum change** needed to address the finding
- Do not refactor surrounding code unless the action item specifically calls for it
- Preserve existing style and conventions
- If an action item references multiple files or a glob, address every location
- If an item turns out larger or riskier than the triage suggested, stop and check with the user rather than pushing through

If no test covers a change (common for shell scripts and config), do a quick behavioral check instead: run `bash -n` or the tool's validator, and exercise the changed branch, for example by putting a stub of the failing command first on `PATH`. Say in the summary that this was a manual check, not a test.

After all items are done, run the project's full check suite once. Several small edits can interact, and a per-item test run will not catch that. Use the commands CI runs (`.github/workflows/`, `Makefile`, `package.json`, root `pyproject.toml`). If the repo has none of these at its root, run the suite of each package you touched instead, for example `uv run --with pytest pytest` in each directory with its own `pyproject.toml` (`--with` covers projects that don't declare pytest). Name the commands in the summary so the reader knows what "checks pass" covered.

### Step 5: Summarize Changes

```markdown
## Changes Applied

### Addressed
1. [HIGH] description — what was changed
   - `file:line` — edit summary

### Already Resolved
1. [HIGH] description — evidence

### Deferred
1. [MEDIUM] description — reason for deferral

### Verification
- Tests run: [commands and pass/fail]
- Files modified: [count]
```

Report failures as failures. If a check failed or an item was only partly addressed, say so in the summary.

### Step 6: Close the Report

#### GitHub issue source

Add a comment to the issue with the Step 5 summary. Always pass `-R <owner>/<repo>` from Step 1, so the comment and close reach the issue you read even when it lives in another repo:

```bash
gh issue comment <n> -R <owner>/<repo> --body "$(cat <<'EOF'
## Fitness Report — Changes Applied

[summary from Step 5]

### Still open
[each deferred item, with its follow-up issue link, or "not tracked elsewhere"]
EOF
)"
```

Handle deferred items the way the user chose at the triage. If they asked for follow-up issues, open one per item before closing (`gh issue create -R <owner>/<repo> --title "<item>" --body "From #<n>: <reason deferred>"`) and link them in the comment.

Close the issue only when the user agreed at the triage, every actionable item was addressed, and the checks pass. With zero actionable items, the close rests on the user's answer, not on "nothing failed":

```bash
gh issue close <n> -R <owner>/<repo> --reason completed
```

If something failed or was left half done, leave the issue open and say why in the comment. A closed issue tells the team the work is finished, so closing on a failure hides it.

#### Local file source

Skip issue closing. Present the Step 5 summary directly to the user. Do not edit or delete the report file unless the user asks.

## What NOT to Change

- Do not make changes unrelated to the action items
- Do not refactor code that the report scored well (8-10)
- Do not add dependencies unless an action item specifically requires it
- Do not modify CI/CD pipelines without user confirmation
- Do not delete files unless an action item specifically calls for it
- Do not commit or push unless the user asks
