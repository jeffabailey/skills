# Project Fitness Report

**Date:** 2026-02-26
**Scope:** Entire repository — 12 skill directories (SKILL.md + checklists), CI/CD workflows, engine-config.py, test scripts, and documentation.
**Architecture type:** Documentation/skills library — no traditional application code, no database, no frontend.

## Overall Score: 7.3 / 10

| Domain | Score | Status |
|--------|-------|--------|
| Architecture | 8.1/10 | ✅ Healthy |
| Security | 8.5/10 | ✅ Healthy |
| Reliability | 5.6/10 | ⚠️ Needs Attention |
| Testing | 4.2/10 | ❌ Critical |
| Performance | 7.6/10 | ⚠️ Needs Attention |
| Algorithms | 7.8/10 | ⚠️ Needs Attention |
| Data | — | ⏭️ Skipped (no DB) |
| Accessibility | — | ⏭️ Skipped (no frontend) |
| Process | 7.4/10 | ⚠️ Needs Attention |
| Maintainability | 7.4/10 | ⚠️ Needs Attention |

**Status:** 8-10 = ✅ Healthy, 5-7 = ⚠️ Needs Attention, 1-4 = ❌ Critical

**Skipped domains (weights redistributed):** Data (no SQL, migrations, or ORM code), Accessibility (no HTML/CSS/JSX/TSX).
**Redistributed weights:** Architecture 17.1%, Security 17.1%, Reliability 12.2%, Testing 12.2%, Performance 12.2%, Algorithms 12.2%, Process 9.8%, Maintainability 7.3%.

---

## Top 10 Action Items (Priority Order)

1. **[HIGH]** Fix scoring weight inconsistency in `docs/index.md` — shows Architecture/Security at 15%, omits Maintainability entirely; contradicts the canonical 14%/6% in 4 other files — `docs/index.md:40-49`
2. **[HIGH]** Pin actions in `pr-checks.yml` to full SHA hashes — uses mutable `@v4`/`@v5` tags while `fitness-review.yml` correctly uses SHA pins; supply chain risk — `.github/workflows/pr-checks.yml:22,25,51,60`
3. **[HIGH]** Fix stale CONTRIBUTING.md section requirements — states SKILL.md must have `## Triggers` and `## Scoring` sections, but actual skills use frontmatter for triggers and `## Scoring Dimensions` for scoring — `CONTRIBUTING.md:32`
4. **[HIGH]** Run `workflow-tests.sh` in CI (non-act subset) — 30+ assertions in `workflow-tests.sh` are not run in any CI workflow; extract the non-`act` tests into a CI-runnable script — `tests/workflow-tests.sh`
5. **[HIGH]** Add Dependabot for GitHub Actions — no automated dependency monitoring for pinned action SHAs or engine CLI versions — `.github/dependabot.yml` (missing)
6. **[MEDIUM]** Fix `write_outputs` dict merge order — `**config` spread overwrites explicit `engine_id`/`detection_*` keys if they ever collide; swap to safe order — `.github/scripts/engine-config.py:319-325`
7. **[MEDIUM]** Add alerting for workflow failures — no mechanism to detect failures beyond manually checking Actions tab — `.github/workflows/fitness-review.yml`
8. **[MEDIUM]** Delete stale `docs/process-fitness-report.md` — old report predates the naming fix; references outdated findings (claims "No CONTRIBUTING.md", "No .gitignore") — `docs/process-fitness-report.md`
9. **[MEDIUM]** Separate stderr from stdout in `workflow-tests.sh` — `2>&1` on engine-config invocation could mix Python warnings into grepped output — `tests/workflow-tests.sh:70`
10. **[LOW]** Add `.env*` and credential file patterns to `.gitignore` — defensive measure against accidental secret commits — `.gitignore`

---

## Domain Details

### Architecture — 8.1/10

