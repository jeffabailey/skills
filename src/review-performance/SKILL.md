---
name: review-performance
description: Analyzes code for performance and scalability issues, producing fitness scores (1-10) across algorithmic efficiency, database design, caching strategy, scalability readiness, resource utilization, and data pipeline efficiency. Use when the user says /review:performance, requests a performance review, asks for scalability analysis, wants to find N+1 queries or Big-O hot paths, or needs performance fitness scores before shipping. Only reports findings with confidence >= 7/10.
---

# Performance and Scalability Fitness Review

Analyze the codebase (or specified files/modules) for performance and scalability fitness. Identify hot paths, inefficient patterns, and scaling bottlenecks using evidence from the code.

Reference: [Fundamentals of Software Performance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-performance/), [Fundamentals of Software Scalability](https://jeffbailey.us/blog/2025/12/22/fundamentals-of-software-scalability/), [Fundamentals of Software Caching](https://jeffbailey.us/blog/2025/12/24/fundamentals-of-software-caching/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

For detailed scoring rubrics, severity definitions, what-good-looks-like / what-bad-looks-like criteria, and domain expertise, read `references/wisdom.md` before scoring. That file is auto-generated from:

- [Fundamentals of Software Performance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-performance/)
- [Fundamentals of Software Scalability](https://jeffbailey.us/blog/2025/12/22/fundamentals-of-software-scalability/)
- [Fundamentals of Software Caching](https://jeffbailey.us/blog/2025/12/24/fundamentals-of-software-caching/)

Use the wisdom reference when evaluating code and assigning dimension scores.

## Workflow

1. **Read domain knowledge** — Read `references/wisdom.md` to load scoring rubrics, thresholds, and severity definitions.

2. **Identify hot paths** — Use Grep/Glob to find request handlers, API endpoints, background jobs, and data processing pipelines. These are the entry points where performance matters most.

3. **Trace data flow** — For each hot path, trace how data moves: what gets queried, what gets cached, what gets computed. Map the critical path from request to response.

4. **Analyze algorithmic complexity** — Look for nested loops, repeated scans, unbounded collections, and O(n^2) patterns on hot paths. Apply the rubrics/thresholds from the wisdom reference.

5. **Audit database interactions** — Find N+1 query patterns, missing indexes, full table scans, missing connection pooling, and unbounded result sets. Apply the rubrics/thresholds from the wisdom reference.

6. **Evaluate caching** — Check for missing caches on repeated expensive work, improper invalidation, stampede risk, and unbounded cache growth. Apply the rubrics/thresholds from the wisdom reference.

7. **Assess scalability readiness** — Look for in-process state that prevents horizontal scaling, shared bottlenecks, synchronous calls that could be async, and missing backpressure or rate limiting. Apply the rubrics/thresholds from the wisdom reference.

8. **Check resource utilization** — Identify unbounded memory growth, connection/thread pool sizing issues, large payload serialization on hot paths, and missing timeouts. Apply the rubrics/thresholds from the wisdom reference.

9. **Review data pipeline efficiency** — For batch or streaming pipelines, check processing patterns, schema validation placement, error handling, and monitoring gaps. Apply the rubrics/thresholds from the wisdom reference.

10. **Score each dimension** with file:line evidence, using the rubrics from `references/wisdom.md`.

11. **Produce the report** with scores, evidence, and prioritized action items.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

For severity level definitions (CRITICAL, HIGH, MEDIUM, LOW) with domain-specific examples, consult `references/wisdom.md`.

## Scoring Dimensions (1-10 each)

Dimensions to score (detailed rubrics including what-to-check, what-good-looks-like, and what-bad-looks-like are in `references/wisdom.md`):

1. **Algorithmic Efficiency** — Big-O complexity of hot paths, data structure selection, bounded vs unbounded collections
2. **Database Design** — N+1 queries, indexing, connection pooling, result set bounding, query patterns
3. **Caching Strategy** — Cache coverage, TTL/invalidation, stampede protection, bounded growth, observability
4. **Scalability Readiness** — Stateless design, downstream resilience, database scaling, async processing, backpressure
5. **Resource Utilization** — Memory bounds, connection pools, timeouts, payload sizing, thread/goroutine management
6. **Data Pipeline Efficiency** — Incremental processing, validation placement, error isolation, idempotency, schema handling

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

Based on [Fundamentals of Software Performance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-performance/), [Fundamentals of Software Scalability](https://jeffbailey.us/blog/2025/12/22/fundamentals-of-software-scalability/), [Fundamentals of Software Caching](https://jeffbailey.us/blog/2025/12/24/fundamentals-of-software-caching/) and guidance from https://jeffbailey.us/categories/fundamentals/
```

Refer to the performance checklist at `review-performance/references/checklist.md` for detailed checks within each dimension.
