---
name: review-reliability
description: Analyzes code and configuration for production reliability fitness, producing scores (1-10) across observability, availability design, timeout/retry hygiene, CI/CD maturity, incident readiness, capacity planning, and container/deploy hygiene. Use when the user says /review:review-reliability, requests a reliability review, says check observability, asks if the system is production ready, wants a monitoring setup review, asks about CI/CD pipeline quality, or wants an operational readiness assessment. Only reports findings with confidence >= 7/10.
---

# Reliability Fitness Review

Analyze the codebase (or specified files/modules) for production reliability fitness. Identify gaps in observability, fault tolerance, deployment safety, and operational readiness using evidence from the code and configuration.

## Workflow

1. **Map service boundaries** -- Use Grep/Glob to find HTTP clients, gRPC stubs, database connectors, message queue producers/consumers, and external API calls. These are the boundaries where reliability patterns must exist.

2. **Audit observability instrumentation** -- Search for logging frameworks, metrics libraries (Prometheus, StatsD, OpenTelemetry, Datadog), structured log calls, distributed tracing setup (trace ID propagation, span creation), and dashboard/alert definitions. Check whether the golden signals (latency, traffic, errors, saturation) are covered.

3. **Evaluate availability design** -- Look for redundancy configuration (multiple replicas, multi-AZ deployments), health check endpoints (liveness, readiness), graceful shutdown handlers (SIGTERM), circuit breaker implementations, and fallback/degradation paths for non-critical features.

4. **Check timeout and retry hygiene** -- Find all outbound network calls (HTTP, gRPC, database, cache, message queue). Verify each has explicit timeouts (connection, read, write). Check retry logic for exponential backoff with jitter. Verify timeout layering: child timeouts must be shorter than parent timeouts. Look for circuit breaker patterns on critical dependencies.

5. **Assess CI/CD maturity** -- Examine pipeline configuration files (GitHub Actions, GitLab CI, Jenkinsfile, CircleCI). Check for automated tests in pipeline, deployment gates, rollback mechanisms, blue-green or canary deployment configuration, feature flags, and artifact versioning.

6. **Evaluate incident readiness** -- Search for runbooks, on-call configuration, alert definitions with severity levels and runbook links, postmortem templates, status page integration, and escalation paths. Check whether alerts are symptom-based (error rate, latency) rather than cause-based (CPU, disk).

7. **Review capacity planning** -- Look for auto-scaling configuration, resource limits and requests (CPU, memory), load testing scripts or configuration, connection pool sizing, queue depth limits, and rate limiting configuration. Check whether peak demand patterns are accounted for.

8. **Inspect container and deployment hygiene** -- Check Dockerfiles for minimal base images, non-root users, multi-stage builds, health check instructions, and proper signal handling. Review Kubernetes manifests or deployment configs for resource limits, pod disruption budgets, anti-affinity rules, and rolling update parameters.

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

- **CRITICAL** -- Directly causes outages or data loss under normal conditions. No health checks, no graceful shutdown, single point of failure on critical path, no monitoring of production systems.
- **HIGH** -- Causes outages or degraded service under realistic conditions. Missing timeouts on external calls, no circuit breakers on failing dependencies, no rollback capability, no alerting on error rate spikes.
- **MEDIUM** -- Reduces reliability under specific conditions. Missing retry backoff, incomplete observability coverage, no capacity planning, deployment without smoke tests.
- **LOW** -- Defense-in-depth improvements. Additional metrics coverage, improved alert tuning, documentation of runbooks, container image optimization.

## Scoring Dimensions (1-10 each)

Evaluate and score each dimension with evidence from the code.

### 1. Observability

What to check:
- Structured logging with consistent fields (timestamp, level, service, trace_id, user context)
- Metrics emission covering the golden signals: latency (histograms with percentiles), traffic (request rate counters), errors (error rate counters by type/status), saturation (resource utilization gauges)
- Distributed tracing setup with trace context propagation across service boundaries
- Dashboard definitions or configuration for operational visibility
- Alert definitions that target user-visible symptoms (P95 latency + error rate) rather than low-level causes (CPU usage alone)
- Log levels used appropriately (ERROR for failures, WARN for degraded, INFO for business events, DEBUG for development)
- Correlation IDs or request IDs threaded through log entries for request tracing

What good looks like (8-10):
- Structured JSON logging with consistent fields across all services
- Golden signals instrumented at every service boundary (latency histograms, error counters, traffic counters, saturation gauges)
- OpenTelemetry or equivalent tracing with automatic context propagation
- Alerts combine multiple signals (latency AND error rate) with appropriate time windows
- Dashboards exist for SLO tracking and error budget burn rate
- Log sampling strategy for high-volume paths to control costs

What bad looks like (1-3):
- Unstructured print/println statements instead of a logging framework
- No metrics emission or only basic counters without histograms
- No distributed tracing; debugging cross-service issues requires manual log correlation
- Alerts on low-level metrics only (CPU > 80%) with no user-visible symptom alerts
- No correlation IDs; impossible to trace a request across services
- No dashboards; system health requires SSH and manual log inspection

