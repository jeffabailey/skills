---
name: review-algorithms
description: Analyzes code for algorithm/data structure correctness, concurrency safety, and edge case handling, producing fitness scores (1-10) across algorithm choice, data structure selection, complexity awareness, concurrency safety, edge case handling, and correctness patterns. Use when the user says /review:review-algorithms, requests an algorithm review, asks about correctness of data structure choices, wants a concurrency safety check, asks about edge case coverage, or wants to verify algorithmic complexity. This is NOT a performance review -- it asks "is this correct and appropriate?" not "is this fast enough?" Only reports findings with confidence >= 7/10.
---

# Algorithm & Data Structure Fitness Review

Analyze the codebase (or specified files/modules) for algorithm and data structure fitness. Identify correctness risks, inappropriate structure choices, concurrency hazards, and edge case gaps using evidence from the code. This review asks "is this correct? is this the right approach? will this break?" -- not "is this fast enough?"

Reference: [Fundamentals of Algorithms](https://jeffbailey.us/blog/2025/12/04/fundamentals-of-algorithms/) — see also [Fundamental Algorithmic Patterns](https://jeffbailey.us/blog/2025/12/12/fundamental-algorithmic-patterns/), [Fundamental Data Structures](https://jeffbailey.us/blog/2025/12/10/fundamental-data-structures/), and [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

For detailed scoring rubrics, severity definitions, what-good-looks-like / what-bad-looks-like criteria, and domain expertise, read `references/wisdom.md` before scoring. That file is auto-generated from:

- [Fundamentals of Algorithms](https://jeffbailey.us/blog/2025/12/04/fundamentals-of-algorithms/)
- [Fundamental Algorithmic Patterns](https://jeffbailey.us/blog/2025/12/12/fundamental-algorithmic-patterns/)
- [Fundamental Data Structures](https://jeffbailey.us/blog/2025/12/10/fundamental-data-structures/)

Use the wisdom reference when evaluating code and assigning dimension scores.

## Workflow

1. **Read domain knowledge** — Read `references/wisdom.md` to load scoring rubrics, thresholds, and severity definitions.

2. **Map algorithmic hotspots** — Use Grep/Glob to find sorting operations, search implementations, graph/tree traversals, recursive functions, collection manipulations, loops with nested iterations, and custom data structure implementations. These are the locations where algorithm and structure choices matter most.

3. **Audit algorithm choices** — For each hotspot, evaluate whether the chosen algorithm matches the problem characteristics. Apply the rubrics/thresholds from the wisdom reference for algorithm fitness.

4. **Evaluate data structure selection** — Find collection declarations and usages. Check whether collections match their access patterns and whether mutable vs immutable choices are intentional. Apply the rubrics/thresholds from the wisdom reference for data structure fitness.

5. **Assess complexity awareness** — Identify hidden O(n^2) patterns, unnecessary recomputation, unbounded growth, and repeated work. Apply the thresholds from the wisdom reference.

6. **Check concurrency safety** — Find shared mutable state, concurrent collection access, lock usage, and atomic operations. Look for race conditions, deadlock potential, and missing synchronization. Apply the rubrics/thresholds from the wisdom reference.

7. **Evaluate edge case handling** — Search for boundary conditions: empty collections, null/nil/None inputs, off-by-one errors, integer overflow, floating-point comparison, division by zero, and Unicode handling. Apply the rubrics/thresholds from the wisdom reference.

8. **Assess correctness patterns** — Check for invariant maintenance, idempotency, determinism, loop termination, precondition/postcondition checks, and error propagation. Apply the rubrics/thresholds from the wisdom reference.

9. **Score each dimension** with specific file:line evidence, using the rubrics from `references/wisdom.md`.

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

1. **Algorithm Choice** — Whether algorithms match problem structure: sorting strategy, search approach, graph traversal, divide-and-conquer, dynamic programming, greedy, batching
2. **Data Structure Selection** — Whether collections match access patterns, bounded vs unbounded, mutable vs immutable, concurrent structures where needed
3. **Complexity Awareness** — Hidden quadratic behavior, unnecessary recomputation, unbounded growth, string concatenation in loops, amortized cost awareness
4. **Concurrency Safety** — Shared mutable state protection, race conditions, lock ordering, atomic operations, thread-safe collections, ownership model
5. **Edge Case Handling** — Empty collections, null inputs, boundary values, off-by-one errors, integer overflow, floating-point comparison, division by zero, Unicode
6. **Correctness Patterns** — Invariant maintenance, idempotency, determinism, error propagation, loop termination, precondition/postcondition checks, equality/hash consistency

## Output Format

Write the report to `docs/algorithms-review.md` with this structure:

```markdown
# Algorithm & Data Structure Fitness Review

## Summary

Overall fitness score: X.X / 10 (average of dimensions)

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Algorithm Choice | X/10 | ... |
| Data Structure Selection | X/10 | ... |
| Complexity Awareness | X/10 | ... |
| Concurrency Safety | X/10 | ... |
| Edge Case Handling | X/10 | ... |
| Correctness Patterns | X/10 | ... |

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

### Algorithm Choice (X/10)
- Evidence: file:line references
- Issues found
- Recommendations

(repeat for each dimension)

## Top 5 Action Items (by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...

## Checklist Reference

See references/checklist.md for the full algorithm and data structure checklist.

## Reference

Based on [Fundamentals of Algorithms](https://jeffbailey.us/blog/2025/12/04/fundamentals-of-algorithms/), [Fundamental Algorithmic Patterns](https://jeffbailey.us/blog/2025/12/12/fundamental-algorithmic-patterns/), [Fundamental Data Structures](https://jeffbailey.us/blog/2025/12/10/fundamental-data-structures/), and guidance from https://jeffbailey.us/categories/fundamentals/
```

Refer to the algorithm and data structure checklist at `review-algorithms/references/checklist.md` for detailed checks within each dimension.

Reference: [Fundamentals of Algorithms](https://jeffbailey.us/blog/2025/12/04/fundamentals-of-algorithms/), [Fundamental Algorithmic Patterns](https://jeffbailey.us/blog/2025/12/12/fundamental-algorithmic-patterns/), [Fundamental Data Structures](https://jeffbailey.us/blog/2025/12/10/fundamental-data-structures/)
