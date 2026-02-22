# Reliability Fitness Review

**Date:** 2026-02-22  
**Scope:** Project at `/Users/jeffbailey/Projects/skills` — skills repository (SKILL.md, markdown, CI config, Backstage catalog)

---

## Summary

Overall fitness score: **5.0 / 10** (average of dimensions)

This repository is a **content/library project** (skill definitions, markdown docs, checklists, CI workflow) rather than a deployed application. Reliability dimensions are evaluated in that context: the main runtime surface is the GitHub Actions fitness-review workflow and the content delivery via git/GitHub.

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Observability | 4/10 | GitHub Actions provides run visibility; no custom metrics, structured logs, or dashboards |
| Availability Design | 6/10 | Content highly available via GitHub; CI has concurrency control; no service to health-check |
| Timeout/Retry Hygiene | 6/10 | Job-level timeouts present; no application-level outbound calls to audit |
| CI/CD Maturity | 6/10 | Pipeline exists with schedule + manual trigger; pinned actions; no tests (content is prose) |
| Incident Readiness | 3/10 | No runbooks, alerts, or on-call config; minimal troubleshooting in SETUP.md |
| Capacity Planning | 5/10 | Ephemeral GitHub runners; no explicit capacity docs or load testing |
| Container/Deploy Hygiene | 5/10 | No containers; deploy = git push; SETUP.md documents install and troubleshooting |

---

## Service Boundaries Mapped

| Boundary | Type | Location | Notes |
|----------|------|----------|-------|
| GitHub API | HTTP | Via `actions/checkout`, `github-script`, MCP gateway | Token-authenticated; no explicit timeouts in workflow |
| Copilot API | External | `.github/workflows/fitness-review.lock.yml` (agent job) | Via Copilot CLI in firewall container; 20min job timeout |
| Safe Outputs MCP | HTTP server | `fitness-review.lock.yml:598-617` | Local HTTP server on `host.docker.internal`; ephemeral per run |
| Docker registry | Image pull | `fitness-review.lock.yml:361` | Pulls ghcr.io images; no explicit timeout |
| Content delivery | Git/GitHub | README, SETUP, catalog-info | Users clone/symlink; high availability via GitHub |

---

## Detailed Findings

### Observability (4/10)

**Evidence:**
- `.github/workflows/fitness-review.lock.yml:538-541` — Artifact uploads: `prompt`, `safe-output`, `agent-output`, `agent-artifacts`
- `.github/workflows/fitness-review.lock.yml:534-543` — `redact_secrets` step masks tokens in logs
- `SETUP.md:249-254` — Troubleshooting section (partial operational guidance)
- No file references for: structured logging, metrics (Prometheus/StatsD/OTel), tracing, dashboards, alert definitions

**Issues found:**
- No structured logging framework; workflow step output is free-form
- No metrics emission (latency, error rate, traffic, saturation)
- No distributed tracing; correlation relies on GitHub run ID
- No dashboards for SLO or error-budget tracking
- No alert definitions; failures discovered via Actions tab or notifications

**Recommendations:**
- Add workflow status badge and link to recent runs in README
- Document failure modes and how to inspect run logs in a runbook
- Consider GitHub Actions failure notifications (branch protection, status checks)

---

### Availability Design (6/10)

**Evidence:**
- `.github/workflows/fitness-review.lock.yml:38-40` — Concurrency group `gh-aw-${{ github.workflow }}` prevents overlapping runs
- `.github/workflows/fitness-review.lock.yml:254-255` — `concurrency` on agent job: `gh-aw-copilot-${{ github.workflow }}`
- `catalog-info.yaml:29` — `lifecycle: production`; `type: library`
- Content delivered via git clone; GitHub provides redundancy

**Issues found:**
- No health check endpoints (N/A — no long-running service)
- No liveness/readiness probes (N/A)
- Single workflow; no redundancy at workflow-definition level (relies on GitHub)
- No graceful degradation paths documented for Copilot API outage

**Recommendations:**
- Document behavior when Copilot API or GitHub is degraded
- Consider fallback engine (Claude vs Copilot) if one is unavailable

---

### Timeout/Retry Hygiene (6/10)

**Evidence:**
- `.github/workflows/fitness-review.lock.yml:687` — `timeout-minutes: 20` on Execute GitHub Copilot CLI (agent job)
- `.github/workflows/fitness-review.lock.yml:946` — `timeout-minutes: 10` on detection job
- `.github/workflows/fitness-review.lock.yml:1049` — `timeout-minutes: 15` on safe_outputs job
- `.github/workflows/fitness-review.lock.yml:354-358` — Secret validation fails fast if `COPILOT_GITHUB_TOKEN` missing

**Issues found:**
- No application-level HTTP clients in repo; external calls are in third-party actions
- No explicit connect/read timeouts for GitHub API or Copilot API (handled by actions)
- No retry logic in workflow steps; Actions may retry at the runner level
- Timeout layering: detection (10min) < agent (20min) — reasonable

**Recommendations:**
- Document expected run duration and when to investigate timeouts
- Consider `continue-on-error` with explicit failure handling for non-critical steps if appropriate

