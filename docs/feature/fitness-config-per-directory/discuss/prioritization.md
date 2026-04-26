# Prioritization: fitness-config-per-directory

## Release Priority

| Priority | Release | Target Outcome | KPI | Rationale |
|----------|---------|---------------|-----|-----------|
| 1 | Walking Skeleton | End-to-end override flow works | At least one module-scoped review reflects override weights AND report header proves it | Validates riskiest assumption: that the resolver-as-single-source-of-truth pattern is feasible. Without this, nothing else is worth building. |
| 2 | Authoring & Validation | High-confidence override authoring | 90%+ of authoring attempts produce valid configs on first commit | Reduces foot-gun rate; without it, adoption stalls because users get burned by silent fallback or weight-sum errors. |
| 3 | Per-domain coverage | All domain skills honor overrides | 100% of `review-<domain>` skills produce identical effective-weights line in their report headers when scope is in an override directory | Prevents partial coverage. The mechanism exists in v1 only for review-full; this release makes it consistent everywhere. |

## Backlog Suggestions

(Story IDs assigned in Phase 4; here they are placeholders.)

| Story | Release | Priority | Outcome Link | Dependencies |
|-------|---------|----------|--------------|--------------|
| US-01: Resolver walks up to find nearest config | WS | P1 | KPI-1 (override applied) | None |
| US-02: Resolver merges child over root and exposes effective config | WS | P1 | KPI-1 | US-01 |
| US-03: review-full report header names config sources | WS | P1 | KPI-2 (Devin trusts the report) | US-02 |
| US-04: `show --path` subcommand displays merged config | R1/WS | P1 | KPI-3 (Devin can preview before running review) | US-02 |
| US-05: `validate --path` checks effective merged sum to 100 | R2 | P2 | KPI-4 (high-confidence authoring) | US-02 |
| US-06: `init --path` scaffolds override with inheritance comments | R2 | P3 | KPI-5 (lower authoring effort) | US-05 |
| US-07: Schema version mismatch produces clear error | R2 | P3 | KPI-4 | US-05 |
| US-08: Each domain skill calls resolver and reports config provenance | R3 | P4 | KPI-6 (consistency across all domains) | US-02, US-03 |

## Riskiest Assumption Ordering

1. **Resolver can be single source of truth without breaking existing skills**: Validated by US-01 + US-02 + US-03. If review-full can be retrofitted to call the resolver without regressions, all other skills can.
2. **Walk-up rule matches user mental model**: Validated by US-01 acceptance criteria (Gherkin scenarios for nested files).
3. **Report header is enough provenance**: Validated by US-03; if Devin still asks "did my config get used?", the header design failed.

## Value/Effort Matrix

| | Low Effort | High Effort |
|---|---|---|
| **High Value** | US-03 (header line, content already in resolver) | US-01 + US-02 (the resolver itself — strategic core) |
| **Low Value** | US-06 (init helper, nice-to-have) | US-08 (per-domain rollout — necessary but mechanical) |

Quick wins: US-03 builds momentum (very visible, low effort once US-02 lands).
Strategic investment: US-01 + US-02 — the rest of the feature depends on getting these right.