| Dimension | Score | Evidence |
|-----------|-------|----------|
| Coupling | 8/10 | One-way dependency graph; `review-full` orchestrates, no skill depends on another; skill list repeated in 8 locations creates data coupling |
| Cohesion | 9/10 | Each skill directory has single clear responsibility; SKILL.md + checklist separation is clean |
| Layering | 8/10 | Skills / checklists / docs / tests / CI layers are identifiable; `fitness-review-prompt.md` partially duplicates `review-full/SKILL.md` |
| Modularity | 9/10 | Consistent `review-<domain>/SKILL.md` interface; adding/removing skills documented in CONTRIBUTING.md |
| Naming | 8/10 | All skills follow `review-<domain>` convention; output paths follow `docs/<domain>-review.md` convention (process path now fixed) |
| API Design | 7/10 | Trigger phrases well-scoped; ADR 0001 documents overlap resolution; weight inconsistency in `docs/index.md:40-49` |
| Maintainability | 8/10 | All SKILL.md under 300 lines; PR checks enforce structural correctness; domain list documented in CONTRIBUTING.md |

**Strengths:** No circular dependencies; consistent skill structure; ADR 0001 explains key design trade-off; PR checks validate structure and report path convention on every PR.

**Gaps:** Weight inconsistency in `docs/index.md`; `fitness-review-prompt.md` and `review-full/SKILL.md` are near-duplicates; CLAUDE.md and AGENTS.md contain identical content requiring manual sync.

---

### Security — 8.5/10

| Dimension | Score | Evidence |
|-----------|-------|----------|
| Input Validation | 9/10 | Workflow input constrained to `type: choice`; `argparse` with `choices=` in engine-config.py; safe output sanitization |
| Authentication/Authorization | 9/10 | `permissions: {}` at workflow root; per-job least-privilege scoping; `persist-credentials: false` on all checkouts |
| Data Protection | 8/10 | Secrets via GitHub Secrets; ephemeral keys masked immediately; log redaction on `always()`; `.gitignore` missing `.env` patterns |
| Dependency Security | 7/10 | `fitness-review.yml` pins all actions by SHA; `pr-checks.yml` uses unpinned `@v4`/`@v5` tags — inconsistent |
| Error Handling/Logging | 8/10 | `redact_secrets.cjs` covers 6 secret names; telemetry/error reporting disabled; `set -euo pipefail` in test scripts |
| Cryptography | 9/10 | `openssl rand -base64 45` (~360 bits entropy); no weak algorithms; no hardcoded keys |

**Strengths:** Exemplary least-privilege permissions model; SHA-pinned actions in main workflow; network allowlists per engine; ephemeral keys with immediate masking.

**Gaps:** `pr-checks.yml` uses unpinned action tags (supply chain risk); `.gitignore` missing `.env*` patterns; `*.githubusercontent.com` wildcard in Claude domain allowlist.

---

### Reliability — 5.6/10

| Dimension | Score | Evidence |
|-----------|-------|----------|
| Observability | 3/10 | Visibility limited to GitHub Actions run logs; no metrics, dashboards, structured logging, or alerting |
| Availability Design | 6/10 | Multi-engine failover; concurrency group prevents collisions; content via GitHub (high availability) |
| Timeout/Retry Hygiene | 6/10 | Good timeout layering (bash 60s < MCP 120s < agent 30min); detection step timeout (20min) exceeds its job timeout (10min) |
| CI/CD Maturity | 7/10 | PR checks + scheduled + manual dispatch; action versions pinned; `skill-structure-tests.sh` runs in CI |
| Incident Readiness | 5/10 | `incident-response.md` with severity levels; `RUN.md` covers 6 failure modes; no alerts, no postmortem template |
| Capacity Planning | 4/10 | Concurrency limits present; no documented API quotas, run durations, or runner-minute costs |
| Container/Deploy Hygiene | 8/10 | Least-privilege permissions; `persist-credentials: false`; domain allowlists; container images pinned by tag |

**Strengths:** Multi-engine failover architecture; incident-response.md and expanded RUN.md troubleshooting; least-privilege permissions.

**Gaps:** No observability beyond Actions UI; no alerting for failures; detection step/job timeout mismatch; no capacity documentation.

---

### Testing — 4.2/10

