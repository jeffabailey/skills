# Project Fitness Report

**Date:** 2026-02-26
**Scope:** Full repository -- 13 skill definitions, GitHub Actions CI/CD pipeline, engine-config.py, test scripts, and documentation

## Overall Score: 6.9 / 10

> Data (10%) and Accessibility (8%) skipped -- no database code and no frontend. Remaining weights redistributed proportionally.

| Domain | Score | Status |
|--------|-------|--------|
| Architecture | 8.1/10 | ✅ Healthy |
| Security | 7.8/10 | ⚠️ Needs Attention |
| Reliability | 5.1/10 | ⚠️ Needs Attention |
| Testing | 4.3/10 | ❌ Critical |
| Performance | 7.5/10 | ⚠️ Needs Attention |
| Algorithms | 7.8/10 | ⚠️ Needs Attention |
| Data | -- | Skipped (no database) |
| Accessibility | -- | Skipped (no frontend) |
| Process | 6.5/10 | ⚠️ Needs Attention |
| Maintainability | 7.4/10 | ⚠️ Needs Attention |

Status: 8-10 = ✅ Healthy, 5-7 = ⚠️ Needs Attention, 1-4 = ❌ Critical

---

## Top 10 Action Items (Priority Order)

1. **[HIGH]** Enforce PR workflow for all changes to main -- configure branch protection requiring PR reviews and passing status checks; ~80% of commits bypass the PR pipeline, skipping CI, CODEOWNERS, and PR template checklist -- repository settings
2. **[HIGH]** Add unit tests for engine-config.py -- 367 lines of security-critical configuration (API key names, permission models, CLI command assembly) with zero unit tests; only validated by running with 3 known-good inputs -- `.github/scripts/engine-config.py:315-367`
3. **[HIGH]** Standardize detailed finding format across all domain skills -- `review-security` and `review-algorithms` use a rich structured format (Severity, Confidence, Location, Evidence, Remediation) while the other 8 domain skills use a simpler format; inconsistent output makes synthesis and `review-apply` parsing harder -- `review-security/SKILL.md:243-254`, `review-architecture/SKILL.md:226-237`
4. **[HIGH]** Apply confidence threshold consistently across all domain skills -- only `review-security` and `review-algorithms` gate findings at confidence >= 7/10; the other 8 skills may produce lower-confidence findings that dilute reports -- `review-security/SKILL.md:36`, `review-testing/SKILL.md`
5. **[HIGH]** Add expected-vs-actual diagnostic output to all shell test assertions -- 98 of 99 assertions produce only "FAIL: description" with no diagnostic; the `fail()` function supports a second "got:" argument but only 1 assertion uses it -- `tests/workflow-tests.sh:11,73-76`, `tests/skill-structure-tests.sh:10,35-39`
6. **[HIGH]** Add shellcheck to CI and add `timeout-minutes` to all pr-checks.yml jobs -- no linting enforcement for shell scripts; no job timeouts (defaults to GitHub's 6-hour timeout) -- `.github/workflows/pr-checks.yml`
7. **[HIGH]** Add automated alerting for workflow failures -- failures are discoverable only by checking Actions tab or relying on default GitHub email notifications -- `.github/workflows/fitness-review.yml`
8. **[HIGH]** Add retry logic for transient API failures -- 529 Overloaded from Anthropic is explicitly documented as transient but the only recovery is manual re-run; add retry with backoff on the agent step -- `fitness-review.yml:724-730`, `.github/RUN.md:60-66`
9. **[MEDIUM]** Create a single source of truth for the skill list -- duplicated in 10+ locations; `review-apply` already missing from `pr-checks.yml:88`, proving the invariant fails in practice -- `CONTRIBUTING.md:60-71`, `tests/skill-structure-tests.sh:12-14`
10. **[MEDIUM]** Increase detection job timeout from 10 to 15 minutes -- only 2 minutes of headroom above the 8-minute step timeout for 6 setup steps; under slow conditions the job timeout preempts the step timeout -- `fitness-review.yml:983,1053`

---

## Domain Details

### Architecture -- 8.1/10 ✅

| Dimension | Score |
|-----------|-------|
| Coupling | 8/10 |
| Cohesion | 9/10 |
| Layering | 8/10 |
| Modularity | 9/10 |
| Naming | 8/10 |
| API Design | 7/10 |
| Maintainability | 7/10 |

**Strengths:**
- Skills are fully independent at runtime; each SKILL.md is self-contained. `review-full` orchestrates via slash commands (contract-based coupling).
- Clear three-layer architecture: orchestrator -> domain skills -> reference checklists. Dependencies flow strictly downward.
- Excellent modularity -- each skill is independently installable, testable, and evolvable. ADR 0001 documents the design.
- Consistent `review-<domain>` naming convention enforced by `skill-structure-tests.sh`.

**Weaknesses:**
- Scoring weights duplicated in 4 files (`review-full/SKILL.md`, `README.md`, `CONTRIBUTING.md`, `.github/fitness-review-prompt.md`) requiring manual sync.
- Skill list duplicated in 8+ locations per `CONTRIBUTING.md:60-70`.
- No formal interface definition for what `review-full` expects from domain skills -- the contract is implicit in prose.
- `.github/fitness-review-prompt.md` partially duplicates `review-full/SKILL.md` (skip-layer pattern).
- Confidence threshold inconsistently applied: only `review-security` and `review-algorithms` define one.
- Finding format varies: 2 skills use rich structured findings, 8 use simpler format.
- Section headers inconsistent: `review-accessibility` uses `## Scoring Rubric` vs `## Scoring Dimensions`; `## Reference` vs `## References` vs `## Checklist Reference`.

---

### Security -- 7.8/10 ⚠️

| Dimension | Score |
|-----------|-------|
| Input Validation | 7/10 |
| Authentication/Authorization | 9/10 |
| Data Protection | 8/10 |
| Dependency Security | 9/10 |
| Error Handling/Logging | 8/10 |
| Cryptography | 9/10 |

**Strengths:**
- `permissions: {}` at workflow root with per-job least-privilege grants. `persist-credentials: false` on all checkouts.
- All GitHub Actions pinned by full SHA. Dependabot configured for weekly updates.
- Ephemeral API keys generated with `openssl rand -base64 45` (~360 bits) and masked immediately.
- `workflow_dispatch` engine input uses `type: choice` restricting values to `claude`, `copilot`, `codex`.

**Findings (confidence >= 7/10):**
- **MEDIUM** (8/10): Dynamic `require()` path from step output enables code injection if `log_parser` output is compromised; validate against allowlist -- `fitness-review.yml:840`
- **MEDIUM** (8/10): Step outputs from `engine-config.py` interpolated directly into `run:` shell blocks; accepted pattern but fragile -- `fitness-review.yml:365,368,729,1047`
- **MEDIUM** (9/10): `--env-all` passes full runner environment into AWF sandbox; replace with explicit env vars -- `fitness-review.yml:729`
- **MEDIUM** (8/10): `bypassPermissions` on Claude and `--allow-all-tools` on Copilot; mitigated by sandbox + firewall -- `engine-config.py:163,175`
- **LOW** (7/10): `.claude/settings.local.json` not in `.gitignore`; contributors could accidentally commit it
- **LOW** (7/10): Shell test scripts lack `shellcheck` validation in CI

---

### Reliability -- 5.1/10 ⚠️

| Dimension | Score |
|-----------|-------|
| Observability | 2/10 |
| Availability Design | 6/10 |
| Timeout/Retry Hygiene | 5/10 |
| CI/CD Maturity | 6/10 |
| Incident Readiness | 5/10 |
| Capacity Planning | 4/10 |
| Container/Deploy Hygiene | 8/10 |

**Strengths:**
- Multi-engine failover (claude/copilot/codex) with per-engine concurrency groups.
- Timeout layering partially correct: Bash 60s < MCP 60s < MCP connection 120s < agent 30min.
- `--max-turns 200` (agent) and `--max-turns 50` (detection) bound agent resource consumption.
- `docs/incident-response.md` with P1-P4 severity levels; `RUN.md` with 6 troubleshooting runbooks.
- All actions SHA-pinned; pinned container version (`--image-tag 0.20.2`); `persist-credentials: false`.

**Weaknesses:**
- No structured logging, metrics, dashboards, or alerting anywhere -- relies entirely on GitHub Actions default UI.
- No retry logic for transient failures; manual re-run is the only recovery path.
- Detection job timeout (10min) leaves only 2 minutes of headroom above step timeout (8min).
- No documented API quotas, expected run cost, or capacity forecasting.
- No postmortem template despite `docs/incident-response.md` existing.
- Most commits bypass PRs, skipping CI checks.

---

### Testing -- 4.3/10 ❌

| Dimension | Score |
|-----------|-------|
| Test Pyramid Balance | 5/10 |
| Test Quality | 6/10 |
| Coverage Strategy | 3/10 |
| Performance Testing | 1/10 |
| Debugging Support | 4/10 |
| CI Integration | 7/10 |

**Strengths:**
- 99 automated shell assertions in CI across `skill-structure-tests.sh` and `workflow-tests.sh`.
- 4 parallel CI jobs on every PR/push provide fast feedback.
- Tests are deterministic and independent.

**Weaknesses:**
- 132+ trigger scenarios and 32+ functional scenarios exist only as manual markdown documentation -- never run in CI.
- `engine-config.py` (367 lines, security-critical) has zero unit tests; only validated by 3 integration runs.
- 98 of 99 assertions produce no expected-vs-actual diagnostic on failure.
- No coverage tooling, no performance benchmarks, no machine-parseable test output (TAP/JUnit).
- No `timeout-minutes` on any of the 4 pr-checks.yml jobs.

---

### Performance -- 7.5/10 ⚠️

| Dimension | Score |
|-----------|-------|
| Algorithmic Efficiency | 8/10 |
| Database Design | N/A |
| Caching Strategy | N/A |
| Scalability Readiness | 7/10 |
| Resource Utilization | 7/10 |
| Data Pipeline Efficiency | 8/10 |

**Strengths:**
- All operations O(n) or better on bounded, compile-time-constant inputs (n < 80).
- `review-full` launches domain reviews in parallel via Task tool.
- Scope determination is incremental: pending changes -> specified files -> full project.
- Weekly schedule is appropriate frequency; incremental processing avoids unnecessary work.

**Weaknesses:**
- No partial failure handling in `review-full` orchestrator -- if one domain skill fails, behavior is undefined.
- No npm cache for agent CLI installation in CI; each run installs from scratch.
- No size guidelines for checklist files; risk of exceeding useful context window capacity as checklists grow.
- No execution time tracking or token usage monitoring for the review process.

---

### Algorithms -- 7.8/10 ⚠️

| Dimension | Score |
|-----------|-------|
| Algorithm Choice | 8/10 |
| Data Structure Selection | 8/10 |
| Complexity Awareness | 9/10 |
| Concurrency Safety | 9/10 |
| Edge Case Handling | 6/10 |
| Correctness Patterns | 7/10 |

**Strengths:**
- Dictionary lookup for O(1) engine config access; `sorted(set(...))` for deterministic dedup; `",".join()` for efficient string assembly.
- No hidden quadratic behavior; all iterations over bounded collections.
- Single-threaded scripts with workflow concurrency groups preventing collisions.

**Weaknesses:**
- Dict merge in `write_outputs` uses `{**config, ...}` parameter shadowing -- silent key collision risk -- `engine-config.py:321-327`
- Heredoc delimiter `GH_AW_EOF` hardcoded with no collision guard -- `engine-config.py:337-339`
- Detection job timeout margin is tight (2 minutes for 6 setup steps) -- `fitness-review.yml:983,1053`
- Skill list invariant already violated (`review-apply` missing from `pr-checks.yml:88`)
- Shell test `grep -q` produces no diagnostic output on mismatch

---

### Process -- 6.5/10 ⚠️

| Dimension | Score |
|-----------|-------|
| Documentation Quality | 8/10 |
| Development Workflow | 6/10 |
| Code Review Practices | 5/10 |
| Dependency Management | 8/10 |
| Project Organization | 9/10 |
| Portability | 7/10 |
| Technical Leadership Signals | 6/10 |
| Agile & Iteration Signals | 5/10 |
| Open Source Readiness | 6/10 |
| Operational Readiness | 5/10 |

**Strengths:**
- Comprehensive documentation: README, SETUP (5 platforms), CONTRIBUTING, RUN (6 runbooks), ADR, incident-response.
- PR-gated CI with 4 parallel jobs; Dependabot active; SHA-pinned actions.
- Clean `review-<domain>/` directory structure with consistent naming.
- Evidence of iterative improvement: fitness report cycle generates findings, then they are addressed.

**Weaknesses:**
- ~80% of commits go directly to `main` without PRs, bypassing CI, CODEOWNERS, and PR template.
- 6 commits use uninformative placeholder message "If a git tree falls in a forest..."
- No CODE_OF_CONDUCT.md despite the process checklist requiring one.
- Only 1 ADR; multi-engine, gh-aw, and review-apply decisions lack formal ADRs.
- No CHANGELOG, release tags, or semantic versioning.
- No linting enforcement (no shellcheck, yamllint, markdownlint).
- `.claude/settings.local.json` contains machine-specific path committed to repo.

---

### Maintainability -- 7.4/10 ⚠️

| Dimension | Score |
|-----------|-------|
| Structural Complexity | 8/10 |
| Understandability | 8/10 |
| Technical Debt Indicators | 7/10 |
| Coupling/Dependency Depth | 8/10 |
| Code Smell Density | 6/10 |

**Strengths:**
- All functions under 36 lines; nesting at most 3 levels.
- Zero TODO/FIXME/HACK in project code; zero lint suppressions.
- Excellent naming and consistent patterns across all 13 skills.
- Version constants centralized as `CLAUDE_VERSION`, `COPILOT_VERSION`, `CODEX_VERSION`.

**Weaknesses:**
- `fitness-review.yml` at 1150 lines is the one complexity outlier (207 lines of embedded inline JSON schemas).
- Skill list duplicated in 9+ locations across 6 files -- shotgun surgery risk proven by `review-apply` omission.
- `_TOOLCACHE_PATH` one-liner at `engine-config.py:149-153` uses extremely dense quoting with no explanatory comment.
- `heredoc_threshold = 200` magic number at `engine-config.py:331` lacks a "why" comment.

---

## References

Based on guidance from https://jeffbailey.us/categories/fundamentals/
