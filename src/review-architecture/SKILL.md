---
name: review-architecture
description: Analyzes code for software architecture fitness, producing scores (1-10) across coupling, cohesion, layering, modularity, naming, API design, and maintainability. Use when the user says /review:review-architecture, requests an architecture review, asks about coupling and cohesion, wants to analyze design or check code structure, asks to review naming or API design, or needs architecture fitness scores. Triggers on "architecture review", "coupling and cohesion", "analyze design", "check code structure", "review naming", "API design".
---

# Software Architecture Fitness Review

Analyze the codebase (or specified files/modules) for software architecture fitness. Identify structural problems, design violations, and maintainability risks using evidence from the code.

Reference: https://jeffbailey.us/categories/fundamentals/

## Workflow

1. **Identify scope and boundaries** -- Use Glob/Grep to map the codebase structure: top-level directories, module boundaries, entry points, configuration files, and dependency declarations. Determine whether the system is a monolith, modular monolith, microservices, or layered architecture. Identify where boundaries exist (or should exist) between distinct areas of responsibility.

2. **Map dependency graph** -- Trace imports and references between modules. Identify which modules depend on which others. Look for circular dependencies, dependency direction violations (e.g., domain depending on infrastructure), and modules that are imported by everything (hub modules).

3. **Analyze coupling** -- For each module boundary, check how tightly components are connected. Look for concrete class references crossing boundaries, shared mutable state, temporal coupling (must-call-in-order sequences), and data coupling (passing entire objects when only a field is needed). Count cross-boundary imports.

4. **Assess cohesion** -- For each module or class, check whether its contents belong together. Look for classes with unrelated methods, modules that mix concerns (e.g., HTTP handling with business logic with database access), and files that change for multiple unrelated reasons.

5. **Evaluate layering and modularity** -- Check whether the architecture has clear layers (presentation, business logic, data access) or modules with defined responsibilities. Look for skip-layer violations (presentation directly accessing the database), business logic leaking into controllers, and infrastructure concerns mixed into domain code.

6. **Review naming quality** -- Assess names of files, classes, functions, variables, and modules for clarity, consistency, context-appropriateness, convention compliance, and discoverability. Look for generic names, inconsistent patterns, abbreviations that require lookup, misleading names, and names that do not scale.

7. **Audit API design** -- Check internal and external API contracts for consistency, backward compatibility awareness, error handling uniformity, semantic clarity, and idempotency where needed. Look for inconsistent error shapes, missing versioning strategy, breaking changes without migration paths, and unclear field semantics.

8. **Evaluate maintainability** -- Check for code smells that indicate maintainability risk: god classes (500+ lines), long methods (50+ lines), deep nesting (4+ levels), magic numbers, duplicated logic, missing tests for critical paths, and undocumented non-obvious decisions.

9. **Score each dimension** with specific file:line evidence.

10. **Produce the report** with scores, evidence, and prioritized action items.

## Scoring Dimensions (1-10 each)

Evaluate and score each dimension with evidence from the code.

### 1. Coupling

What to check:
- Cross-boundary import count between modules
- Concrete vs abstract dependencies at module boundaries
- Shared mutable state between components
- Circular dependency chains (A depends on B depends on A)
- Data coupling: passing full objects when only a field is needed
- Temporal coupling: sequences that must be called in a specific order without enforcement
- God modules that everything imports

What good looks like (8-10):
- Modules communicate through well-defined interfaces or abstractions
- No circular dependencies between modules
- Changes to one module rarely force changes to others
- Dependencies point inward (infrastructure depends on domain, not the reverse)
- Cross-boundary communication uses data transfer objects or events, not shared internal types

What bad looks like (1-3):
- Circular dependency chains spanning three or more modules
- Changing one file requires updating files in multiple unrelated modules
- Direct database access from presentation code, bypassing business logic
- Shared mutable global state used for communication between components
- A single utility module imported by more than 70% of other modules

### 2. Cohesion

What to check:
- Whether each class or module has a single, identifiable responsibility
- Whether methods in a class use the same instance data (functional cohesion)
- Whether a module mixes unrelated concerns (HTTP handling, business logic, database queries)
- Whether files change for multiple unrelated reasons
- Whether related functionality is scattered across multiple distant modules

What good looks like (8-10):
- Each module or class has one clear reason to change
- Methods within a class operate on the same data and serve the same purpose
- Related functionality is grouped together (feature cohesion or domain cohesion)
- A class can be described in a single sentence without using "and"

What bad looks like (1-3):
- Classes with 20+ public methods spanning unrelated responsibilities
- A single file contains HTTP routing, validation, business rules, and SQL queries
- Related functionality split across three or more distant directories with no clear organizing principle
- Modules named "utils", "helpers", or "common" that accumulate unrelated functions

### 3. Layering

What to check:
- Whether clear architectural layers exist (presentation, business logic, data access)
- Whether dependencies between layers follow a consistent direction
- Whether skip-layer access occurs (controllers directly calling the database)
- Whether business logic leaks into infrastructure layers (validation in database code, business rules in HTTP handlers)
- Whether domain objects carry infrastructure concerns (ORM annotations on domain models, HTTP status codes in business logic)

