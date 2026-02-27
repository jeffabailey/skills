# Reliability Fitness Checklist

Detailed checklist for reviewing code and configuration against production reliability fundamentals. Use alongside the review-reliability skill to systematically evaluate each dimension.

---

## 1. Observability

### Logging
- [ ] **Structured logging** -- Log entries are JSON or key-value format, not free-form text strings. Structured logs enable filtering, aggregation, and correlation across services.
- [ ] **Consistent fields across services** -- Every log entry includes timestamp, log level, service name, and request/trace ID. Missing fields break cross-service correlation.
- [ ] **Appropriate log levels** -- ERROR for failures requiring action, WARN for degraded states, INFO for significant business events, DEBUG for development. Misused levels hide real problems in noise.
- [ ] **Request context in logs** -- User ID, request ID, or trace ID included in log entries so that a single user journey can be traced through logs.
- [ ] **No sensitive data in logs** -- Passwords, tokens, PII, and credit card numbers are redacted or excluded from log output.
- [ ] **Log sampling on high-volume paths** -- High-frequency endpoints log a sample of requests to control storage costs without losing visibility into patterns.

### Metrics (Golden Signals)
- [ ] **Latency histograms** -- Response time tracked as histograms with percentile buckets (P50, P95, P99), not just averages. Averages hide tail latency that affects real users.
- [ ] **Traffic counters** -- Request rate tracked per endpoint and per service. Traffic volume is the denominator for error rate calculations.
- [ ] **Error rate counters** -- Errors counted by type (4xx, 5xx, timeout, circuit open) and by endpoint. A single global error counter hides per-endpoint problems.
- [ ] **Saturation gauges** -- CPU utilization, memory usage, connection pool utilization, queue depth, and thread pool usage tracked as gauges. Saturation predicts capacity exhaustion before it causes outages.
- [ ] **Business metrics** -- Key business transactions (orders placed, payments processed, logins completed) tracked alongside technical metrics. Business metrics connect technical health to user impact.

### Distributed Tracing
- [ ] **Trace context propagation** -- Trace ID and span ID propagated across HTTP headers (W3C traceparent or equivalent) and message queue metadata. Broken propagation creates orphaned traces.
- [ ] **Spans at service boundaries** -- Spans created for inbound requests, outbound HTTP/gRPC calls, database queries, and cache operations. Missing spans create gaps in the trace.
- [ ] **Span attributes** -- Spans include HTTP method, status code, database query type, and error details. Sparse attributes make traces less useful for debugging.
- [ ] **Sampling strategy** -- Tail-based sampling retains error and slow traces. Head-based sampling with a reasonable rate (1-10%) for normal traffic. Over-sampling inflates costs; under-sampling loses important traces.

### Dashboards and Alerts
- [ ] **SLO dashboard** -- Current SLI values displayed against SLO targets with clear pass/fail indicators and error budget remaining.
- [ ] **Service health dashboard** -- Golden signals for each service on a single pane: latency P95, error rate, traffic, and saturation.
- [ ] **Alerts on symptoms** -- Alerts fire on user-visible symptoms (error rate > threshold AND latency > threshold for N minutes), not on causes alone (CPU > 80%).
- [ ] **Alert severity levels** -- Critical (user-facing outage, page immediately), High (significant degradation, respond within minutes), Medium (partial impact, respond within hours), Low (warning, respond within days).
- [ ] **Runbook links on alerts** -- Every alert includes a link to a runbook or at minimum describes what to check and how to mitigate.
- [ ] **Alert tuning** -- Alerts reviewed periodically; noisy alerts are tuned or removed. Alert fatigue causes real alerts to be ignored.

