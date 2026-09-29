# Performance and Scalability Checklist

Detailed checklist for reviewing code against performance and scalability fundamentals. Use alongside the review-performance skill to systematically evaluate each dimension.

---

## 1. Algorithmic Complexity Red Flags

### Nested Loop Patterns
- [ ] **Nested loops over growing data** -- Any `for x in items: for y in items` pattern on hot paths is O(n^2). Check whether the inner collection grows with input.
- [ ] **Loops with remote calls** -- A loop that makes a database query, HTTP call, or cache lookup per iteration multiplies latency linearly. Batch or prefetch instead.
- [ ] **Repeated scans** -- Scanning the same collection multiple times in sequence (filter, then search, then count) when a single pass would suffice.
- [ ] **Sorting inside loops** -- Sorting a collection on every iteration instead of sorting once and reusing.

### Unbounded Collections
- [ ] **Hash maps without capacity limits** -- In-memory maps that grow with user data or request volume without eviction. These cause OOM in long-running services.
- [ ] **Lists that accumulate without bounds** -- Appending to a list over time without draining, truncating, or evicting old entries.
- [ ] **Graph traversals without visit tracking** -- Traversing a graph without a visited set risks infinite loops on cycles and unbounded memory.
- [ ] **Tree recursion without depth limits** -- Recursive tree processing on user-generated hierarchies can exceed stack depth.

### Data Structure Mismatches
- [ ] **Lists used for lookups** -- Searching a list by iterating (O(n)) when a hash map would give O(1) average-case lookup.
- [ ] **Hash maps used for ordering** -- Using a hash map when ordered iteration is needed, then sorting separately. Use a sorted structure or maintain order explicitly.
- [ ] **Flat arrays for hierarchical data** -- Storing hierarchical data in flat arrays forces O(n) scans to find children; tree structures give O(1) child access.
- [ ] **Wrong structure for the access pattern** -- Describe the data shape and key operations in plain language. If the structure does not match, refactor.

### Growth Pattern Recognition
- [ ] **Can you name the Big-O of each hot path?** -- If you cannot state the complexity, measure it by doubling input and observing latency growth.
- [ ] **Does latency grow linearly or worse with input size?** -- Linear is often acceptable; quadratic or worse requires redesign.
- [ ] **Are there amortized cost spikes?** -- Dynamic arrays and hash maps have occasional O(n) resizes. Monitor for latency spikes during rehashing.

