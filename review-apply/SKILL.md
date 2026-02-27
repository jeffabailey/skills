---
name: review-apply
description: Pulls a fitness report issue from GitHub, addresses the action items by updating the codebase, and closes the issue when done. Use when the user says "apply review", "fix review issues", "address review feedback", "apply fitness report", or provides a GitHub issue URL containing a fitness report.
---

# Apply Fitness Report

Pull a fitness report from a GitHub issue, address each action item by modifying the codebase, and close the issue when complete.

Reference: https://jeffbailey.us/blog/2026/02/14/what-is-fitness-review/

## Workflow

### Step 1: Fetch the Issue

Use the `gh` CLI to retrieve the issue. Accept any of these as input:
- A full GitHub issue URL (e.g., `https://github.com/owner/repo/issues/18`)
- An issue number (resolves against the current repo)
- No input — search for the most recent open issue with the `fitness-review` label

```bash
# Full URL
gh issue view <URL> --json title,body,state,labels,number

# Issue number
gh issue view <number> --json title,body,state,labels,number

# Auto-discover
gh issue list --label fitness-review --state open --limit 1 --json number,title
```

If the issue is already closed, inform the user and stop.

### Step 2: Parse Action Items

Extract the **Top 10 Action Items** section from the issue body. Each item follows this pattern:

```
N. **[PRIORITY]** description — file:line
```

Where PRIORITY is one of: CRITICAL, HIGH, MEDIUM, LOW.

Build a work list ordered by priority:
1. CRITICAL items first
2. HIGH items second
3. MEDIUM items third
4. LOW items last

### Step 3: Triage Action Items

For each action item, classify it as one of:

- **Actionable** — A concrete code or config change can be made (e.g., "add trigger tests for review-maintainability", "add `--max-turns` flag")
- **Deferred** — Requires external decisions, new infrastructure, or is out of scope (e.g., "implement semantic versioning", "add external alerting")

Present the triage to the user:

```
## Action Items Triage

### Will Address Now
1. [HIGH] description — approach
2. [MEDIUM] description — approach

### Deferred (requires discussion)
3. [MEDIUM] description — reason
```

Ask the user to confirm before proceeding. If the user wants to adjust which items are addressed, follow their guidance.

### Step 4: Address Each Actionable Item

For each actionable item, in priority order:

1. **Read the referenced file(s)** at the cited line numbers to understand context
2. **Plan the change** — determine the minimal edit needed
3. **Make the change** using Edit, Write, or Bash tools
4. **Verify the change** — run any relevant tests or validation

Follow these principles:
- Make the **minimum change** needed to address the finding
- Do not refactor surrounding code unless the action item specifically calls for it
- Preserve existing style and conventions
- If an action item references multiple files, address all of them
- If a test file needs updating, run the tests after editing

### Step 5: Summarize Changes

After addressing all actionable items, produce a summary:

```markdown
## Changes Applied

### Addressed
1. [HIGH] description — what was changed
   - `file:line` — edit summary

### Deferred
1. [MEDIUM] description — reason for deferral

### Verification
- Tests run: [pass/fail/none]
- Files modified: [count]
```

### Step 6: Close the Issue

Add a comment to the issue summarizing what was done, then close it:

```bash
gh issue comment <number> --body "$(cat <<'EOF'
## Fitness Report — Changes Applied

[summary from Step 5]

Remaining deferred items may be tracked in separate issues if needed.
EOF
)"

gh issue close <number> --reason completed
```

## What NOT to Change

- Do not make changes unrelated to the action items
- Do not refactor code that the report scored well (8-10)
- Do not add dependencies unless an action item specifically requires it
- Do not modify CI/CD pipelines without user confirmation
- Do not delete files unless an action item specifically calls for it
