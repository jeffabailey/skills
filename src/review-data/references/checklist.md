# Data Fitness Checklist

Detailed checklist for reviewing code, schema definitions, migration files, and data pipeline code against data fundamentals. Use alongside the review-data skill to systematically evaluate each dimension.

---

## 1. Schema Design

### Column Types
- [ ] **Appropriate column types** -- Timestamps use TIMESTAMP or TIMESTAMP WITH TIME ZONE, not VARCHAR. Booleans use BOOLEAN, not INTEGER or CHAR(1). Counts and quantities use INTEGER or BIGINT, not VARCHAR. UUIDs use a UUID type where the database supports it, not CHAR(36).
- [ ] **No generic varchar for everything** -- Columns storing structured data (dates, numbers, booleans, enums) use the correct database type. VARCHAR(255) as a default type for all columns is a sign of schema avoidance.
- [ ] **String length constraints** -- VARCHAR columns have a length limit appropriate for the data (email max 254, country code 2-3, phone number 15). Unbounded TEXT is used only where variable-length content is genuinely needed (descriptions, comments, body text).
- [ ] **Decimal precision for money** -- Financial values use DECIMAL/NUMERIC with explicit precision and scale (e.g., DECIMAL(10,2)), not FLOAT or DOUBLE which introduce rounding errors.

### Constraints
- [ ] **NOT NULL on required fields** -- Columns that must always have a value are NOT NULL. Nullable columns represent genuinely optional data, not missing design decisions.
- [ ] **CHECK constraints for valid ranges** -- Prices are positive (CHECK price > 0). Status values are constrained (CHECK status IN ('draft','active','archived')). Dates are in valid ranges. Percentages are between 0 and 100.
- [ ] **UNIQUE constraints for business keys** -- Email addresses, usernames, external identifiers, and natural keys have UNIQUE constraints. Application-level uniqueness checks alone are race-condition prone.
- [ ] **DEFAULT values where appropriate** -- Timestamps default to CURRENT_TIMESTAMP. Boolean flags default to false. Status columns default to an initial state. Defaults reduce the chance of null insertion errors.

### Relationships
- [ ] **Foreign keys defined** -- Every relationship between tables has a foreign key constraint, not just a column with a matching name. Foreign keys prevent orphaned records and document the data model.
- [ ] **ON DELETE behavior specified** -- Foreign keys specify ON DELETE RESTRICT, CASCADE, or SET NULL based on the business rule. Missing ON DELETE behavior uses the database default (usually RESTRICT), which should be intentional.
- [ ] **Join tables for many-to-many** -- Many-to-many relationships use a join table with foreign keys to both sides and a composite primary key or unique constraint on the pair.
- [ ] **No circular foreign keys without careful design** -- Circular references between tables (A references B, B references A) are rare and require deferred constraints or nullable FKs with documented justification.

### Naming and Organization
- [ ] **Consistent naming convention** -- All tables use the same convention (snake_case preferred). Table names are either all plural or all singular. Column names follow a pattern (user_id, not userId or UserID mixed with user_email).
- [ ] **ID column convention** -- Primary key columns follow a consistent pattern (id, or table_name_id). Foreign key columns match the referenced table (user_id references users.id).
- [ ] **Timestamp column convention** -- Created and modified timestamps use consistent names (created_at/updated_at, not created_date/modified_on/last_update mixed).
- [ ] **No reserved word conflicts** -- Table and column names do not conflict with SQL reserved words (user, order, group, select, table). If they do, they are consistently quoted.

### Indexes
- [ ] **Indexes on foreign keys** -- Every foreign key column has an index. Without indexes, JOIN operations on foreign keys perform full table scans.
- [ ] **Indexes on filtered columns** -- Columns frequently used in WHERE clauses have indexes. Check query patterns against existing indexes.
- [ ] **Composite indexes for multi-column queries** -- Queries that filter on multiple columns (WHERE status = 'active' AND created_at > ?) benefit from composite indexes with column order matching the query pattern.
- [ ] **No redundant indexes** -- An index on (a, b) makes a separate index on (a) alone redundant. Redundant indexes waste storage and slow writes.