### 2. Availability Design

What to check:
- Health check endpoints: liveness (is the process running?) and readiness (can it serve traffic?) implemented separately
- Graceful shutdown handling (SIGTERM handler that drains in-flight requests before exiting)
- Redundancy configuration (multiple replicas, multi-AZ/region spread)
- Load balancer configuration with health check integration
- Graceful degradation paths for non-critical features (fallback to cached data, static defaults, feature disabling)
- Single points of failure identification (single database instance, single cache, single queue)
- Failover mechanisms (database replica promotion, DNS failover, multi-region routing)
- Error budget and SLO definitions in configuration or documentation

What good looks like (8-10):
- Separate liveness and readiness probes that check actual dependency health
- SIGTERM handler that stops accepting new requests and drains in-flight work with a bounded timeout
- Multiple replicas with anti-affinity across failure domains
- Non-critical features degrade gracefully (serve cached data, hide section, return defaults)
- SLOs defined with error budget policies documented
- No single points of failure for critical path components

What bad looks like (1-3):
- No health check endpoints or only TCP port checks
- Process killed with SIGKILL; in-flight requests are dropped
- Single instance deployment with no redundancy
- Any dependency failure causes complete service outage
- No SLOs or availability targets defined
- No graceful degradation; all features treated as equally critical

### 3. Timeout/Retry Hygiene

What to check:
- Every outbound call (HTTP, gRPC, database, cache, queue) has explicit timeout configuration
- Separate connection timeout and read/write timeout where supported
- Timeout values based on dependency P99 or SLO (not arbitrary large values like 60s or 300s)
- Timeout layering: child service timeouts shorter than parent service timeouts
- Retry logic uses exponential backoff with jitter (not immediate retry)
- Retry budget or limit to prevent retry storms
- Circuit breaker pattern on dependencies that can fail (open after threshold, half-open to test, close on recovery)
- Idempotency keys for retried write operations to prevent duplicates
- Overall request deadline/budget that propagates through the call chain

What good looks like (8-10):
- All HTTP clients configured with explicit connect_timeout and read_timeout
- Database connection pool has connect, query, and idle timeouts configured
- Retry logic with exponential backoff (e.g., 1s, 2s, 4s) plus random jitter
- Circuit breakers on external API calls with configurable thresholds
- Child timeouts are demonstrably shorter than parent timeouts
- Idempotency keys on payment, order, or state-changing retry paths
- Timeout values are configurable via environment variables, not hardcoded

What bad looks like (1-3):
- HTTP calls with no timeout (uses library default which may be infinite)
- Database queries with no statement timeout; a slow query blocks the connection pool
- Immediate retries without backoff (for i in range(3): call_service())
- No circuit breakers; failing services are called on every request
- Child service timeout exceeds parent timeout (causes confusing cascading failures)
- Hardcoded timeout values buried in code with no way to tune in production

### 4. CI/CD Maturity

What to check:
- Pipeline configuration exists and runs automatically on code changes
- Automated test suites run in the pipeline (unit, integration, end-to-end)
- Build speed: whether pipelines use caching, parallelism, incremental builds
- Deployment automation: one-command or zero-touch deployment to production
- Deployment strategy: blue-green, canary, rolling update (not direct replacement)
- Rollback mechanism: ability to revert to a previous version quickly
- Artifact versioning: immutable, versioned build artifacts stored in a registry
- Feature flags for decoupling deploy from release
- Deployment gates: smoke tests or health checks that run after deploy before serving traffic
- Pipeline-as-code: pipeline configuration is versioned alongside application code
- Environment parity: staging mirrors production configuration

What good looks like (8-10):
- Pipeline runs on every commit with unit tests, integration tests, and linting
- Builds complete in under 10 minutes with caching and parallel test execution
- Canary or blue-green deployment with automated rollback on error rate spike
- Immutable versioned artifacts (Docker images with SHA tags, not :latest)
- Feature flags decouple deployment from feature activation
- Staging environment mirrors production; acceptance tests run before promotion
- Pipeline failures block merges

What bad looks like (1-3):
- No CI pipeline; builds and tests are run manually
- Deployment is a manual SSH-and-restart process
- No rollback plan; rolling forward is the only option
- Artifacts tagged as :latest with no version tracking
- No automated tests in the pipeline
- Direct deployment to production with no staging or smoke tests
- Pipeline takes over 30 minutes with no caching

### 5. Incident Readiness

What to check:
- Alert definitions with severity levels (critical, high, medium, low)
- Alerts target symptoms (error rate, latency, availability) not just causes (CPU, memory)
- Every alert has a linked runbook or at least a description of what to investigate
- On-call rotation configuration or escalation path documented
- Runbooks exist for common failure scenarios (database down, dependency timeout, high error rate)
- Postmortem template or process documented
- Status page integration for external communication
- Incident communication channel configuration (Slack channel, PagerDuty)
- Synthetic monitoring or health check probes from external vantage points

