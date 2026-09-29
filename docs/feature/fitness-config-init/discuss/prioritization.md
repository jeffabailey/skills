# Prioritization: fitness-config-init

Score = Value x Urgency / Effort (1-5 each). Ties are broken in this order: Walking Skeleton, then Riskiest Assumption, then Value.

## Release Priority

| Priority | Release | Target Outcome | KPI | Rationale |
|---|---|---|---|---|
| 1 | Walking Skeleton (US-01..03) | Explained, valid, purpose-tuned config written for a fresh project | KPI-1, KPI-2 | Validates the core assumption that fast-scan evidence produces acceptable weights |
| 2 | R1 (US-04) | Re-tune existing configs without loss | KPI-3 | Removes the only data-loss path and enables repeat use |
| 3 | R2 (US-05) | Full-review evidence improves acceptance | KPI-4 | High value, high cost; builds on the skeleton format |
| 4 | R3 (US-06) | Purpose-tuned thresholds | KPI-1 (guardrail) | Incremental; defaults are already reasonable |

## Backlog

| Story | Release | MoSCoW | V | U | E | Score | Outcome link | Depends on |
|---|---|---|---|---|---|---|---|---|
| US-01 Classify project purpose from a fast scan | WS | Must | 5 | 5 | 2 | 12.5 | KPI-1 | none |
| US-02 Propose purpose-tuned weights with a reason for each change | WS | Must | 5 | 5 | 2 | 12.5 | KPI-1 | US-01 |
| US-03 Write only a valid config, never over an existing one | WS | Must | 5 | 5 | 2 | 12.5 | KPI-2 | US-02; existing `fitness-config.py validate` |
| US-04 Review a diff before replacing an existing config | R1 | Must | 4 | 4 | 2 | 8.0 | KPI-3 | US-03 |
| US-05 Use a full review to sharpen the proposal | R2 | Should | 4 | 2 | 3 | 2.7 | KPI-4 | US-02; `skills/review-full` |
| US-06 Tune thresholds and security cutoff to purpose | R3 | Could | 2 | 2 | 2 | 2.0 | KPI-1 | US-02 |