Source: [Fundamentals of Databases](https://jeffbailey.us/blog/2025/09/24/fundamentals-of-databases/)

---

## 2. Migration Safety

### Reversibility
- [ ] **Up and down methods** -- Every migration includes both an up (apply) and down (rollback) method. Down methods are the inverse of up methods and are tested.
- [ ] **Rollback tested** -- Migration rollbacks are tested in a non-production environment before deploying. A rollback that fails is worse than no rollback at all.
- [ ] **Data preservation on rollback** -- Rolling back a migration that added a column does not lose data in that column if it has been populated. Consider whether rollback scenarios need data migration.

### Zero-Downtime Patterns
- [ ] **Add column, then constraint** -- Adding a NOT NULL column is a multi-step process: (1) add nullable column, (2) backfill data, (3) add NOT NULL constraint. Adding NOT NULL without a default in one step fails on tables with existing rows or locks the table.
- [ ] **Expand-contract for renames** -- Renaming a column or table uses expand-contract: (1) add new column, (2) dual-write to both, (3) migrate reads to new column, (4) drop old column. A direct rename breaks running application code.
- [ ] **Non-blocking index creation** -- Creating indexes on large tables uses CONCURRENTLY (PostgreSQL) or equivalent non-blocking DDL. A standard CREATE INDEX locks the table for writes.
- [ ] **No rewriting ALTER on large tables under load** -- Operations that rewrite the table (changing column type, adding a column with a non-null default in some databases) are avoided on large tables during peak traffic. Use online schema change tools (pt-online-schema-change, gh-ost) when needed.

### Migration Hygiene
- [ ] **One concern per migration** -- Each migration file addresses one change (add a table, add a column, add an index). Mixing schema changes, data backfills, and constraint additions in one migration makes rollback difficult.
- [ ] **Migration order dependencies** -- Migrations that depend on each other are ordered correctly. A migration that adds a foreign key must run after the migration that creates the referenced table.
- [ ] **No DDL and DML in the same transaction** -- Some databases (MySQL) implicitly commit DDL statements. Mixing DDL and DML in a transaction produces unexpected commit behavior. Separate schema changes from data changes.
- [ ] **Idempotent migrations** -- Migrations use IF NOT EXISTS / IF EXISTS guards where possible so re-running does not fail if the object already exists or has already been dropped.
- [ ] **Migration comments** -- Migration files include comments explaining the purpose of the change, especially for non-obvious operations (why a column is being added, what business requirement drives the change).

### Data Migrations
- [ ] **Separate from schema migrations** -- Data backfills and data transformations are in separate migration files from schema changes. This allows schema and data to be rolled back independently.
- [ ] **Batched for large tables** -- Data migrations on large tables process rows in batches (e.g., 1000 at a time) to avoid long-running transactions and lock contention.
- [ ] **Verified after running** -- Data migrations include verification steps: row counts match, values are in expected ranges, no nulls where values should exist.

Source: [Fundamentals of Databases](https://jeffbailey.us/blog/2025/09/24/fundamentals-of-databases/)

---

## 3. Data Integrity

### Referential Integrity
- [ ] **Foreign keys on all relationships** -- Every column that references another table has a foreign key constraint. Application-level checks alone allow orphaned records through race conditions, bulk imports, and manual database operations.
- [ ] **Cascading behavior intentional** -- ON DELETE CASCADE is used only where child records should genuinely be deleted with the parent (e.g., order line items when an order is deleted). ON DELETE RESTRICT prevents accidental deletion of parents with active children.
- [ ] **No orphaned records** -- Run queries to check for records where a foreign key column references a non-existent parent. Orphaned records indicate missing constraints or past constraint violations.

### Uniqueness
- [ ] **Unique constraints on business keys** -- Email, username, external_id, and composite natural keys have database-level UNIQUE constraints. Application-level uniqueness checks without database constraints are vulnerable to race conditions.
- [ ] **Composite unique constraints** -- Where uniqueness spans multiple columns (one vote per user per poll, one membership per user per organization), a composite UNIQUE constraint enforces it.
- [ ] **Unique partial indexes** -- Where uniqueness applies only to active records (unique email among non-deleted users), use a partial/filtered unique index.

### Transactions
- [ ] **Atomic business operations** -- Multi-step business operations (create order + create line items + decrement inventory) are wrapped in a single transaction. Partial completion leaves inconsistent state.
- [ ] **Transaction scope not too wide** -- Transactions do not span external HTTP calls, user input waits, or long-running computations. Wide transactions hold locks that block other operations.
- [ ] **Transaction scope not too narrow** -- Operations that must be atomic are not split into separate transactions. Check-then-act patterns (read balance, then update balance) without a transaction allow interleaving.
- [ ] **Explicit isolation levels for critical operations** -- Financial operations, inventory management, and other operations where phantom reads or non-repeatable reads cause bugs use SERIALIZABLE or REPEATABLE READ isolation. The default READ COMMITTED is insufficient for these cases.
- [ ] **Deadlock handling** -- Code that operates on multiple tables in transactions handles deadlocks (retry on deadlock error) and acquires locks in a consistent order across the codebase.

### Domain Constraints
- [ ] **CHECK constraints for value ranges** -- Prices, quantities, and percentages have CHECK constraints (price > 0, quantity >= 0, percentage BETWEEN 0 AND 100). Invalid values are rejected at the database level.
- [ ] **Enum constraints** -- Status columns and type columns are constrained to valid values using CHECK constraints, database ENUM types, or a foreign key to a reference table.
- [ ] **Date and time constraints** -- End dates are after start dates (CHECK end_date > start_date). Dates are in valid ranges. Timestamps use timezone-aware types for data that crosses time zones.

Source: [Fundamentals of Databases](https://jeffbailey.us/blog/2025/09/24/fundamentals-of-databases/)

---

## 4. Query Correctness

### JOIN Usage
- [ ] **INNER JOIN for required relationships** -- When both sides of the join must exist (an order must have a customer), use INNER JOIN. LEFT JOIN here would mask data integrity problems by returning rows with NULL customer data instead of surfacing the missing relationship.
- [ ] **LEFT JOIN only when nulls are valid** -- LEFT JOIN is correct when the right side is genuinely optional (a user may or may not have a profile picture). If LEFT JOIN results always produce nulls on the right side, it may indicate a data integrity issue rather than a valid absence.
- [ ] **No accidental cross joins** -- Queries with multiple FROM tables and no JOIN condition or WHERE clause matching produce a cartesian product. Verify that every multi-table query has an explicit join condition.
- [ ] **JOIN conditions on indexed columns** -- Join conditions reference indexed columns. Joining on non-indexed columns causes full table scans on the joined table.

### Aggregation
- [ ] **Complete GROUP BY** -- Every non-aggregated column in the SELECT list appears in the GROUP BY clause. Databases that allow partial GROUP BY (MySQL in some modes) produce non-deterministic results for the ungrouped columns.
- [ ] **HAVING for aggregate filters** -- Filters on aggregated values use HAVING, not WHERE. WHERE filters rows before aggregation; HAVING filters groups after aggregation.
- [ ] **COUNT with correct arguments** -- COUNT(*) counts all rows including nulls. COUNT(column) counts non-null values. COUNT(DISTINCT column) counts unique non-null values. Using the wrong variant produces incorrect results.
- [ ] **Window functions partitioned correctly** -- PARTITION BY and ORDER BY in window functions match the analytical intent. A ROW_NUMBER() without the correct PARTITION BY assigns numbers globally instead of per group.

### Parameterization and Type Safety
- [ ] **Parameterized queries everywhere** -- All user input reaches the database through parameterized queries or ORM parameter binding. String interpolation in SQL is a correctness risk (truncation, type mismatch) in addition to a security risk.
- [ ] **No implicit type coercion** -- Columns are compared to values of matching types. Comparing a VARCHAR column to an INTEGER forces implicit casting that can prevent index usage and produce unexpected results.
- [ ] **Dynamic IN clauses handled correctly** -- IN clauses with dynamic lists use parameterized arrays or generated parameter placeholders, not string-joined values. Empty IN clauses are handled (IN () is a syntax error in most databases).
- [ ] **LIKE patterns escaped** -- User input in LIKE patterns escapes wildcard characters (% and _) to prevent unintended matching.

### Transaction Scoping in Queries
- [ ] **Read-modify-write in transactions** -- Patterns that read a value, modify it, and write it back (check balance, subtract, update) are in a transaction with appropriate isolation to prevent lost updates.
- [ ] **SELECT FOR UPDATE where needed** -- When a read is followed by a conditional write (reserve inventory if available), SELECT FOR UPDATE prevents concurrent readers from acting on the same row.
- [ ] **No long-running read transactions holding locks** -- Reporting or analytics queries that scan large amounts of data use READ COMMITTED or run against a read replica to avoid blocking writers.

Source: [Fundamentals of Databases](https://jeffbailey.us/blog/2025/09/24/fundamentals-of-databases/)

---

## 5. Data Modeling

### Temporal Data
- [ ] **created_at on all entities** -- Every table has a created_at column with a database DEFAULT (CURRENT_TIMESTAMP or equivalent). The application should not need to set this manually.
- [ ] **updated_at on mutable entities** -- Tables whose rows are updated have an updated_at column populated by a database trigger or application-level before-save hook. This enables change detection for incremental processing and debugging.
- [ ] **Timezone-aware timestamps** -- Timestamps use TIMESTAMP WITH TIME ZONE (or store in UTC with documented convention). TIMESTAMP WITHOUT TIME ZONE is ambiguous when the application and database are in different time zones.
- [ ] **Effective dating for temporal records** -- Records with time-bound validity (prices, subscriptions, permissions) use valid_from/valid_to columns with appropriate constraints (valid_to > valid_from or valid_to IS NULL for open-ended).

### Soft Deletes and Hard Deletes
- [ ] **Consistent strategy** -- The codebase uses one strategy consistently. If soft deletes (deleted_at column), all queries filter on deleted_at IS NULL by default (via default scope or query builder). If hard deletes, foreign key cascades handle child records.
- [ ] **Soft delete filtering in all queries** -- Every query that should exclude deleted records has the filter. Missing the filter in one query path returns deleted data to users. Default scopes or query middleware help enforce this.
- [ ] **Unique constraints with soft deletes** -- Unique constraints account for soft-deleted records. A unique index on (email) prevents re-registration with the same email after soft delete. A partial unique index on (email) WHERE deleted_at IS NULL allows it.
- [ ] **Soft-deleted record cleanup** -- A process exists to permanently delete soft-deleted records after a retention period. Without cleanup, soft deletes accumulate indefinitely and degrade query performance.

### Audit Trails
- [ ] **Audit on sensitive entities** -- Changes to financial records, user permissions, account settings, and compliance-relevant data are tracked in an audit log with who, what, when, and previous value.
- [ ] **Immutable audit records** -- Audit log records are insert-only. No UPDATE or DELETE on the audit table. If using database triggers, verify the trigger does not allow modification.
- [ ] **Audit log includes actor** -- Every audit entry records who performed the action (user ID, system process, API key). Anonymous changes are not auditable.
- [ ] **Audit log queryable** -- Audit logs are structured and queryable (not just appended to a text file). Analysts and compliance teams can answer "who changed this record and when?"

### Polymorphism and Flexibility
- [ ] **Polymorphic associations use type discriminators** -- If a single table stores multiple entity types (single-table inheritance), a type column with a CHECK constraint or ENUM distinguishes them. Polymorphic foreign keys (commentable_type + commentable_id) have documented limitations and no database-level referential integrity.
- [ ] **JSON columns for genuinely variable data** -- JSON columns store data that genuinely varies per record (user preferences, plugin configuration, API response caching). Data with a known, stable structure belongs in typed columns.
- [ ] **JSON columns validated** -- JSON data has application-level or database-level schema validation. Unconstrained JSON columns accumulate inconsistent structures over time.
- [ ] **Graph-like relationships modeled appropriately** -- Tree structures use a proven pattern: adjacency list (simple, recursive queries), materialized path (fast reads, complex writes), closure table (fast reads and writes, more storage), or nested sets. Ad-hoc parent_id columns without supporting structures make tree queries difficult.

### Versioning and History
- [ ] **Version tracking for mutable records** -- Important records that change over time have a versioning strategy: version counter, history table, or event-sourced changelog. Without versioning, the previous state is lost on update.
- [ ] **History table structure** -- If using a history table, it mirrors the main table schema plus valid_from/valid_to timestamps and optionally the actor who made the change. Inserts to the history table happen via trigger or application hook.

Source: [Fundamentals of Databases](https://jeffbailey.us/blog/2025/09/24/fundamentals-of-databases/), [Fundamentals of Graph Databases](https://jeffbailey.us/blog/2026/02/14/fundamentals-of-graph-databases/)

---

## 6. Pipeline Quality

### Idempotency
- [ ] **Re-runnable without duplicates** -- Pipelines use UPSERT (INSERT ON CONFLICT UPDATE), MERGE, or deduplication keys so that re-running produces the same result. A pipeline that creates duplicates on re-run is not safe to retry.
- [ ] **Deduplication keys** -- Each record has a natural key or generated deduplication key that uniquely identifies it. The pipeline uses this key to detect and skip already-processed records.
- [ ] **Idempotent transformations** -- Transformations produce the same output for the same input regardless of how many times they run. Side-effecting transformations (sending emails, calling APIs) are guarded against re-execution.

### Error Handling
- [ ] **Dead-letter queue for unprocessable records** -- Records that fail processing are routed to a dead-letter queue or error table with the original data, error message, and timestamp. Failed records are not silently dropped.
- [ ] **Partial failure handling** -- A batch of 1000 records where 5 fail does not cause the entire batch to fail. The 995 good records are processed; the 5 failures land in the error queue.
- [ ] **Retry with backoff** -- Transient failures (network timeout, temporary unavailability) are retried with exponential backoff. Permanent failures (invalid data format) are not retried endlessly.
- [ ] **Error context preserved** -- Error records include enough context to diagnose and reprocess: the original data, the transformation stage that failed, the error message, and a timestamp.

### Monitoring and Alerting
- [ ] **Pipeline run tracking** -- Each pipeline run is tracked with start time, end time, status (success/failure), rows processed, and rows errored.
- [ ] **Row count monitoring** -- Row counts in vs out are tracked per stage. A sudden drop in row count (source had 10000 rows yesterday, 100 today) triggers an alert.
- [ ] **Processing duration monitoring** -- Pipeline duration is tracked and alerted on. A pipeline that normally takes 5 minutes but suddenly takes 2 hours indicates a problem.
- [ ] **Data freshness monitoring** -- The age of the most recent record in the destination is tracked. If data stops flowing (no new records in 24 hours when hourly is expected), an alert fires.
- [ ] **Error rate alerting** -- The error rate (failed records / total records) is tracked per run. A spike in error rate triggers an alert before downstream consumers are affected.

### Load Strategy
- [ ] **Incremental loads for large datasets** -- Pipelines processing large tables use incremental loads based on a watermark column (updated_at, sequence_id, or CDC) rather than full table scans every run.
- [ ] **Full reconciliation periodically** -- Incremental pipelines periodically run a full reconciliation to catch records missed by the incremental logic (late-arriving data, updated_at not set correctly).
- [ ] **Backfill capability** -- Pipelines can reprocess a historical date range without affecting current data or creating duplicates. Backfill jobs are parameterized by date range or record range.
- [ ] **Upsert loading** -- Loading uses upsert (insert or update) patterns so that re-delivered records update rather than duplicate. The upsert key matches the business key or deduplication key.

### Schema Evolution
- [ ] **New column handling** -- Pipelines handle new columns in the source gracefully: ignoring unknown columns, or adding them to the destination automatically, rather than failing on unexpected schema.
- [ ] **Type change detection** -- Changes in column types (string to integer, date format change) are detected and flagged rather than silently truncating or coercing data.
- [ ] **Schema drift monitoring** -- Source schemas are periodically compared against expected schemas. Drift is logged and alerted on before it causes pipeline failures.
- [ ] **Backward-compatible destination schema** -- Destination schema changes (adding columns, changing types) are backward-compatible with running pipeline versions. A pipeline that was deployed yesterday should not break because a destination column was added today.

### Data Quality Between Stages
- [ ] **Null rate checks** -- The null rate of key columns is measured between stages. A column that is normally 2% null jumping to 50% null indicates an extraction or transformation problem.
- [ ] **Referential integrity checks** -- Foreign key relationships are validated between pipeline stages (all order.customer_id values exist in the customers table at the destination).
- [ ] **Row count variance checks** -- The difference between source row count and destination row count is within an expected threshold. Large variances trigger alerts.
- [ ] **Value distribution checks** -- Key categorical columns (status, type, country) have expected value distributions. A new unexpected value or a missing expected value triggers a warning.
- [ ] **Freshness checks** -- The maximum timestamp in loaded data is recent (within expected SLA). Stale maximum timestamps indicate the pipeline is loading old data or skipping recent records.

Source: [Fundamentals of Data Engineering](https://jeffbailey.us/blog/2025/11/22/fundamentals-of-data-engineering/)

---

## Quick Reference: The Five Most Common Data Problems in Code

1. **No foreign keys** -- Relationships exist only in application code. Orphaned records accumulate silently. Fix: add foreign key constraints with explicit ON DELETE behavior.
2. **Everything is VARCHAR(255)** -- Column types do not match the data. Invalid values are not rejected by the database. Fix: use the most specific type (TIMESTAMP, BOOLEAN, INTEGER, DECIMAL, UUID) and add CHECK constraints.
3. **Migrations without rollback** -- Schema changes cannot be reversed. A bad migration requires a manual fix under pressure. Fix: every migration has a tested down/rollback method.
4. **Non-idempotent pipelines** -- Re-running a data load creates duplicate records. Fix: use UPSERT or deduplication keys and verify idempotency in tests.
5. **No audit trail on sensitive data** -- Changes to financial records, permissions, or user data are not tracked. Fix: add an audit log table with who, what, when, and previous value.

---

## Source Articles

- [Fundamentals of Databases](https://jeffbailey.us/blog/2025/09/24/fundamentals-of-databases/)
- [Fundamentals of Data Engineering](https://jeffbailey.us/blog/2025/11/22/fundamentals-of-data-engineering/)
- [Fundamentals of Graph Databases](https://jeffbailey.us/blog/2026/02/14/fundamentals-of-graph-databases/)