Source: [Fundamentals of Monitoring and Observability](https://jeffbailey.us/blog/2025/11/16/fundamentals-of-monitoring-and-observability/), [Fundamentals of Metrics](https://jeffbailey.us/blog/2025/11/09/fundamentals-of-metrics/)

---

## 2. Availability Patterns

### Health Checks
- [ ] **Liveness probe** -- Returns 200 if the process is running and not deadlocked. Does not check external dependencies. A liveness failure causes the container to restart.
- [ ] **Readiness probe** -- Returns 200 if the service can accept traffic: database connections are established, caches are warm, startup tasks complete. A readiness failure removes the pod from the load balancer.
- [ ] **Deep health check** -- A separate endpoint (not used by the load balancer) that verifies all dependencies: database connectivity, cache connectivity, downstream service reachability. Used for dashboards and diagnostics.
- [ ] **Health check response time** -- Health checks return within 1-2 seconds. Slow health checks cause false unhealthy signals and load balancer flapping.
- [ ] **Health check interval and threshold** -- Multiple consecutive failures required before marking unhealthy (e.g., 3 failures). A single failure could be transient packet loss.

### Redundancy and Failover
- [ ] **Multiple replicas** -- At least 2 replicas for non-critical services, 3+ for critical services. A single replica means any restart is an outage.
- [ ] **Anti-affinity across failure domains** -- Replicas spread across nodes, availability zones, or regions so a single infrastructure failure does not take all replicas.
- [ ] **Database redundancy** -- Primary with at least one replica for failover. Read replicas for read-heavy workloads. No single-instance databases for production services.
- [ ] **Load balancer health integration** -- Load balancer routes traffic only to healthy instances based on readiness probe results.
- [ ] **Failover tested** -- Failover mechanisms have been tested (kill a replica, fail a database, block a network path) and recovery time is documented.

### Graceful Degradation
- [ ] **Critical vs non-critical features identified** -- The team has explicitly listed which features are critical (must always work) and which can degrade (show cached data, hide section, return defaults).
- [ ] **Fallback to cached data** -- When a data source is slow or unavailable, stale cached data is served instead of returning an error for non-critical features.
- [ ] **Static defaults** -- When personalization or recommendation services fail, generic/popular defaults are returned instead of errors.
- [ ] **Feature flags for degradation** -- Non-critical features can be disabled remotely via feature flags without deploying code.
- [ ] **Circuit breaker fallbacks** -- When a circuit breaker opens on a dependency, the service returns a degraded response (cached data, default, or partial result) instead of an error.

### Graceful Shutdown
- [ ] **SIGTERM handler** -- Application handles SIGTERM by stopping acceptance of new requests and draining in-flight work.
- [ ] **Drain timeout** -- In-flight requests are given a bounded time to complete (e.g., 30 seconds) before the process exits.
- [ ] **Connection cleanup** -- Database connections, cache connections, and file handles are closed during shutdown.
- [ ] **Pre-stop hook** -- In Kubernetes, a preStop hook or readiness probe failure ensures the pod is removed from the service before receiving SIGTERM.

### SLOs and Error Budgets
- [ ] **SLOs defined** -- Availability and latency SLOs defined for each service based on user needs and business impact (e.g., 99.9% availability, P95 latency < 500ms).
- [ ] **SLIs measured** -- Service Level Indicators that feed SLOs are actively measured and tracked (successful request rate, latency percentiles).
- [ ] **Error budget tracked** -- Error budget remaining is visible on dashboards and used to guide deployment risk decisions.
- [ ] **Error budget policy** -- A documented policy specifies actions when the error budget is depleted (freeze deployments, prioritize reliability).
- [ ] **SLO review cadence** -- SLOs are reviewed quarterly or when user needs change. Outdated SLOs give false confidence.

Source: [Fundamentals of Software Availability](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-software-availability/), [Fundamentals of Reliability Engineering](https://jeffbailey.us/blog/2025/11/17/fundamentals-of-reliability-engineering/)

---

## 3. Timeout Configuration

### Connection Timeouts
- [ ] **HTTP client connection timeout** -- Every HTTP client has an explicit connection timeout (typically 1-5 seconds). No connection attempt should block indefinitely.
- [ ] **Database connection timeout** -- Database connection pool has a connect timeout. A slow or unreachable database should fail the connection attempt in seconds, not minutes.
- [ ] **Cache connection timeout** -- Redis, Memcached, or other cache clients have explicit connection timeouts.
- [ ] **Message queue connection timeout** -- Kafka, RabbitMQ, or SQS clients have bounded connection timeouts.

### Read/Write Timeouts
- [ ] **HTTP read timeout** -- Maximum time to wait for a response body after connecting. Set based on dependency P99 plus headroom (e.g., 1.5x P99).
- [ ] **Database query timeout** -- Statement-level timeout prevents long-running queries from holding connections. Separate from connection timeout.
- [ ] **Cache operation timeout** -- Read and write operations on cache have explicit timeouts to prevent blocking on a slow cache.
- [ ] **Overall request timeout** -- A total timeout covering the entire request lifecycle (connection + send + receive) exists in addition to per-phase timeouts.

### Timeout Layering
- [ ] **Child timeout < parent timeout** -- Downstream service timeouts are shorter than the calling service timeout. This ensures the child fails first, allowing the parent to handle the failure within its own budget.
- [ ] **Timeout budget propagation** -- In multi-hop call chains, the remaining time budget is propagated so downstream services know how long they have.
- [ ] **No default/infinite timeouts in production** -- Every outbound call has an explicit timeout. Library defaults (often 0/infinite) are overridden.
- [ ] **Timeouts are configurable** -- Timeout values are in configuration (environment variables, config files), not hardcoded. This enables tuning in production without code changes.

### Timeout Values from Data
- [ ] **Based on P99 or SLO** -- Timeout values are set based on measured dependency latency percentiles (P99, P99.9) or published SLOs, not guesses.
- [ ] **Monitored timeout rate** -- The rate of timeout errors is tracked per dependency. Rising timeout rates signal dependency degradation.
- [ ] **Different timeouts per dependency** -- Fast dependencies (cache: 100ms) have short timeouts. Slow dependencies (report API: 10s) have longer ones. One global timeout for all calls is a code smell.

Source: [Fundamentals of Timeouts](https://jeffbailey.us/blog/2026/02/01/fundamentals-of-timeouts/), [Fundamentals of Software Availability](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-software-availability/)

---

## 4. Retry Patterns

### Exponential Backoff
- [ ] **Backoff between retries** -- Retry delay increases with each attempt (e.g., 1s, 2s, 4s). Immediate retries (no delay) hammer a failing dependency and worsen outages.
- [ ] **Jitter on retry delay** -- Random jitter (e.g., +/- 50%) added to backoff delays. Without jitter, all clients retry at the same time (thundering herd) when a dependency recovers.
- [ ] **Maximum retry count** -- Retries are bounded (e.g., 3 attempts max). Unbounded retries can loop indefinitely.
- [ ] **Total retry budget** -- Total time for all retry attempts fits within the parent timeout. Three retries of 10 seconds each (30s total) must not exceed a 15-second parent timeout.

### Circuit Breakers
- [ ] **Circuit breaker on external dependencies** -- Dependencies that can fail have a circuit breaker that opens after a configurable error threshold.
- [ ] **Open state returns fallback** -- When the circuit is open, calls fail fast and return a fallback (cached data, default, error) instead of waiting for a timeout.
- [ ] **Half-open state tests recovery** -- After a cooldown period, the circuit breaker allows a test request through. If it succeeds, the circuit closes. If it fails, it stays open.
- [ ] **Circuit breaker metrics** -- Circuit state transitions (closed/open/half-open) and trip counts are instrumented and visible on dashboards.
- [ ] **Per-dependency circuit breakers** -- Each dependency has its own circuit breaker. A single global circuit breaker hides which dependency is failing.

### Idempotency
- [ ] **Idempotency keys on write retries** -- Retried write operations (payments, orders, state changes) include an idempotency key to prevent duplicate processing.
- [ ] **Safe-to-retry classification** -- The code distinguishes retryable errors (timeout, 503, connection reset) from non-retryable errors (400, 401, 404). Non-retryable errors are not retried.

Source: [Fundamentals of Timeouts](https://jeffbailey.us/blog/2026/02/01/fundamentals-of-timeouts/), [Fundamentals of Software Availability](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-software-availability/)

---

## 5. CI/CD Pipeline Checks

### Continuous Integration
- [ ] **Pipeline runs on every commit** -- Every push or pull request triggers a build and test run. Skipping CI for "small changes" is how bugs reach production.
- [ ] **Automated test suite in pipeline** -- Unit tests, integration tests, and linting run automatically. Manual testing does not scale.
- [ ] **Build speed under 10 minutes** -- Slow builds discourage frequent commits. Use caching, parallelism, and incremental builds.
- [ ] **Failures block merges** -- Pull requests cannot be merged if CI fails. Bypassing CI defeats its purpose.
- [ ] **Deterministic builds** -- Same code produces the same artifact. No time-dependent or random behavior in builds.
- [ ] **Flaky test management** -- Flaky tests are tracked, prioritized for fixing, and quarantined if they cannot be fixed immediately. Flaky tests erode CI trust.

### Continuous Delivery / Deployment
- [ ] **One-command deployment** -- Deploying to any environment is a single command or button click, not a multi-step manual process.
- [ ] **Immutable artifacts** -- Built artifacts (Docker images, binaries) are versioned with commit SHA or semantic version, not :latest. The same artifact deploys to staging and production.
- [ ] **Staging environment mirrors production** -- Same OS, dependencies, configuration structure, and resource proportions. Environment drift causes "works in staging, fails in production" bugs.
- [ ] **Deployment gates** -- Smoke tests or health checks run after deployment and before the new version serves production traffic.
- [ ] **Rollback mechanism** -- A previous version can be deployed within minutes. Rollback has been tested and documented.

### Deployment Strategies
- [ ] **Blue-green or canary deployment** -- New versions are deployed alongside old versions. Traffic is shifted gradually (canary: 5% -> 25% -> 100%) or switched atomically (blue-green). Direct replacement causes downtime.
- [ ] **Automated rollback on error spike** -- If error rate or latency exceeds a threshold after deployment, the system automatically or semi-automatically rolls back.
- [ ] **Feature flags** -- New features are deployed behind flags and enabled gradually. Feature flags decouple deployment from release and provide instant rollback for features.
- [ ] **Database migration safety** -- Schema changes are backward-compatible (add column, not rename). Migrations run before code deployment so old code works with the new schema and rollback is safe.

### Pipeline Security
- [ ] **Dependency scanning** -- Dependencies are scanned for known vulnerabilities in the CI pipeline. Critical CVEs block builds.
- [ ] **Image scanning** -- Container images are scanned for vulnerabilities before being pushed to a registry.
- [ ] **Secrets not in pipeline logs** -- Secrets are masked in CI output. Pipeline logs do not contain credentials, tokens, or API keys.

Source: [Fundamentals of CI/CD and Release Engineering](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-ci-cd-and-release-engineering/), [Fundamentals of Software Development Operations](https://jeffbailey.us/blog/2026/01/13/fundamentals-of-software-development-operations/)

---

## 6. Incident Management Readiness

### Alert Design
- [ ] **Symptom-based alerts** -- Alerts fire on user-visible symptoms (error rate, latency P95, availability) not on causes alone (CPU, memory, disk). High CPU might be normal under load.
- [ ] **Multi-signal conditions** -- Alerts combine signals: "error_rate > 5% AND latency_p95 > 500ms for 5 minutes." Single-metric alerts cause false positives.
- [ ] **Severity levels defined** -- Critical (page immediately), High (respond within minutes), Medium (respond within hours), Low (next business day).
- [ ] **Time windows prevent flapping** -- Alerts require sustained conditions (5+ minutes), not single-sample spikes. Brief transients should not page on-call.
- [ ] **Alert routing** -- Critical alerts go to PagerDuty or equivalent with phone/SMS. Low alerts go to a Slack channel or email.
- [ ] **No alert without action** -- Every alert has a documented action. Alerts that cannot be acted on create noise and should be removed.

### Runbooks
- [ ] **Runbook per common failure mode** -- At minimum: database connection exhaustion, high error rate, dependency timeout, out of memory, deployment failure.
- [ ] **Runbook structure** -- Each runbook includes: symptoms, diagnosis steps (specific commands or dashboard links), resolution steps (ordered from least disruptive), verification (how to confirm the fix worked), escalation path (who to contact if resolution fails).
- [ ] **Runbooks tested** -- Runbooks are periodically tested during low-stress periods or game days. Untested runbooks may contain outdated steps.
- [ ] **Runbooks maintained** -- Runbooks are updated after incidents that reveal gaps or outdated information.

### On-Call and Escalation
- [ ] **On-call rotation defined** -- Clear rotation schedule with reasonable shift lengths (no single person always on call).
- [ ] **Escalation path documented** -- If the primary responder cannot resolve within a defined time, the issue escalates to a secondary responder or team lead.
- [ ] **Communication channel** -- Dedicated incident channel (Slack, Teams) created automatically or by convention during incidents.
- [ ] **Status page** -- External-facing status page for communicating outages to users, updated during incidents.

### Postmortem Process
- [ ] **Postmortem within 48 hours** -- Conducted while details are fresh. Delayed postmortems lose critical context.
- [ ] **Blame-free format** -- Focus on systems and processes, not individuals. Blame prevents honest discussion of root causes.
- [ ] **Action items with owners and deadlines** -- Every postmortem produces concrete improvements assigned to specific people with due dates.
- [ ] **Postmortems for small incidents too** -- Minor incidents reveal patterns that cause major outages. Do not skip postmortems because the outage was "small."
- [ ] **Postmortem review cadence** -- Action items are tracked and reviewed; incomplete items are escalated.

### Proactive Monitoring
- [ ] **Leading indicators monitored** -- Resource utilization trends, connection pool usage, error rate trends, and queue depth growth. These predict incidents before they become outages.
- [ ] **Synthetic monitoring** -- Automated probes simulate critical user journeys (login, checkout, API call) from external locations. Detects problems before real users are affected.
- [ ] **Dependency monitoring** -- External dependencies (third-party APIs, cloud services, CDN) are monitored separately so their failures are distinguished from your own.

Source: [Fundamentals of Incident Management](https://jeffbailey.us/blog/2025/11/16/fundamentals-of-incident-management/), [Fundamentals of Reliability Engineering](https://jeffbailey.us/blog/2025/11/17/fundamentals-of-reliability-engineering/)

---

## 7. Capacity Planning

### Resource Limits and Sizing
- [ ] **CPU limits set** -- Container CPU limits defined based on measured usage under load, not arbitrary values. Missing limits allow a single container to starve others on the node.
- [ ] **Memory limits set** -- Container memory limits defined. Missing limits risk OOM-killing other containers on the same node.
- [ ] **CPU requests match typical usage** -- Requests (guaranteed allocation) set to typical usage. Requests much higher than usage waste cluster resources.
- [ ] **Connection pool sizing** -- Database, cache, and HTTP connection pools sized based on downstream capacity and expected concurrency. Default pool sizes are often wrong.
- [ ] **Thread/worker pool sizing** -- Worker pools sized to match available CPU and expected concurrency. Too few workers cause queuing; too many cause context-switching overhead.

### Auto-Scaling
- [ ] **Horizontal auto-scaling configured** -- Auto-scaler triggers on CPU utilization, request rate, or queue depth. Manual scaling cannot respond to sudden traffic spikes.
- [ ] **Scale-up threshold and cooldown** -- Scale-up triggers quickly (1-2 minutes of high utilization). Cooldown prevents thrashing (wait 5-10 minutes before scaling down).
- [ ] **Minimum and maximum replica counts** -- Minimum replicas ensure baseline availability. Maximum replicas prevent runaway cost.
- [ ] **Scale metrics match bottleneck** -- Auto-scaling triggers based on the actual bottleneck (CPU for compute-bound, queue depth for event-driven). Scaling on the wrong metric wastes resources.

### Load Testing
- [ ] **Load testing exists** -- Load tests simulate expected and peak traffic. Without load testing, actual capacity limits are unknown.
- [ ] **Load test includes peak scenarios** -- Tests cover normal load, peak load (e.g., 3x normal), and stress load (find the breaking point).
- [ ] **Load tests run regularly** -- Load tests run after significant changes to detect capacity regressions. Annual load tests miss regressions between runs.
- [ ] **Load test results tracked** -- Results are stored and compared over time. Capacity trends show whether the system is gaining or losing headroom.

### Rate Limiting
- [ ] **API rate limiting** -- Public and internal API endpoints have rate limits to prevent abuse and protect backend capacity.
- [ ] **Rate limit by caller** -- Rate limits applied per API key, user, or IP, not just globally. Global limits let one bad actor consume all capacity.
- [ ] **Rate limit responses** -- Rate-limited requests return HTTP 429 with a Retry-After header so callers can back off.
- [ ] **Rate limit monitoring** -- Rate limit triggers are tracked to identify callers who consistently hit limits and to validate that limits are set correctly.

### Queue and Backpressure
- [ ] **Queue depth limits** -- Message queues have maximum depth configured. Unbounded queues consume memory until the broker crashes.
- [ ] **Dead-letter queues** -- Failed messages are routed to a dead-letter queue for inspection and reprocessing, not silently dropped or retried infinitely.
- [ ] **Backpressure mechanism** -- When the system is overloaded, it rejects or delays new work (HTTP 503, queue nack) instead of accepting unbounded work that degrades all requests.
- [ ] **Consumer scaling** -- Queue consumers can scale horizontally with queue depth to handle traffic spikes.

Source: [Fundamentals of Capacity Planning](https://jeffbailey.us/blog/2025/12/22/fundamentals-of-capacity-planning/), [Fundamentals of Reliability Engineering](https://jeffbailey.us/blog/2025/11/17/fundamentals-of-reliability-engineering/)

---

## 8. Networking

### DNS
- [ ] **DNS TTL appropriate for the use case** -- Short TTLs (30-60s) for services that need fast failover. Long TTLs (300s+) for stable services to reduce DNS query load.
- [ ] **DNS resolution monitored** -- DNS lookup failures and latency tracked as metrics. DNS failures make every downstream dependency appear unavailable.
- [ ] **Internal DNS for service discovery** -- Services use internal DNS names or service discovery (Consul, Kubernetes DNS), not hardcoded IP addresses that break on infrastructure changes.

### Load Balancing
- [ ] **Load balancer health check integration** -- Load balancer checks service readiness probes and routes only to healthy instances.
- [ ] **Load balancing algorithm appropriate** -- Round-robin for stateless services, least-connections for long-lived connections, weighted for heterogeneous capacity.
- [ ] **Connection draining on removal** -- When an instance is removed from the load balancer, in-flight requests complete before the instance stops receiving traffic.

### TLS
- [ ] **TLS for external traffic** -- All user-facing traffic uses HTTPS. HTTP redirects to HTTPS.
- [ ] **TLS for internal traffic** -- Service-to-service communication uses TLS (mTLS preferred). Unencrypted internal traffic is vulnerable to network-level attacks.
- [ ] **Certificate rotation** -- TLS certificates are rotated automatically before expiry. Expired certificates cause outages.
- [ ] **Certificate chain complete** -- Intermediate certificates are included. Missing intermediates cause failures in clients that do not fetch them automatically.

Source: [Fundamentals of Networking](https://jeffbailey.us/blog/2025/12/13/fundamentals-of-networking/)

---

## 9. Container Hygiene

### Dockerfile Best Practices
- [ ] **Minimal base image** -- Use distroless, alpine, or slim variants. Full OS images (ubuntu:latest, debian:latest) contain unnecessary packages that increase attack surface and image size.
- [ ] **Multi-stage build** -- Build tools, test dependencies, and source code excluded from the production image via multi-stage builds.
- [ ] **Non-root user** -- USER instruction sets a non-root user. Running as root in containers is a security risk.
- [ ] **Read-only root filesystem** -- Container runs with read-only root filesystem where possible. Writable volumes are mounted for specific paths that need writes.
- [ ] **COPY specific files** -- COPY specific files and directories, not COPY . which includes unnecessary files. A .dockerignore file excludes .git, node_modules, tests, docs, and local config.
- [ ] **Pinned base image versions** -- Base images use specific versions or digests (node:20.11-alpine), not :latest which changes unpredictably.
- [ ] **HEALTHCHECK instruction** -- Dockerfile includes a HEALTHCHECK or the orchestrator defines health checks. Without health checks, the orchestrator cannot detect unhealthy containers.

### Orchestrator Configuration
- [ ] **Resource limits and requests** -- CPU and memory limits prevent resource exhaustion. Requests guarantee minimum resources for scheduling.
- [ ] **Readiness and liveness probes** -- Liveness restarts deadlocked containers. Readiness prevents traffic to unready containers. Both are configured with appropriate timeouts and thresholds.
- [ ] **Pod disruption budget** -- PDB prevents all replicas from being evicted simultaneously during node maintenance or cluster operations.
- [ ] **Rolling update strategy** -- maxUnavailable=0 and maxSurge=1 (or equivalent) for zero-downtime rolling deployments.
- [ ] **Anti-affinity rules** -- Replicas spread across nodes and availability zones. All replicas on one node means a node failure is a service outage.
- [ ] **Startup probe for slow-starting apps** -- Applications that take time to initialize use a startup probe with a longer timeout to prevent liveness probe kills during startup.

### Image Security
- [ ] **Vulnerability scanning in CI** -- Images scanned for CVEs before push to registry. Critical/high vulnerabilities block the build.
- [ ] **Base image updates** -- Base images rebuilt regularly (weekly or on CVE advisory) to pick up OS-level security patches.
- [ ] **No secrets in images** -- Secrets (API keys, passwords, certificates) are not baked into the image. They are injected at runtime via secrets manager, mounted volumes, or init containers.
- [ ] **Image signing** -- Production images are signed. Orchestrator verifies signatures before running. Prevents running tampered images.

### Signal Handling and Lifecycle
- [ ] **SIGTERM handled** -- Application traps SIGTERM and performs graceful shutdown (stop accepting, drain, close connections, exit).
- [ ] **Startup and shutdown ordering** -- Dependencies are checked during startup (readiness probe). Connections are closed during shutdown before the process exits.
- [ ] **Pre-stop hook** -- In Kubernetes, a preStop hook (or readiness probe failure) gives the load balancer time to remove the pod before SIGTERM is sent. This prevents requests to a shutting-down pod.

Source: [Fundamentals of Containerization](https://jeffbailey.us/blog/2026/02/01/fundamentals-of-containerization/), [Fundamentals of Software Availability](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-software-availability/)

---

## Quick Reference: The Five Most Common Reliability Problems

1. **No timeouts on outbound calls** -- A slow dependency blocks threads/connections indefinitely, exhausting the pool and crashing the service. Fix: set explicit connection and read timeouts on every outbound call.
2. **No health checks or shallow health checks** -- Load balancer sends traffic to broken instances (TCP-only check), or liveness and readiness are conflated. Fix: implement separate liveness and readiness probes that check real functionality.
3. **No structured observability** -- When an incident happens, the team spends hours grepping unstructured logs across services. Fix: structured logging, golden signal metrics, and distributed tracing.
4. **No graceful degradation** -- A non-critical recommendation service failure takes down the entire checkout flow. Fix: identify critical vs non-critical features and implement fallbacks.
5. **No rollback mechanism** -- A bad deployment requires a forward fix under pressure because there is no fast rollback. Fix: immutable versioned artifacts with tested rollback to the previous version.

---

## Source Articles

- [Fundamentals of Reliability Engineering](https://jeffbailey.us/blog/2025/11/17/fundamentals-of-reliability-engineering/)
- [Fundamentals of Monitoring and Observability](https://jeffbailey.us/blog/2025/11/16/fundamentals-of-monitoring-and-observability/)
- [Fundamentals of Incident Management](https://jeffbailey.us/blog/2025/11/16/fundamentals-of-incident-management/)
- [Fundamentals of Software Availability](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-software-availability/)
- [Fundamentals of CI/CD and Release Engineering](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-ci-cd-and-release-engineering/)
- [Fundamentals of Software Development Operations](https://jeffbailey.us/blog/2026/01/13/fundamentals-of-software-development-operations/)
- [Fundamentals of Timeouts](https://jeffbailey.us/blog/2026/02/01/fundamentals-of-timeouts/)
- [Fundamentals of Capacity Planning](https://jeffbailey.us/blog/2025/12/22/fundamentals-of-capacity-planning/)
- [Fundamentals of Metrics](https://jeffbailey.us/blog/2025/11/09/fundamentals-of-metrics/)
- [Fundamentals of Networking](https://jeffbailey.us/blog/2025/12/13/fundamentals-of-networking/)
- [Fundamentals of Containerization](https://jeffbailey.us/blog/2026/02/01/fundamentals-of-containerization/)
