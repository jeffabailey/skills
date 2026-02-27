---
name: review-performance
description: Analyzes code for performance and scalability issues, producing fitness scores (1-10) across algorithmic efficiency, database design, caching strategy, scalability readiness, resource utilization, and data pipeline efficiency. Use when the user says /review:performance, requests a performance review, asks for scalability analysis, wants to find N+1 queries or Big-O hot paths, or needs performance fitness scores before shipping. Only reports findings with confidence >= 7/10.
---

# Performance and Scalability Fitness Review

Analyze the codebase (or specified files/modules) for performance and scalability fitness. Identify hot paths, inefficient patterns, and scaling bottlenecks using evidence from the code.

## Workflow

1. **Identify hot paths** -- Use Grep/Glob to find request handlers, API endpoints, background jobs, and data processing pipelines. These are the entry points where performance matters most.

2. **Trace data flow** -- For each hot path, trace how data moves: what gets queried, what gets cached, what gets computed. Map the critical path from request to response.

3. **Analyze algorithmic complexity** -- Look for nested loops, repeated scans, unbounded collections, and O(n^2) patterns on hot paths. Check that data structures match access patterns (hash maps for lookups, sorted structures for range queries, bounded collections for caches).

4. **Audit database interactions** -- Find N+1 query patterns (queries inside loops), missing indexes on filtered/joined columns, full table scans, missing connection pooling, and unbounded result sets.

5. **Evaluate caching** -- Check for missing caches on repeated expensive work, improper invalidation, missing TTLs, cache stampede risk (hot key expiry without coalescing), unbounded cache growth, and cache penetration from high-cardinality keys.

6. **Assess scalability readiness** -- Look for in-process state that prevents horizontal scaling, shared bottlenecks (single database, single queue), synchronous calls that could be async, and missing backpressure or rate limiting.

7. **Check resource utilization** -- Identify unbounded memory growth (collections without limits, missing eviction), connection/thread pool sizing, large payload serialization on hot paths, and missing timeouts on external calls.

8. **Review data pipeline efficiency** -- For batch or streaming pipelines, check processing patterns (full reload vs incremental/CDC), schema validation placement, error handling that stops entire pipelines, and monitoring gaps.

9. **Score each dimension** with specific file:line evidence.

10. **Produce the report** with scores, evidence, and prioritized action items.

## Confidence and Severity

### Confidence Threshold

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

### Severity Levels

- **CRITICAL** -- Performance issue causing outages or severe degradation under normal load. N+1 queries on high-traffic endpoints, unbounded memory growth causing OOM in production, O(n^2) on hot paths with large datasets.
- **HIGH** -- Significant performance degradation under realistic conditions. Missing database indexes on frequently queried columns, no caching on expensive repeated operations, synchronous blocking calls on critical paths.
- **MEDIUM** -- Performance concern under specific conditions or at scale. Suboptimal algorithm choice that works at current scale, missing connection pool tuning, cache stampede risk on hot keys.
- **LOW** -- Optimization opportunities. Better data structure selection, additional caching layers, query optimization for non-critical paths.

## Scoring Dimensions (1-10 each)

Evaluate and score each dimension with evidence from the code.

### 1. Algorithmic Efficiency

What to check:
- Big-O complexity of hot paths (request handlers, loops over data)
- Nested loops that create O(n^2) or worse behavior
- Linear scans where hash lookups or indexed searches would work
- Unbounded collections that grow with input size
- Data structures that mismatch their access patterns (e.g., lists used for lookups, hash maps used for ordered iteration)

What good looks like (8-10):
- Hot paths are O(n) or better
- Data structures match access patterns (hash maps for lookups, trees for ordered data)
- Collections have explicit size limits or eviction policies
- No nested loops over growing datasets on critical paths

What bad looks like (1-3):
- Nested loops over unbounded data on hot paths (O(n^2) or worse)
- Linear scans for lookups that should be hash-based
- Collections that grow without bounds in long-running processes
- Sorting or searching repeated inside loops instead of precomputing

### 2. Database Design

What to check:
- N+1 query patterns (database queries inside loops)
- Missing indexes on columns used in WHERE, JOIN, and ORDER BY
- SELECT * instead of specific columns on large tables
- Missing connection pooling
- Unbounded query results (no LIMIT)
- Full table scans on large tables
- Missing EXPLAIN plan analysis for complex queries
- Denormalization decisions and their trade-offs

What good looks like (8-10):
- Queries use indexes; EXPLAIN plans show index scans
- Batch fetching replaces per-item queries
- Connection pools are sized and monitored
- Result sets are bounded with pagination or LIMIT
- Query patterns match the data model

What bad looks like (1-3):
- Queries inside for-loops (N+1 pattern)
- No indexes on frequently filtered columns
- Unbounded SELECT * on tables that grow
- No connection pooling; connections created per request
- Cross-shard or cross-partition queries on hot paths

