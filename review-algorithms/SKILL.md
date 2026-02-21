---
name: review-algorithms
description: Analyzes code for algorithm/data structure correctness, concurrency safety, and edge case handling, producing fitness scores (1-10) across algorithm choice, data structure selection, complexity awareness, concurrency safety, edge case handling, and correctness patterns. Use when the user says /review:review-algorithms, requests an algorithm review, asks about correctness of data structure choices, wants a concurrency safety check, asks about edge case coverage, or wants to verify algorithmic complexity. This is NOT a performance review -- it asks "is this correct and appropriate?" not "is this fast enough?" Only reports findings with confidence >= 7/10.
---

# Algorithm & Data Structure Fitness Review

Analyze the codebase (or specified files/modules) for algorithm and data structure fitness. Identify correctness risks, inappropriate structure choices, concurrency hazards, and edge case gaps using evidence from the code. This review asks "is this correct? is this the right approach? will this break?" -- not "is this fast enough?"

## Workflow

1. **Map algorithmic hotspots** -- Use Grep/Glob to find sorting operations, search implementations, graph/tree traversals, recursive functions, collection manipulations, loops with nested iterations, and custom data structure implementations. These are the locations where algorithm and structure choices matter most.

2. **Audit algorithm choices** -- For each hotspot, evaluate whether the chosen algorithm matches the problem characteristics. Check whether sorting strategies match data properties (nearly sorted, small n, stability requirements). Look for linear searches where indexed or hash-based lookups would be appropriate. Check graph traversals for correct BFS vs DFS selection. Identify divide-and-conquer, dynamic programming, or greedy patterns and verify they match the problem structure.

3. **Evaluate data structure selection** -- Find collection declarations and usages. Check whether lists are used where sets or maps would be more appropriate. Look for unbounded collections without capacity limits. Verify that mutable vs immutable choices are intentional. Check whether sorted structures are used where ordering is needed vs hash structures where only lookup matters. Identify structures that don't match their access patterns (e.g., linked lists used for random access, arrays used for frequent middle insertion).

4. **Assess complexity awareness** -- Identify hidden O(n^2) patterns: nested loops over growing data, repeated linear searches inside loops, string concatenation in loops for immutable string languages, repeated sorting of the same data. Check for unnecessary recomputation that could be memoized. Look for unbounded growth patterns in caches, accumulators, or in-memory collections.

5. **Check concurrency safety** -- Find shared mutable state, concurrent collection access, lock usage, and atomic operations. Look for race conditions in read-modify-write patterns. Check for deadlock potential from inconsistent lock ordering. Verify thread-safe collection usage where concurrent access occurs. Look for missing synchronization on shared counters, caches, or configuration. Check for proper use of volatile/atomic for visibility guarantees.

6. **Evaluate edge case handling** -- Search for boundary conditions: empty collections, null/nil/None inputs, single-element cases, maximum value inputs, zero-value inputs, negative numbers where unsigned expected. Check for off-by-one errors in loop bounds, array indexing, and range calculations. Look for integer overflow risks, floating-point comparison with equality, division by zero, and Unicode handling issues.

7. **Assess correctness patterns** -- Check for invariant maintenance across state mutations. Verify idempotency where operations may be retried. Look for deterministic behavior requirements. Check that loop termination is guaranteed (no infinite loops). Verify precondition/postcondition checks or assertions. Evaluate error propagation in algorithmic code -- do errors get swallowed silently?

8. **Score each dimension** with specific file:line evidence.

9. **Produce the report** with scores, evidence, and prioritized action items.

## Confidence and Severity

### Confidence Threshold

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

### Severity Levels

- **CRITICAL** -- Guaranteed incorrect behavior under normal conditions. Wrong algorithm producing wrong results, data corruption from race conditions, infinite loops, invariant violations that cause crashes.
- **HIGH** -- Incorrect behavior under realistic conditions. Race conditions under concurrent load, edge cases that will be hit with production data, O(n^2) on paths that handle large inputs, missing synchronization on shared state.
- **MEDIUM** -- Potential incorrectness or poor fit requiring specific conditions. Suboptimal algorithm choice that works but may break at scale, missing edge case handling for uncommon inputs, concurrency patterns that are fragile but not yet broken.
- **LOW** -- Improvement opportunities. Better algorithm or structure available, defensive checks that could be added, complexity that could be reduced, patterns that would improve maintainability.

## Scoring Dimensions (1-10 each)

Evaluate and score each dimension with evidence from the code.

### 1. Algorithm Choice

