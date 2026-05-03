# Outcome KPIs: fitness-config-per-directory

## Feature: fitness-config-per-directory

### Objective
Devin Park (and engineers like him) trust fitness reviews on multi-module repos because module-specific weights are applied automatically and the report makes the applied config visible.

---

### Outcome KPIs (Epic-Level)

| # | Who | Does What | By How Much | Baseline | Measured By | Type |
|---|-----|-----------|-------------|----------|-------------|------|
| 1 | Engineers reviewing module subtrees | Have module-specific weights applied to their reviews | 100% of review-target paths under an override directory pick up that override | 0% (feature does not exist) | Functional test: 5 representative target paths, assert resolver source chain | Leading (primary) |
| 2 | Anyone reading a fitness report | Identifies which config drove the scores without reading code | 100% of reports include Config: and Effective weights: header lines | 0% (no header lines today) | Grep functional test on generated reports | Leading (primary) |
| 3 | Override authors | Author valid overrides that pass validation on first attempt | 90% first-attempt success rate | N/A (no overrides today) | CI telemetry on `validate --path` exit codes; ratio pass-on-first vs. fail-then-retry | Leading (secondary) |
| 4 | Per-domain skill users | See the same override applied whether they run review-full or review-<domain> | 100% per-domain skill coverage | 0% | Functional test gate: per-skill override-aware scenario | Leading (secondary) |

---

### Story-Level KPI Mapping

| Story | Contributes to KPI |
|-------|-------------------|
| US-01: Walk-up resolver | KPI 1 (override applied) |
| US-02: Merge and validate | KPI 1, KPI 3 (valid overrides) |
| US-03: Report header provenance | KPI 2 (visible config) |
| US-04: Show subcommand | KPI 3 (preview supports first-attempt success) |
| US-05: Validate subcommand | KPI 3 (validation gate) |
| US-06: Init helper | KPI 3 (lower authoring effort) |
| US-07: Schema version mismatch | KPI 1 (correctness) |
| US-08: All domain skills honor override | KPI 4 (per-domain coverage) |

---

### Metric Hierarchy

- **North Star**: KPI 1 — "100% of subtree reviews under an override directory pick up that override". Without this, the feature has no purpose.
- **Leading Indicators (predict North Star adoption)**:
  - KPI 2: visible header lines drive trust → users actually use the feature
  - KPI 3: low authoring friction → users create overrides in the first place
  - KPI 4: per-domain consistency → users don't get burned by inconsistent behavior, retain trust
- **Guardrail Metrics (must NOT degrade)**:
  - Existing `tests/functional-tests.md` continues to pass unchanged (NFR-3 backward compatibility)
  - Resolver overhead < 100 ms (NFR-1)
  - Resolver output deterministic across runs (NFR-2)
  - No silent fallback to root config on validation failure (NFR-4)

---

### Measurement Plan

| KPI | Data Source | Collection Method | Frequency | Owner |
|-----|------------|-------------------|-----------|-------|
| KPI 1: Override applied | Resolver functional tests | Test corpus of 5 target paths (deep nested, sibling, root, no-override, no-config) | Per CI run | Skill maintainer |
| KPI 2: Header lines visible | Functional test grep over report outputs | Grep for `Config:` and `Effective weights:` in first 10 lines of every generated report | Per CI run | Skill maintainer |
| KPI 3: First-attempt success | CI telemetry on `validate` exit codes (where available); fallback: manual sampling of PR history if telemetry unavailable | Track ratio of `validate` runs passing on first attempt vs. requiring iteration in PRs | Per release | Skill maintainer |
| KPI 4: Per-domain coverage | `tests/functional-tests.md` extended | At least one override-aware scenario per `review-<domain>` skill | Per CI run | Skill maintainer |

Guardrail measurement:
- Existing functional tests run unchanged, no failures introduced
- Benchmark `fitness-config.py show --path <deep>` 10x in 10k-file fixture, assert avg < 100ms
- Run resolver twice on same input, byte-compare output
- Run validate with deliberately broken configs, assert exit code 1 and no downstream review starts

---

### Hypothesis

We believe that a per-directory `fitness-config.json` discovery + merge mechanism with visible report provenance for engineers maintaining multi-module repos will achieve module-appropriate scoring that engineers trust enough to act on.

We will know this is true when:
- 100% of subtree reviews under an override directory pick up that override (KPI 1)
- 100% of reports include Config: and Effective weights: header lines (KPI 2)
- 90% of override authoring attempts produce valid configs on first commit (KPI 3)
- 100% of per-domain skills honor overrides consistently (KPI 4)

---

### Customer Factory (AARRR) Mapping

| Stage | Mapping for this feature |
|-------|--------------------------|
| Acquisition | Discoverability via README/SETUP.md mention + `init --path` and `show --path` subcommands |
| **Activation** | First time an engineer drops an override, runs review, sees the Config: line in the report header confirming it was applied (this is the "aha moment" — KPI 1 + KPI 2) |
| Retention | Per-domain consistency (KPI 4) prevents user from getting burned and abandoning the feature |
| Revenue | N/A (open-source skill repo) |
| Referral | Engineers recommending the pattern to peers maintaining their own multi-module repos |

Activation is causal here: if KPI 1 + KPI 2 land on first use, retention follows.

---

### Handoff to DEVOPS (platform-architect)

For instrumentation planning:

1. **Data collection requirements**:
   - `validate` exit codes per invocation (for KPI 3 first-attempt success rate)
   - Resolver execution time (for NFR-1 guardrail)
   - Per-domain skill report generation success/failure (for KPI 4)
2. **Dashboard / monitoring needs**:
   - Functional test pass rate trend (CI dashboard)
   - Benchmark trend for resolver overhead (CI artifact + chart)
3. **Alerting thresholds**:
   - Any guardrail breach (existing tests fail, resolver > 100ms, non-deterministic output) blocks merge
4. **Baseline measurement**:
   - Pre-feature: capture current report structure (no Config: line) to confirm KPI 2 baseline of 0%
   - Pre-feature: capture current resolver overhead (zero, since resolver doesn't exist) to set NFR-1 baseline
