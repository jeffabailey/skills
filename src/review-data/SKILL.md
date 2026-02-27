---
name: review-data
description: Analyzes database schema design, migration safety, data integrity, query correctness, data modeling, and pipeline quality, producing fitness scores (1-10) with file:line evidence. Use when the user says /review:review-data, requests a data review, asks about schema design, migration safety, data integrity, query correctness, data modeling, or pipeline quality. Distinct from review-performance (which asks "are queries fast?"); this asks "is the schema correct? are migrations safe? will data integrity hold?"
---

# Data Fitness Review

Analyze the codebase (or specified files/modules) for data fitness. Identify gaps in schema design, migration safety, data integrity, query correctness, data modeling, and pipeline quality using evidence from the code, schema definitions, migration files, and configuration.

## Workflow

1. **Map data boundaries** -- Use Grep/Glob to find database schema definitions (CREATE TABLE, model definitions, ORM models), migration files, SQL queries, database configuration, connection setup, and data pipeline code. These are the surfaces where data fitness matters most.

2. **Audit schema design** -- Examine table definitions, column types, constraints, foreign key relationships, and naming conventions. Check whether normalization level is appropriate for the use case. Look for columns typed as generic varchar or text where a more specific type (integer, boolean, timestamp, enum, UUID) would enforce correctness. Verify that business rules are expressed as database constraints, not only in application code.

3. **Evaluate migration safety** -- Find migration files (Alembic, Flyway, Rails migrations, Knex, Django, Prisma, or raw SQL DDL scripts). Check whether each migration has a reversible down/rollback. Look for dangerous patterns: adding a NOT NULL column without a default in a single step, renaming columns or tables without a multi-step approach, dropping columns without verifying no code references remain, and long-running locks on large tables (e.g., ALTER TABLE that rewrites the table under lock).

4. **Check data integrity** -- Look for foreign key constraints, unique constraints, check constraints, and NOT NULL enforcement. Examine transaction boundaries: are they too wide (holding locks across slow operations) or too narrow (allowing partial state)? Check isolation levels for correctness. Verify that business-critical operations use transactions where atomicity is required.

5. **Assess query correctness** -- Find SQL queries and ORM query patterns. Check JOIN types (LEFT JOIN used where INNER JOIN is appropriate, or vice versa). Verify proper use of GROUP BY (all non-aggregated columns in SELECT are in GROUP BY). Look for implicit type coercion that could cause silent data loss. Verify parameterized queries are used (overlap with security, but here focus on correctness of parameter binding). Check transaction scoping around multi-statement business operations.

6. **Evaluate data modeling** -- Check temporal data handling: are created_at and updated_at columns present and auto-populated? Is the soft-delete vs hard-delete strategy consistent? Look for audit trail patterns on important entities. Check how polymorphic associations are handled (STI, separate tables, or JSON). Evaluate JSON/document column usage: is it serving a genuine flexibility need or avoiding proper schema design?

7. **Assess pipeline quality** -- Find ETL/ELT code, data import/export scripts, batch processing jobs, and streaming consumers. Check for idempotent load patterns (can the pipeline re-run without creating duplicates?). Look for error handling that preserves failed records (dead-letter queues, error tables). Check for data quality validation between pipeline stages. Evaluate incremental vs full load strategy and schema evolution handling.

8. **Score each dimension** with specific file:line evidence.

9. **Produce the report** with scores, evidence, and prioritized action items.

## Scoring Dimensions (1-10 each)

Evaluate and score each dimension with evidence from the code.

### 1. Schema Design

What to check:
- Normalization level is appropriate for the use case (not under-normalized with redundant data, not over-normalized causing excessive joins for simple reads)
- Column types match the data they store (timestamps for dates, integers for counts, booleans for flags, UUIDs for identifiers -- not everything stored as varchar)
- Constraints enforce business rules at the database level (CHECK constraints for valid ranges, NOT NULL for required fields, UNIQUE where duplicates are invalid)
- Relationships are properly modeled with foreign keys, not just application-level conventions
- Naming conventions are consistent across all tables and columns (snake_case or camelCase, singular or plural table names, consistent suffix patterns for timestamps and IDs)
- Indexes exist for columns used in WHERE clauses, JOIN conditions, and ORDER BY statements
- No single-column tables or tables with dozens of nullable columns suggesting poor decomposition

What good looks like (8-10):
- Every column uses the most specific type available (TIMESTAMP WITH TIME ZONE for timestamps, BOOLEAN for flags, INTEGER for counts, UUID for identifiers)
- Business rules enforced by CHECK, UNIQUE, and NOT NULL constraints at the database level
- Foreign keys defined for all relationships with appropriate ON DELETE behavior (CASCADE, SET NULL, RESTRICT)
- Consistent naming: all tables use the same convention, ID columns follow a pattern, timestamp columns are uniform
- Normalization appropriate to workload: OLTP at 3NF, read-heavy tables with deliberate denormalization documented
- Composite indexes cover common multi-column query patterns

