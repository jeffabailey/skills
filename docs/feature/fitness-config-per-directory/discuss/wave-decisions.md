# Wave Decisions: DISCUSS — fitness-config-per-directory

**Wave**: DISCUSS
**Date**: 2026-04-25
**Persona**: Luna (nw-product-owner)
**Feature**: fitness-config-per-directory

---

## Configuration Used

| Setting | Value |
|---------|-------|
| Feature type | infrastructure / tooling |
| Walking skeleton (greenfield) | No (brownfield: fitness-config already exists) |
| UX research depth | Lightweight (single-developer persona) |
| JTBD analysis | No (single clear job) |
| Format | all (visual + yaml + gherkin) |
| Interactive | high — but auto mode active, no questions asked |
| Elicitation depth | comprehensive |
| Output directory | `docs/feature/fitness-config-per-directory/discuss/` |

---

## Phases Executed

- Phase 2: Journey Design (visual + YAML + Gherkin)
- Phase 2.5: User Story Mapping (story map + prioritization)
- Phase 2.7: Scope Assessment — PASS (6-7 stories, 3 releases, ~4-6 days, well within Elephant Carpaccio limits)
- Phase 3: Coherence Validation (shared-artifacts registry)
- Phase 4: Requirements Crafting (requirements + user stories + AC + outcome KPIs)
- Phase 5: DoR validation + peer review (self-review against review-dimensions)

Skipped (per orchestrator config):
- Phase 1.5: JTBD (jtbd_analysis=No)
- Phase 1: Discovery interview (lightweight depth + auto mode; assumptions documented as DQ-1 through DQ-5)

---

## Key Decisions Made

### D-1: Persona = Devin Park, infrastructure engineer
Chose a single concrete persona with a real-world repo structure (12 Terraform modules in a homelab) rather than abstract "developers". All examples use real module names (postgresql, networking, logging) and real file paths.

### D-2: Walk-up discovery as v1 default
Resolver walks up from review target path to find the nearest `fitness-config.json` ancestor. Matches user mental model from `.gitignore`, `.editorconfig`, `.git`. Marked DQ-1 for DESIGN to confirm or override.

### D-3: Deep-merge as v1 default merge semantics
Child overrides root per top-level key, and within `weights`, per domain. Allows partial overrides (low-friction authoring). Marked DQ-2 for DESIGN.

### D-4: Effective weights MUST sum to 100 after merge
Validation runs on the merged effective config, not the override file alone. Allows partial overrides while still enforcing the existing constraint. Captured in BR-1 and AC-02.3.

### D-5: Schema version mismatch is a hard error
Prevents silent surprises. Marked DQ-3 for DESIGN to confirm error vs. warn-and-proceed.

### D-6: Resolver is the single source of truth
No skill loads `fitness-config.json` directly. Captured as BR-5 and FR-7. Lint/grep gate enforces.

### D-7: Report header MUST surface provenance
Without visible Config: and Effective weights: lines in the first 10 lines of every report, the override is invisible and untrustworthy. Captured as US-03 (P1).

### D-8: 3 release slices, walking skeleton first
Release 1 (walking skeleton): override applied + visible in report. Release 2: validation + authoring helpers. Release 3: per-domain coverage. Each release maps to specific outcome KPIs (KPI 1+2, KPI 3, KPI 4).

### D-9: Out of scope for v1 (Won't Have)
- Multiple stacked overrides in one path (DQ-5)
- Glob-based discovery
- Explicit `--config <path>` flag
- Full-replacement merge mode opt-in
- Cross-version migration tooling

---

## Open Questions for DESIGN

| ID | Question | Luna's Assumption |
|----|----------|-------------------|
| DQ-1 | Discovery rule: walk-up only, or also explicit `--config` flag and/or glob? | walk-up only for v1; explicit flag is v2+ |
| DQ-2 | Merge semantics: deep-merge or full-replacement at top-level keys? | deep-merge for weights; future-proof full-replacement opt-in via `mergeMode` field |
| DQ-3 | Schema version mismatch behavior: error / warn / use-child / use-root? | error (hard fail) |
| DQ-4 | Where canonical resolver lives: `scripts/fitness-config.py` only, or embedded into SKILL.md? | single resolver in scripts/, SKILL.md tells skills to call it |
| DQ-5 | Broad scope crossing multiple overrides: which config wins? | v1 ignores subtree configs when scope is broader than any override; documented as known limitation |

DESIGN may revise any assumption. None of these revisions invalidates the user-observable AC (override applied, header proves it, validation catches errors, etc.).

---

## DoR Status

**PASSED** for all 8 user stories. See `dor-checklist.md` for per-story evidence.

---

## Peer Review Outcome

**APPROVED** at iteration 1. See `peer-review.md`.

- 0 critical issues
- 0 high issues
- 4 medium issues (all addressed in-place or documented as DESIGN decisions)
- 3 low issues (documentation/clarity, addressed)

---

## Artifacts Produced

```
docs/feature/fitness-config-per-directory/discuss/
├── journey-fitness-config-per-directory-visual.md
├── journey-fitness-config-per-directory.yaml
├── journey-fitness-config-per-directory.feature
├── shared-artifacts-registry.md
├── story-map.md
├── prioritization.md
├── requirements.md
├── user-stories.md
├── acceptance-criteria.md
├── outcome-kpis.md
├── dor-checklist.md
├── peer-review.md
└── wave-decisions.md
```

---

## Handoff Package — Ready for DESIGN Wave

To `solution-architect`:
- All 13 artifacts above
- 5 open design questions (DQ-1 through DQ-5)
- 3 release slices with explicit outcome KPIs and dependencies

To `acceptance-designer` (downstream from DESIGN):
- Journey YAML (machine-readable)
- Gherkin feature file (3 happy + 4 edge + 2 error scenarios)
- Shared artifact registry (integration validation points)

To `platform-architect` (DEVOPS):
- Outcome KPIs measurement plan
- Guardrail metrics (NFR-1 through NFR-4)

---

## Next Wave: DESIGN

Pass to `solution-architect` (`*handoff-design`).