---

### CI/CD Maturity (6/10)

**Evidence:**
- `.github/workflows/fitness-review.md:8-9` — Triggers: `schedule` (weekly Sunday), `workflow_dispatch`
- `.github/aw/actions-lock.json` — Pinned action: `github/gh-aw/actions/setup@v0.49.0` with sha
- `.github/workflows/fitness-review.lock.yml` — All actions pinned by sha (e.g. `0eb518a648ba8178f4f42559a4c250d3e513acd1`)
- `.github/workflows/fitness-review.lock.yml:63-70` — `sparse-checkout` for activation; full checkout in agent job
- `SETUP.md:47-54` — `gh aw compile`, commit, push; clear release flow

**Issues found:**
- No automated tests in pipeline (skills are markdown; no unit/integration tests for content)
- No deployment gates or smoke tests (content repo; deploy = git push)
- No blue-green or canary (N/A)
- Rollback = `git revert`; not automated
- Staging: N/A (single content stream)

**Recommendations:**
- Add markdown lint or link check in CI if desired
- Document rollback procedure (revert + push) in SETUP or runbook

---

### Incident Readiness (3/10)

**Evidence:**
- `SETUP.md:249-254` — Troubleshooting: skills not loading, workflow fails, OIDC error
- `.github/workflows/fitness-review.lock.yml:606-641` — `handle_agent_failure`, `handle_noop_message` steps in conclusion job
- No runbooks, alert definitions, on-call config, postmortem template

**Issues found:**
- No runbook for: workflow timeout, Copilot API failure, secret misconfiguration
- No alert definitions (beyond default GitHub Actions notifications)
- No on-call rotation or escalation path
- No postmortem template or process
- No status page integration

**Recommendations:**
- Add `docs/runbooks/` with: workflow-failure, secret-missing, copilot-timeout
- Document how to receive workflow failure notifications (email, Slack, etc.)
- Add postmortem template in `docs/` for significant incidents

---

### Capacity Planning (5/10)

**Evidence:**
- `.github/workflows/fitness-review.lock.yml:45,249` — `runs-on: ubuntu-slim` (activation), `ubuntu-latest` (agent)
- Ephemeral runners; no persistent resources
- Concurrency limits parallel agent runs

**Issues found:**
- No resource limits (GitHub provides; not configurable in workflow)
- No connection pool or rate-limit configuration (N/A for content)
- No load testing (N/A for skills content)
- No documented capacity limits (e.g., max concurrent runs, API quotas)

**Recommendations:**
- Document Copilot/GitHub API quotas if they affect usage
- Note any limits in README or SETUP for high-frequency users

---

### Container/Deploy Hygiene (5/10)

**Evidence:**
- No `Dockerfile` in repo
- No Kubernetes manifests or container orchestration
- `catalog-info.yaml:27-28` — `type: library`, `lifecycle: production`
- `SETUP.md` — Documented install (clone, symlink), `gh aw` workflow add/compile

**Issues found:**
- No container image to evaluate
- Workflow uses pre-built images (ghcr.io/github/*); not built by this repo
- Deploy = git push; users install via clone/symlink per SETUP.md

**Recommendations:**
- N/A for container hygiene (no containers)
- Keep SETUP.md and README install steps accurate; consider version pinning for `gh aw` add

---

## Top 5 Action Items (by impact)

1. **[HIGH]** Add runbooks for common failure modes — `docs/runbooks/`  
   - Workflow failure (timeout, Copilot error), secret missing, compilation failure. Include diagnosis steps and resolution. *Reference: review-reliability/references/checklist.md:177-180*

2. **[HIGH]** Document incident notification and escalation — `SETUP.md` or `docs/`  
   - How to get notified on workflow failure (GitHub notifications, branch protection). Escalation path if maintainer unavailable. *Reference: review-reliability/references/checklist.md:182-185*

3. **[MEDIUM]** Add postmortem template — `docs/postmortem-template.md`  
   - Blame-free format: impact, timeline, root cause, action items. *Reference: review-reliability/references/checklist.md:187-191*

4. **[MEDIUM]** Document capacity and rate limits — `README.md` or `SETUP.md`  
   - Copilot API quotas, GitHub Actions concurrency, any known limits for high-frequency runs. *Reference: review-reliability/references/checklist.md:208-212*

5. **[LOW]** Add workflow status badge to README  
   - Link to Actions tab for recent run visibility. Improves operational transparency. *Reference: CI/CD best practices*

---

## Key Findings

- **Strengths:** Concurrency control, job-level timeouts, pinned actions, clear install/deploy docs, failure-handling steps in conclusion job.
- **Gaps:** No runbooks, no alert/runbook links, no postmortem process, minimal incident readiness.
- **Context:** This is a content/library repo; many dimensions (containers, health probes, app-level timeouts) are N/A. Scores reflect what exists and what would improve operational reliability for the CI workflow and content delivery.

---

## Checklist Reference

See `review-reliability/references/checklist.md` for the full reliability checklist.
