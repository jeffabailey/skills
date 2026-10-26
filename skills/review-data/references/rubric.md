# Data Review Scoring Rubric

Hand-maintained scoring rubric. sync-wisdom does not regenerate this file.

Score from this file. Use `checklist.md` for what to inspect; use `wisdom.md` only as optional background.

## Severity

| Severity | Definition | Data examples |
|----------|------------|---------------|
| CRITICAL | Data loss, corruption, or silent wrong results are likely in normal operation, or a deploy will fail or take an outage. | Migration drops or rewrites a populated column with no backfill/copy; money stored as FLOAT and summed into balances. |
| HIGH | Integrity can be violated by an ordinary race, retry, or bulk path; or a migration takes a long write lock on a table that is large in production. | Read-modify-write of a balance or counter outside a transaction / without `FOR UPDATE`; pipeline re-run inserts duplicates (no upsert or dedup key). |
| MEDIUM | A constraint or guard is missing, so bad data is possible but needs an unusual path; or a pattern will break on the next schema change. | Status column with no CHECK/enum; LEFT JOIN on a required relationship hides orphans. |
| LOW | Convention or hygiene gap with no current integrity effect. | Mixed `created_at` / `created_date` naming; migration with no comment explaining a non-obvious change. |

Severity follows the data consequence, not the effort to fix.

## Dimension anchors

Score each applicable dimension from the band whose description fits the evidence best. Within a band, pick the higher number when the strengths are broad and the gaps are isolated. One CRITICAL finding in a dimension caps that dimension at 3; one HIGH caps it at 6.

### 1. Schema Design

- **9-10**: Specific types everywhere (TIMESTAMPTZ, BOOLEAN, NUMERIC(p,s) for money, UUID); NOT NULL on required columns; FKs on every relationship with explicit ON DELETE; consistent naming.
- **7-8**: As above with 1-3 isolated gaps (one nullable-by-accident column, one missing ON DELETE).
- **5-6**: Types mostly right, but several relationships lack FKs or several required columns are nullable.
- **3-4**: Structured data in VARCHAR/TEXT (dates, numbers, enums), or FKs mostly absent.
- **1-2**: Schema-less in practice (everything TEXT/JSON) or money in FLOAT on a financial path.

### 2. Migration Safety

- **9-10**: Every migration is reversible OR the project documents a forward-only policy (ADR, README, migration guide) and follows it; NOT NULL added via add-nullable, backfill, then constrain; large-table indexes use `CONCURRENTLY` or equivalent; renames use expand-contract.
- **7-8**: Safe patterns are the norm; 1-2 migrations take avoidable locks or mix DDL and backfill on small tables.
- **5-6**: No rollback path and no documented policy, or several lock-heavy DDL statements on tables that grow with usage.
- **3-4**: A direct rename/type change that breaks running code, or a NOT NULL without default added to a populated table.
- **1-2**: A migration destroys data (DROP/ALTER TYPE losing values) with no preservation step.

A documented forward-only policy satisfies the "Reversibility" items in `checklist.md`. Credit it and cite the document; do not file "no down migrations" as a finding. Do file migrations that break the policy's own rules.

### 3. Data Integrity

- **9-10**: Business keys UNIQUE at the database level (partial/composite where needed); CHECK or enum on constrained values; multi-step writes in one transaction; check-then-act uses `FOR UPDATE`, SERIALIZABLE, or an atomic UPSERT.
- **7-8**: One or two invariants enforced only in application code, with no reachable race.
- **5-6**: Uniqueness or a multi-step write relies on application checks that a concurrent request can bypass.
- **3-4**: Several business invariants unenforced; partial writes possible on error.
- **1-2**: No constraints beyond primary keys; integrity is entirely in application code.

### 4. Query Correctness

- **9-10**: All queries parameterized or compile-time checked; JOIN types match optionality; complete GROUP BY; dynamic IN lists and LIKE input handled; read-modify-write inside a transaction.
- **7-8**: One or two queries with a semantic slip that only matters on edge data (empty list, NULL side).
- **5-6**: A query that returns wrong rows for reachable inputs (wrong JOIN type, missing soft-delete filter, ungrouped column).
- **3-4**: SQL built by string interpolation of non-constant values, or several wrong-result queries.
- **1-2**: Wrong results on the main path (e.g. lost updates on every concurrent write).

### 5. Data Modeling

- **9-10**: `created_at`/`updated_at` with DB defaults on mutable entities, tz-aware; one soft- or hard-delete strategy applied everywhere; audit or history for sensitive records; JSON only for genuinely variable data, validated.
- **7-8**: Strategy is consistent; 1-2 tables miss timestamps or audit.
- **5-6**: Mixed delete strategies, or JSON holding stable, queried fields.
- **3-4**: Soft-deleted rows leak into reads, or sensitive changes are untracked with no history.
- **1-2**: The model cannot represent required states (lost history, overloaded columns with ambiguous meaning).

### 6. Pipeline Quality

- **9-10**: Loads are idempotent (upsert/dedup key); failed records go to an error table or DLQ with context; runs record counts and status; schema drift detected.
- **7-8**: Idempotent with basic error handling; monitoring partial.
- **5-6**: Re-runs are safe only by convention; failures logged but records dropped.
- **3-4**: Re-runs duplicate data, or one bad record fails the whole batch silently.
- **1-2**: Pipeline corrupts or loses data on retry.

## Applicability (N/A)

Mark a dimension `N/A` when nothing in scope can be evaluated for it, and give the reason: e.g. Pipeline Quality N/A because there is no ETL, import, batch, or stream code. Do not give a neutral or placeholder score; it distorts the average and the review-full aggregate.

- **No data layer at all** (no schema, migrations, SQL/ORM queries, or pipelines): every dimension is N/A. Write the short "no data layer" report (see SKILL.md) and set the overall to `N/A`.
- **Partial**: a database with no ETL/batch/stream code makes Pipeline Quality N/A. A database with no migration files is not N/A for Migration Safety: score how schema changes ship (ORM auto-sync, ad hoc SQL). It is N/A only when migrations live outside the reviewed scope; say where.
- **Absence as a finding**: when something should exist but does not (a DB with no migrations, an FK-shaped column with no constraint), cite the place it should be: `migrations/ (none)`, `schema.sql:42 (user_id, no REFERENCES)`.

## Scope boundaries

- Speed only (missing index for a slow query, N+1, full scans, pool size): route to review-performance. Mention in one line; do not score it here. An index that a constraint needs (UNIQUE, FK for ON DELETE checks) is in scope.
- Non-data correctness (an off-by-one in a parser, a wrong regex, a concurrency bug outside DB access): route to review-algorithms.
- SQL injection as an attack: review-security. Here, string-built SQL counts only for wrong results or type errors.

## Overall score

- Overall = mean of the scored (non-N/A) dimensions, to one decimal. State which dimensions were averaged.
- If any CRITICAL finding exists, cap the overall at 4.0.
- If every dimension is N/A, overall is `N/A`.
- Status bands: a score at or above `statusThresholds.healthy[0]` is Healthy, at or above `statusThresholds.needsAttention[0]` is Needs Attention, anything lower is Critical (defaults 8 / 5 when the resolver gives none). Only the lower bounds count, so a fractional score such as 7.5 is Needs Attention, never a gap; review-full uses the same rule.
