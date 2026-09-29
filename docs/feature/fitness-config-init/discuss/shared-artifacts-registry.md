# Shared Artifacts Registry: fitness-config-init

| Artifact | Source of truth | Consumers (journey step) | Risk | Validation |
|---|---|---|---|---|
| `target_folder` | Agent working directory at invocation | 1, 2, 7, 8 | MEDIUM: writing to the wrong folder | First output line names it; `config_path` is derived from it |
| `evidence_mode` | User choice at runtime, default `fast` | 2, 3, 4, 5 | LOW | Echoed in the evidence header |
| `evidence_list` | Files and directories read during the scan | 3, 4, 5 | MEDIUM: invented evidence erodes trust | Every item names a path that exists |
| `review_scores` | review-full output (`docs/fitness-report.md`) | 5 | MEDIUM: side-effect file in the user's project | Full mode only; disclosed before the run |
| `project_purpose`, `purpose_confidence` | Classification from `evidence_list` | 4, 5, 8 | MEDIUM | User can correct it before the proposal is final |
| `default_config_source` | `fitness-config.example.json` (today identical to `DEFAULT_*` in `scripts/fitness-config.py`) | 5, 6 | **HIGH: two sources of truth.** If they drift, "non-default" means different things. | DQ-3: DESIGN picks one; a test asserts parity or single-sourcing |
| `proposed_config` | Generated in session | 5, 6, 7 | HIGH: the written file must equal the reviewed proposal | Written bytes parse to the same object as the proposal |
| `rationale_entries` | Generated in session, one per non-default value | 5, 8 (and a sidecar if DQ-1 chooses one) | MEDIUM | Count of rationale lines equals count of changed values |
| `existing_config` | `${target_folder}/fitness-config.json` before the run | 6 | HIGH: data loss on silent overwrite | Byte-identical unless the user confirms |
| `config_path` | `${target_folder}/fitness-config.json` | 5, 6, 7, 8 | HIGH | Same path shown in proposal, diff, write message, and chain |
| `validation_result` | `fitness-config.schema.json` + `scripts/fitness-config.py validate` | 7 | HIGH: the schema alone does not enforce the sum-to-100 rule | Both gates must pass |
| `resolution_chain` | `fitness-config.py show --path <folder>` `Config:` line | 8 | MEDIUM: in a subdirectory, the file is an override (ADR-001/002/005) | Shown verbatim from the resolver |

Rule: the skill must not hardcode any default weights in its SKILL.md prose. It reads them from `default_config_source`, which is consistent with ADR-002 / FR-7 of fitness-config-per-directory.
