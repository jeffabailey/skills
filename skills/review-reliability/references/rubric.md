# Reliability Scoring Rubric

Hand-maintained scoring rubric. sync-wisdom does not regenerate this file.

Use this file to assign severities and scores. Use `checklist.md` for what to look at. Anchors are cumulative: a 7-8 meets the 5-6 bar plus its own.

## Severity

| Severity | Definition | Reliability examples |
|----------|------------|----------------------|
| CRITICAL | Will cause an outage or unrecoverable data loss in normal operation, with no mitigation in place. | Production database with no volume or backup, so a container recreate wipes data; outbound call in the request path with no timeout and an unbounded retry loop. |
| HIGH | Likely to cause an outage, a long recovery, or a silent failure under a common failure (one dependency down, one bad deploy). | Single replica of a stateful service with no healthcheck or restart policy; deploy pipeline with no rollback path; PR-gating CI jobs with no `timeout-minutes` (a hang blocks merges for the 6-hour default). |
| MEDIUM | Degrades recovery or detection, or fails under load or rare conditions. | `:latest` or unpinned images and actions; no resource limits on one service; a scheduled CI job with no `timeout-minutes`. |
| LOW | Hygiene gap with small blast radius; fix when nearby. | Healthcheck interval too long; missing `concurrency` group on a docs-only workflow; no `.dockerignore`. |

## Target type and N/A

Decide the target type before scoring. A dimension is N/A only when the target has nothing it could reasonably contain for that dimension. If it should contain something and does not, that absence is a finding and the dimension is scored.

| Dimension | App code | Compose / IaC / k8s | CI-only (workflows, CI scripts) |
|-----------|----------|---------------------|---------------------------------|
| Observability | score | score (logging driver, exporters, log volumes) | N/A |
| Availability Design | score | score (healthchecks, restart, replicas, `depends_on` conditions) | N/A |
| Timeout/Retry Hygiene | score | score (probe/healthcheck timeouts, client config passed by env) | score (job `timeout-minutes`, network calls in scripts) |
| CI/CD Maturity | score | score | score |
| Incident Readiness | score | score | N/A (failure notification goes under CI/CD) |
| Capacity Planning | score | score (limits, pool sizes, scaling) | N/A (`concurrency` goes under CI/CD) |
| Container/Deploy Hygiene | score if a Dockerfile/manifest exists, else N/A | score | N/A unless jobs build or run container images |

A mixed repo uses the union of the columns that apply. If a review is scoped to part of a repo (for example `.github`), dimensions outside that scope are N/A with the reason "outside requested scope", not scored from the rest of the repo.

Evidence for an absence cites where the thing should be: `docker-compose.yml:11-20 (no healthcheck:)`, `.github/workflows/ (none)`, `docs/runbooks/ (none)`. Confirm an absence by searching the whole target (for example `grep -n timeout-minutes` on every workflow) before claiming it; never infer it from one file.

## Dimension anchors

### Observability
- 9-10: Structured logs with trace/request ID; golden-signal metrics (latency histograms, traffic, errors, saturation); tracing across service boundaries; symptom-based alerts on SLOs.
- 7-8: Structured logs and golden-signal metrics on every service; alerts exist but are partly cause-based or lack runbook links.
- 5-6: Structured or consistent logs; some metrics; no tracing; few or no alerts.
- 3-4: Free-text logs only (stdout defaults); no metrics endpoint or exporter.
- 1-2: Errors swallowed or logs discarded (`logging: none`, logs inside an ephemeral container path with no volume).

### Availability Design
- 9-10: 2+ replicas (3+ for critical) across failure domains; separate liveness/readiness; graceful shutdown with drain; documented SLOs and error budget.
- 7-8: Health checks on every long-running service, readiness-gated startup (`depends_on: condition: service_healthy` or readiness probes), restart policy, graceful SIGTERM handling.
- 5-6: Restart policy everywhere and health checks on some services; single replicas; no SLOs.
- 3-4: Restart policy only; no health checks; startup order by container start, not readiness.
- 1-2: No restart policy and no health checks; a single crash means a manual restart; stateful data on no volume.