Source: [Fundamentals of Algorithms](https://jeffbailey.us/blog/2025/12/04/fundamentals-of-algorithms/), [Fundamentals of Data Structures](https://jeffbailey.us/blog/2025/12/06/fundamentals-of-data-structures/)

---

## 2. Database Optimization Checks

### Query Patterns
- [ ] **N+1 queries** -- A query inside a loop that fetches related records one at a time. Replace with a single batch query or JOIN.
- [ ] **SELECT * on large tables** -- Fetching all columns when only a few are needed wastes I/O, memory, and network bandwidth. Select specific columns.
- [ ] **Unbounded result sets** -- Queries without LIMIT or pagination on tables that grow. Add pagination or cursors.
- [ ] **Missing WHERE clauses on large tables** -- Full table scans where a filter would reduce the result set significantly.
- [ ] **Complex joins on hot paths** -- Multi-table joins on frequently executed queries. Consider denormalization or precomputed views.

### Indexing
- [ ] **Missing indexes on WHERE columns** -- Columns used in WHERE, JOIN ON, and ORDER BY clauses should have indexes.
- [ ] **Missing composite indexes** -- Queries filtering on multiple columns may need composite indexes rather than individual ones.
- [ ] **Over-indexing** -- Too many indexes slow writes. Index only columns that appear in frequent query patterns.
- [ ] **EXPLAIN plan review** -- Run EXPLAIN on complex queries. Look for sequential scans on large tables, missing index usage, and sort operations that could be avoided.

### Connection Management
- [ ] **Connection pooling** -- Database connections are reused via a pool, not created per request.
- [ ] **Pool sizing** -- Pool max size is configured based on downstream database capacity, not left at defaults.
- [ ] **Connection leak detection** -- Connections are returned to the pool in finally/defer blocks. Leaked connections exhaust the pool.
- [ ] **Connection timeouts** -- Connect and query timeouts are set to prevent hanging on unresponsive databases.

### Data Model
- [ ] **Normalization vs denormalization trade-offs** -- Normalized for write-heavy, denormalized for read-heavy. The choice is intentional.
- [ ] **Transaction scope** -- Transactions are as short as possible. Long-held transactions cause lock contention.
- [ ] **Read replicas for read-heavy workloads** -- Read queries go to replicas when eventual consistency is acceptable.
- [ ] **Partitioning or sharding plan** -- Large tables have a partitioning strategy (by date, tenant, or key range).

Source: [Fundamentals of Databases](https://jeffbailey.us/blog/2025/09/24/fundamentals-of-databases/), [Fundamentals of Graph Databases](https://jeffbailey.us/blog/2026/02/14/fundamentals-of-graph-databases/)

---

## 3. Caching Analysis

### Cache Presence and Placement
- [ ] **Are expensive repeated operations cached?** -- Database queries, API calls, and computations that repeat with the same inputs should be candidates for caching.
- [ ] **Is the cache on the right layer?** -- Application cache, CDN, HTTP cache headers, database query cache. Each layer serves different access patterns.
- [ ] **Is the backend viable without the cache?** -- If the cache fails or cold-starts, can the backend survive full load? If not, the cache is a reliability dependency, not an optimization.

### Freshness and Invalidation
- [ ] **Is "fresh enough" defined for each cached data type?** -- Freshness is a product requirement. Define how stale the data can be before it harms users.
- [ ] **TTL matches data change frequency** -- TTLs that are too long serve stale data. TTLs that are too short defeat the cache.
- [ ] **Invalidation strategy exists** -- TTL-only, explicit invalidation on write, or versioned keys. The choice is intentional.
- [ ] **No caching of data that must be correct immediately** -- Authorization decisions, payment state, and last-item inventory should not be cached (or cached with extreme care).

### Stampede and Failure Protection
- [ ] **Hot key expiry protection** -- When a popular key expires, many simultaneous requests can overwhelm the backend (cache stampede). Use request coalescing (single-flight) or stale-while-revalidate.
- [ ] **Jittered TTLs** -- Avoid synchronized expiry across the fleet by adding random jitter to TTL values.
- [ ] **Cold start plan** -- After a deploy or cache restart, the hit rate drops to zero. The backend must handle the load spike, or the cache must be warmed.
- [ ] **Cache penetration defense** -- High-cardinality keys, bot traffic, or nonexistent IDs bypass the cache entirely. Consider negative caching or bloom filters.

### Bounded Growth
- [ ] **Cache has a maximum size** -- Unbounded caches grow until memory is exhausted. Set a max size with an eviction policy (LRU, LFU).
- [ ] **Eviction policy matches access patterns** -- LRU works for recency-biased workloads. LFU works for frequency-biased workloads. The choice is deliberate.
- [ ] **Large values do not crowd out small ones** -- A few large cached objects can evict many useful small objects. Consider size-aware eviction.

### Observability
- [ ] **Hit rate is tracked per endpoint or key family** -- A single global hit rate hides problems. Break it down.
- [ ] **Miss latency is tracked** -- The cost of a miss (backend call + cache populate) is measured and alerted on.
- [ ] **Eviction rate is monitored** -- High eviction rates signal the working set exceeds cache capacity.
- [ ] **Backend load correlates with hit rate** -- If backend load does not drop when the cache is working, the cache is not protecting what it should.

Source: [Fundamentals of Software Caching](https://jeffbailey.us/blog/2025/12/24/fundamentals-of-software-caching/)

---

## 4. Scalability Patterns

### Stateless Design
- [ ] **No in-process session state** -- Session data is stored in an external store (Redis, database), not in server memory. Any instance can handle any request.
- [ ] **No local file storage for shared data** -- Files used across requests are stored in object storage or a shared filesystem, not local disk.
- [ ] **Configuration is externalized** -- Config comes from environment variables, config services, or mounted secrets, not hardcoded or local files that differ per instance.
- [ ] **Instances are disposable** -- Any instance can be killed and replaced without data loss or user impact.

### Horizontal Readiness
- [ ] **Load balancer compatible** -- Services work behind a load balancer with no sticky session requirements (or sticky sessions are a conscious, documented choice).
- [ ] **Independent scaling of components** -- Read-heavy services scale separately from write-heavy services. Database reads scale via replicas.
- [ ] **No global locks or single-threaded bottlenecks** -- Shared locks, global counters, or single-queue consumers limit throughput regardless of instance count.
- [ ] **Coordination overhead is accounted for** -- Adding 10x instances does not yield 10x capacity. Measure actual throughput gain per instance added.

### Bottleneck Identification
- [ ] **The current bottleneck is identified** -- Is it CPU, memory, I/O, database, network, or a downstream service? Measure all components under load.
- [ ] **Scaling targets the bottleneck** -- Adding web servers when the database is the bottleneck wastes resources. Scale the limiting component.
- [ ] **Bottleneck shifts are anticipated** -- After scaling one component, another becomes the limit. Plan for the next bottleneck.

### Resilience Under Load
- [ ] **Timeouts on all external calls** -- Every HTTP call, database query, and cache lookup has a bounded timeout.
- [ ] **Retries with exponential backoff** -- Retries do not hammer failing services. Backoff with jitter prevents thundering herds.
- [ ] **Circuit breakers on critical dependencies** -- When a dependency fails, stop calling it temporarily instead of queuing failures.
- [ ] **Backpressure mechanisms** -- When the system is overloaded, it rejects or delays new work instead of accepting unbounded queues.
- [ ] **Graceful degradation** -- The system returns partial results or falls back to cached data when dependencies are slow.

Source: [Fundamentals of Software Scalability](https://jeffbailey.us/blog/2025/12/22/fundamentals-of-software-scalability/), [Fundamentals of Software Performance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-performance/)

---

## 5. Data Structure Fitness

### Right Structure for Access Patterns
- [ ] **Can you name the data structure?** -- If you cannot name it (array, hash map, tree, graph, or a known variant), the design is ad hoc and harder to reason about.
- [ ] **Lookups use hash maps** -- Key-based access should be O(1) average, not O(n) list scans.
- [ ] **Ordered data uses sorted structures** -- If you need sorted iteration, use a structure that maintains order instead of sorting a hash map after the fact.
- [ ] **Hierarchical data uses trees** -- Parent-child relationships stored in flat arrays force O(n) scans to find children.
- [ ] **Relationship-heavy data uses graphs** -- When queries are about connections and traversal depth, graph structures (or graph databases) remove join-chain friction.

### Safeguards
- [ ] **Every collection has a size limit** -- Capacity caps, eviction policies, or max-depth checks prevent unbounded growth.
- [ ] **Traversals track visited nodes** -- Graph and tree traversals use a visited set to prevent infinite loops on cycles.
- [ ] **Recursion has depth limits** -- Recursive processing on user-generated data has explicit depth bounds.
- [ ] **Structure sizes are instrumented** -- Metrics on collection sizes, growth rates, and eviction counts convert suspicion into evidence.

Source: [Fundamentals of Data Structures](https://jeffbailey.us/blog/2025/12/06/fundamentals-of-data-structures/), [Fundamentals of Algorithms](https://jeffbailey.us/blog/2025/12/04/fundamentals-of-algorithms/)

---

## 6. Resource and Processing Efficiency

### Compute
- [ ] **Workload matches processing model** -- Sequential logic on CPUs, parallel data processing on GPUs. Do not force parallel hardware on branchy sequential code.
- [ ] **No busy-waiting** -- Polling loops should have sleep intervals or use event-driven patterns.
- [ ] **Background work is throttled** -- Background jobs have concurrency limits and do not compete with request-serving work.

### Memory
- [ ] **Large payloads are streamed** -- Responses and request bodies over a threshold are streamed, not fully buffered in memory.
- [ ] **Object lifetimes are bounded** -- Temporary objects created per request are garbage-collected promptly. Long-lived objects have explicit cleanup.
- [ ] **Memory growth is monitored** -- Heap and RSS metrics are tracked over time to catch leaks.

### I/O and Network
- [ ] **Batch network calls** -- Multiple small requests to the same service are batched into fewer larger requests.
- [ ] **Compression on large payloads** -- Responses over a threshold use gzip or similar compression.
- [ ] **Connection reuse** -- HTTP keep-alive, connection pooling, and persistent connections reduce handshake overhead.
- [ ] **Data locality** -- Frequently communicating services are co-located to reduce network latency.

Source: [Fundamentals of Computer Processing](https://jeffbailey.us/blog/2025/12/11/fundamentals-of-computer-processing/), [Fundamentals of Software Performance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-performance/)

---

## 7. Data Pipeline Efficiency

### Processing Strategy
- [ ] **Incremental over full reload** -- Use change data capture (CDC) or timestamp-based incremental loads instead of reprocessing entire datasets.
- [ ] **Batch vs streaming is a conscious choice** -- Batch for hourly/daily freshness. Streaming for seconds/minutes. Do not add streaming complexity when batch suffices.
- [ ] **Pipeline stages are idempotent** -- Rerunning a stage produces the same result. This enables safe retries and reprocessing.

### Validation and Quality
- [ ] **Validate early** -- Check data types, ranges, completeness, and referential integrity at extraction time, not after loading.
- [ ] **Schema drift detection** -- Monitor source schemas for changes. Alert when fields are added, removed, or change type.
- [ ] **Data quality metrics** -- Track completeness, accuracy, and freshness. Alert when they drop below thresholds.

### Error Handling
- [ ] **Partial failure handling** -- A bad record should not stop the entire pipeline. Use dead-letter queues for unprocessable records.
- [ ] **Retry with limits** -- Transient failures retry with backoff. Permanent failures route to dead-letter handling.
- [ ] **Pipeline monitoring** -- Processing time, throughput, error rate, and data freshness are tracked and alerted on.

Source: [Fundamentals of Data Engineering](https://jeffbailey.us/blog/2025/11/22/fundamentals-of-data-engineering/)

---

## Quick Reference: The Five Most Common Performance Problems

1. **N+1 queries** -- A database query inside a loop. Fix: batch fetch or JOIN.
2. **Unbounded collections** -- In-memory structures that grow without limits. Fix: capacity caps and eviction.
3. **Missing indexes** -- Full table scans on filtered columns. Fix: add indexes, verify with EXPLAIN.
4. **No caching on repeated work** -- The same expensive computation or query runs on every request. Fix: cache with appropriate TTL.
5. **Synchronous calls on hot paths** -- Blocking on slow downstream services. Fix: timeouts, async processing, circuit breakers.

---

## Source Articles

- [Fundamentals of Software Performance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-performance/)
- [Fundamentals of Software Scalability](https://jeffbailey.us/blog/2025/12/22/fundamentals-of-software-scalability/)
- [Fundamentals of Software Caching](https://jeffbailey.us/blog/2025/12/24/fundamentals-of-software-caching/)
- [Fundamentals of Databases](https://jeffbailey.us/blog/2025/09/24/fundamentals-of-databases/)
- [Fundamentals of Data Engineering](https://jeffbailey.us/blog/2025/11/22/fundamentals-of-data-engineering/)
- [Fundamentals of Data Structures](https://jeffbailey.us/blog/2025/12/06/fundamentals-of-data-structures/)
- [Fundamentals of Algorithms](https://jeffbailey.us/blog/2025/12/04/fundamentals-of-algorithms/)
- [Fundamentals of Computer Processing](https://jeffbailey.us/blog/2025/12/11/fundamentals-of-computer-processing/)
- [Fundamentals of Graph Databases](https://jeffbailey.us/blog/2026/02/14/fundamentals-of-graph-databases/)
