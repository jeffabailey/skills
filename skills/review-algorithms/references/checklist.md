# Algorithm & Data Structure Fitness Checklist

Detailed checklist for reviewing code against algorithm correctness, data structure appropriateness, concurrency safety, and edge case handling fundamentals. Use alongside the review-algorithms skill to systematically evaluate each dimension.

---

## 1. Algorithm Choice

### Searching
- [ ] **Appropriate search strategy** -- Linear search used only for small or unsorted collections. Sorted data uses binary search or tree-based lookup. Hash-based lookup used where only equality matching is needed. Linear search inside a loop over the same data is a red flag for missing index or hash map.
- [ ] **Index usage for repeated searches** -- When the same collection is searched repeatedly, an index (hash map, sorted structure, or database index) is built once and queried many times rather than scanning on every request.
- [ ] **Search preconditions verified** -- Binary search is only used on sorted data. Hash-based search uses appropriate key types. Tree search uses a properly maintained tree (balanced where needed).

### Sorting
- [ ] **Standard library sort used** -- Custom sort implementations are avoided unless there is a documented reason (e.g., specialized comparator, radix sort for specific data). Standard library sorts are well-tested and optimized.
- [ ] **Stability considered** -- When sort order of equal elements matters for correctness, a stable sort is used. Unstable sorts are only used when stability is irrelevant.
- [ ] **Sort-once pattern** -- Data is sorted once and kept sorted (or inserted into a sorted structure) rather than re-sorted on every access.
- [ ] **Comparator correctness** -- Custom comparators are transitive, antisymmetric, and total. Inconsistent comparators cause nondeterministic or incorrect sort results.

