# Definition of Ready: fitness-config-init

## Feature-level validation (applies to US-01..US-06)

| # | DoR Item | Status | Evidence |
|---|---|---|---|
| 1 | Problem statement clear, domain language | PASS | Each story has a Problem section naming a real situation. For example, US-02: "accessibility stays at 8 on a service with no UI". `requirements.md` Context. |
| 2 | User/persona with specific characteristics | PASS | Priya Raman (`ledgerd`, a Postgres service with no UI), Jeff Bailey (`jeffbaileyblog`, a Hugo site), Tomas Okafor (`homelab-cli`), Ana Lima (`geo-notes`, an empty idea folder), Kenji Watanabe (`fieldnotes`, Rails and Postgres, subfolder override) |
| 3 | 3+ domain examples with real data | PASS | Every story has exactly 3 examples (happy, edge, error/boundary) with concrete weights, paths, and file counts |
| 4 | UAT in Given/When/Then, 3-7 per story | PASS | US-01: 5, US-02: 5, US-03: 4, US-04: 5, US-05: 4, US-06: 3 |
| 5 | AC derived from UAT | PASS | Each AC maps to a scenario. The index with verification method is in `acceptance-criteria.md` (32 AC). |
| 6 | Right-sized (1-3 days, 3-7 scenarios) | PASS | Each story is one skill workflow section plus fixtures, estimated at 1-2 days. The feature total of about 6-8 days passed the scope gate in `wave-decisions.md`. |
| 7 | Technical notes: constraints/dependencies | PASS | Each story has Technical Notes. System Constraints cover the stdlib-only rule, no hardcoded baseline, resolver compatibility, and the resolver path convention. |
| 8 | Dependencies resolved or tracked | PASS | Story order runs US-01 -> 02 -> 03 -> 04. US-05 depends on `skills/review-full`, and US-03 depends on `fitness-config.py validate|show --path`; both exist and have shipped. Design unknowns are tracked as DQ-1..DQ-8 and do not block DESIGN, which owns them. |
| 9 | Outcome KPIs with measurable targets | PASS | Every story has Who / Does what / By how much / Measured by / Baseline. The feature KPIs are in `outcome-kpis.md` (KPI-1..5 with guardrails). |

## Additional gates

| Gate | Status | Evidence |
|---|---|---|
| `job_id` on every story | PASS (conditional) | All six stories carry `J-FCI-01`. `docs/product/jobs.yaml` is absent, and the JTBD phase was skipped by instruction. Tracked as DQ-8. |
| Elevator Pitch on every non-infrastructure story | PASS | All six stories have Before/After/Decision. Each After names the `/fitness-config-init` entry point and concrete output text. |
| Anti-patterns | PASS | No Implement-X titles, no generic data, and no technical scenario titles. Titles describe outcomes, such as "Declining keeps the current config". |
| Solution neutrality | PASS | Validation mechanics, rationale storage, and the profile approach are deferred to DESIGN (DQ-1, DQ-4, DQ-6). |

## DoR Status: PASSED

## Peer Review (nw-product-owner-reviewer, iteration 1)

The review was approved with 0 blocking issues and 9/9 DoR items passing. It found no anti-patterns, and the Elevator Pitch test passed for all 6 stories.

- High (1): DQ-8, the missing `docs/product/jobs.yaml`. It was accepted as known and non-blocking.
- Medium (2): DQ-3 (two default sources) and DQ-6 (stdlib schema validation and the python3 fallback). Both are routed to DESIGN.

No iteration 2 was needed.
