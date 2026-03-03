---
name: review-maintainability
description: Analyzes code for maintainability, understandability, and simplicity fitness, producing scores (1-10) across structural complexity, comprehensibility, technical debt indicators, coupling/dependency depth, and code smell density. Use when the user says /review:review-maintainability, requests a maintainability review, asks about code complexity or understandability, wants cyclomatic/cognitive complexity analysis, or needs simplicity/maintainability fitness scores. Triggers on "maintainability review", "understandability", "code complexity", "cognitive complexity", "cyclomatic complexity", "simplicity", "code smells". Only reports findings with confidence >= 7/10.
---

# Maintainability & Understandability Fitness Review

Analyze the codebase for maintainability and understandability fitness. Maintainability is a core quality attribute (ISO 25010); simplicity and understandability are means to achieve it. This skill evaluates structural complexity, comprehensibility, technical debt, and code smells with concrete metrics where observable.

Reference: [Fundamentals of Maintainability](https://jeffbailey.us/blog/2026/02/22/fundamentals-of-maintainability/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

For detailed scoring rubrics, severity definitions, what-good-looks-like / what-bad-looks-like criteria, and domain expertise, read `references/wisdom.md` before scoring. That file is auto-generated from:

- [Fundamentals of Maintainability](https://jeffbailey.us/blog/2026/02/22/fundamentals-of-maintainability/)

Use the wisdom reference when evaluating code and assigning dimension scores.

## Workflow

1. **Read domain knowledge** — Read `references/wisdom.md` to load scoring rubrics, thresholds, and severity definitions.

2. **Identify scope** — Use Glob/Grep to locate source files (excluding generated code, vendored libs). Determine primary language(s) and module structure.

3. **Assess structural complexity** — For each significant module or hot path, estimate or measure cyclomatic complexity, nesting depth, and LOC per function. Apply the thresholds from the wisdom reference.

4. **Evaluate understandability** — Check naming clarity, control-flow readability, and whether non-obvious logic is documented. Apply the rubrics from the wisdom reference.

5. **Count technical debt indicators** — Search for TODO, FIXME, HACK, XXX comments; duplicated logic blocks; magic numbers and strings; suppressed linter/compiler warnings. Estimate duplication percentage where feasible.

6. **Assess coupling and dependency depth** — Trace afferent/efferent coupling (how many modules depend on this vs. how many this depends on). Check inheritance hierarchies and dependency trees for excessive depth.

7. **Tally code smells** — Identify god classes, long methods, feature envy, inappropriate intimacy, shotgun surgery patterns. Apply the thresholds from the wisdom reference.

8. **Score each dimension** with file:line evidence, using the rubrics from `references/wisdom.md`.

9. **Produce the report** with scores, evidence, and prioritized action items.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

For severity level definitions (CRITICAL, HIGH, MEDIUM, LOW) with domain-specific examples, consult `references/wisdom.md`.

## Scoring Dimensions (1-10 each)

Dimensions to score (detailed rubrics including what-to-check, what-good-looks-like, and what-bad-looks-like are in `references/wisdom.md`):

1. **Structural Complexity** — Cyclomatic complexity, nesting depth, LOC per function/class, parameter count
2. **Understandability / Comprehensibility** — Naming clarity, control-flow readability, documentation of non-obvious logic, consistency
3. **Technical Debt Indicators** — TODO/FIXME counts, duplication, magic numbers, lint suppressions, stale comments
4. **Coupling and Dependency Depth** — Afferent/efferent coupling, inheritance depth, dependency tree depth, boundary respect
5. **Code Smell Density** — God classes, long methods, feature envy, shotgun surgery, dead code

## Output Format

Write the report to `docs/maintainability-review.md` with this structure:

```markdown
# Maintainability & Understandability Fitness Review

## Summary

Overall fitness score: X.X / 10 (average of dimensions)

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Structural Complexity | X/10 | ... |
| Understandability | X/10 | ... |
| Technical Debt Indicators | X/10 | ... |
| Coupling and Dependency Depth | X/10 | ... |
| Code Smell Density | X/10 | ... |

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line
- **Description:** What the issue is and why it matters.
- **Evidence:** The specific code pattern found.
- **Impact:** What could go wrong during maintenance or refactoring.
- **Remediation:** Concrete fix with code example or specific steps.

(repeat for each finding, ordered by severity)

### Structural Complexity (X/10)
- Evidence: file:line references
- Issues found
- Recommendations

(repeat for each dimension)

## Top 5 Action Items (by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...

## Metrics Summary (where measurable)

| Metric | Observed | Target | Status |
|--------|----------|--------|--------|
| Max LOC per function | X | < 50 | ... |
| Max nesting depth | X | < 4 | ... |
| TODO/FIXME count | X | < 5 tracked | ... |
| God class count (500+ LOC) | X | 0 | ... |

## Checklist Reference

See review-maintainability/references/checklist.md for the full checklist.

## Reference

Based on [Fundamentals of Maintainability](https://jeffbailey.us/blog/2026/02/22/fundamentals-of-maintainability/) and guidance from https://jeffbailey.us/categories/fundamentals/
```