What to check:
- Whether sorting strategy matches data characteristics (nearly sorted data, small n, stability needs, key extraction cost)
- Whether search approach matches data organization (linear scan vs binary search vs hash lookup vs index)
- Whether graph traversal choice matches the problem (BFS for shortest path in unweighted graphs, DFS for exhaustive exploration, topological sort for dependency ordering)
- Whether pattern matching, string search, or text processing uses appropriate algorithms
- Whether divide-and-conquer, dynamic programming, or greedy approaches are applied where their preconditions hold
- Whether batching is used instead of per-item remote calls or I/O

What good looks like (8-10):
- Algorithms match problem structure: BFS for level-order, DFS for backtracking, topological sort for dependencies
- Sorting uses language standard library or well-understood algorithm with correct stability and complexity guarantees
- Searches use indexes, hash lookups, or binary search where data supports it
- Batching used for I/O-bound operations instead of per-item calls
- Dynamic programming or memoization applied where subproblems overlap
- Greedy algorithms used only where greedy-choice property is proven to hold

What bad looks like (1-3):
- Linear search used repeatedly on the same unsorted collection when a hash map or index would serve
- Naive nested-loop joins instead of hash-based or sort-merge approaches
- DFS used where BFS is needed for shortest path (or vice versa)
- Per-item remote calls inside loops instead of batching
- Brute-force exponential search where dynamic programming would apply
- Custom sort implementation instead of well-tested standard library sort

### 2. Data Structure Selection

What to check:
- Whether collections match their access patterns (list vs set vs map vs tree)
- Whether bounded vs unbounded collections are chosen intentionally
- Whether mutable vs immutable choices are deliberate and consistent
- Whether concurrent data structures are used where concurrent access exists
- Whether structure choice matches the dominant operation (e.g., hash map for lookup-heavy, sorted tree for range-query-heavy)
- Whether ad hoc nested structures could be replaced with named types or well-known patterns

What good looks like (8-10):
- Hash sets used for membership testing instead of list iteration
- Hash maps used for key-based lookup instead of linear scan through a list of pairs
- Bounded collections with explicit capacity and eviction for caches and buffers
- Immutable structures where shared state is read concurrently
- Sorted structures (TreeMap, BTreeMap) used where range queries or ordered iteration is needed
- Appropriate use of queues for FIFO processing, stacks for LIFO, deques for both-end access
- Concurrent collections (ConcurrentHashMap, sync.Map) used where threads share data

What bad looks like (1-3):
- Lists used for repeated membership checks (O(n) per check instead of O(1) with a set)
- Unbounded hash maps or lists used as caches without eviction or capacity limits
- Mutable shared collections accessed from multiple threads without synchronization
- Arrays used for frequent middle insertion/deletion where linked structures would be better
- Using a sorted structure when only equality lookup is needed (unnecessary ordering overhead)
- Flat arrays storing hierarchical data requiring brittle index arithmetic

### 3. Complexity Awareness

What to check:
- Nested loops over growing data that produce hidden O(n^2) or worse behavior
- Repeated work: sorting the same collection multiple times, rebuilding indexes unnecessarily
- String concatenation in loops in languages with immutable strings (creates O(n^2) copy behavior)
- Unbounded growth: caches, accumulators, event listeners, or log buffers that grow without limit
- Redundant computation that could be memoized or precomputed
- Calls inside loops that are individually O(n), making the overall path O(n^2)
- Amortized costs not accounted for (hash map rehashing, dynamic array resizing under latency-sensitive paths)

What good looks like (8-10):
- Single-pass algorithms where the data shape permits
- Precomputation of indexes, lookup tables, or sorted structures before repeated queries
- String building uses StringBuilder, join(), or equivalent instead of repeated concatenation
- Explicit capacity limits on all in-memory collections with eviction policies
- Memoization or caching applied to expensive pure computations
- Clear documentation or comments when a higher-complexity algorithm is chosen deliberately (with justification)

What bad looks like (1-3):
- Nested loops with no limit producing O(n^2) on paths that handle unbounded input
- String concatenation in a loop building a result character by character in an immutable-string language
- In-memory caches or maps that grow without bound until out-of-memory
- The same list sorted multiple times in the same request path
- Expensive computation repeated on every call with no caching or memoization
- No awareness of amortized cost spikes (e.g., hash map resize during a latency-sensitive request)

### 4. Concurrency Safety

What to check:
- Shared mutable state accessed from multiple threads or goroutines without synchronization
- Read-modify-write patterns without atomic operations or locks (check-then-act, increment, compare-and-swap)
- Lock ordering inconsistencies that could cause deadlocks
- Missing volatile/atomic for visibility of shared flags or counters
- Non-thread-safe collections used in concurrent contexts (e.g., HashMap in Java without synchronization)
- Double-checked locking implemented incorrectly
- Shared mutable iterators or generators accessed concurrently
- Signal handling that modifies shared state
- Race conditions in lazy initialization patterns
- Concurrent modification of collections during iteration

