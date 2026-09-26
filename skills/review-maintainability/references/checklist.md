# Maintainability & Understandability Fitness Checklist

Detailed checklist for reviewing code against maintainability and understandability fundamentals. Use alongside the review-maintainability skill.

Reference: https://jeffbailey.us/categories/fundamentals/

---

## 1. Structural Complexity

### Cyclomatic & Cognitive Complexity
- [ ] **Cyclomatic complexity below 10** for critical paths — Count branches, loops, and conditionals. High complexity indicates many execution paths and higher testing burden.
- [ ] **Cognitive complexity below 15** (SonarQube-style) — Nested structures and control flow add to comprehension difficulty. Prefer early returns and extraction.
- [ ] **No functions over 50 lines** — Long functions are hard to reason about and test. Extract helpers and name them clearly.
- [ ] **No classes over 300 lines** — God classes accumulate responsibilities. Split by domain concept or reason-to-change.
- [ ] **Nesting depth 4 or less** — Deep nesting obscures flow. Extract to named functions or use guard clauses.
- [ ] **Parameter count 5 or less** — Many parameters suggest missing abstraction. Use parameter objects or builder patterns.

### LOC Guards
- [ ] **Functions under 30 lines** — Ideal for single-screen comprehension.
- [ ] **Methods under 30 lines** — Same; delegate to helpers with descriptive names.
- [ ] **Modules under 500 lines** — Large files indicate mixing of concerns or missing decomposition.

---

## 2. Understandability / Comprehensibility

### Naming
- [ ] **Names communicate intent** — No generic `data`, `info`, `process()`, `handle()` without domain context.
- [ ] **Verbs for actions** — `calculateTotalPrice()`, `validateUserInput()`, not `doStuff()`.
- [ ] **Booleans prefixed** — `isValid`, `hasPermission`, `canEdit`.
- [ ] **Abstractions match domain** — Names use business terminology, not implementation details.

### Flow Clarity
- [ ] **Sequence of operations is obvious** — Control flow reads top-to-bottom or follows named steps.
- [ ] **No hidden side effects** — Functions that mutate globals or external state are clearly named or documented.
- [ ] **Non-obvious logic documented** — "Why" comments, links to ADRs, or inline rationale for invariants.

### Consistency
- [ ] **Similar patterns used similarly** — Error handling, validation, and data flow follow conventions.
- [ ] **New developers can understand without tracing 10 call sites** — Modules are self-contained enough.

---

## 3. Technical Debt Indicators

### TODO / FIXME / HACK
- [ ] **Fewer than 5 untracked items** — TODO/FIXME either have issue references or are actively triaged.
- [ ] **No HACK without explanation** — Suppressed warnings and workarounds have "why" and "when to fix."

### Duplication
- [ ] **Shared logic extracted** — Same validation, transformation, or formatting in one place.
- [ ] **No copy-paste blocks** — Repeated code blocks extracted to named functions.
- [ ] **DRY applied to business logic** — Domain rules live in one source of truth.

### Magic Values
- [ ] **Named constants for numbers** — `SECONDS_PER_DAY` not `86400`.
- [ ] **Enums or constants for strings** — `OrderStatus.ACTIVE` not `"active"`.
- [ ] **Configuration injected** — Thresholds and flags from config, not literals.

### Suppressions
- [ ] **No broad lint suppressions** — `eslint-disable` for whole files is avoided.
- [ ] **Targeted suppressions with justification** — Each suppression has a comment explaining why.
- [ ] **Suppressions tracked** — Known suppressions have tech debt issues.

### Comments & Docs
- [ ] **Comments explain "why" not "what"** — Code shows what; comments explain rationale.
- [ ] **No stale or misleading comments** — Comments match current behavior.
- [ ] **Non-obvious decisions documented** — Invariants, business rules, and edge cases have context.

---

## 4. Coupling and Dependency Depth

### Afferent / Efferent Coupling
- [ ] **No god modules** — No module imported by 70%+ of the codebase.
- [ ] **Public interfaces defined** — Modules expose clear APIs; internals are hidden.
- [ ] **Dependencies point inward** — Domain does not depend on infrastructure.

### Inheritance & Dependency Depth
- [ ] **Inheritance depth 2–3 levels** — Deeper hierarchies are hard to reason about.
- [ ] **Composition over inheritance** — Where appropriate, prefer composition.
- [ ] **Dependency tree depth reasonable** — No 10-layer transitive stacks for simple tasks.
- [ ] **No skip-layer imports** — Boundaries respected; no presentation importing from data layer.

---

## 5. Code Smell Density

### God Classes & Long Methods
- [ ] **No classes over 500 lines** — Split by responsibility.
- [ ] **No methods over 50 lines** — Extract and name helpers.
- [ ] **Single responsibility** — Each class has one reason to change.

### Feature Envy & Inappropriate Intimacy
- [ ] **Objects encapsulate their data** — Minimal cross-object data peeking.
- [ ] **No anemic data bags** — Objects with behavior, not just getters/setters.
- [ ] **No classes knowing internals of others** — Use interfaces and public contracts.

### Shotgun Surgery
- [ ] **Changes localize** — One feature change touches one or two modules, not 10+.
- [ ] **No scattered related logic** — Related code lives together.

### Dead Code
- [ ] **No dead code** — Unused functions and unreachable branches removed.
- [ ] **No commented-out blocks** — Removed or replaced with version control.
- [ ] **No primitive obsession** — Domain concepts as value objects where appropriate.
