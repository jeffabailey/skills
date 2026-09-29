# Wave Decisions: DISCUSS — fitness-config-init

**Wave**: DISCUSS | **Date**: 2026-09-28 | **Persona**: Luna (nw-product-owner) | **Mode**: subagent, autonomous

## Configuration

| Setting | Value |
|---|---|
| feature_type | infrastructure/tooling (one new skill) |
| walking_skeleton | depends: brownfield. The resolver, schema, and example config already exist. The skeleton is the new skill end to end on top of them. |
| research_depth | lightweight |
| JTBD phase | skipped (per caller) |
| format | all |

## Scope Assessment: PASS: 6 stories, 1 context, estimated 6-8 days

- Stories: 6. This is under the 10-story limit.
- Bounded contexts: 1. The context is fitness configuration. The new skill uses existing `scripts/fitness-config.py` and `skills/review-full` and does not change them.
- Walking skeleton integration points: 3. They are the project folder files, `fitness-config.example.json`, and `fitness-config.py validate`.
- Independent outcomes: only one (full-review evidence) could ship separately, and it is already sliced as Release 2.

## Risks Noted

| Risk | Note |
|---|---|
| No DIVERGE / JTBD artifacts | Skipped by instruction. The job statement is inferred in `requirements.md`. Stories use the proposed `job_id: J-FCI-01`. `docs/product/jobs.yaml` does not exist; see DQ-8. |
| Two default sources | `fitness-config.example.json` and `DEFAULT_*` in `scripts/fitness-config.py` are identical today but kept separately. See DQ-3. |
| Schema does not enforce the sum rule | JSON Schema has no sum constraint. The resolver `validate` is the only sum gate. Both gates are required (FR-4). |
| Full-review side effect | review-full writes `docs/fitness-report.md` in the target project. The user must be told before opting in. |

## Deviation from agent defaults

The caller explicitly asked for a standalone `journey-fitness-config-init.feature` and `acceptance-criteria.md`. Both were produced as thin derived views. The source of truth stays in the journey YAML and `user-stories.md`.
