# Project Fitness Report

**Date:** 2026-02-26
**Scope:** Full repository -- 13 skill definitions, GitHub Actions CI/CD pipeline, engine-config.py, test scripts, and documentation

## Overall Score: 7.1 / 10

> Data (10%) and Accessibility (8%) skipped -- no database code and no frontend. Remaining weights redistributed proportionally.

| Domain | Score | Status |
|--------|-------|--------|
| Architecture | 7.6/10 | ⚠️ Needs Attention |
| Security | 8.5/10 | ✅ Healthy |
| Reliability | 5.4/10 | ⚠️ Needs Attention |
| Testing | 4.5/10 | ⚠️ Needs Attention |
| Performance | 7.5/10 | ⚠️ Needs Attention |
| Algorithms | 7.7/10 | ⚠️ Needs Attention |
| Data | -- | Skipped (no database) |
| Accessibility | -- | Skipped (no frontend) |
| Process | 7.4/10 | ⚠️ Needs Attention |
| Maintainability | 7.8/10 | ⚠️ Needs Attention |

Status: 8-10 = ✅ Healthy, 5-7 = ⚠️ Needs Attention, 1-4 = ❌ Critical

---

## Top 10 Action Items (Priority Order)

1. **[HIGH]** `review-apply` exists in `review-apply/SKILL.md` and tests but is absent from `README.md`, `SETUP.md`, `CONTRIBUTING.md`, `.github/fitness-review-prompt.md`, `docs/index.md`, and `.github/workflows/pr-checks.yml:88` -- violates `CONTRIBUTING.md:60-71` checklist
2. **[HIGH]** Detection step/job timeout inversion -- `fitness-review.yml:983` sets job `timeout-minutes: 10` but `fitness-review.yml:1053` sets step `timeout-minutes: 20`; step timeout is unreachable -- `fitness-review.yml:983,1053`
3. **[HIGH]** No automated failure alerting -- workflow failures discoverable only by checking Actions tab or relying on default GitHub email notifications -- `.github/workflows/fitness-review.yml`
4. **[HIGH]** 132+ trigger scenarios in `tests/trigger-tests.md` are documented but never run in CI -- even 1 trigger per skill (13 checks) would catch regressions -- `tests/trigger-tests.md`
5. **[HIGH]** `CONTRIBUTING.md:32` states SKILL.md must have `## Triggers` section but no skill uses that pattern; actual triggers are in YAML frontmatter `description` field -- `CONTRIBUTING.md:32`
6. **[HIGH]** Shell test failures show `FAIL: description` but no expected-vs-actual output; `grep -q` produces no diagnostic on mismatch -- `tests/workflow-tests.sh:73-76`, `tests/skill-structure-tests.sh:35-39`
7. **[HIGH]** Most changes bypass PRs (direct commits to `main`), skipping the PR template checklist, CI checks, and CODEOWNERS review -- git log shows `ec30ba6`, `027b10d`, `a5cd755`, etc.
8. **[MEDIUM]** `--env-all` in AWF execution forwards all runner environment variables into the agent sandbox; consider passing only required variables -- `fitness-review.yml:729`
9. **[MEDIUM]** Skill list duplicated across 10+ locations with no automated sync check; `review-apply` omission proves this already fails in practice -- `CONTRIBUTING.md:60-71`
10. **[MEDIUM]** No linting enforcement in CI -- no shellcheck, yamllint, or markdownlint configured -- `.github/workflows/pr-checks.yml`

---

## Domain Details

### Architecture -- 7.6/10 ⚠️

| Dimension | Score |
|-----------|-------|
| Coupling | 8/10 |
| Cohesion | 9/10 |
| Layering | 8/10 |
| Modularity | 8/10 |
| Naming | 9/10 |
| API Design | 7/10 |
| Maintainability | 8/10 |

**Strengths:**
- Flat, one-way dependency graph with zero circular dependencies. Each skill is self-contained; only `review-full` orchestrates.
- Consistent `review-<domain>/SKILL.md + references/checklist.md` module interface documented in ADR 0001.
- Excellent naming convention enforced by `skill-structure-tests.sh`.

