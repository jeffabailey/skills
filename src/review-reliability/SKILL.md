---
name: review-reliability
description: Analyzes code and configuration for production reliability fitness, producing scores (1-10) across observability, availability design, timeout/retry hygiene, CI/CD maturity, incident readiness, capacity planning, and container/deploy hygiene. Use when the user says /review:review-reliability, requests a reliability review, says check observability, asks if the system is production ready, wants a monitoring setup review, asks about CI/CD pipeline quality, or wants an operational readiness assessment. Only reports findings with confidence >= 7/10.
---

# Reliability Fitness Review

Analyze the codebase (or specified files/modules) for production reliability fitness. Identify gaps in observability, fault tolerance, deployment safety, and operational readiness using evidence from the code and configuration.

Reference: [Fundamentals of Reliability Engineering](https://jeffbailey.us/blog/2025/11/17/fundamentals-of-reliability-engineering/), [Fundamentals of Monitoring and Observability](https://jeffbailey.us/blog/2025/11/16/fundamentals-of-monitoring-and-observability/), [Fundamentals of Software Availability](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-software-availability/), [Fundamentals of Timeouts](https://jeffbailey.us/blog/2026/02/01/fundamentals-of-timeouts/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

For detailed scoring rubrics, severity definitions, what-good-looks-like / what-bad-looks-like criteria, and domain expertise, read `references/wisdom.md` before scoring. That file is auto-generated from:

- [Fundamentals of Reliability Engineering](https://jeffbailey.us/blog/2025/11/17/fundamentals-of-reliability-engineering/)
- [Fundamentals of Monitoring and Observability](https://jeffbailey.us/blog/2025/11/16/fundamentals-of-monitoring-and-observability/)
- [Fundamentals of Software Availability](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-software-availability/)
- [Fundamentals of Timeouts](https://jeffbailey.us/blog/2026/02/01/fundamentals-of-timeouts/)

Use the wisdom reference when evaluating code and assigning dimension scores.

## Workflow

1. **Read domain knowledge** — Read `references/wisdom.md` to load scoring rubrics, thresholds, and severity definitions.

2. **Map service boundaries** — Use Grep/Glob to find HTTP clients, gRPC stubs, database connectors, message queue producers/consumers, and external API calls. These are the boundaries where reliability patterns must exist.

3. **Audit observability instrumentation** — Search for logging frameworks, metrics libraries, structured log calls, distributed tracing setup, and dashboard/alert definitions. Apply the rubrics/thresholds from the wisdom reference.

4. **Evaluate availability design** — Look for redundancy configuration, health check endpoints, graceful shutdown handlers, circuit breaker implementations, and fallback/degradation paths. Apply the rubrics/thresholds from the wisdom reference.

5. **Check timeout and retry hygiene** — Find all outbound network calls. Verify each has explicit timeouts, retry logic with backoff, and timeout layering. Apply the rubrics/thresholds from the wisdom reference.

6. **Assess CI/CD maturity** — Examine pipeline configuration files. Check for automated tests, deployment gates, rollback mechanisms, and deployment strategies. Apply the rubrics/thresholds from the wisdom reference.

7. **Evaluate incident readiness** — Search for runbooks, on-call configuration, alert definitions with severity levels, and postmortem templates. Apply the rubrics/thresholds from the wisdom reference.

8. **Review capacity planning** — Look for auto-scaling configuration, resource limits, load testing scripts, connection pool sizing, and rate limiting. Apply the rubrics/thresholds from the wisdom reference.

9. **Inspect container and deployment hygiene** — Check Dockerfiles for minimal base images, non-root users, multi-stage builds, and proper signal handling. Review orchestrator manifests for resource limits and rolling update parameters. Apply the rubrics/thresholds from the wisdom reference.

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

1. **Observability** — Structured logging, metrics emission covering golden signals, distributed tracing, dashboards, and alerting
2. **Availability Design** — Health checks, graceful shutdown, redundancy, load balancing, graceful degradation, and SLO definitions
3. **Timeout/Retry Hygiene** — Explicit timeouts on all outbound calls, exponential backoff with jitter, circuit breakers, timeout layering, and idempotency
4. **CI/CD Maturity** — Pipeline automation, test coverage in CI, deployment strategies, rollback mechanisms, artifact versioning, and feature flags
5. **Incident Readiness** — Alert definitions, runbooks, on-call rotation, postmortem process, synthetic monitoring, and status page integration
6. **Capacity Planning** — Resource limits, auto-scaling, connection pool sizing, rate limiting, load testing, and headroom planning
7. **Container/Deploy Hygiene** — Minimal base images, multi-stage builds, non-root users, signal handling, image scanning, pod disruption budgets, and secrets management

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

Based on [Fundamentals of Reliability Engineering](https://jeffbailey.us/blog/2025/11/17/fundamentals-of-reliability-engineering/), [Fundamentals of Monitoring and Observability](https://jeffbailey.us/blog/2025/11/16/fundamentals-of-monitoring-and-observability/), [Fundamentals of Software Availability](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-software-availability/), [Fundamentals of Timeouts](https://jeffbailey.us/blog/2026/02/01/fundamentals-of-timeouts/) and guidance from https://jeffbailey.us/categories/fundamentals/
```

Refer to the reliability checklist at `review-reliability/references/checklist.md` for detailed checks within each dimension.
