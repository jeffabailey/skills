---
name: review-data
description: Analyzes database schema design, migration safety, data integrity, query correctness, data modeling, and pipeline quality, producing fitness scores (1-10) with file:line evidence. Use when the user says /review:review-data, requests a data review, asks about schema design, migration safety, data integrity, query correctness, data modeling, or pipeline quality. Distinct from review-performance (which asks "are queries fast?"); this asks "is the schema correct? are migrations safe? will data integrity hold?" Only reports findings with confidence >= 7/10.
---

# Data Fitness Review

Analyze the codebase (or specified files/modules) for data fitness. Identify gaps in schema design, migration safety, data integrity, query correctness, data modeling, and pipeline quality using evidence from the code, schema definitions, migration files, and configuration.

Reference: [Fundamentals of Databases](https://jeffbailey.us/blog/2025/09/24/fundamentals-of-databases/), [Fundamentals of Data Engineering](https://jeffbailey.us/blog/2025/11/22/fundamentals-of-data-engineering/), [Fundamentals of Graph Databases](https://jeffbailey.us/blog/2026/02/14/fundamentals-of-graph-databases/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

- `references/rubric.md` is the scoring source: severity definitions, score anchors per dimension, the N/A rule, scope boundaries, and the overall-score formula. Read it first; it is short.
- `references/checklist.md` lists what to inspect in each dimension during steps 4-9.
- `references/wisdom.md` is optional background, auto-generated from the three articles above. It has no rubric. When you need depth on one topic (normalization, CDC, data quality dimensions), grep it for that heading and read only that section; never read it whole (~25k tokens).

## Configuration

Invoke the resolver CLI to obtain effective weights and thresholds for the review target. Never load `fitness-config.json` directly.

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py" show --path <target>
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; the resolver ships two levels up in the plugin's `scripts/`. If your agent does not expand the variable, substitute the directory containing this `SKILL.md`.

Where `<target>` is the file or directory under review. The CLI walks up to discover any module override and merges it with the root config. Include the `Config:` and `Effective weights:` lines from the resolver output within the first 10 lines of the final report as the provenance trail (AC-03.1, AC-08.2). The `effective` object inside the JSON block delimited by `<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->` / `<!-- END_EFFECTIVE_CONFIG_JSON -->` carries weights, status thresholds, security, and scoring for any programmatic needs.

## Workflow

1. **Load the rubric** — Read `references/rubric.md`, then `references/checklist.md`. Run the resolver (see Configuration) on the target.

2. **Map data boundaries** — Grep/Glob for schema definitions (CREATE TABLE, ORM models), migration directories, SQL and query-builder calls, database configuration, and pipeline code (ETL, import/export, batch jobs, stream consumers). Skip build output, vendored dependencies, and test fixtures (`target/`, `bin/`, `obj/`, `_build/`, `dist/`, `node_modules/`, `vendor/`, `.venv/`, test dirs) unless the user asks for them. For files over ~500 lines, grep for the data-access patterns (`query`, `execute`, `BEGIN`, `FOR UPDATE`, `ON CONFLICT`, `JOIN`) and read only the surrounding ranges. Also look for documented data policies (ADRs, `docs/`, migration READMEs), because a documented choice changes what counts as a gap.

3. **Decide applicability** — For each of the six dimensions, decide whether anything in scope can be evaluated, using the N/A rule in `rubric.md`. If nothing data-related exists at all, skip to step 10 and write the short "no data layer" report described under Output Format. Do not invent scores or findings to fill the template.

4. **Audit schema design** — Table definitions, column types, constraints, foreign keys, naming.

5. **Evaluate migration safety** — Migration files (sqlx, Alembic, Flyway, Rails, Knex, Django, Prisma, raw DDL). Check rollback path or documented forward-only policy, zero-downtime patterns (add-nullable/backfill/constrain, expand-contract), lock-safe DDL, data preservation.

6. **Check data integrity** — Unique and CHECK constraints, NOT NULL, transaction boundaries, isolation levels, check-then-act races.

7. **Assess query correctness** — JOIN semantics, GROUP BY, parameterization, dynamic IN/LIKE, read-modify-write scoping, type coercion.

8. **Evaluate data modeling** — Temporal columns, delete strategy, audit/history, polymorphism, JSON column use.

9. **Assess pipeline quality** — Idempotent loads, error routing, run tracking, schema evolution, quality gates between stages.

   For steps 4-9, use `checklist.md` for what to look at and `rubric.md` for severity and score. Route speed-only findings (missing index for a slow query, N+1, scans) to review-performance and non-data correctness bugs (parsing, regex, general concurrency) to review-algorithms: mention them in one line under "Out of scope", do not score them.

10. **Score and write** — Score each applicable dimension against the `rubric.md` anchors, compute the overall per `rubric.md`, run the self-check below, then write the report.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

Severity levels (CRITICAL, HIGH, MEDIUM, LOW) are defined with data examples in `references/rubric.md`. A documented, followed policy (for example an ADR choosing forward-only migrations) meets the matching checklist intent; it is not a finding.

## Scoring Dimensions (1-10 each)

Score anchors for each dimension are in `references/rubric.md`. A dimension with nothing in scope is `N/A` with a reason, not a number.

1. **Schema Design** — Column types, constraints, normalization level, foreign keys, naming conventions, constraint-backing indexes
2. **Migration Safety** — Rollback path or documented forward-only policy, zero-downtime patterns, expand-contract renames, lock-safe DDL, data preservation
3. **Data Integrity** — Foreign keys, unique constraints, CHECK constraints, NOT NULL enforcement, transaction boundaries, isolation levels
4. **Query Correctness** — JOIN type semantics, GROUP BY completeness, parameterized queries, transaction scoping, type coercion avoidance
5. **Data Modeling** — Temporal columns, soft-delete consistency, audit trails, versioning, polymorphic associations, JSON column appropriateness
6. **Pipeline Quality** — Idempotent loads, error handling, monitoring, incremental vs full loads, schema evolution, data quality gates

## Output Format

Write the report to `docs/data-review.md` at the root of the repository that contains the target, unless the user gives a path. For a review scoped to a subdirectory or file set, write `docs/data-review-<scope-slug>.md` (e.g. `docs/data-review-crates-foundry-store.md`) so a scoped run does not replace the whole-repo report.

Before writing, self-check:
- Every file:line exists and the line says what the finding claims.
- Every finding has confidence >= 7 and belongs to this skill (not speed, not non-data correctness).
- The overall equals the stated computation, including the CRITICAL cap.
- No secret values (connection strings, passwords) are reproduced; refer to them by file:line only.

```markdown
# Data Fitness Review

**Target:** <path(s) or scope reviewed>
Config: <copied from resolver output>
Effective weights: <copied from resolver output>

## Direct Answer

(Only when the user asked a specific question, e.g. "are the migrations safe?". Two to five sentences answering it, citing the key findings.)

## Summary

Overall fitness score: X.X / 10 (mean of <list scored dimensions>; <cap note if any>) — <status band>

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Schema Design | X/10 | ... |
| Migration Safety | X/10 | ... |
| Data Integrity | X/10 | ... |
| Query Correctness | X/10 | ... |
| Data Modeling | X/10 | ... |
| Pipeline Quality | N/A — no ETL/batch/stream code in scope | — |

Documented policies credited: <e.g. forward-only migrations, docs/adr/0007.md> (omit if none)

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line
- **Description:** What the issue is and why it matters.
- **Evidence:** The specific code pattern found.
- **Impact:** What could go wrong with data integrity or quality.
- **Remediation:** Concrete fix with code example or specific steps.

(repeat for each finding, ordered by severity)

### Schema Design (X/10)
- Evidence: file:line references
- Issues found
- Recommendations

(repeat for each scored dimension; one line per N/A dimension)

## Out of scope

(Optional. One line each: finding, file:line, route to review-performance / review-algorithms / review-security.)

## Top Action Items (up to 5, by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...

## Checklist Reference

See references/checklist.md for the full data checklist.

## Reference

Based on [Fundamentals of Databases](https://jeffbailey.us/blog/2025/09/24/fundamentals-of-databases/), [Fundamentals of Data Engineering](https://jeffbailey.us/blog/2025/11/22/fundamentals-of-data-engineering/), [Fundamentals of Graph Databases](https://jeffbailey.us/blog/2026/02/14/fundamentals-of-graph-databases/), and guidance from https://jeffbailey.us/categories/fundamentals/
```

### No data layer

When step 3 finds no schema, migrations, queries, or pipelines, write a short report instead: the H1 and provenance lines, a sentence stating that no database schema, migrations, SQL/ORM queries, or data pipelines were found and where you looked (e.g. `grep -ri "CREATE TABLE|SELECT |migrat|sqlx|ORM" (none)`), the summary table with every dimension `N/A`, `Overall fitness score: N/A (no scored dimensions)`, and any out-of-scope notes. No action items are required. Do not file regex, parsing, or file-handling issues as data findings; list them under Out of scope for review-algorithms.