### Graph and Tree Traversal
- [ ] **BFS vs DFS chosen correctly** -- BFS used for shortest path in unweighted graphs and level-order processing. DFS used for exhaustive search, cycle detection, and backtracking. The wrong choice produces incorrect results, not just slower results.
- [ ] **Cycle handling** -- Graph traversals track visited nodes to prevent infinite loops in cyclic graphs. Recursion depth is bounded for trees that could be deeply nested.
- [ ] **Topological sort for dependencies** -- Dependency ordering uses topological sort (Kahn's algorithm or DFS-based). Cycle detection is included to surface circular dependencies.

### Algorithmic Patterns
- [ ] **Dynamic programming applied to overlapping subproblems** -- When a problem has overlapping subproblems and optimal substructure, memoization or tabulation is used instead of exponential brute force.
- [ ] **Greedy algorithms validated** -- Greedy approaches are used only where the greedy-choice property holds. A counterexample check or proof justifies the greedy approach.
- [ ] **Batching for I/O operations** -- Per-item remote calls or database queries inside loops are replaced with batch operations. N+1 query patterns are identified and fixed.
- [ ] **Divide and conquer where applicable** -- Problems that decompose into independent subproblems use divide-and-conquer rather than monolithic processing.

Source: [Fundamentals of Algorithms](https://jeffbailey.us/blog/2025/12/04/fundamentals-of-algorithms/), [Fundamental Algorithmic Patterns](https://jeffbailey.us/blog/2025/12/12/fundamental-algorithmic-patterns/)

---

## 2. Data Structure Selection

### Collection Type Matching
- [ ] **Hash sets for membership testing** -- Membership checks (`x in collection`) use sets with O(1) average lookup, not lists with O(n) scan. Converting a list to a set before repeated membership checks is worth the one-time cost.
- [ ] **Hash maps for key-value lookup** -- Key-based access uses hash maps with O(1) average lookup, not iteration through a list of pairs or objects.
- [ ] **Sorted structures for range queries** -- Range queries, ordered iteration, or min/max operations use sorted structures (TreeMap, BTreeMap, sorted arrays with binary search) rather than filtering unsorted collections.
- [ ] **Queues for FIFO, stacks for LIFO** -- Processing order matches the data structure: queues (deque) for first-in-first-out, stacks (list with append/pop) for last-in-first-out. Using the wrong end of an array for queue operations (e.g., list.pop(0) in Python, Array.shift() in JavaScript) causes O(n) performance.
- [ ] **Heaps for priority access** -- When only the minimum or maximum element is needed repeatedly, a heap or priority queue is used instead of sorting the entire collection on each access.

### Bounded vs Unbounded
- [ ] **Caches have capacity limits** -- In-memory caches (hash maps, dictionaries) have explicit maximum size and eviction policy (LRU, TTL, LFU). Unbounded caches grow until out-of-memory.
- [ ] **Buffers have depth limits** -- Queues, buffers, and accumulators have maximum depth configured. Unbounded buffers consume memory until the process crashes under load.
- [ ] **Growth monitored** -- Collection sizes on critical paths are instrumented with metrics or logging so unbounded growth is detected before it causes an outage.

### Mutable vs Immutable
- [ ] **Immutable where shared** -- Data shared across threads or components uses immutable structures to avoid synchronization issues. Mutations create new copies rather than modifying in place.
- [ ] **Mutable only with clear ownership** -- Mutable collections have a single clear owner. If multiple components need to modify a collection, synchronization is explicit.
- [ ] **Defensive copies at boundaries** -- Collections passed across API boundaries are copied (or wrapped as unmodifiable) to prevent callers from modifying internal state.

### Structure vs Access Pattern
- [ ] **No linked lists for random access** -- Linked lists are not used where index-based access is the dominant pattern. Arrays or array-backed lists are used for positional access.
- [ ] **No arrays for frequent middle insertion** -- Frequent insertion or deletion in the middle of a sequence uses a linked list, deque, or skip list, not an array that shifts elements on every operation.
- [ ] **Hash maps not used where ordering matters** -- When iteration order matters for correctness, ordered maps (LinkedHashMap, OrderedDict, BTreeMap) are used instead of unordered hash maps.

Source: [Fundamental Data Structures](https://jeffbailey.us/blog/2025/12/10/fundamental-data-structures/), [Fundamentals of Data Structures](https://jeffbailey.us/blog/2025/12/06/fundamentals-of-data-structures/)

---

## 3. Complexity Awareness

### Hidden Quadratic Behavior
- [ ] **No nested loops over unbounded input** -- Nested loops where both iterate over collections that grow with input size are flagged. Each nesting level multiplies complexity. Inner loops that call O(n) operations make the overall path O(n^2).
- [ ] **No linear search inside loops** -- Searching a list inside a loop produces O(n^2). Replace with a hash set or map built before the loop for O(n) total.
- [ ] **No repeated sorting** -- The same collection is not sorted multiple times in the same request path. Sort once, then maintain order or use the sorted result.
- [ ] **String concatenation uses builder** -- In languages with immutable strings (Java, Python, Go, C#), string building inside loops uses StringBuilder, join(), strings.Builder, or equivalent instead of `+=` which creates O(n^2) copy behavior.

### Redundant Computation
- [ ] **Expensive computations memoized** -- Pure functions with expensive computation that are called with the same arguments are memoized or cached.
- [ ] **Indexes precomputed** -- Lookup tables, frequency counts, or indexes are built once before they are queried multiple times, not rebuilt on each query.
- [ ] **Results reused across iterations** -- Loop iterations do not recompute values that could be computed once before the loop or carried forward from the previous iteration.

### Unbounded Growth
- [ ] **All in-memory collections bounded** -- Every hash map, list, cache, queue, and accumulator on a long-lived path has an explicit maximum size.
- [ ] **Eviction policy defined** -- Bounded collections have a defined eviction strategy (LRU, TTL, FIFO) rather than silently failing or overwriting.
- [ ] **Event listeners cleaned up** -- Event subscriptions, callbacks, and listeners are unsubscribed when the subscriber is done. Leaked subscriptions keep objects alive and grow listener lists.
- [ ] **Temporary allocations bounded** -- Intermediate results, buffers, and temporary collections created during processing are bounded and released after use.

### Amortized Cost Awareness
- [ ] **Resize spikes accounted for** -- Dynamic arrays and hash maps resize occasionally, causing O(n) spikes. Latency-sensitive paths either pre-allocate capacity or document the acceptable spike.
- [ ] **Batch size limits** -- Operations that process items in batches have maximum batch sizes to prevent single large batches from causing latency spikes.

Source: [Fundamentals of Algorithms](https://jeffbailey.us/blog/2025/12/04/fundamentals-of-algorithms/), [Fundamentals of Data Structures](https://jeffbailey.us/blog/2025/12/06/fundamentals-of-data-structures/)

---

## 4. Concurrency Safety

### Shared Mutable State
- [ ] **Shared state identified** -- All mutable state accessed from multiple threads, goroutines, or async tasks is explicitly identified and documented.
- [ ] **Synchronization on every access** -- Every read and write to shared mutable state uses appropriate synchronization: mutexes, read-write locks, channels, or atomic operations.
- [ ] **No bare global mutable variables** -- Global variables modified by request handlers or background tasks are protected. Unprotected globals are the most common source of race conditions.
- [ ] **Immutable sharing preferred** -- Data shared across threads is immutable where possible. Immutable data requires no synchronization.

### Atomicity
- [ ] **Read-modify-write is atomic** -- Patterns like `counter += 1`, check-then-act, and compare-and-swap on shared state use atomic operations or are protected by a lock. Non-atomic read-modify-write causes lost updates.
- [ ] **Lazy initialization is thread-safe** -- Singletons or lazy-initialized values use thread-safe patterns (sync.Once in Go, double-checked locking with volatile in Java, std::once_flag in C++). Naive check-then-set is racy.
- [ ] **Compound operations are atomic** -- Operations that require multiple steps to maintain consistency (e.g., transfer between accounts: debit + credit) are wrapped in a single lock or transaction.

### Lock Discipline
- [ ] **Lock ordering is consistent** -- When multiple locks must be held simultaneously, they are always acquired in the same order across all code paths. Inconsistent ordering causes deadlocks.
- [ ] **Lock scope is minimal** -- Locks are held for the shortest time possible. I/O operations, remote calls, and expensive computations are not performed while holding a lock.
- [ ] **No lock held across await/yield** -- In async code, locks are not held across await points. Awaiting while holding a lock can cause deadlocks or extended lock contention.
- [ ] **Read-write locks where appropriate** -- When reads significantly outnumber writes, read-write locks (RWMutex, ReadWriteLock) are used instead of exclusive mutexes to allow concurrent reads.

### Thread-Safe Collections
- [ ] **Concurrent collections for shared access** -- Collections accessed from multiple threads use concurrent variants (ConcurrentHashMap, sync.Map, concurrent queues) or are protected by external synchronization.
- [ ] **No concurrent modification during iteration** -- Collections are not modified by one thread while another iterates over them. Concurrent modification causes crashes or skipped/duplicate elements.
- [ ] **Iterator invalidation handled** -- When a collection may change during iteration, the code uses a snapshot, a copy, or a concurrent-safe iterator.

### Visibility and Ordering
- [ ] **Volatile or atomic for flags** -- Shared boolean flags (shutdown flags, ready flags) use volatile, atomic, or memory-barrier primitives to ensure changes are visible across threads.
- [ ] **Happens-before relationships established** -- Synchronization points (lock acquire/release, channel send/receive, atomic operations) establish happens-before relationships that make prior writes visible to subsequent reads.

Source: [Fundamentals of Concurrency and Parallelism](https://jeffbailey.us/blog/2025/12/26/fundamentals-of-concurrency-and-parallelism/), [Fundamental Software Concepts](https://jeffbailey.us/blog/2025/10/11/fundamental-software-concepts/)

---

## 5. Edge Case Handling

### Empty and Null Inputs
- [ ] **Empty collection check before access** -- Code checks collection length before accessing elements by index (arr[0], arr[-1], arr.first()). Direct access to an empty collection causes index-out-of-bounds or null pointer errors.
- [ ] **Null/None/nil validated at boundaries** -- Function parameters that could be null are validated at the function entry. Null propagation through multiple layers causes cryptic errors far from the source.
- [ ] **Optional/Result types used where appropriate** -- Languages with Option/Maybe/Result types use them for values that may be absent instead of returning null and relying on callers to check.
- [ ] **Empty string handled distinctly from null** -- Functions distinguish between null (no value), empty string (value present but empty), and whitespace-only strings where the distinction matters.

### Numeric Boundaries
- [ ] **Integer overflow checked** -- Multiplication, addition, and exponentiation of values that could be large (user-controlled sizes, counters, timestamps) are checked for overflow or use arbitrary-precision types.
- [ ] **Negative value handling** -- Functions that expect non-negative input (array sizes, counts, indices) validate that values are non-negative rather than assuming.
- [ ] **Division by zero guarded** -- Every division operation where the denominator is derived from input, configuration, or calculation has a zero check.
- [ ] **Floating-point comparison uses epsilon** -- Equality comparison of floating-point values uses an epsilon/tolerance threshold rather than `==`. Direct equality on floats fails for values like 0.1 + 0.2.
- [ ] **Maximum/minimum value edge cases** -- Code handles INT_MAX, INT_MIN, MAX_SAFE_INTEGER, and similar boundary values without wrapping or producing incorrect results.

### Off-by-One Errors
- [ ] **Loop bounds correct** -- Loop conditions use correct inclusive/exclusive semantics. `< length` vs `<= length`, starting at 0 vs 1, and ending conditions are verified against the intended range.
- [ ] **Fence-post errors avoided** -- Algorithms that process gaps between elements (intervals, ranges, segments) account for the fence-post problem: n elements have n-1 gaps.
- [ ] **Range endpoints documented** -- Range parameters document whether they are inclusive or exclusive. Mixed conventions (some inclusive, some exclusive) are a source of bugs.
- [ ] **Slice/substring bounds verified** -- Substring and array slice operations have bounds checked against the source length to prevent out-of-range access.

### String and Encoding
- [ ] **Unicode length vs byte length** -- String length operations use character count (or grapheme cluster count) rather than byte length where user-visible length matters. UTF-8 characters can be 1-4 bytes.
- [ ] **String normalization** -- String comparison and hashing normalize Unicode forms (NFC, NFD) when comparing strings from different sources that may use different normalization.
- [ ] **Locale-aware comparison** -- String sorting and comparison that is user-visible uses locale-aware collation rather than byte-order comparison.

### Type Coercion
- [ ] **No implicit precision loss** -- Conversions from float to int, long to int, or double to float are explicit and checked for precision loss or truncation.
- [ ] **Boolean coercion explicit** -- Truthy/falsy coercion in languages like JavaScript and Python is explicit where 0, empty string, or empty collection could be valid non-false values.

Source: [Fundamental Software Concepts](https://jeffbailey.us/blog/2025/10/11/fundamental-software-concepts/), [Fundamentals of Algorithms](https://jeffbailey.us/blog/2025/12/04/fundamentals-of-algorithms/)

---

## 6. Correctness Patterns

### Invariant Maintenance
- [ ] **Class/struct invariants documented** -- Key invariants (e.g., "this list is always sorted", "balance is never negative", "start < end") are documented in comments or enforced by the type system.
- [ ] **Invariants enforced on mutation** -- Every mutation method verifies that the invariant still holds after the change. Violations are caught immediately with assertions or exceptions, not left to surface later.
- [ ] **State machine transitions validated** -- Objects with lifecycle states (e.g., CREATED -> ACTIVE -> CLOSED) only allow valid transitions. Invalid transitions raise errors rather than silently proceeding.

### Idempotency
- [ ] **Retryable operations are idempotent** -- Operations that may be retried (HTTP handlers, message consumers, job processors) produce the same result when executed multiple times with the same input.
- [ ] **Idempotency keys on write operations** -- State-changing operations that may be retried (payments, order creation, resource allocation) use idempotency keys to prevent duplicate side effects.
- [ ] **At-least-once delivery handled** -- Message consumers handle duplicate delivery by checking for already-processed message IDs or by designing processing to be naturally idempotent.

### Determinism
- [ ] **No reliance on unordered iteration** -- Code correctness does not depend on the iteration order of hash maps, sets, or other unordered collections. Different runs or implementations may iterate in different orders.
- [ ] **No reliance on wall clock for logic** -- Business logic does not use wall clock time (System.currentTimeMillis, time.time(), Date.now()) where monotonic or logical clocks are needed. Wall clock can jump backward.
- [ ] **Random values seeded for reproducibility where needed** -- When deterministic behavior is required for testing or debugging, random number generators use configurable seeds.
- [ ] **Sort stability relied upon explicitly** -- When sort stability matters for correctness (preserving relative order of equal elements), the sort algorithm is documented as stable or a stable sort is explicitly chosen.

### Error Propagation
- [ ] **No silent error swallowing** -- Catch-all exception handlers (`except Exception`, `catch (Exception e)`, `catch { ... }`) do not silently ignore errors. At minimum, errors are logged with context. Algorithmic errors that are swallowed can produce silently wrong results.
- [ ] **Error context preserved** -- When errors are caught and re-thrown or wrapped, the original error context (message, stack trace, cause) is preserved for debugging.
- [ ] **Partial failure handled** -- When processing a collection of items, failure on one item is handled without silently skipping it or aborting the entire batch (unless abort-on-first-error is the intended behavior).

### Loop Termination
- [ ] **Every loop has a termination guarantee** -- While loops and recursive functions have a clear condition that is guaranteed to become true. Each iteration must make progress toward the exit condition.
- [ ] **Recursion has a base case** -- Recursive functions have an explicit base case that stops recursion. The recursive call must reduce the problem toward the base case.
- [ ] **Maximum iteration limits** -- Loops that depend on external input or convergence conditions have a maximum iteration count to prevent infinite loops in edge cases.

### Comparison and Equality
- [ ] **Equals and hashCode are consistent** -- In languages where these are overridden (Java, Kotlin, Python __eq__/__hash__), objects that are equal produce equal hash codes. Inconsistency breaks hash sets and hash maps.
- [ ] **Comparators are total, transitive, and antisymmetric** -- Custom comparison functions satisfy the contract required by sort algorithms. Violating these properties causes nondeterministic sort results or crashes.
- [ ] **Reference vs value equality intentional** -- Use of `==` vs `.equals()` (Java), `is` vs `==` (Python), `===` vs `==` (JavaScript) is intentional and matches the comparison semantics needed.

Source: [Fundamental Software Concepts](https://jeffbailey.us/blog/2025/10/11/fundamental-software-concepts/), [Fundamentals of Concurrency and Parallelism](https://jeffbailey.us/blog/2025/12/26/fundamentals-of-concurrency-and-parallelism/)

---

## Quick Reference: The Five Most Common Algorithm/Structure Problems

1. **Hidden quadratic behavior** -- Nested loops or linear search inside a loop over growing data produce O(n^2) paths that work in tests with small data but cause latency incidents with production volumes. Fix: replace inner linear scans with hash-based lookups or precomputed indexes.

2. **Wrong data structure for the access pattern** -- Using a list for repeated membership checks (O(n) per check) when a set gives O(1), or using an unordered map where iteration order matters for correctness. Fix: match the structure to the dominant operation.

3. **Unprotected shared mutable state** -- Global or shared variables modified from multiple threads without synchronization cause race conditions that produce intermittent, hard-to-reproduce bugs. Fix: use atomic operations, locks, or immutable data sharing.

4. **Missing edge case handling at boundaries** -- Empty collections, null inputs, zero denominators, and integer overflow are not handled, causing crashes or silent data corruption with unusual but valid inputs. Fix: validate inputs at function boundaries and handle boundary values explicitly.

5. **Unbounded in-memory growth** -- Caches, accumulators, event listeners, or buffers that grow without limit until the process runs out of memory. Fix: add explicit capacity limits and eviction policies to every long-lived in-memory collection.

---

## Source Articles

- [Fundamentals of Algorithms](https://jeffbailey.us/blog/2025/12/04/fundamentals-of-algorithms/)
- [Fundamental Algorithmic Patterns](https://jeffbailey.us/blog/2025/12/12/fundamental-algorithmic-patterns/)
- [Fundamental Data Structures](https://jeffbailey.us/blog/2025/12/10/fundamental-data-structures/)
- [Fundamentals of Data Structures](https://jeffbailey.us/blog/2025/12/06/fundamentals-of-data-structures/)
- [Fundamental Software Concepts](https://jeffbailey.us/blog/2025/10/11/fundamental-software-concepts/)
- [Fundamentals of Concurrency and Parallelism](https://jeffbailey.us/blog/2025/12/26/fundamentals-of-concurrency-and-parallelism/)