| Dimension | Score | Evidence |
|-----------|-------|----------|
| Test Pyramid Balance | 4/10 | Two automated bash scripts (structural); two manual test plans (100+ scenarios); no automated integration/E2E tests |
| Test Quality | 6/10 | Bash scripts have clear pass/fail naming; manual tests follow Given/When/Then; no expected-vs-actual output on failure |
| Coverage Strategy | 3/10 | No coverage tooling; engine-config.py partially covered by CI; skill behavior untested in CI |
| Performance Testing | 1/10 | No benchmarks; N/A for this repo type |
| Debugging Support | 4/10 | Descriptive PASS/FAIL messages; `set -euo pipefail`; no structured logging or reproduction helpers |
| CI Integration | 5/10 | `pr-checks.yml` runs `skill-structure-tests.sh` on every PR; `workflow-tests.sh` not run in CI (requires `act`) |

**Strengths:** `skill-structure-tests.sh` (56 assertions) runs in CI on every PR; manual test plans are well-structured with positive and negative cases; PR template reminds contributors to run `workflow-tests.sh` locally.

**Gaps:** Testing remains the highest-priority gap. `workflow-tests.sh` not in CI; no automated skill behavior tests; `pr-checks.yml` duplicates some `workflow-tests.sh` logic; no expected-vs-actual diagnostics in test failures.

---

### Performance — 7.6/10

| Dimension | Score | Evidence |
|-----------|-------|----------|
| Algorithmic Efficiency | 9/10 | O(1) dict lookup; `_domains()` with `sorted(set(...))` on bounded lists; all operations linear or better |
| Parallel Execution Design | 9/10 | `review-full/SKILL.md` launches domain reviews concurrently; smart domain skipping |
| Caching Strategy | 6/10 | Module-level domain dedup; `package-manager-cache: false` forces full npm install per run; Docker images pulled fresh each run |
| Scalability Readiness | 7/10 | Multi-engine architecture easily extensible; top-level concurrency group prevents parallel runs |
| Resource Utilization | 8/10 | Sparse checkout in activation job; bounded `find` with `maxdepth 4`; 1-day artifact retention |
| Data Pipeline Efficiency | 7/10 | Delta-aware review scope via `git diff`; no skip-if-no-changes for scheduled runs |

**Strengths:** Excellent data structure usage in engine-config.py; parallel review design; efficient checkout strategy; bounded resource usage.

**Gaps:** No npm/Docker caching across runs; single-agent bottleneck in CI (all domains in one session); weekly runs re-analyze entire codebase even without changes.

---

### Algorithms — 7.8/10

| Dimension | Score | Evidence |
|-----------|-------|----------|
| Algorithm Choice | 8/10 | Dictionary lookup, `",".join()`, `sorted()` — all appropriate for problem domain |
| Data Structure Selection | 8/10 | `ENGINES` dict for O(1) key access; lists for concatenation; sets for dedup — correct patterns |
| Complexity Awareness | 9/10 | No hidden quadratic behavior; all iterations over small, bounded (n<=57) collections |
| Concurrency Safety | 8/10 | Single-threaded scripts; workflow concurrency groups prevent collisions; no shared mutable state |
| Edge Case Handling | 6/10 | Dict merge order bug in `write_outputs` (explicit keys overwritten by `**config` spread); heredoc delimiter collision risk; stderr mixed into test output |
| Correctness Patterns | 8/10 | Deterministic output (sorted keys/domains); guaranteed loop termination; idempotent engine-config.py |

**Strengths:** Clean implementation with no overengineering; deterministic output via sorted iteration; version constants as single source of truth for install commands.

**Gaps:** `write_outputs` dict merge order (`engine-config.py:319-325`) lets `**config` overwrite explicit keys; `GH_AW_EOF` heredoc delimiter has no collision guard; `workflow-tests.sh:70` mixes stderr into grepped output.

---

### Process — 7.4/10

