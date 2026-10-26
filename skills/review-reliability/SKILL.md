---
name: review-reliability
description: Analyzes code and configuration (application code, Docker Compose or IaC stacks, and CI-only pipelines) for production reliability fitness, producing scores (1-10) across observability, availability design, timeout/retry hygiene, CI/CD maturity, incident readiness, capacity planning, and container/deploy hygiene. Use when the user says /review:review-reliability, requests a reliability review, says check observability, asks if the system is production ready, wants a monitoring setup review, asks about CI/CD pipeline quality, or wants an operational readiness assessment. Only reports findings with confidence >= 7/10.
---

# Reliability Fitness Review

Analyze the codebase (or specified files/modules) for production reliability fitness. Identify gaps in observability, fault tolerance, deployment safety, and operational readiness using evidence from the code and configuration.

Reference: [Fundamentals of Reliability Engineering](https://jeffbailey.us/blog/2025/11/17/fundamentals-of-reliability-engineering/), [Fundamentals of Monitoring and Observability](https://jeffbailey.us/blog/2025/11/16/fundamentals-of-monitoring-and-observability/), [Fundamentals of Software Availability](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-software-availability/), [Fundamentals of Timeouts](https://jeffbailey.us/blog/2026/02/01/fundamentals-of-timeouts/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

- `references/rubric.md` is the scoring source: severity definitions, which dimensions apply to which target type, per-dimension score anchors, and the overall-score rule. It is short; read it first.
- `references/checklist.md` is what to check during the workflow steps, including CI job hygiene and Docker Compose checks.
- `references/wisdom.md` is optional background, auto-generated from the articles below (about 45k tokens). Never read it whole; grep its headings (`grep -n '^##' references/wisdom.md`) and read one section when a specific question needs depth.

- [Fundamentals of Reliability Engineering](https://jeffbailey.us/blog/2025/11/17/fundamentals-of-reliability-engineering/)
- [Fundamentals of Monitoring and Observability](https://jeffbailey.us/blog/2025/11/16/fundamentals-of-monitoring-and-observability/)
- [Fundamentals of Software Availability](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-software-availability/)
- [Fundamentals of Timeouts](https://jeffbailey.us/blog/2026/02/01/fundamentals-of-timeouts/)

## Configuration

Invoke the resolver CLI to obtain effective weights and thresholds for the review target. Never load `fitness-config.json` directly.

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py" show --path <target>
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; the resolver ships two levels up in the plugin's `scripts/`. If your agent does not expand the variable, substitute the directory containing this `SKILL.md`.

Where `<target>` is the file or directory under review. The CLI walks up to discover any module override and merges it with the root config. Include the `Config:` and `Effective weights:` lines from the resolver output within the first 10 lines of the final report as the provenance trail (AC-03.1, AC-08.2). The `effective` object inside the JSON block delimited by `<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->` / `<!-- END_EFFECTIVE_CONFIG_JSON -->` carries weights, status thresholds, security, and scoring for any programmatic needs.

The resolver walks up from the target, so a target outside the tree that holds `fitness-config.json` (a copied checkout, a sandbox, a sibling repo) resolves to `Config: built-in defaults (no fitness-config.json found)`. Copy that line as reported; do not copy or create a config file to change the answer. If you expected a project config, add one sentence under the provenance lines saying the target is outside its tree. Use `effective.statusThresholds` for the status band; the cross-skill weights are provenance only for this single-domain report.

## Workflow

1. **Load the rubric** -- Read `references/rubric.md`, then skim `references/checklist.md`.

2. **Scope and classify the target** -- Decide what is under review (whole repo, a subdirectory such as `.github`, or files) and its type: application code, deploy config (Docker Compose, Kubernetes, Helm, Terraform), CI-only (workflows and CI scripts), or a mix. Look for source files and HTTP/DB clients, `docker-compose*.yml`/`compose*.yml`, manifests, `*.tf`, and `.github/workflows/` or other pipeline files. Run the resolver on the target.

3. **Decide applicability** -- Use the target-type table in rubric.md to mark each dimension scored or N/A, with a one-line reason for each N/A. A missing thing that should exist (no CI for shipped code, no healthchecks in a production compose file) is a finding, not N/A.

4. **Map failure boundaries** -- App code: HTTP clients, gRPC stubs, DB/cache/queue connectors, external APIs. Compose/IaC: services, their images, volumes, ports, and `depends_on` edges. CI: jobs, the actions and images they use, and network calls in scripts. These are where reliability patterns must exist.

5. **Check each applicable dimension against checklist.md**:
   - Observability: logging format and fields, metrics/exporters, tracing, alert definitions.
   - Availability: health checks, readiness-gated startup, restart policy, replicas, graceful shutdown, SLOs.
   - Timeout/retry: explicit timeouts on every outbound call; in CI, `timeout-minutes` on every job (check each job in each workflow; the default is 360 minutes) and timeouts on `curl`/HTTP calls in scripts; backoff and bounded retries.
   - CI/CD: tests on PRs, merge blocking, pinned actions and images, `concurrency`, artifact versioning, deploy gates, rollback. For generated workflows (gh-aw `*.lock.yml` or a "generated" header), point fixes at the source file after confirming it exists in the repo.
   - Incident readiness: alerts with severities, runbooks, backup/restore docs, on-call, postmortems.
   - Capacity: CPU/memory limits, pool sizes, autoscaling, load tests, rate limits.
   - Container/deploy: image pinning, base images, non-root, secrets handling, healthchecks, orchestrator rollout settings.

6. **Score** each applicable dimension against the rubric.md anchors with file:line evidence. Compute the overall as rubric.md defines it.

7. **Self-check, then write the report** (see below).

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code or config, not a guess about runtime behavior?
- Can you point to a specific file and line (or, for an absence, the file or directory where it should be)?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise. Severity levels (CRITICAL, HIGH, MEDIUM, LOW) and their reliability examples are defined in `references/rubric.md`.

## Scoring Dimensions (1-10 each)

Score anchors for each dimension are in `references/rubric.md`; a dimension may be N/A when the target type has nothing to evaluate for it.

1. **Observability** -- Structured logging, metrics emission covering golden signals, distributed tracing, dashboards, and alerting
2. **Availability Design** -- Health checks, graceful shutdown, redundancy, load balancing, graceful degradation, and SLO definitions
3. **Timeout/Retry Hygiene** -- Explicit timeouts on all outbound calls and CI jobs, exponential backoff with jitter, circuit breakers, timeout layering, and idempotency
4. **CI/CD Maturity** -- Pipeline automation, test coverage in CI, pinned actions, concurrency control, deployment strategies, rollback mechanisms, artifact versioning, and feature flags
5. **Incident Readiness** -- Alert definitions, runbooks, backup/restore, on-call rotation, postmortem process, synthetic monitoring, and status page integration
6. **Capacity Planning** -- Resource limits, auto-scaling, connection pool sizing, rate limiting, load testing, and headroom planning
7. **Container/Deploy Hygiene** -- Pinned images, minimal base images, multi-stage builds, non-root users, signal handling, image scanning, pod disruption budgets, and secrets management

## Output Format

Write the report to `docs/reliability-review.md` at the root of the repository that contains the target (`git -C <target> rev-parse --show-toplevel`; if the target is not in a git repo, the project directory you were pointed at, or the parent of a file or dot-directory target such as `.github`), unless the user gives a path. For a review scoped to a subdirectory or file set, write `docs/reliability-review-<scope-slug>.md` (for example `docs/reliability-review-github.md` for `.github`) so a scoped run does not replace the whole-repo report.

Before writing, check:
- Every file:line exists and says what the finding claims; every claimed absence was confirmed by searching all relevant files.
- Every finding has confidence >= 7.
- The overall equals the mean of the scored dimensions (with the CRITICAL cap applied), and the averaged dimensions are named.
- No secret or password values are reproduced; refer to them by file:line only.

```markdown
# Reliability Fitness Review

**Target:** <path(s) or scope reviewed> (<target type>)
Config: <copied from resolver output>
Effective weights: <copied from resolver output>

## Direct Answer

(Only when the user asked a specific question, such as "is it production ready?": a short, direct answer with the two or three findings that decide it.)

## Summary

Overall fitness score: X.X / 10 -- <status> (mean of <scored dimensions>; <CRITICAL cap applied, if any>)

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Observability | X/10 or N/A -- reason | ... |
| Availability Design | X/10 or N/A -- reason | ... |
| Timeout/Retry Hygiene | X/10 or N/A -- reason | ... |
| CI/CD Maturity | X/10 or N/A -- reason | ... |
| Incident Readiness | X/10 or N/A -- reason | ... |
| Capacity Planning | X/10 or N/A -- reason | ... |
| Container/Deploy Hygiene | X/10 or N/A -- reason | ... |

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line
- **Description:** What the issue is and why it matters.
- **Evidence:** The specific code or config pattern found.
- **Impact:** What could go wrong in production.
- **Remediation:** Concrete fix with a code example or specific steps (for generated files, the source file to edit).

(repeat for each finding, ordered by severity)

### Observability (X/10)
- Evidence: file:line references
- Issues found
- Recommendations

(repeat for each scored dimension)

## Action Items (up to 5, by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...

## Checklist Reference

See references/checklist.md for the full reliability checklist.

## Reference

Based on [Fundamentals of Reliability Engineering](https://jeffbailey.us/blog/2025/11/17/fundamentals-of-reliability-engineering/), [Fundamentals of Monitoring and Observability](https://jeffbailey.us/blog/2025/11/16/fundamentals-of-monitoring-and-observability/), [Fundamentals of Software Availability](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-software-availability/), [Fundamentals of Timeouts](https://jeffbailey.us/blog/2026/02/01/fundamentals-of-timeouts/) and guidance from https://jeffbailey.us/categories/fundamentals/
```