What bad looks like (1-3):
- Most columns are VARCHAR(255) or TEXT regardless of actual data type
- No foreign keys; relationships exist only in application code
- No CHECK constraints; business rules like "status must be one of draft, active, archived" are only validated in application code
- Inconsistent naming: mix of snake_case and camelCase, some tables plural, some singular, ID columns vary between id, ID, table_id
- Tables with 30+ nullable columns suggesting a "god table" that should be decomposed
- No indexes beyond primary keys

### 2. Migration Safety

What to check:
- Every migration has a reversible rollback (up + down) that can undo the schema change
- Zero-downtime patterns used for additive changes: add nullable column, backfill data, then add NOT NULL constraint (not add NOT NULL column in one step)
- Column renames and table renames use a multi-step expand-contract approach (add new, copy data, update code, drop old)
- Data preservation is verified: migrations that modify data include validation that no records are lost
- Migration ordering and dependencies are handled (migrations do not assume state from uncommitted migrations)
- Lock-safe DDL for large tables: operations that rewrite tables (adding a column with a default in some databases, changing column type) use online DDL or are scheduled during low-traffic windows
- Migrations are tested in a staging environment before production

What good looks like (8-10):
- Every migration file includes both up and down methods that are inverses of each other
- Adding a required column is a three-step migration: add nullable column, backfill, add NOT NULL constraint
- Column renames use expand-contract: add new column, dual-write, migrate reads, drop old column
- Large table operations use CREATE INDEX CONCURRENTLY or equivalent non-blocking DDL
- Migration files include comments explaining why the change is being made
- Rollback procedures are documented and tested

What bad looks like (1-3):
- Migrations have no down/rollback method (irreversible by default)
- Adding NOT NULL columns without defaults in a single migration (fails on existing rows or causes downtime)
- DROP COLUMN without verifying no application code references the column
- Large table ALTER operations with no consideration for lock contention
- No migration testing; migrations are run directly in production
- Data migrations mixed with schema migrations in the same file

### 3. Data Integrity

What to check:
- Foreign key constraints are defined for all relationships between tables
- Unique constraints exist where business logic requires uniqueness (email addresses, usernames, external identifiers, composite keys)
- CHECK constraints enforce valid data ranges and states (positive prices, valid status values, dates in reasonable ranges)
- NOT NULL is used on columns where null would indicate a bug rather than a valid absence of data
- Transaction boundaries are correct: multi-step business operations (transfer funds, place order) are wrapped in transactions
- Transaction scope is appropriate: not too wide (holding locks while making HTTP calls or waiting for user input) and not too narrow (committing after each INSERT in a batch that should be atomic)
- Isolation levels are appropriate: READ COMMITTED for most operations, SERIALIZABLE for financial or inventory operations where phantom reads would cause bugs
- Cascading deletes and updates are intentional and documented

What good looks like (8-10):
- All relationships have foreign keys with explicit ON DELETE behavior
- Unique constraints on business-significant fields (email, external_id, composite natural keys)
- CHECK constraints enforce domain rules (price > 0, status IN ('draft','active','archived'))
- Transactions wrap business operations that must be atomic (order creation with line items, fund transfers)
- Isolation levels are explicitly set for operations that require stronger guarantees
- Orphaned record prevention: foreign keys prevent deleting a parent with active children, or cascades are intentional

What bad looks like (1-3):
- No foreign keys; referential integrity enforced only in application code (or not at all)
- No unique constraints; duplicate detection relies on application-level checks that are race-condition prone
- No CHECK constraints; invalid data (negative prices, impossible dates) can be inserted
- No transactions around multi-step operations; partial failures leave inconsistent state
- Default isolation level used everywhere with no consideration for correctness requirements
- Orphaned records exist because parent rows were deleted without cascading or checking children

### 4. Query Correctness

What to check:
- JOIN types match the intended semantics (INNER JOIN when both sides must exist, LEFT JOIN only when the right side is optional, not LEFT JOIN by default on every query)
- GROUP BY includes all non-aggregated columns in the SELECT list (databases that allow partial GROUP BY produce undefined results)
- Transaction scoping matches the business operation (a multi-step operation like "check inventory, reserve stock, create order" is in one transaction, not separate queries)
- Parameterized queries or prepared statements are used everywhere (focus here is on correctness of parameter binding, not just security)
- Window functions are used correctly (PARTITION BY and ORDER BY clauses match the analytical intent)
- Implicit type coercion is avoided (comparing strings to integers, joining on mismatched types, storing numbers as strings)
- HAVING is used for filtering aggregated results, not WHERE on aggregate aliases
- Subqueries and CTEs are correct (correlated subqueries return expected row counts, CTEs produce expected intermediate results)
- DISTINCT is not used to mask a join that produces unintended duplicates

What good looks like (8-10):
- JOIN types are deliberate: INNER JOIN for required relationships, LEFT JOIN only where nulls are expected and handled
- Every GROUP BY lists all non-aggregated SELECT columns explicitly
- Multi-step business operations use explicit transactions with appropriate isolation
- All queries use parameterized binding, including dynamic IN clauses and LIKE patterns
- No implicit type coercion; columns are compared to values of matching types
- DISTINCT is used only where genuine duplicates are expected, not to fix join fan-out