| Dimension | Score | Evidence |
|-----------|-------|----------|
| Documentation Quality | 9/10 | README, SETUP, CONTRIBUTING, RUN.md, ADR, incident-response.md — comprehensive and cross-linked; `docs/index.md` has stale weights |
| Development Workflow | 8/10 | PR-gate CI with 3 validation jobs; fitness-review on schedule + manual dispatch; no commit convention enforcement |
| Code Review Practices | 7/10 | PR template with 5-item checklist; CODEOWNERS; issue templates; single-maintainer limits multi-reviewer evidence |
| Dependency Management | 5/10 | Actions pinned to SHA; engine versions pinned; no Dependabot/Renovate; no vulnerability scanning |
| Project Organization | 9/10 | Consistent `review-<domain>/` structure; tests, docs, CI cleanly separated; comprehensive `.gitignore`; `catalog-info.yaml` |
| Portability | 7/10 | Markdown/YAML inherently portable; symlink install; no Windows path handling documented |
| Technical Leadership Signals | 7/10 | ADR with alternatives and rationale; design article cross-linked; incident response; no changelog or roadmap |

**Strengths:** Documentation is the strongest area — README, SETUP, CONTRIBUTING, RUN.md, and ADR work together well. PR checks pipeline validates structure on every PR. CODEOWNERS and templates establish contributor workflow.

**Gaps:** No Dependabot for automated dependency updates; `CONTRIBUTING.md:32` documents section requirements that don't match actual SKILL.md structure; no changelog or release tagging; no Windows support documented.

---

### Maintainability — 7.4/10

| Dimension | Score | Evidence |
|-----------|-------|----------|
| Structural Complexity | 8/10 | All SKILL.md under 300 lines; engine-config.py at 365 lines with flat structure; max nesting depth 2; no function over 25 lines |
| Understandability | 7/10 | Consistent `review-<domain>` naming; SKILL.md internal structure uniform; `_TOOLCACHE_PATH` shell string hard to parse; scoring section headers inconsistent |
| Technical Debt | 6/10 | Zero TODO/FIXME in code; weight inconsistency in `docs/index.md`; stale `docs/process-fitness-report.md`; CONTRIBUTING.md section requirements stale |
| Coupling Depth | 9/10 | Flat module structure; skills fully independent; engine-config.py self-contained with stdlib only |
| Code Smell Density | 7/10 | Skill list duplicated in 10+ locations (shotgun surgery); `review-accessibility/SKILL.md` uses different scoring section header than all other skills; stale report artifacts |

**Strengths:** All files are readable and consistently structured; engine-config.py cleanly separates data from logic; zero TODO/FIXME/HACK markers; zero lint suppressions.

**Gaps:** Skill list duplication across 10+ locations is the most significant maintainability risk; CONTRIBUTING.md documents conventions that don't match reality; stale reports and weight inconsistency indicate manual sync has already failed.

---

## Previous Review Comparison (2026-02-22 → 2026-02-26)

| Domain | Previous | Current | Change |
|--------|----------|---------|--------|
| Architecture | 7.6 | 8.1 | +0.5 |
| Security | 8.7 | 8.5 | -0.2 |
| Reliability | 5.0 | 5.6 | +0.6 |
| Testing | 3.8 | 4.2 | +0.4 |
| Performance | 7.8 | 7.6 | -0.2 |
| Algorithms | 8.2 | 7.8 | -0.4 |
| Process | 7.0 | 7.4 | +0.4 |
| Maintainability | — | 7.4 | New |
| **Overall** | **7.0** | **7.3** | **+0.3** |

**What improved:** PR-triggered CI (`pr-checks.yml`), `skill-structure-tests.sh` (56 automated tests), expanded RUN.md troubleshooting (6 failure modes), `incident-response.md`, CODEOWNERS, issue/PR templates, `.gitignore`, process report path fix, engine-config.py readability improvements.

**What remains:** Testing automation (workflow-tests.sh not in CI), observability/alerting, stale documentation (`docs/index.md` weights, `docs/process-fitness-report.md`, `CONTRIBUTING.md:32`), dependency automation (no Dependabot), and the engine-config.py `write_outputs` dict merge order bug.

---

## References

Based on guidance from https://jeffbailey.us/categories/fundamentals/