What good looks like (8-10):
- Shared state protected by appropriate synchronization (mutexes, read-write locks, channels)
- Atomic operations used for simple counters and flags
- Lock ordering documented and consistent across the codebase
- Concurrent collections used where threads share data structures
- Immutable data shared across threads without locks
- Clear ownership model: each piece of mutable state has one owner or one lock
- Channel-based or message-passing patterns used instead of shared mutable state where appropriate

What bad looks like (1-3):
- Global mutable variables accessed from request handlers without synchronization
- Increment operations on shared counters without atomic instructions
- Multiple locks acquired in different orders across different code paths
- Regular HashMap/dict used from multiple threads with no locking
- Lazy initialization with check-then-set pattern without synchronization
- Collections modified during iteration from concurrent threads
- No concurrent data structures used despite multi-threaded access patterns

### 5. Edge Case Handling

What to check:
- Empty collection handling: does code check for empty input before accessing first/last elements?
- Null/nil/None handling: are null inputs validated or do they cause null pointer exceptions deeper in the code?
- Boundary values: zero, negative numbers, maximum integer, minimum integer, empty string, single character
- Off-by-one errors: loop bounds, array index calculations, range endpoints (inclusive vs exclusive)
- Integer overflow: multiplication or addition of large values without overflow checks
- Floating-point comparison: equality checks on floats instead of epsilon-based comparison
- Division by zero: denominators derived from user input or calculations that could produce zero
- Unicode and encoding: string length vs byte length, multi-byte characters, normalization
- Type coercion edge cases: implicit conversions that lose precision or change meaning

What good looks like (8-10):
- Empty collection checks before indexing or destructuring
- Null checks or Option/Result types at API boundaries
- Explicit handling of zero, negative, and maximum values where relevant
- Loop bounds verified with clear inclusive/exclusive semantics
- Arithmetic overflow protected by checked operations or range validation
- Floating-point comparison uses epsilon or approximate equality
- Division guarded by zero checks on the denominator
- String operations handle Unicode correctly (grapheme clusters, normalization)

What bad looks like (1-3):
- Direct indexing into collections without checking length (arr[0] on possibly empty array)
- No null checks; null pointer exceptions surface in production
- Loop bounds off by one (< vs <=, or starting at 1 instead of 0)
- Integer multiplication without overflow checks on user-controlled values
- Floating-point == used for currency or measurement comparison
- Division by a value derived from user input with no zero guard
- String operations assume ASCII (string[5] to get 5th character in a UTF-8 string)
- Silently truncating data when types are coerced (e.g., float to int)

### 6. Correctness Patterns

What to check:
- Invariant maintenance: do state transitions preserve documented or implied invariants?
- Idempotency: can operations be safely retried without side effects? Are idempotency keys used where needed?
- Determinism: does the code produce the same output for the same input? Are there hidden dependencies on iteration order of unordered collections, wall clock time, or random values?
- Error propagation: are errors in algorithmic code caught and surfaced, or silently swallowed?
- Loop termination: is every loop guaranteed to terminate? Are there clear progress conditions?
- Precondition and postcondition checks: are assertions or validation used to verify assumptions?
- Comparison and equality: are custom equals/hashCode implementations consistent? Are comparison functions transitive?
- Sort stability: when sorting matters for correctness, is a stable sort used?

What good looks like (8-10):
- State transitions enforce invariants through assertions or type system constraints
- Retryable operations are idempotent with proper idempotency keys
- Behavior is deterministic; no reliance on unordered iteration, wall clock, or random values for correctness
- Errors are propagated with context, never silently swallowed in catch-all handlers
- Every loop has a clear termination condition; recursion has a base case and provable progress
- Preconditions validated at function entry; postconditions asserted where practical
- Equality and hash implementations are consistent (objects that are equal produce equal hashes)
- Sort comparators are transitive, antisymmetric, and total

What bad looks like (1-3):
- State mutations that break class invariants with no validation
- Write operations retried without idempotency keys, causing duplicates
- Code depends on HashMap iteration order or system clock for correctness
- Catch-all exception handlers that log and continue, hiding algorithmic failures
- While loops with no guaranteed progress toward the exit condition
- No precondition checks; invalid input causes cryptic failures deep in the call stack
- hashCode not overridden when equals is overridden (or vice versa)
- Sort comparators that are not transitive, causing nondeterministic sort results

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

Based on guidance from https://jeffbailey.us/categories/fundamentals/
```

Refer to the algorithm and data structure checklist at `review-algorithms/references/checklist.md` for detailed checks within each dimension.

Reference: https://jeffbailey.us/categories/fundamentals/
