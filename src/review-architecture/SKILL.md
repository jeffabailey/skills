---
name: review-architecture
description: Analyzes code for software architecture fitness, producing scores (1-10) across coupling, cohesion, layering, modularity, naming, API design, and maintainability. Use when the user says /review:review-architecture, requests an architecture review, asks about coupling and cohesion, wants to analyze design or check code structure, asks to review naming or API design, or needs architecture fitness scores. Triggers on "architecture review", "coupling and cohesion", "analyze design", "check code structure", "review naming", "API design". Only reports findings with confidence >= 7/10.
---

# Software Architecture Fitness Review

Analyze the codebase (or specified files/modules) for software architecture fitness. Identify structural problems, design violations, and maintainability risks using evidence from the code.

Reference: [Fundamentals of Software Architecture](https://jeffbailey.us/blog/2025/10/19/fundamentals-of-software-architecture/), [Fundamentals of Software Design](https://jeffbailey.us/blog/2025/11/05/fundamentals-of-software-design/), [Fundamentals of API Design and Contracts](https://jeffbailey.us/blog/2026/01/16/fundamentals-of-api-design-and-contracts/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

For detailed scoring rubrics, severity definitions, what-good-looks-like / what-bad-looks-like criteria, and domain expertise, read `references/wisdom.md` before scoring. That file is auto-generated from:

- [Fundamentals of Software Architecture](https://jeffbailey.us/blog/2025/10/19/fundamentals-of-software-architecture/)
- [Fundamentals of Software Design](https://jeffbailey.us/blog/2025/11/05/fundamentals-of-software-design/)
- [Fundamentals of API Design and Contracts](https://jeffbailey.us/blog/2026/01/16/fundamentals-of-api-design-and-contracts/)

Use the wisdom reference when evaluating code and assigning dimension scores.

## Workflow

1. **Read domain knowledge** — Read `references/wisdom.md` to load scoring rubrics, thresholds, and severity definitions.

2. **Identify scope and boundaries** — Use Glob/Grep to map the codebase structure: top-level directories, module boundaries, entry points, configuration files, and dependency declarations. Determine whether the system is a monolith, modular monolith, microservices, or layered architecture. Identify where boundaries exist (or should exist) between distinct areas of responsibility.

3. **Map dependency graph** — Trace imports and references between modules. Identify which modules depend on which others. Look for circular dependencies, dependency direction violations, and hub modules. Apply the rubrics/thresholds from the wisdom reference.

4. **Analyze coupling** — For each module boundary, check how tightly components are connected. Count cross-boundary imports. Apply the rubrics/thresholds from the wisdom reference.

5. **Assess cohesion** — For each module or class, check whether its contents belong together. Apply the rubrics/thresholds from the wisdom reference.

6. **Evaluate layering and modularity** — Check whether the architecture has clear layers or modules with defined responsibilities. Apply the rubrics/thresholds from the wisdom reference.

7. **Review naming quality** — Assess names of files, classes, functions, variables, and modules for clarity, consistency, context-appropriateness, convention compliance, and discoverability. Apply the rubrics/thresholds from the wisdom reference.

8. **Audit API design** — Check internal and external API contracts for consistency, backward compatibility awareness, error handling uniformity, semantic clarity, and idempotency where needed. Apply the rubrics/thresholds from the wisdom reference.

9. **Evaluate maintainability** — Check for code smells that indicate maintainability risk. Apply the rubrics/thresholds from the wisdom reference.

10. **Score each dimension** with file:line evidence, using the rubrics from `references/wisdom.md`.

11. **Produce the report** with scores, evidence, and prioritized action items.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

For severity level definitions (CRITICAL, HIGH, MEDIUM, LOW) with domain-specific examples, consult `references/wisdom.md`.

## Scoring Dimensions (1-10 each)

Dimensions to score (detailed rubrics including what-to-check, what-good-looks-like, and what-bad-looks-like are in `references/wisdom.md`):

1. **Coupling** — Cross-boundary import count, concrete vs abstract dependencies, shared mutable state, circular dependencies, temporal coupling
2. **Cohesion** — Single responsibility, functional cohesion, concern separation, change-reason analysis
3. **Layering** — Layer separation, dependency direction, skip-layer violations, infrastructure leakage
4. **Modularity** — Boundary clarity, public interfaces, information hiding, independent testability
5. **Naming** — Clarity, consistency, context-appropriateness, convention compliance, discoverability, truthfulness
6. **API Design** — Contract explicitness, error consistency, backward compatibility, semantic clarity, idempotency
7. **Maintainability** — Code smells, duplication, magic numbers, test coverage, documentation, dependency health

## Output Format

Write the report to `docs/architecture-review.md` with this structure:

```markdown
# Software Architecture Fitness Review

## Summary

Overall fitness score: X.X / 10 (average of dimensions)

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Coupling | X/10 | ... |
| Cohesion | X/10 | ... |
| Layering | X/10 | ... |
| Modularity | X/10 | ... |
| Naming | X/10 | ... |
| API Design | X/10 | ... |
| Maintainability | X/10 | ... |

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line
- **Description:** What the issue is and why it matters.
- **Evidence:** The specific code pattern found.
- **Impact:** What could go wrong as the codebase evolves.
- **Remediation:** Concrete fix with code example or specific steps.

(repeat for each finding, ordered by severity)

### Coupling (X/10)
- Evidence: file:line references
- Issues found
- Recommendations

(repeat for each dimension)

## Top 5 Action Items (by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...

## Checklist Reference

See references/checklist.md for the full architecture checklist.

## Reference

Based on [Fundamentals of Software Architecture](https://jeffbailey.us/blog/2025/10/19/fundamentals-of-software-architecture/), [Fundamentals of Software Design](https://jeffbailey.us/blog/2025/11/05/fundamentals-of-software-design/), [Fundamentals of API Design and Contracts](https://jeffbailey.us/blog/2026/01/16/fundamentals-of-api-design-and-contracts/), and guidance from https://jeffbailey.us/categories/fundamentals/
```

Refer to the architecture checklist at `review-architecture/references/checklist.md` for detailed checks within each dimension.
