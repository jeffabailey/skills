---
name: review-maintainability
description: Analyzes code for maintainability, understandability, and simplicity fitness, producing scores (1-10) across structural complexity, comprehensibility, technical debt indicators, coupling/dependency depth, and code smell density. Use when the user says /review:review-maintainability, requests a maintainability review, asks about code complexity or understandability, wants cyclomatic/cognitive complexity analysis, or needs simplicity/maintainability fitness scores. Triggers on "maintainability review", "understandability", "code complexity", "cognitive complexity", "cyclomatic complexity", "simplicity", "code smells". Only reports findings with confidence >= 7/10.
---

# Maintainability & Understandability Fitness Review

Analyze the codebase for maintainability and understandability fitness. Maintainability is a core quality attribute (ISO 25010); simplicity and understandability are means to achieve it. This skill evaluates structural complexity, comprehensibility, technical debt, and code smells with concrete metrics where observable.

Reference: [Fundamentals of Maintainability](https://jeffbailey.us/blog/2026/02/22/fundamentals-of-maintainability/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

- `references/rubric.md` is the scoring source: the single threshold table, severity definitions, 1-10 anchors per dimension, the N/A rule, and the overall-score formula. Read it first; it is short.
- `references/checklist.md` is what to inspect during the workflow steps. Its numbers match the rubric's threshold table.
- `references/wisdom.md` is optional background, auto-generated from [Fundamentals of Maintainability](https://jeffbailey.us/blog/2026/02/22/fundamentals-of-maintainability/). It holds no rubric. Grep it by heading for a specific question (e.g. `Mistake 3: Copy-Paste`); never read it whole.
- `scripts/metrics.py` measures what the rubric thresholds need, so the Metrics Summary is measured rather than estimated.

## Configuration

Invoke the resolver CLI to obtain effective weights and thresholds for the review target. Never load `fitness-config.json` directly.

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py" show --path <target>
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; the resolver ships two levels up in the plugin's `scripts/`. If your agent does not expand the variable, substitute the directory containing this `SKILL.md`.

Where `<target>` is the file or directory under review. The CLI walks up to discover any module override and merges it with the root config. Include the `Config:` and `Effective weights:` lines from the resolver output within the first 10 lines of the final report as the provenance trail (AC-03.1, AC-08.2). The `effective` object inside the JSON block delimited by `<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->` / `<!-- END_EFFECTIVE_CONFIG_JSON -->` carries weights, status thresholds, security, and scoring for any programmatic needs.

## Workflow

1. **Read the rubric** — Read `references/rubric.md`, then skim `references/checklist.md`.

2. **Identify scope** — List source files and the primary language(s). Exclude generated code (`*.min.js`, `*_pb2.py`, build output) and vendored dependencies (`vendor/`, `third_party/`, copied-in libraries), and name what you excluded in the report's Target line.
   - **Vendored code: decide by ownership, not size.** The question is whether the team maintains this copy. Review it as owned code when it has local edits or local commits (`git log -- <path>`), or when it is what actually runs (the project imports the copy, not an installed package). Say so in the Target line ("includes vendored fork of X"). Exclude it when it is an unmodified copy of a published version (compare against the version named in the manifest or lockfile when you can fetch it read-only) or when nothing in scope loads it; then name it under excluded, and report the dead copy itself under Technical Debt. If you cannot tell, treat it as owned and say why.
   - To measure without an excluded copy that is not under `vendor/` or `third_party/`, pass `--exclude <glob>` to the metrics helper (step 4).

3. **Decide applicability** — For each of the five dimensions, decide whether anything in scope can be evaluated. Mark the rest `N/A — <reason>` per the rubric's N/A rule. A dimension with clean code is scored, not N/A.

4. **Measure** — Run the metrics helper on the target (add `--include-vendored` if step 2 decided vendored code is the project):
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/metrics.py" <target> --top 15
   ```
   It reports max function LOC, cyclomatic complexity, nesting, parameter count, class and file size, and every TODO/FIXME/HACK/XXX and lint suppression, each with file:line, and marks rows over the finding thresholds. `--include-vendored` scans `vendor/`-style directories it skips by default; `--exclude <glob>` (repeatable) drops other paths. Python is AST-exact; brace languages are approximate, so read the code before basing a HIGH finding on a brace-language number. For unsupported languages, or functions the helper misses, measure by reading and mark the value `(read)`.

5. **Assess structural complexity** — Start from the metrics output; read the worst functions to confirm and to judge cognitive complexity.

6. **Evaluate understandability** — Naming, control-flow readability, "why" comments on non-obvious logic, consistency between modules.

7. **Count technical debt indicators** — Use the markers and suppressions from step 4; check whether each TODO has an issue reference. Look for duplicated blocks (`diff` near-identical files; grep for a distinctive line from a suspected copy), magic values, and hardcoded configuration.

8. **Assess coupling and dependency depth** — Trace imports: fan-in per module, cycles, skip-layer imports, inheritance depth.

9. **Tally code smells** — God classes (or closure factories / stateful modules in class-less code), long methods, feature envy, shotgun surgery, dead or commented-out code. Normalize per 1,000 non-blank LOC as the rubric asks.

10. **Score** each applicable dimension against the rubric anchors, with file:line evidence.

11. **Self-check, then write the report** (see Output Format). Before writing, confirm:
    - every cited file:line exists and shows what the finding claims;
    - every finding has confidence >= 7 and all eight template fields (Severity through Remediation);
    - the overall score equals the stated computation (mean of scored dimensions, CRITICAL cap applied);
    - Metrics Summary values match the metrics output;
    - no secret value appears anywhere in the report (see Secrets below).

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

Severity levels (CRITICAL, HIGH, MEDIUM, LOW) are defined with maintainability examples in `references/rubric.md`. Tie severity to the threshold table: over Severe is HIGH, over Finding is MEDIUM, between Target and Finding is LOW.

### Secrets

Maintainability targets often contain hardcoded credentials, tokens, or session cookies. Never reproduce a secret value in Evidence, code excerpts, or remediation examples: cite the file:line and write `<redacted>` in place of the value. Here, hardcoded credentials count only as configuration-in-code debt (Technical Debt). Leave exposure, rotation, and severity to `review-security`, and add one line to the report recommending it ("Hardcoded credentials at file:line; run review-security").

## Scoring Dimensions (1-10 each)

Anchors for each band are in `references/rubric.md`.

1. **Structural Complexity** — Cyclomatic complexity, nesting depth, LOC per function/class, parameter count
2. **Understandability / Comprehensibility** — Naming clarity, control-flow readability, documentation of non-obvious logic, consistency
3. **Technical Debt Indicators** — TODO/FIXME counts, duplication, magic numbers, lint suppressions, stale comments
4. **Coupling and Dependency Depth** — Afferent/efferent coupling, inheritance depth, dependency tree depth, boundary respect
5. **Code Smell Density** — God classes, long methods, feature envy, shotgun surgery, dead code

## Output Format

Write the report at the root of the repository that contains the target (the nearest ancestor with `.git`; the target directory itself if there is none), unless the user names a path:

- Whole repository: `docs/maintainability-review.md`
- A subdirectory or file set: `docs/maintainability-review-<scope-slug>.md` (e.g. `docs/maintainability-review-scripts-fitness-config.md`), so a scoped review does not overwrite the whole-repo report.

Use this structure:

```markdown
# Maintainability & Understandability Fitness Review

**Target:** <path(s) reviewed; languages; N source files, N non-blank LOC; excluded: ...>
Config: <copied from resolver output>
Effective weights: <copied from resolver output>

## Direct Answer
(Only when the user asked a specific question, e.g. "is cli.py getting too big?" Answer it in 2-4 sentences with the numbers.)

## Summary

Overall fitness score: X.X / 10 (mean of <list of scored dimensions>) — <Healthy / Needs Attention / Critical>

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Structural Complexity | X/10 | ... |
| Understandability | X/10 | ... |
| Technical Debt Indicators | X/10 | ... |
| Coupling and Dependency Depth | X/10 or N/A — reason | ... |
| Code Smell Density | X/10 | ... |

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line
- **Description:** What the issue is and why it matters.
- **Evidence:** The specific code pattern or metric found (secrets as `<redacted>`).
- **Impact:** What could go wrong during maintenance or refactoring.
- **Remediation:** Concrete fix with code example or specific steps.

(repeat for each finding, ordered by severity)

### Structural Complexity (X/10)
- Evidence: file:line references
- Issues found
- Recommendations

(repeat for each dimension)

## Action Items (up to 5, by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line

(Fewer than 5 is fine; do not pad with low-value items.)

## Metrics Summary

Measured with scripts/metrics.py (<ast | brace (approximate)>); values marked (read) were measured by reading the code. Targets from the rubric's threshold table.

| Metric | Observed | Target / Finding | Status |
|--------|----------|------------------|--------|
| Max LOC per function | X (file:line) | <= 30 / > 50 | ... |
| Max cyclomatic complexity | X (file:line) | <= 10 / > 15 | ... |
| Max nesting depth | X (file:line) | <= 3 / > 4 | ... |
| Max parameters | X (file:line) | <= 4 / > 5 | ... |
| Largest class (or closure/stateful module used instead) | X (file:line) | <= 300 / > 500 | ... |
| Largest file (non-blank LOC) | X (file) | <= 500 / > 1000 | ... |
| Untracked TODO/FIXME/HACK | X | < 5 / >= 5 | ... |
| Lint/type suppressions | X | justified / blanket or >= 5 unjustified | ... |

## Checklist Reference

See review-maintainability/references/checklist.md for the full checklist.

## Reference

Based on [Fundamentals of Maintainability](https://jeffbailey.us/blog/2026/02/22/fundamentals-of-maintainability/) and guidance from https://jeffbailey.us/categories/fundamentals/
```