What bad looks like (1-3):
- LEFT JOIN used on every query regardless of whether nulls are valid (masks missing data that should cause an error)
- GROUP BY with partial column lists producing non-deterministic results
- Multi-step operations without transactions (check-then-act patterns without atomicity)
- String concatenation or interpolation in SQL (even with ORM escape, this is a correctness risk)
- DISTINCT applied everywhere to suppress duplicate rows caused by incorrect joins
- Comparing varchar columns to integer values relying on implicit casting

### 5. Data Modeling

What to check:
- Temporal data handling: created_at and updated_at columns present on entities where creation and modification time matter, with automatic population (database defaults or triggers)
- Soft delete vs hard delete strategy is consistent and intentional (deleted_at column for soft deletes, with queries filtering deleted records; or hard deletes with appropriate cascading)
- Audit trails exist for important changes: who changed what, when, and what the previous value was (audit tables, event sourcing, or change history)
- Versioning strategy for mutable records: how are changes to important records tracked over time (version column, history table, event log)
- Polymorphic associations are handled cleanly (single-table inheritance with a type discriminator, separate tables per type, or a join table -- not a polymorphic foreign key pointing to multiple tables without a constraint)
- JSON/document columns are used appropriately for genuinely flexible data (user preferences, metadata, plugin configuration) not as schema avoidance for data that has a known, stable structure
- Enum values are stored as database enums or constrained strings, not as magic numbers or unconstrained text
- Graph-like relationships (if present) are modeled appropriately: adjacency lists, materialized paths, or nested sets for tree structures; a dedicated graph database for heavily traversed relationships

What good looks like (8-10):
- All entities have created_at with a database default and updated_at populated by trigger or application
- Soft deletes used consistently with a deleted_at timestamp; all queries include a WHERE deleted_at IS NULL filter (or equivalent default scope)
- Audit table records who, what, when, and previous value for sensitive entities (users, payments, permissions)
- JSON columns are used for genuinely variable-structure data with JSON schema validation or application-level validation
- Polymorphic associations use a type discriminator column with CHECK constraints or separate join tables
- Tree/hierarchy structures use a proven pattern (closure table, materialized path) with documented trade-offs

What bad looks like (1-3):
- No created_at or updated_at on any table; no way to know when records were created or last modified
- Mix of soft delete and hard delete with no consistency; some queries filter deleted records, others do not
- No audit trail; changes to financial records, user permissions, or sensitive data are not tracked
- JSON columns used for data that has a known, stable structure (essentially a schema-within-a-schema that avoids migration work)
- Polymorphic foreign keys pointing to multiple tables with no constraint (type column missing or unchecked)
- Enum values stored as unconstrained strings or magic numbers with no database-level validation

### 6. Pipeline Quality

What to check:
- ETL/ELT patterns: pipelines follow a clear extract-transform-load or extract-load-transform pattern with separation of concerns between stages
- Idempotent loads: re-running a pipeline produces the same result (using UPSERT, merge patterns, or deduplication keys) rather than duplicating data
- Error handling preserves failed records: dead-letter queues, error tables, or retry mechanisms that do not lose data on failure
- Monitoring and alerting: pipeline runs are tracked (success/failure, row counts, processing time) with alerts on failure or anomalous row counts
- Incremental vs full load strategy: large datasets use incremental loads (processing only new or changed records) with periodic full reconciliation
- Schema evolution handling: pipelines handle source schema changes gracefully (new columns, changed types) without silent data loss
- Data quality checks between stages: row counts, null rates, referential integrity, and value distributions are validated between extraction and loading
- Backfill capability: pipelines can reprocess historical data without affecting current data or creating duplicates

What good looks like (8-10):
- Pipelines are idempotent: re-running produces the same result with no duplicate records
- Failed records land in a dead-letter queue or error table with enough context to diagnose and reprocess
- Pipeline monitoring tracks row counts in vs out, processing duration, and error rates; alerts fire on anomalies
- Incremental loads use watermarks (updated_at, sequence IDs) with periodic full reconciliation to catch drift
- Schema changes in sources are detected and handled (new columns added, type changes flagged)
- Data quality gates between stages: null rate thresholds, row count variance limits, referential integrity checks
- Backfill jobs can reprocess date ranges without duplicating existing data

What bad looks like (1-3):
- Pipelines are not idempotent: re-running creates duplicate records with no deduplication
- Errors cause the entire pipeline to fail with no record of which rows succeeded and which failed
- No monitoring: pipeline failures are discovered when downstream consumers report missing data
- Full table loads every run regardless of table size (millions of rows reprocessed nightly when only hundreds changed)
- Source schema changes cause silent data loss (new columns ignored, type changes cause truncation)
- No data quality checks: bad data passes through to the destination and corrupts downstream analysis
- No backfill capability: correcting historical data requires manual intervention

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
```

Refer to the data checklist at `review-data/references/checklist.md` for detailed checks within each dimension.

Reference: https://jeffbailey.us/categories/fundamentals/
