# Definition of Ready: fitness-config-per-directory

Each user story validated against the 9-item DoR. Stories pass ALL items before handoff to DESIGN wave.

---

## US-01: Walk-Up Resolver Finds Nearest Config

| DoR Item | Status | Evidence/Issue |
|----------|--------|----------------|
| 1. Problem statement clear, domain language | PASS | "Devin maintains 12 Terraform modules; today only root config is read; he wants nearest-ancestor config applied automatically" |
| 2. User/persona with specific characteristics | PASS | Devin Park, infrastructure engineer, multi-module homelab repo |
| 3. 3+ domain examples with real data | PASS | postgresql/main.tf (override hit), postgresql/scripts/migrate.sh (walk past), networking/main.tf (root fallback) — real module names |
| 4. UAT in Given/When/Then (3-7 scenarios) | PASS | 4 scenarios (override hit, walk past, root fallback, defaults fallback) |
| 5. AC derived from UAT | PASS | AC-01.1 through AC-01.6 trace to specific UATs |
| 6. Right-sized (1-3 days, 3-7 scenarios) | PASS | Pure resolver function, ~1-2 days, 4 scenarios |
| 7. Technical notes: constraints/dependencies | PASS | "Walk-up stops at .git or filesystem root; use Path.resolve() for symlinks" |
| 8. Dependencies resolved or tracked | PASS | Existing `scripts/fitness-config.py` (modified); no blockers |
| 9. Outcome KPIs defined | PASS | KPI 1: 100% of subtree paths pick up nearest override |

**Status: PASS**

---

## US-02: Effective Config Merge with Validation

| DoR Item | Status | Evidence/Issue |
|----------|--------|----------------|
| 1. Problem statement clear | PASS | "Override might redefine only some weights; user wants minimal-diff configs but valid sum-100 effective result" |
| 2. User/persona | PASS | Override author (infrastructure engineer authoring module configs) |
| 3. 3+ domain examples | PASS | Partial override valid sum, full override valid sum, partial override sum=95 (error) |
| 4. UAT scenarios | PASS | 4 scenarios (partial valid, full override, sum-error, non-weight key merge) |
| 5. AC from UAT | PASS | AC-02.1 through AC-02.7 trace to UATs |
| 6. Right-sized | PASS | ~1-2 days; merge + validate logic |
| 7. Technical notes | PASS | "Extend merge_defaults() to chain; validate post-merge; preserve existing validate_config()" |
| 8. Dependencies | PASS | Depends on US-01 (resolver chain). Tracked. |
| 9. Outcome KPIs | PASS | KPI 1 (override applied correctly), KPI 3 (validation catches errors) |

**Status: PASS**

---

## US-03: Report Header Names Config Sources and Effective Weights

| DoR Item | Status | Evidence/Issue |
|----------|--------|----------------|
| 1. Problem statement clear | PASS | "Devin can't trust review unless header proves which config was applied" |
| 2. User/persona | PASS | Anyone reading a report (Devin, peers, CI consumers) |
| 3. 3+ domain examples | PASS | Override applied, root-only, no-config-anywhere |
| 4. UAT scenarios | PASS | 3 scenarios covering override, root-only, defaults |
| 5. AC from UAT | PASS | AC-03.1 through AC-03.7 trace to UATs |
| 6. Right-sized | PASS | ~1 day; header writer modification |
| 7. Technical notes | PASS | "Resolver called once; output drives both scoring and header; weights ordered by descending value" |
| 8. Dependencies | PASS | Depends on US-01, US-02. Tracked. |
| 9. Outcome KPIs | PASS | KPI 2: 100% of reports include header lines |

**Status: PASS**

---

## US-04: Show Subcommand Displays Resolved Config

| DoR Item | Status | Evidence/Issue |
|----------|--------|----------------|
| 1. Problem statement clear | PASS | "User wants to preview config without running full review" |
| 2. User/persona | PASS | Override authors and review consumers |
| 3. 3+ domain examples | PASS | Override preview, root-only preview, defaults preview |
| 4. UAT scenarios | PASS | 3 scenarios |
| 5. AC from UAT | PASS | AC-04.1 through AC-04.6 |
| 6. Right-sized | PASS | ~0.5-1 day; argparse extension + table renderer |
| 7. Technical notes | PASS | "Reuse cmd_show; add --path arg; preserve no-arg behavior" |
| 8. Dependencies | PASS | US-01, US-02 |
| 9. Outcome KPIs | PASS | KPI 3: lowers authoring friction via preview |

**Status: PASS**

---

## US-05: Validate Subcommand Checks Effective Merged Config

