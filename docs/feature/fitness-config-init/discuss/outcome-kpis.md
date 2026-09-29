# Outcome KPIs: fitness-config-init

## Feature: fitness-config-init

### Objective

Within a month of release, maintainers starting fitness reviews get weights that fit their project on the first try, and they understand why.

### Outcome KPIs

| # | Who | Does What | By How Much | Baseline | Measured By | Type |
|---|---|---|---|---|---|---|
| KPI-1 (North Star) | Maintainers running the skill | Accept the proposed weights with at most 1 manual adjustment | 80% or more of runs | 0%: every tuned config today is hand-edited from the example | Dogfood log over 10 repos (repo, purpose, adjustments, accepted y/n) | Leading |
| KPI-2 | Maintainers who ran the skill | Run review-full afterward with no config error | 100% of skill-written files pass `fitness-config.py validate` | Unmeasured for hand-edited configs | Functional tests (AC-03.1) plus dogfood log | Leading (guardrail) |
| KPI-3 | Maintainers with an existing config | Re-run the skill without losing an edit they did not approve | 0 unconfirmed overwrites; 60% or more of re-runs end in an accepted overwrite | The skeleton refuses 100% | Functional tests (AC-04.2) plus dogfood log | Leading |
| KPI-4 | Maintainers choosing full mode | Accept proposals with no adjustment | At least 10 percentage points above the fast-mode rate | Fast-mode rate from KPI-1 | Dogfood log split by mode | Leading |
| KPI-5 | Maintainers | Accept the classified purpose without correction | 80% or more of runs | None | Dogfood log | Leading |

### Metric Hierarchy

- **North Star**: KPI-1, acceptance with at most one adjustment.
- **Leading indicators**: KPI-5 (classification accepted) predicts KPI-1. KPI-4 shows whether full mode is worth its cost.
- **Guardrails**:
  - KPI-2 (validity) must stay at 100%.
  - KPI-3 unconfirmed overwrites must stay at 0.
  - The fast scan must finish in under 2 minutes (NFR-5).
  - The fast scan must write no files outside `fitness-config.json` (NFR-1).

### Measurement Plan

| KPI | Data Source | Collection Method | Frequency | Owner |
|---|---|---|---|---|
| KPI-1, 4, 5 | Dogfood log (`docs/feature/fitness-config-init/deliver/dogfood-log.md`, created in DELIVER) | Manual entry per run by the maintainer | Per run, reviewed after 10 runs | Jeff Bailey |
| KPI-2, 3 | `tests/functional-tests.md` scenarios | Functional test run | Every change to the skill | Jeff Bailey |

No telemetry exists or is proposed. This is a local agent skill, and the dogfood log is sufficient at this scale.

### Hypothesis

We believe that proposing purpose-tuned weights with evidence-backed reasons, for maintainers adopting fitness reviews, will replace hand-editing the example config. We will know this is true when 80% of runs across 10 dogfood repos are accepted with at most one adjustment.