What good looks like (8-10):
- Clear separation between presentation, business logic, and data access
- Each layer depends only on the layer directly below it
- Business logic is free of infrastructure concerns (no SQL, no HTTP, no file paths)
- Domain objects are plain data structures without framework coupling
- Infrastructure details can be swapped without changing business logic

What bad looks like (1-3):
- Controllers contain SQL queries or direct file system access
- Business rules are embedded in database migration scripts or stored procedures with no application-layer equivalent
- Domain models inherit from framework base classes, making them untestable without the framework
- No identifiable layers; every file imports from every other directory

### 4. Modularity

What to check:
- Whether the codebase is organized into modules with clear boundaries
- Whether modules have explicit public interfaces (index files, facade classes, API modules)
- Whether internal implementation details are hidden from other modules
- Whether modules can be understood, tested, and modified independently
- Whether module boundaries align with domain concepts or team boundaries

What good looks like (8-10):
- Each module exposes a public interface and hides internal implementation
- Modules can be tested independently with their dependencies mocked or stubbed
- Adding a new feature requires changes to one or two modules, not five
- Module boundaries align with business domain areas (orders, users, payments)
- Internal module structure can change without affecting consumers

What bad looks like (1-3):
- No clear module boundaries; the codebase is a flat collection of files
- Other modules reach into internal implementation details of another module
- Adding a feature requires coordinated changes across many modules
- Module boundaries are based on technical type (all models together, all controllers together) rather than domain
- No public interface definition; any file can import any other file

### 5. Naming

What to check:
- Whether names communicate intent without requiring code reading (clarity)
- Whether similar concepts use the same naming patterns (consistency)
- Whether name specificity matches scope (short names in local scope, descriptive names in public interfaces)
- Whether names follow language and framework conventions (conventions)
- Whether names are searchable and distinctive (discoverability)
- Whether names accurately describe what the code does (truthfulness)

What good looks like (8-10):
- Functions named with verbs that describe the action: `calculateTotalPrice()`, `validateUserInput()`
- Consistent patterns: if one module uses `getUser()`, others use `getOrder()` not `fetchOrder()`
- Booleans prefixed with `is`, `has`, `can`: `isValid`, `hasPermission`, `canEdit`
- Public interfaces use self-documenting names; local variables use context-appropriate brevity
- Names follow language conventions (snake_case in Python, camelCase in JavaScript)

What bad looks like (1-3):
- Generic names: `data`, `info`, `temp`, `result`, `process()`, `handle()`, `Manager` (without domain prefix)
- Inconsistent patterns: `getUser()`, `fetchOrder()`, `retrieveProduct()` for the same concept
- Abbreviations requiring lookup: `usrAcct`, `calcTot`, `procDat`
- Names that lie: a function called `getUser()` that creates a user
- Single-letter variables in non-trivial scopes; domain terms vary across files

### 6. API Design

What to check:
- Whether API contracts define inputs, outputs, and error behavior explicitly
- Whether error responses use a consistent shape across all endpoints
- Whether breaking changes are managed through versioning or backward-compatible evolution
- Whether field semantics are clear (what does `amount` mean? cents or dollars? what currency?)
- Whether idempotency is addressed for write operations
- Whether APIs follow RESTful conventions (resource-based URLs, proper HTTP method usage)

What good looks like (8-10):
- Consistent error response shape across all endpoints with code, message, and field-level detail
- API changes add optional fields rather than modifying or removing existing ones
- Write endpoints support idempotency keys or are naturally idempotent
- Field names are self-documenting with units where needed (`amount_cents`, `duration_seconds`)
- Contract is validated (schema validation, contract tests, OpenAPI spec)

What bad looks like (1-3):
- Every endpoint returns errors in a different format
- Fields are removed or renamed between releases without versioning
- No idempotency strategy; retrying a payment creates duplicate charges
- Field semantics are ambiguous (`status` could mean anything; `amount` has no currency or unit)
- No API specification; consumers must read the code to understand the contract

### 7. Maintainability

What to check:
- Code smells: god classes (500+ lines), long methods (50+ lines), deep nesting (4+ levels)
- Duplicated logic across the codebase (same validation in multiple places)
- Magic numbers and strings without named constants
- Missing tests for business-critical paths
- Missing or outdated documentation for non-obvious decisions
- Technical debt indicators: TODO/FIXME/HACK comments, suppressed warnings
- Cyclomatic complexity of critical functions
- Dependency health: outdated, unmaintained, or vulnerable dependencies

What good looks like (8-10):
- Functions under 30 lines; classes under 300 lines
- Shared logic extracted into reusable functions with single responsibility
- Named constants replace magic numbers; enums replace magic strings
- Critical business logic has test coverage
- Non-obvious decisions documented with "why" comments or ADRs
- Dependencies are current and monitored for vulnerabilities

What bad looks like (1-3):
- God classes over 1000 lines handling multiple unrelated responsibilities
- The same validation logic copy-pasted in five places
- Numbers like `86400` or strings like `"active"` scattered through the code without constants
- No tests; refactoring is too risky because nothing verifies behavior
- More than 10 TODO/FIXME/HACK comments without tracking or prioritization
- Dependencies years out of date with known CVEs

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
```

Refer to the architecture checklist at `review-architecture/references/checklist.md` for detailed checks within each dimension.