### 3. Caching Strategy

What to check:
- Whether expensive repeated work is cached
- TTL settings and whether they match data freshness requirements
- Cache invalidation strategy (TTL, explicit, versioned keys)
- Stampede protection for hot keys (request coalescing, jittered TTLs)
- Unbounded cache growth (missing eviction policies, no size limits)
- Cache penetration risk (high-cardinality or nonexistent keys bypassing cache)
- Negative caching for "not found" results
- Cache observability (hit rate, miss latency, eviction counts)

What good looks like (8-10):
- High-frequency reads are cached with appropriate TTLs
- Cache has bounded size with eviction policy (LRU or similar)
- Hot keys have stampede protection (single-flight or jittered expiry)
- Cache hit/miss rates are instrumented
- Invalidation strategy matches write patterns

What bad looks like (1-3):
- No caching on repeated expensive operations
- Unbounded in-memory caches that grow until OOM
- All keys expire at the same TTL causing synchronized misses
- No observability on cache behavior
- Cache treated as source of truth with no fallback

### 4. Scalability Readiness

What to check:
- In-memory session state or local file storage that prevents horizontal scaling
- Stateless vs stateful service design
- Database as a shared bottleneck (single writer, no read replicas, no sharding plan)
- Synchronous blocking calls to downstream services
- Missing backpressure, rate limiting, or circuit breakers
- Single points of contention (global locks, single queues, hot partitions)
- Ability to add instances behind a load balancer

What good looks like (8-10):
- Services are stateless; state is externalized to databases or caches
- Downstream calls have timeouts, retries with backoff, and circuit breakers
- Database can scale reads (replicas) and writes (partitioning) independently
- Work can be distributed across instances without coordination overhead
- Async processing for non-critical-path work

What bad looks like (1-3):
- Session state stored in server memory
- No timeouts on external service calls
- Single database instance with no replication or scaling plan
- Synchronous fan-out to many services on the critical path
- Global locks or single-threaded bottlenecks

### 5. Resource Utilization

What to check:
- Memory: unbounded collections, large object retention, missing eviction
- CPU: tight loops, busy-waiting, unthrottled background work
- Connections: pool sizing, leak detection, proper cleanup
- Serialization: large payloads on hot paths, unnecessary marshalling
- Timeouts: missing or overly generous timeouts on I/O operations
- Thread/goroutine leaks in long-running services

What good looks like (8-10):
- Collections have capacity limits and eviction
- Connection pools are sized based on downstream capacity
- All external calls have bounded timeouts
- Large payloads are paginated or streamed
- Background work is throttled and observable

What bad looks like (1-3):
- Hash maps or lists that grow without limit
- No timeouts on database or HTTP calls
- Connection pools with no max size
- Large responses serialized fully into memory
- No monitoring of memory, connection, or thread usage

### 6. Data Pipeline Efficiency

What to check:
- Full reload vs incremental processing (CDC, timestamps)
- Validation placement (early in pipeline vs late)
- Error handling (fail entire pipeline vs dead-letter problematic records)
- Monitoring and alerting on pipeline health
- Idempotency of pipeline stages
- Schema drift handling
- Data quality checks at pipeline boundaries

What good looks like (8-10):
- Incremental processing where possible (CDC, watermarks)
- Validation at extraction and transformation boundaries
- Failed records handled individually without stopping the pipeline
- Pipeline stages are idempotent and retryable
- Schema changes detected and handled gracefully

What bad looks like (1-3):
- Full table reloads on every run for large datasets
- No validation; bad data propagates to downstream consumers
- Single failure stops entire pipeline
- No monitoring; failures discovered when users complain
- No schema evolution strategy

## Output Format

Write the report to `docs/performance-review.md` with this structure:

```markdown
# Performance and Scalability Review

## Summary

Overall fitness score: X.X / 10 (average of dimensions)

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Algorithmic Efficiency | X/10 | ... |
| Database Design | X/10 | ... |
| Caching Strategy | X/10 | ... |
| Scalability Readiness | X/10 | ... |
| Resource Utilization | X/10 | ... |
| Data Pipeline Efficiency | X/10 | ... |

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line
- **Description:** What the issue is and why it matters.
- **Evidence:** The specific code pattern found.
- **Impact:** What could go wrong in production.
- **Remediation:** Concrete fix with code example or specific steps.

(repeat for each finding, ordered by severity)

### Algorithmic Efficiency (X/10)
- Evidence: file:line references
- Issues found
- Recommendations

(repeat for each dimension)

## Top 5 Action Items (by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...

## Checklist Reference

See references/checklist.md for the full performance checklist.

## Reference

Based on guidance from https://jeffbailey.us/categories/fundamentals/
```

Refer to the performance checklist at `review-performance/references/checklist.md` for detailed checks within each dimension.
