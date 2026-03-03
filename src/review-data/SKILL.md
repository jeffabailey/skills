---
name: review-data
description: Analyzes database schema design, migration safety, data integrity, query correctness, data modeling, and pipeline quality, producing fitness scores (1-10) with file:line evidence. Use when the user says /review:review-data, requests a data review, asks about schema design, migration safety, data integrity, query correctness, data modeling, or pipeline quality. Distinct from review-performance (which asks "are queries fast?"); this asks "is the schema correct? are migrations safe? will data integrity hold?" Only reports findings with confidence >= 7/10.
---

# Data Fitness Review

Analyze the codebase (or specified files/modules) for data fitness. Identify gaps in schema design, migration safety, data integrity, query correctness, data modeling, and pipeline quality using evidence from the code, schema definitions, migration files, and configuration.

Reference: [Fundamentals of Databases](https://jeffbailey.us/blog/2025/09/24/fundamentals-of-databases/), [Fundamentals of Data Engineering](https://jeffbailey.us/blog/2025/11/22/fundamentals-of-data-engineering/), [Fundamentals of Graph Databases](https://jeffbailey.us/blog/2026/02/14/fundamentals-of-graph-databases/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

For detailed scoring rubrics, severity definitions, what-good-looks-like / what-bad-looks-like criteria, and domain expertise, read `references/wisdom.md` before scoring. That file is auto-generated from:

- [Fundamentals of Databases](https://jeffbailey.us/blog/2025/09/24/fundamentals-of-databases/)
- [Fundamentals of Data Engineering](https://jeffbailey.us/blog/2025/11/22/fundamentals-of-data-engineering/)
- [Fundamentals of Graph Databases](https://jeffbailey.us/blog/2026/02/14/fundamentals-of-graph-databases/)

Use the wisdom reference when evaluating code and assigning dimension scores.

## Workflow

1. **Read domain knowledge** — Read `references/wisdom.md` to load scoring rubrics, thresholds, and severity definitions.

2. **Map data boundaries** — Use Grep/Glob to find database schema definitions (CREATE TABLE, model definitions, ORM models), migration files, SQL queries, database configuration, connection setup, and data pipeline code. These are the surfaces where data fitness matters most.

3. **Audit schema design** — Examine table definitions, column types, constraints, foreign key relationships, and naming conventions. Apply the rubrics/thresholds from the wisdom reference.

4. **Evaluate migration safety** — Find migration files (Alembic, Flyway, Rails migrations, Knex, Django, Prisma, or raw SQL DDL scripts). Check for reversible rollbacks, zero-downtime patterns, and lock-safe DDL. Apply the rubrics/thresholds from the wisdom reference.

5. **Check data integrity** — Look for foreign key constraints, unique constraints, check constraints, NOT NULL enforcement, transaction boundaries, and isolation levels. Apply the rubrics/thresholds from the wisdom reference.

6. **Assess query correctness** — Find SQL queries and ORM query patterns. Check JOIN types, GROUP BY correctness, parameterized queries, transaction scoping, and implicit type coercion. Apply the rubrics/thresholds from the wisdom reference.

7. **Evaluate data modeling** — Check temporal data handling, soft-delete consistency, audit trails, polymorphic associations, and JSON column usage. Apply the rubrics/thresholds from the wisdom reference.

8. **Assess pipeline quality** — Find ETL/ELT code, data import/export scripts, batch jobs, and streaming consumers. Check for idempotent loads, error handling, data quality validation, and schema evolution handling. Apply the rubrics/thresholds from the wisdom reference.

9. **Score each dimension** with file:line evidence, using the rubrics from `references/wisdom.md`.

10. **Produce the report** with scores, evidence, and prioritized action items.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

For severity level definitions (CRITICAL, HIGH, MEDIUM, LOW) with domain-specific examples, consult `references/wisdom.md`.

## Scoring Dimensions (1-10 each)

Dimensions to score (detailed rubrics including what-to-check, what-good-looks-like, and what-bad-looks-like are in `references/wisdom.md`):

1. **Schema Design** — Column types, constraints, normalization level, foreign keys, naming conventions, indexes
2. **Migration Safety** — Reversible rollbacks, zero-downtime patterns, expand-contract renames, lock-safe DDL, data preservation
3. **Data Integrity** — Foreign keys, unique constraints, CHECK constraints, NOT NULL enforcement, transaction boundaries, isolation levels
4. **Query Correctness** — JOIN type semantics, GROUP BY completeness, parameterized queries, transaction scoping, type coercion avoidance
5. **Data Modeling** — Temporal columns, soft-delete consistency, audit trails, versioning, polymorphic associations, JSON column appropriateness
6. **Pipeline Quality** — Idempotent loads, error handling, monitoring, incremental vs full loads, schema evolution, data quality gates

## Output Format

Write the report to `docs/data-review.md` with this structure:

```markdown
# Data Fitness Review

## Summary

Overall fitness score: X.X / 10 (average of dimensions)

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Schema Design | X/10 | ... |
| Migration Safety | X/10 | ... |
| Data Integrity | X/10 | ... |
| Query Correctness | X/10 | ... |
| Data Modeling | X/10 | ... |
| Pipeline Quality | X/10 | ... |

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

(repeat for each dimension)

## Top 5 Action Items (by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...

## Checklist Reference

See references/checklist.md for the full data checklist.

## Reference

Based on [Fundamentals of Databases](https://jeffbailey.us/blog/2025/09/24/fundamentals-of-databases/), [Fundamentals of Data Engineering](https://jeffbailey.us/blog/2025/11/22/fundamentals-of-data-engineering/), [Fundamentals of Graph Databases](https://jeffbailey.us/blog/2026/02/14/fundamentals-of-graph-databases/), and guidance from https://jeffbailey.us/categories/fundamentals/
```

Refer to the data checklist at `review-data/references/checklist.md` for detailed checks within each dimension.