### Timeout/Retry Hygiene
- 9-10: Every outbound call has explicit connect and read timeouts sized from data; child < parent; bounded retries with backoff and jitter; idempotency keys on retried writes; circuit breakers on flaky dependencies.
- 7-8: Explicit timeouts on all outbound calls and every CI job; bounded retries with backoff; no circuit breakers.
- 5-6: Timeouts on most calls or jobs; at least one path relies on a library default (often infinite) or the 360-minute GitHub Actions job default; retries without jitter.
- 3-4: Timeouts on a minority of calls or jobs; immediate retries with no delay.
- 1-2: No explicit timeouts anywhere and/or unbounded retry loops.

For CI-only targets: count jobs with `timeout-minutes` (job or step level) over all jobs. All covered and network fetches in scripts have timeouts: 8+. More than a third uncovered: 5 or below.

### CI/CD Maturity
- 9-10: CI on every PR, required checks block merge, immutable versioned artifacts, staged deploy with post-deploy gates, tested rollback, automated rollback on error spike.
- 7-8: CI runs tests and lint on every PR and blocks merge; artifacts versioned by SHA or semver; actions pinned to a SHA or full version; job timeouts and `concurrency` set; rollback documented.
- 5-6: CI runs tests on PRs; some unpinned actions or images; no deploy gates or rollback path.
- 3-4: CI exists but runs only lint or only on main; failures do not block merge.
- 1-2: No pipeline (`.github/workflows/ (none)` or equivalent) for code that ships.

Generated workflows (for example gh-aw `*.lock.yml`, or a header saying the file is generated): cite the compiled file for evidence and point remediation at the source file plus the recompile command. Confirm the source exists first; a hand-frozen compiled file with no source is fixed in place, and the missing source is itself a finding.

### Incident Readiness
- 9-10: Symptom alerts with severities and routing; runbooks per common failure mode with diagnosis and rollback steps; on-call and escalation documented; postmortem template; synthetic checks.
- 7-8: Alerts with severities and runbooks for the main failure modes; backup and restore steps documented and tested.
- 5-6: Some troubleshooting docs (README section); backup procedure described but untested; no alerts in repo.
- 3-4: Only install docs; no backup/restore or failure guidance.
- 1-2: Nothing, and the stack holds data that cannot be recreated.

### Capacity Planning
- 9-10: Limits and requests from measured usage; autoscaling on the bottleneck metric with min/max; load tests run regularly; rate limits and backpressure.
- 7-8: CPU and memory limits on every service; pool sizes configured; a load test or capacity note exists.
- 5-6: Limits on some services (or on the heaviest one only); pools at library defaults.
- 3-4: No limits anywhere but the workload is light or bounded.
- 1-2: No limits on a memory- or GPU-heavy service (LLM inference, databases, search) sharing a host with others.

### Container/Deploy Hygiene
- 9-10: Images pinned by digest; minimal multi-stage images; non-root; read-only root fs; image scanning in CI; secrets injected at runtime; PDB and rolling update settings where orchestrated.
- 7-8: Images pinned to a specific version tag; non-root where the image allows; no secrets in images or committed env files; healthchecks defined.
- 5-6: Mix of pinned and `:latest`/untagged images; default root users; secrets via env files with committed example defaults.
- 3-4: Most images `:latest` or untagged; secrets or weak default passwords committed in config.
- 1-2: Real secrets baked into images or committed; privileged containers or host network without need.

## Overall score

- Overall = mean of the scored (non-N/A) dimensions, one decimal. Name the averaged dimensions in the report.
- If any CRITICAL finding exists, cap the overall at 4.0 and say so.
- Status bands: a score at or above `statusThresholds.healthy[0]` is Healthy, at or above `statusThresholds.needsAttention[0]` is Needs Attention, anything lower is Critical (defaults 8 / 5 when the resolver gives none). Only the lower bounds count, so a fractional score such as 7.5 is Needs Attention, never a gap; review-full uses the same rule.