**Weaknesses:**
- Skill list duplicated in 10+ locations creates shotgun surgery risk; `review-apply` already missing from major docs.
- `fitness-review-prompt.md` partially duplicates `review-full/SKILL.md` domain list and weights.
- `review-accessibility/SKILL.md:22` uses `## Scoring Rubric` instead of `## Scoring Dimensions`.

---

### Security -- 8.5/10 ✅

| Dimension | Score |
|-----------|-------|
| Input Validation | 9/10 |
| Authentication/Authorization | 9/10 |
| Data Protection | 8/10 |
| Dependency Security | 9/10 |
| Error Handling/Logging | 8/10 |
| Cryptography | 9/10 |

**Strengths:**
- `permissions: {}` at workflow root with per-job least-privilege grants. `persist-credentials: false` on all checkouts.
- All GitHub Actions pinned by full SHA. Dependabot configured for weekly updates.
- Ephemeral API keys generated with `openssl rand -base64 45` (~360 bits) and masked immediately.
- XPIA prompt injection defense active. `yaml.safe_load()` used correctly.

**Findings (confidence >= 7/10):**
- **MEDIUM** (8/10): `--env-all` passes all runner env vars into AWF sandbox -- `fitness-review.yml:729`
- **MEDIUM** (8/10): `bypassPermissions` on Claude agent and `--allow-all-tools --allow-all-paths` on Copilot -- mitigated by allowed-tools list and firewall -- `engine-config.py:163,175`
- **LOW** (9/10): `.claude/settings.local.json` committed with local filesystem path -- `settings.local.json:11`
- **LOW** (8/10): `DEBUG: '*'` on safe outputs server could produce verbose logs -- `fitness-review.yml:608`

---

### Reliability -- 5.4/10 ⚠️

| Dimension | Score |
|-----------|-------|
| Observability | 3/10 |
| Availability Design | 7/10 |
| Timeout/Retry Hygiene | 6/10 |
| CI/CD Maturity | 7/10 |
| Incident Readiness | 5/10 |
| Capacity Planning | 4/10 |
| Container/Deploy Hygiene | 6/10 |

**Strengths:**
- Multi-engine failover (claude/copilot/codex) with per-engine concurrency groups.
- Well-layered timeout hierarchy: Bash 60s < MCP 120s < agent 30min.
- `--max-turns 200` (agent) and `--max-turns 50` (detection) bound agent resource consumption.
- `docs/incident-response.md` with P1-P4 severity levels; `RUN.md` with 6 troubleshooting runbooks.

**Weaknesses:**
- No structured logging, metrics, dashboards, or alerting anywhere.
- Detection step timeout (20min) exceeds its job timeout (10min) -- `fitness-review.yml:983,1053`.
- No retry logic; manual re-run is the only failure recovery.
- No documented API quotas, expected run duration, or runner-minute costs.

---

### Testing -- 4.5/10 ⚠️

| Dimension | Score |
|-----------|-------|
| Test Pyramid Balance | 5/10 |
| Test Quality | 6/10 |
| Coverage Strategy | 4/10 |
| Performance Testing | 1/10 |
| Debugging Support | 4/10 |
| CI Integration | 7/10 |

**Strengths:**
- 59+ automated shell assertions in CI across `skill-structure-tests.sh` and `workflow-tests.sh`.
- 4 parallel CI jobs provide fast feedback on PRs.
- Tests are deterministic and independent (file existence checks, grep pattern matching).

**Weaknesses:**
- 132+ trigger scenarios and 32+ functional scenarios exist only as manual markdown documentation.
- Shell test failures show `FAIL: description` with no expected-vs-actual diagnostic output.
- No coverage tooling, no performance benchmarks, no machine-parseable test output (TAP/JUnit).
- `review-maintainability` trigger tests added but no automated trigger validation exists.

---

### Performance -- 7.5/10 ⚠️

