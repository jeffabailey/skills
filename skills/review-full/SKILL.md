---
name: review-full
description: Runs a comprehensive project fitness review combining architecture, security, reliability, testing, performance, algorithms, data, accessibility, process, and maintainability analysis. Use when the user says "full review", "comprehensive review", "project fitness", "review everything", or wants all review skills run on current changes before shipping.
---

# Full Project Fitness Review

Run the ten domain review skills in parallel and combine their results into one weighted fitness report. This skill does not score code itself; it decides scope, reads weights from the resolver, aggregates, and shows its arithmetic so the overall can be checked by hand.

## Configuration

Always invoke the resolver CLI to read effective weights and thresholds. Never load `fitness-config.json` directly. The CLI walks up from the review target to find module overrides and merges them with the root config per ADR-001 / ADR-002 / ADR-005.

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py" show --path <target>
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; the resolver ships two levels up in the plugin's `scripts/`. If your agent does not expand the variable, substitute the directory containing this `SKILL.md`.

Where `<target>` follows the scope chosen in Step 1:
- **User-given path:** that file or directory.
- **Pending changes:** each changed file. Override files are often gitignored, so a module override can govern a changed file without showing up in `git status`; resolving per file is the only way to catch it. Group the files by the `Config:` line they resolve to.
- **Whole project:** the repository root (per ADR-005, only the root config applies at root scope).

Before using any output, run the same command with `validate` in place of `show` for every target. `show` exits 0 even when merged weights do not sum to 100 (its table prints `total ... ERROR`); `validate` exits 1. If validation fails, stop and show the user the error instead of scoring against a broken config.

From each `show` output keep:
- The `Config:` line (which config files were applied; `built-in defaults` means none was found).
- The `Effective weights:` line (all 10 domains).
- The JSON block between `<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->` and `<!-- END_EFFECTIVE_CONFIG_JSON -->`, which carries the weights and `statusThresholds`.

Save each `show` output to a temp file; `scripts/overall.py` reads it. Never hardcode weights here: a per-directory override must change scoring without editing this file (ADR-002 / FR-7). With no config at all, the resolver's built-in defaults are the weights listed in README.md under Reports.

## Workflow

### Step 1: Identify Review Scope

Pick the first that applies. An explicit request beats inferred state:
1. The user named files, directories, or a module: review those.
2. There are uncommitted changes (`git status --porcelain`, covering staged, unstaged, and untracked files): review the changed files.
3. Otherwise: review the whole repository.

Record the scope for the `**Scope:**` line exactly (for example, `Pending changes: scripts/fitness_config/render.py` or `Directory: scripts/fitness_config`). Other skills read that line to tell a diff review from a folder review.

### Step 2: Resolve and Validate Config

Run `validate` then `show` per the Configuration section for each target. With pending changes spanning several configs, keep one saved `show` output per group and note which files belong to which.

### Step 3: Decide Which Domains Apply

Mark a domain N/A, with a reason, instead of launching it when:
- **Accessibility:** no frontend files in scope (HTML, CSS, JSX, TSX, Vue, Svelte). Reason: `Skipped - no frontend code detected`.
- **Data:** no database code in scope (SQL, migrations, ORM models, database config). Reason: `Skipped - no database code detected`.
- **Weight 0:** the effective weight is 0 in every config group. Reason: `Skipped - weight 0 in config`.
- **Process, for a pending-changes scope:** the diff touches no docs, CI, dependency manifests, or contributor files. Process judges the repository, not a diff, so scoring it would dilute the real findings. Reason: `Skipped - diff touches no process files`.

Detect within the scope, not the whole repository, so a diff review is not padded by unrelated code.

### Step 4: Launch the Applicable Reviews in Parallel

Use the Task tool to launch one agent per applicable domain, passing the same scope (paths or changed-file list) to each:

1. **Architecture** (`/review:review-architecture`) - Design, coupling, naming, API fitness
2. **Security** (`/review:review-security`) - Vulnerability and compliance fitness
3. **Reliability** (`/review:review-reliability`) - Operations, observability, availability fitness
4. **Testing** (`/review:review-testing`) - Test strategy and quality fitness
5. **Performance** (`/review:review-performance`) - Scalability and efficiency fitness
6. **Algorithms** (`/review:review-algorithms`) - Algorithm choice, data structures, concurrency, correctness fitness
7. **Data** (`/review:review-data`) - Schema design, migration safety, data integrity fitness
8. **Accessibility** (`/review:review-accessibility`) - UX and a11y fitness
9. **Process** (`/review:review-process`) - Development workflow and documentation fitness
10. **Maintainability** (`/review:review-maintainability`) - Complexity, understandability, technical debt, code smells fitness

