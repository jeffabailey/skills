# Performance Review Rubric

Hand-maintained scoring rubric. sync-wisdom does not regenerate this file.

Use this file to assign severities and dimension scores. Use `checklist.md` for what to look for. `wisdom.md` is background prose only.

"Hot path" means code that runs per request, per record, per item, or per run of a job the user cares about (see SKILL.md step 2). "Growing input" means a collection whose size tracks users, posts, rows, files, or time rather than a fixed constant.

## Severity

| Severity | Definition | Examples |
|----------|------------|----------|
| CRITICAL | At realistic near-term scale this will fail or stall: unbounded resource growth or unbounded wait on a hot path. | A request handler that loads an entire growing table into memory with no LIMIT; a synchronous downstream HTTP call in a request path with no timeout. |
| HIGH | Cost grows faster than linearly with a growing input on a hot path, or one avoidable cost dominates total runtime. | Query per row inside a loop over a growing table (N+1) in a request handler or ranking job; recomputing every embedding or re-parsing every file on every run when only a few changed. |
| MEDIUM | Avoidable linear waste on a hot path, or superlinear cost where n is small today but will grow. | O(n^2) list-membership dedupe over paragraphs of one document; serial network fetches that could be batched or run concurrently in a CI job. |
| LOW | Minor or constant-factor inefficiency with little user-visible effect. | `SELECT *` where two columns are used on a small table; regex compiled inside a loop of fixed small size. |

A finding on cold code (setup, one-off migration, debug command) drops one severity level unless the user said that path matters.

## Dimension anchors

Score each applicable dimension 1-10. Start from the band that matches the worst confirmed finding, then move within the band by how much of the hot path is clean. Numbers refer to `checklist.md` sections.

### 1. Algorithmic Efficiency (checklist sections 1, 5)

- **9-10:** Every hot path is O(n) or O(n log n) in its growing input; lookups use hash maps or sets; collections that grow have caps.
- **7-8:** One superlinear pattern on a cold path or over a provably small, fixed-size input; otherwise as above.
- **5-6:** One O(n^2) or list-scan lookup on a hot path over input that grows, at MEDIUM severity.
- **3-4:** Several superlinear hot-path patterns, or one at HIGH severity (n reaches thousands in normal use).
- **1-2:** Exponential or O(n^3)+ on a hot path, or an unbounded recursion or traversal without a visited set.

### 2. Database Design (checklist section 2)

- **9-10:** No query inside a loop over a growing collection; filtered columns are indexed; result sets on growing tables are bounded; connections are reused.
- **7-8:** One N+1 or unindexed filter on a cold path, or over a table that stays small by design.
- **5-6:** One N+1 or missing index on a hot path at MEDIUM severity; or unbounded `fetchall()` on a table that grows.
- **3-4:** N+1 on the main hot path at HIGH severity, or several missing indexes on hot filters.
- **1-2:** Per-request full table scans or per-row connections on a growing table in a request path.

### 3. Caching Strategy (checklist section 3)

- **9-10:** Repeated expensive work (queries, HTTP calls, model inference) with identical inputs is cached or memoized; caches are bounded and have an invalidation rule.
- **7-8:** Minor repeats on cold paths; or caches exist but one lacks a size bound or TTL with low risk.
- **5-6:** One expensive repeated operation on a hot path recomputed every time, or an unbounded cache in a long-running process.
- **3-4:** The dominant cost of the hot path is repeated identical work, or a cache keyed by user-controlled values grows without bound.
- **1-2:** Cache correctness is broken in a way that serves wrong data, or cache stampede on a hot key can take down the backend.

### 4. Scalability Readiness (checklist section 4)

- **9-10:** Work grows linearly with input; independent I/O runs concurrently or in batches; services are stateless; backpressure or rate limits exist where input is unbounded.
- **7-8:** Serial independent I/O that is bounded and small (tens of calls); minor in-process state with a documented reason.
- **5-6:** Serial I/O or single-threaded processing that grows with input on a hot path; in-process state that blocks running a second instance.
- **3-4:** A global lock, single queue consumer, or shared mutable state that caps throughput at one worker.
- **1-2:** Design cannot scale past one instance or one input size without a rewrite.

### 5. Resource Utilization (checklist section 6)

- **9-10:** Every external call has a timeout; large inputs are streamed; pools are reused; models and clients are loaded once per process; inference is batched.
- **7-8:** One missing timeout or full buffering on a cold path or bounded input.
- **5-6:** Missing timeout on a hot-path external call, a growing input loaded fully into memory, or per-item model/client construction or unbatched inference calls.
- **3-4:** Several of the above on the main hot path, or a resource (connection, file handle, thread) leaked per iteration.
- **1-2:** Unbounded memory growth or resource leak in a long-running process.

### 6. Data Pipeline Efficiency (checklist section 7)

- **9-10:** Batch or streaming jobs process incrementally (only changed inputs), stages are idempotent, bad records are isolated, writes are skipped when content is unchanged.
- **7-8:** Full reprocessing where the full set is small and fixed; otherwise as above.
- **5-6:** Full reprocessing of a growing input on every run, or one bad record aborts the whole run.
- **3-4:** Full reprocessing that dominates runtime and is not idempotent, so retries duplicate work or output.
- **1-2:** Pipeline cannot complete at current input size, or reruns corrupt previous output.

## Where a finding belongs

- Query per item in a loop: Database Design. Loop over items calling a remote API per item: Scalability Readiness.
- Recomputing the same model output or query result for identical inputs: Caching Strategy.
- Reprocessing every input when only some changed (re-embedding all posts, re-fetching all sources): Data Pipeline Efficiency.
- Per-item inference calls instead of batches, model loaded per call, missing timeouts: Resource Utilization.

File each finding under one dimension. If it touches two, file it where the fix lives and mention it in the other dimension's narrative without double-scoring it.

## N/A

Mark a dimension `N/A` when the target has nothing for it to evaluate, for example Database Design for code with no database access, Data Pipeline Efficiency for code that runs no batch or streaming job, or Caching Strategy for a one-shot script that never repeats work. Give the reason and cite where the thing would be: `N/A: no DB access (grep for sqlite3|psycopg|sqlalchemy|execute in .github/scripts/: none)`.

N/A is for absence of the concern, not absence of a problem. If the code repeats expensive work and has no cache, Caching Strategy applies and scores low.

## Overall score

- Overall = mean of the scored (non-N/A) dimensions, rounded to one decimal. State which dimensions were averaged.
- If any CRITICAL finding exists, cap the overall at 4.0.
- Status bands: a score at or above `statusThresholds.healthy[0]` is Healthy, at or above `statusThresholds.needsAttention[0]` is Needs Attention, anything lower is Critical (defaults 8 / 5 when the resolver gives none). Only the lower bounds count, so a fractional score such as 7.5 is Needs Attention, never a gap; review-full uses the same rule.