| DoR Item | Status | Evidence/Issue |
|----------|--------|----------------|
| 1. Problem statement clear | PASS | "Today's validate checks single file; with overrides we need merged-config validation" |
| 2. User/persona | PASS | Override authors and CI pipelines |
| 3. 3+ domain examples | PASS | Partial-merge valid, partial-merge sum=95, schema version mismatch |
| 4. UAT scenarios | PASS | 4 scenarios (valid merge, sum error, version error, no-path preserved) |
| 5. AC from UAT | PASS | AC-05.1 through AC-05.6 |
| 6. Right-sized | PASS | ~1 day |
| 7. Technical notes | PASS | "Reuse validate_config after merge; explicit schema version check; clear error messages" |
| 8. Dependencies | PASS | US-01, US-02 |
| 9. Outcome KPIs | PASS | KPI 3: catches invalid configs before review |

**Status: PASS**

---

## US-06: Init Helper Scaffolds an Override Config

| DoR Item | Status | Evidence/Issue |
|----------|--------|----------------|
| 1. Problem statement clear | PASS | "User doesn't want to handcraft 10-weight JSON; needs a scaffold" |
| 2. User/persona | PASS | First-time override authors |
| 3. 3+ domain examples | PASS | Fresh scaffold, refuse-overwrite, no-root-fallback |
| 4. UAT scenarios | PASS | 3 scenarios |
| 5. AC from UAT | PASS | AC-06.1 through AC-06.5 |
| 6. Right-sized | PASS | ~0.5 day |
| 7. Technical notes | PASS | "Reuse cmd_init; seed from root effective; if schema disallows _comment field, decide in DESIGN" |
| 8. Dependencies | PASS | US-01, US-02 |
| 9. Outcome KPIs | PASS | KPI 3: time-to-first-valid-override < 60s |

**Status: PASS**

---

## US-07: Schema Version Mismatch Produces Clear Error

| DoR Item | Status | Evidence/Issue |
|----------|--------|----------------|
| 1. Problem statement clear | PASS | "Mismatched schema versions in same repo produce undefined merge — needs hard error" |
| 2. User/persona | PASS | Maintainers across branches/forks |
| 3. 3+ domain examples | PASS | Match (success), child newer (error), child older (error) |
| 4. UAT scenarios | PASS | 3 scenarios |
| 5. AC from UAT | PASS | AC-07.1 through AC-07.5 |
| 6. Right-sized | PASS | ~0.5 day |
| 7. Technical notes | PASS | "Schema currently const:1; this story is the migration gate when v2 ships" |
| 8. Dependencies | PASS | US-01 |
| 9. Outcome KPIs | PASS | KPI 1: correctness (no silent merges) |

**Status: PASS**

---

## US-08: All Domain Skills Honor the Override

| DoR Item | Status | Evidence/Issue |
|----------|--------|----------------|
| 1. Problem statement clear | PASS | "Per-domain skill rollout must be complete or users hit inconsistencies" |
| 2. User/persona | PASS | Per-domain skill users |
| 3. 3+ domain examples | PASS | review-security on override, review-data on root-only, review-data on accessibility=0 override |
| 4. UAT scenarios | PASS | 3 scenarios |
| 5. AC from UAT | PASS | AC-08.1 through AC-08.4 |
| 6. Right-sized | PASS | ~2-3 days (mechanical, large surface area). At ceiling — if effort proves higher in DESIGN, split per-domain. |
| 7. Technical notes | PASS | "Lint gate: no direct json.load of fitness-config.json outside resolver" |
| 8. Dependencies | PASS | US-01, US-02, US-03 |
| 9. Outcome KPIs | PASS | KPI 4: 100% per-domain coverage |

**Status: PASS** (with note: this story is at the upper edge of right-sized; revisit during DESIGN if scope grows)

---

## Overall DoR Status: PASSED

All 8 user stories pass all 9 DoR items. Feature is ready for handoff to DESIGN wave.

### Open Questions for DESIGN (do NOT block DoR; tracked for design decisions)
- DQ-1: Discovery rule — walk-up only vs. also explicit `--config` flag (Luna assumed walk-up only for v1)
- DQ-2: Merge semantics — deep-merge per top-level (assumed) vs. full-replacement at top-level keys
- DQ-3: Schema version mismatch — error (assumed) vs. warn-and-proceed
- DQ-4: Where the canonical resolver lives (assumed: `scripts/fitness-config.py`)
- DQ-5: Broad-scope crossing multiple overrides (assumed: ignore subtree configs when scope is broader; document as v1 limitation)

These are design decisions, not requirements gaps. DoR remains PASSED.