Each domain skill also writes its own report: `docs/<domain>-review.md` for a whole-repo review, or `docs/<domain>-review-<scope-slug>.md` for a scoped one. Ask each agent to return its report path, overall score (X.X), dimension scores, findings with severity and file:line, and whether it found any CRITICAL.

### Step 5: Collect Domain Results

For each domain, take the overall the domain skill reported (mean of its scored dimensions, capped at 4.0 when it has a CRITICAL). Keep one decimal; do not round to an integer. A domain becomes N/A when:
- Step 3 skipped it.
- Its review marked every dimension N/A. Reason: `N/A - no dimensions applied`.
- Its agent failed or returned no score. Reason: `Failed - <what happened>`. Say so in the report; never invent a score for it.

### Step 6: Compute the Overall Score

Run the bundled helper rather than doing the arithmetic in your head:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/overall.py" --resolver <saved-show-output> [--resolver <second-group>] \
  --scores "architecture=7.4,security=8.0,data=N/A,..." [--critical]
```

What it does, so you can check it:
- **Overall** = Σ(weight × score) / Σ(weight) over scored domains with weight > 0. Dividing by the scored weights is the same as redistributing N/A weight proportionally.
- **CRITICAL cap:** pass `--critical` when any domain reported a CRITICAL finding; the overall is capped at 4.0, matching the domain skills.
- **Status:** a score at or above `statusThresholds.healthy[0]` is Healthy; at or above `needsAttention[0]` is Needs Attention; anything lower is Critical. Only the lower bounds count, so 7.5 is Needs Attention, not a gap. Defaults when absent: 8 / 5.
- **Several config groups:** domain scores are shared, the weights differ. The helper prints one overall per group; the headline overall is the lowest, because the weakest module gates the ship decision.

Copy its `Arithmetic:` line(s) into the report.

### Step 7: Self-Check, Then Write the Report

Before writing, confirm:
- Every cited file:line exists and says what the finding claims.
- The overall and statuses match the helper output.
- The `Config:` and `Effective weights:` lines are copied verbatim from the resolver.
- No secret values appear; refer to secrets by file:line only.

Write `docs/fitness-report.md` at the root of the repository that contains the target, unless the user gives a path. `review-apply` and `fitness-config-init` read this fixed path. Use this structure:

```markdown
# Project Fitness Report

**Target:** <path(s) or scope reviewed>
Config: <copied from resolver output; one line per config group>
Effective weights: <copied from resolver output; one line per config group>
**Date:** YYYY-MM-DD
**Scope:** <Directory: ... | Pending changes: file, file | Whole repository>

## Overall Score: X.X / 10 (<status>)

Arithmetic: (<w>*<score> + ...) / <scored weight> = X.XX<, capped at 4.0 for a CRITICAL finding>
Averaged: <domains included>. N/A: <domains excluded>.

| Domain | Score | Status |
|--------|-------|--------|
| Architecture | X.X/10 | Healthy / Needs Attention / Critical |
| Data | N/A | Skipped - no database code detected |
...all 10 domains...

## Top 10 Action Items (Priority Order)

1. [CRITICAL] description - path:line
2. [HIGH] description - path:line

## Domain Details

### Architecture
Score X.X/10. Report: docs/architecture-review[-<scope-slug>].md
<dimension scores and key findings with file:line>

### Data
Skipped - no database code detected

...one section per domain, all 10...

## References

Based on guidance from [Fundamentals](https://jeffbailey.us/categories/fundamentals/). Each domain skill scores from its own `references/rubric.md`.
```

If the user asked a specific question ("is this safe to ship?"), add a `## Direct Answer` section right after the overall score. List up to 10 action items; fewer is fine when fewer findings clear confidence 7. Never pad the list.

## Action Item Prioritization

Rank by severity first, then by domain weight, then by how easy the fix is:
1. **CRITICAL** - Security vulnerabilities, data loss risks, production outages
2. **HIGH** - Architecture violations causing maintenance burden, missing tests for critical paths, algorithm correctness issues, data integrity gaps
3. **MEDIUM** - Performance bottlenecks, observability gaps, process improvements, concurrency risks
4. **LOW** - Style issues, minor naming inconsistencies, nice-to-have improvements

Merge duplicates: when two domains flag the same file:line, list it once and name both domains.
