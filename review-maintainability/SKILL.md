---
name: review-maintainability
description: Analyzes code for maintainability, understandability, and simplicity fitness, producing scores (1-10) across structural complexity, comprehensibility, technical debt indicators, coupling/dependency depth, and code smell density. Use when the user says /review:review-maintainability, requests a maintainability review, asks about code complexity or understandability, wants cyclomatic/cognitive complexity analysis, or needs simplicity/maintainability fitness scores. Triggers on "maintainability review", "understandability", "code complexity", "cognitive complexity", "cyclomatic complexity", "simplicity", "code smells".
---

# Maintainability & Understandability Fitness Review

Analyze the codebase for maintainability and understandability fitness. Maintainability is a core quality attribute (ISO 25010); simplicity and understandability are means to achieve it. This skill evaluates structural complexity, comprehensibility, technical debt, and code smells with concrete metrics where observable.

Reference: [Fundamentals of Maintainability](https://jeffbailey.us/blog/2026/02/22/fundamentals-of-maintainability/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Workflow

1. **Identify scope** — Use Glob/Grep to locate source files (excluding generated code, vendored libs). Determine primary language(s) and module structure.

2. **Assess structural complexity** — For each significant module or hot path, estimate or measure cyclomatic complexity, nesting depth, and LOC per function. Look for functions over 50 lines, methods with 10+ branches, nesting beyond 4 levels.

3. **Evaluate understandability** — Check naming clarity, control-flow readability, and whether non-obvious logic is documented. Look for generic names, misleading abstractions, and undocumented invariants or business rules.

4. **Count technical debt indicators** — Search for TODO, FIXME, HACK, XXX comments; duplicated logic blocks; magic numbers and strings; suppressed linter/compiler warnings. Estimate duplication percentage where feasible.

5. **Assess coupling and dependency depth** — Trace afferent/efferent coupling (how many modules depend on this vs. how many this depends on). Check inheritance hierarchies and dependency trees for excessive depth.

6. **Tally code smells** — Identify god classes (500+ lines), long methods (50+ lines), feature envy, inappropriate intimacy, shotgun surgery patterns.

7. **Score each dimension** with file:line evidence.

8. **Produce the report** with scores, evidence, and prioritized action items.

## Scoring Dimensions (1-10 each)

### 1. Structural Complexity

What to check:
- Cyclomatic complexity per function (paths through code; aim &lt; 10 for critical paths)
- Cognitive complexity (SonarQube-style; weights nesting and control flow)
- Lines of code per function (guardrail: no function exceeds 50 lines)
- Lines per class/module (guardrail: no module exceeds 300–500 lines)
- Nesting depth (max 4 levels before extraction)
- Parameter count (functions with 5+ parameters suggest refactoring)

What good looks like (8-10):
- Functions under 30 lines; classes under 300 lines
- Cyclomatic complexity below 10 for business-critical paths
- Nesting limited to 3 levels; complex logic extracted to named helpers
- Parameters kept to 3–4; complex inputs grouped into objects

What bad looks like (1-3):
- God classes over 1000 lines; functions over 100 lines
- Cyclomatic complexity 15+ in core logic
- Nesting 5+ levels deep; deeply nested conditionals and loops
- Functions with 7+ parameters; "parameter objects" never used

### 2. Understandability / Comprehensibility

What to check:
- How easily a new developer can reason about the system
- Naming clarity: do names communicate intent without code reading?
- Control-flow clarity: is the sequence of operations obvious?
- Non-obvious decisions: are invariants, business rules, and "why" documented?
- Abstractions: do they match domain concepts or obscure them?
- Consistency: similar patterns used similarly across the codebase?

What good looks like (8-10):
- Functions named with verbs that describe the action
- Non-obvious logic has "why" comments or links to ADRs
- Abstractions map to domain terms; no leaky or misleading names
- Consistent patterns for error handling, validation, and data flow
- A developer can understand a module without tracing 10 call sites

What bad looks like (1-3):
- Generic names: `data`, `info`, `process()`, `handle()` without domain context
- Complex logic with no comments explaining invariants or rationale
- Abstractions that hide critical behavior or mislead about side effects
- Inconsistent patterns: some modules return errors, others throw; no convention
- Understanding requires reading the entire call graph

### 3. Technical Debt Indicators

What to check:
- TODO, FIXME, HACK, XXX comments and whether they are tracked
- Duplicated logic (copy-paste blocks, similar validations in multiple places)
- Magic numbers and strings without named constants
- Suppressed linter/compiler warnings (eslint-disable, @SuppressWarnings, etc.)
- Outdated or misleading comments
- Test coverage for critical paths (low coverage increases refactoring risk)

What good looks like (8-10):
- Few or no TODO/FIXME; remaining items tracked in issues with owners
- Shared logic extracted into reusable functions or modules
- Named constants replace magic numbers; enums replace magic strings
- No broad lint suppressions; targeted suppressions with justification
- Comments are current and explain "why" not "what"
- Critical paths have test coverage; refactoring is safe

What bad looks like (1-3):
- 10+ TODO/FIXME/HACK with no tracking or prioritization
- Same validation or transformation logic in 5+ places
- Numbers like 86400 or strings like "active" scattered without constants
- eslint-disable-next-line or equivalent used to silence entire categories
- Comments contradict code or describe removed behavior
- No tests; any refactor risks breaking unknown behavior

### 4. Coupling and Dependency Depth

What to check:
- Afferent coupling: how many modules depend on this one (high = hub, fragile)
- Efferent coupling: how many modules this one depends on (high = rigid)
- Depth of inheritance: how deep are class hierarchies?
- Dependency tree depth: how many layers of transitive dependencies?
- Cross-boundary imports: are boundaries respected or bypassed?

What good looks like (8-10):
- Modules have low afferent coupling (few dependents) or clear public interfaces
- Dependencies point inward; domain does not depend on infrastructure
- Inheritance depth 2–3 levels; composition preferred over deep hierarchies
- Dependency depth reasonable; no 10-layer transitive stacks for simple tasks
- Module boundaries are explicit; no skip-layer imports

What bad looks like (1-3):
- A single module imported by 70%+ of the codebase (god module)
- Deep inheritance trees (5+ levels); base classes change for many reasons
- Domain code depends on UI framework, database driver, or HTTP client
- Dependency tree 10+ layers deep for a small feature
- Boundaries bypassed; presentation imports directly from data layer

### 5. Code Smell Density

What to check:
- God classes: 500+ lines, many responsibilities
- Long methods: 50+ lines
- Feature envy: method uses other object's data more than its own
- Inappropriate intimacy: classes knowing too much about each other's internals
- Shotgun surgery: one change requires edits in many files
- Primitive obsession: primitive types instead of small value objects
- Dead code: unused functions, unreachable branches
- Commented-out code blocks left in place

What good looks like (8-10):
- Classes under 300 lines with single responsibility
- Methods under 30 lines; complex logic delegated to helpers
- Objects encapsulate their data; minimal cross-object data peeking
- Changes localize to one or two modules
- Domain concepts modeled as value objects where appropriate
- No dead code; commented-out blocks removed
- Minimal code smells; refactoring is incremental and low-risk

What bad looks like (1-3):
- God classes over 1000 lines with 20+ public methods
- Methods that span multiple screens; impossible to test in isolation
- Feature envy throughout; objects are anemic data bags
- Changing one feature touches 10+ files across unrelated modules
- Primitives everywhere; no value objects for domain concepts
- Significant dead code; commented-out blocks from months ago
- High density of smells; refactoring requires major rewrites

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
| Max LOC per function | X | &lt; 50 | ... |
| Max nesting depth | X | &lt; 4 | ... |
| TODO/FIXME count | X | &lt; 5 tracked | ... |
| God class count (500+ LOC) | X | 0 | ... |

## References

See review-maintainability/references/checklist.md for the full checklist. Based on [Fundamentals of Maintainability](https://jeffbailey.us/blog/2026/02/22/fundamentals-of-maintainability/).
```