What good looks like (8-10):
- Alerts use multi-signal conditions (error rate > 5% AND P95 latency > 500ms for 5 minutes)
- Every alert links to a runbook with diagnosis steps, resolution steps, and escalation criteria
- On-call rotation with clear escalation paths and reasonable shift lengths
- Postmortem process documented with blame-free template
- Synthetic monitoring verifies critical user journeys from external locations
- Status page updated automatically or via integration during incidents

What bad looks like (1-3):
- No alerting configured; problems discovered when users complain
- Alerts fire on single metrics (CPU > 80%) without user-visible context
- No runbooks; responders must guess at diagnosis and resolution
- No on-call rotation; incidents depend on whoever happens to be around
- No postmortem process; same incidents recur
- No synthetic monitoring; failures detected only by real user impact

### 6. Capacity Planning

What to check:
- Resource limits and requests defined (CPU, memory) in deployment configuration
- Auto-scaling configuration with appropriate metrics triggers (CPU, request rate, queue depth)
- Connection pool sizing configured to match downstream capacity
- Rate limiting on API endpoints to prevent overload
- Load testing configuration or scripts (k6, locust, JMeter, gatling)
- Queue depth limits and dead-letter queue configuration
- Database connection limits aligned with pool sizes and replica count
- Headroom: current utilization versus configured limits (is there room for traffic spikes?)
- Peak demand patterns identified and planned for (seasonal, event-driven)

What good looks like (8-10):
- CPU and memory limits set on all containers based on measured usage
- Horizontal pod autoscaler (or equivalent) with sensible thresholds and cooldown
- Connection pools sized to downstream capacity, not left at defaults
- Rate limiting protects endpoints from traffic spikes and abuse
- Load tests run regularly and results track capacity trends
- Queue consumers scale with depth; dead-letter queues capture failures
- 20-30% headroom maintained above normal peak traffic

What bad looks like (1-3):
- No resource limits; containers can consume unlimited memory until node OOM
- No auto-scaling; capacity is manually adjusted after outages
- Connection pool left at framework defaults (often too small or too large)
- No rate limiting; any traffic spike hits the backend directly
- No load testing; actual capacity limits are unknown
- No dead-letter queues; failed messages are lost silently

### 7. Container/Deploy Hygiene

What to check:
- Dockerfile uses a minimal base image (distroless, alpine, or slim variants)
- Multi-stage builds to keep production images small and free of build tools
- Non-root user in the container (USER instruction or securityContext)
- HEALTHCHECK instruction in Dockerfile or health check in orchestrator config
- Signal handling: application responds to SIGTERM for graceful shutdown
- .dockerignore excludes unnecessary files (node_modules, .git, tests, docs)
- Image scanning for vulnerabilities in CI pipeline
- Kubernetes/orchestrator config includes: resource limits, readiness/liveness probes, pod disruption budgets, rolling update strategy with maxUnavailable/maxSurge, anti-affinity to spread across nodes/zones
- Secrets management (not hardcoded in images or environment variable definitions in plain text)
- DNS and service discovery configuration for inter-service communication
- TLS configuration for service-to-service and external communication
- Network policies to restrict traffic between services

What good looks like (8-10):
- Minimal base image with multi-stage build; production image under 200MB
- Non-root user with read-only root filesystem
- SIGTERM handled properly with connection draining
- Image scanned for CVEs in CI; builds fail on critical vulnerabilities
- Pod disruption budget prevents all replicas from being evicted simultaneously
- Rolling update with maxUnavailable=0 for zero-downtime deployments
- Secrets injected via secrets manager or mounted volumes, not in environment definitions
- TLS for all inter-service communication; certificates rotated automatically
- Network policies restrict ingress and egress to necessary paths only

What bad looks like (1-3):
- Large base image (ubuntu:latest) with build tools in production
- Running as root with writable filesystem
- No SIGTERM handling; processes killed abruptly
- No image scanning; known vulnerabilities ship to production
- No pod disruption budget; rolling updates can take down all replicas
- Secrets in plaintext environment variables or committed to version control
- No TLS between services; traffic is unencrypted on the internal network
- No network policies; any service can reach any other service

## Output Format

Write the report to `docs/reliability-review.md` with this structure:

```markdown
# Reliability Fitness Review

## Summary

Overall fitness score: X.X / 10 (average of dimensions)

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Observability | X/10 | ... |
| Availability Design | X/10 | ... |
| Timeout/Retry Hygiene | X/10 | ... |
| CI/CD Maturity | X/10 | ... |
| Incident Readiness | X/10 | ... |
| Capacity Planning | X/10 | ... |
| Container/Deploy Hygiene | X/10 | ... |

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

### Observability (X/10)
- Evidence: file:line references
- Issues found
- Recommendations

(repeat for each dimension)

## Top 5 Action Items (by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...

## Checklist Reference

See references/checklist.md for the full reliability checklist.

## Reference

Based on guidance from https://jeffbailey.us/categories/fundamentals/
```

Refer to the reliability checklist at `review-reliability/references/checklist.md` for detailed checks within each dimension.