| Dimension | Score |
|-----------|-------|
| Algorithmic Efficiency | 8/10 |
| Database Design | N/A |
| Caching Strategy | N/A |
| Scalability Readiness | 7/10 |
| Resource Utilization | 8/10 |
| Data Pipeline Efficiency | 7/10 |

**Strengths:**
- All operations are O(n) or better on bounded, compile-time-constant inputs.
- `review-full` launches domain reviews in parallel via Task tool.
- `--max-turns 200` bounds agent resource consumption; `retention-days: 1` on artifacts is cost-conscious.

**Weaknesses:**
- Single concurrent workflow run limitation (concurrency group).
- No explicit `timeout-minutes` on all jobs in `fitness-review.yml`.
- Docker images downloaded fresh each run (no caching).

---

### Algorithms -- 7.7/10 ⚠️

| Dimension | Score |
|-----------|-------|
| Algorithm Choice | 8/10 |
| Data Structure Selection | 8/10 |
| Complexity Awareness | 9/10 |
| Concurrency Safety | 9/10 |
| Edge Case Handling | 6/10 |
| Correctness Patterns | 8/10 |

**Strengths:**
- Dictionary lookup for O(1) engine config access; `sorted(set(...))` for deterministic dedup; `",".join()` for efficient string assembly.
- No hidden quadratic behavior; all iterations over bounded collections (n < 80).
- Single-threaded scripts with workflow concurrency groups preventing collisions.

**Weaknesses:**
- Dict merge order in `write_outputs` uses parameter shadowing (`config = {**config, ...}`) -- fragile if colliding keys are added -- `engine-config.py:321-327`
- Heredoc delimiter `GH_AW_EOF` has no collision guard -- `engine-config.py:337-339`
- `review-apply` missing from `pr-checks.yml:88` directory validation loop.
- Skill list invariant already violated -- no automated enforcement exists.

---

### Process -- 7.4/10 ⚠️

| Dimension | Score |
|-----------|-------|
| Documentation Quality | 8/10 |
| Development Workflow | 8/10 |
| Code Review Practices | 6/10 |
| Dependency Management | 7/10 |
| Project Organization | 9/10 |
| Portability | 7/10 |
| Technical Leadership | 7/10 |

**Strengths:**
- Comprehensive documentation: README, SETUP (5 platforms), CONTRIBUTING, RUN (6 runbooks), ADR, incident-response.
- PR-gated CI with 4 parallel jobs; Dependabot active; SHA-pinned actions.
- Clean `review-<domain>/` directory structure with consistent naming.
- ADR 0001 documents the skill-based architecture decision with alternatives and rationale.

**Weaknesses:**
- Most commits go directly to `main` without PRs, bypassing the PR template checklist and CI checks.
- No linting enforcement (no shellcheck, yamllint, markdownlint).
- No CODE_OF_CONDUCT.md despite the process checklist calling for one.
- Only 1 ADR; subsequent decisions (multi-engine, gh-aw, review-apply) lack formal ADRs.
- No CHANGELOG, release tags, or semantic versioning.

---

### Maintainability -- 7.8/10 ⚠️

| Dimension | Score |
|-----------|-------|
| Structural Complexity | 8/10 |
| Understandability | 9/10 |
| Technical Debt Indicators | 7/10 |
| Coupling/Dependency Depth | 8/10 |
| Code Smell Density | 7/10 |

**Strengths:**
- All executable files well under size limits; `engine-config.py` cleanly segmented at 367 lines; `main()` is 8 lines.
- Zero TODO/FIXME/HACK in project code; zero lint suppressions; zero dead code.
- Excellent naming and consistent patterns across all 13 skills.

**Weaknesses:**
- Skill list duplicated in 10+ locations (shotgun surgery); `review-apply` already inconsistent.
- `_TOOLCACHE_PATH` (engine-config.py:149-152) uses multi-layer Python/shell quote escaping that is hard to read.
- `fitness-review.yml` at 1150 lines is the one complexity outlier (platform constraint).

---

## References

Based on guidance from https://jeffbailey.us/categories/fundamentals/
