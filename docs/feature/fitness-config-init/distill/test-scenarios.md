# Test Scenarios: fitness-config-init

**Wave**: DISTILL | **Date**: 2026-09-28 | **Persona**: Quinn (nw-acceptance-designer)
**Suite**: `tests/acceptance/fitness-config-init/` (pytest-bdd 8, run with `pytest tests/acceptance/fitness-config-init`)

## Setup

`[lang-mode] python` | `[policy-mode] inherit` (the policy file was absent, so it was bootstrapped at `docs/architecture/atdd-infrastructure-policy.md`) | `[port-mode]` local: `nwave_ai.state_delta` isn't installed, so the suite has a four-parameter equivalent in `steps/fci_state_delta.py`.

Reconciliation passed with 0 contradictions. I compared DISCUSS `wave-decisions.md` with the DESIGN documents. DESIGN has no `wave-decisions.md`; `architecture-design.md` sections 3 and 11 carry its decisions. DEVOPS artifacts are missing, which is a warning only: the default environment matrix applies, and CI wiring is deferred to DELIVER. The refinements I found are not contradictions (see acceptance-review.md, "Upstream issues").

Test placement follows this repo's layout (`tests/acceptance/<feature>/`), not the nWave template path. The `steps/` directory has **no `__init__.py`**. A second `steps` package makes pytest raise `ImportPathMismatchError` against `fitness-config-per-directory/steps`, so the helper modules use an `fci_` prefix and are imported by bare name.

Tags: `@skip` marks a pending scenario; DELIVER removes it one scenario at a time. `@manual` marks an agent-eval scenario that pytest never runs. `FCI_RUN_PENDING=1 pytest tests/acceptance/fitness-config-init` runs every non-manual pending scenario, for RED classification.

## Scenario inventory

| Feature file | Scenario blocks | pytest items | Executable items | @manual items | Enabled |
|---|---|---|---|---|---|
| `walking-skeleton.feature` | 3 | 3 | 3 | 0 | 1 (WS-1) |
| `milestone-1-purpose-and-proposal.feature` | 20 | 20 | 7 | 13 | 0 |
| `milestone-2-safe-first-write.feature` | 15 | 22 | 22 | 0 | 0 |
| `milestone-3-review-before-replace.feature` | 11 | 15 | 9 | 6 | 0 |
| `milestone-4-full-review-evidence.feature` | 8 | 12 | 1 | 11 | 0 |
| `milestone-5-purpose-tuned-thresholds.feature` | 5 | 8 | 6 | 2 | 0 |
| `integration-checkpoints.feature` | 7 | 7 | 7 | 0 | 0 |
| **Total** | **69** | **87** | **55** | **32** | **1** |

Error and edge coverage: 23 of the 45 executable scenario blocks (51%) are tagged `@error`. Counted by pytest items, it's 33 of 55 (60%), because the outlines are all error cases. Both are above the 40% target.

Tier decision (Mandate 10): **Tier A only.** The resolver contract is config-shaped (single-shot check and save), so Tier B state-machine PBT doesn't apply. Every executable scenario is at layer 3 (subprocess plus real filesystem): examples only, with sad paths listed one by one (Mandates 9 and 11), and no Hypothesis. Mandate 8: every action that could touch files snapshots the workspace, and the outcomes assert with `assert_state_delta` over the full file universe.

## Domain vocabulary (fact to step)

| Fact | Step text | Function |
|---|---|---|
| a persona project with no config | `{person}'s project "{project}" has no fitness config` | `project_without_config` |
| check a proposal (dry run) | `{person} checks the {name} proposal for "{target}"` / `has checked ...` | `checks_named_proposal` / `has_checked_named_proposal` |
| save the reviewed proposal | `{person} saves the reviewed proposal for "{target}"` | `saves_reviewed_proposal` |
| replace after confirmation | `{person} confirms replacing the config for "{target}" with the reviewed proposal` | `confirms_replacing` |
| baseline | `{person} asks for the starting weights for "{target}"` / `has asked ...` | `asks_starting_weights` |
| save outcome | `the save reports the config was {created\|replaced\|unchanged\|not written}` | `save_outcome` |
| saved bytes equal reviewed bytes | `the fitness config in "{target}" is identical to the reviewed proposal` | `config_identical_to_reviewed` |
| no side effects | `nothing has been saved in "{project}"` / `nothing else in "{project}" changed` | `nothing_saved` / `nothing_else_changed` |

The chained narrative (Pillar 2) works because each `has checked`, `has asked` or `has saved` Given calls the same function as its When.

## Adapter coverage (Mandate 6)

| Adapter | Real-I/O scenario | Covered by |
|---|---|---|
| Resolver CLI (driving) | yes | WS-1, plus every milestone-2/3/5 scenario |
| Filesystem write gate (atomic write, exclusive create) | yes | WS-1 (create), M3 confirm (replace), M2 read-only folder (failure) |
| Filesystem chain reader | yes | WS-3, M2 subfolder baseline, M2 damaged root, M2 anchor regressions |
| stdin proposal reader | yes | every check and save scenario; M2 "not a config at all" |
| Config audit scan | yes | integration: synthetic checkout (two error cases) and the real repository |
| review-full (external skill) | no, `@manual` | milestone-4 agent-eval (injected domain failure, narrowed scope) |
| Post-write verify and rollback | no (needs an injected writer) | **planned unit test**: `tests/unit/fitness_config/test_write_gate.py` (ADR-010 step 6) |

## AC traceability (all 32)

E = executable (pytest), S = executable static-artifact check, M = @manual agent eval.

| AC | Scenario(s) | File | Kind |
|---|---|---|---|
| AC-01.1 | The first thing Priya sees is the folder being configured | M1 | M |
| AC-01.2 | Fast scan is the default evidence mode; evidence mode outline | M1, M4 | M |
| AC-01.3 | Priya sees what the skill thinks ledgerd is, and why; purpose signal guide defines confidence | M1 | M + S |
| AC-01.4 | A nearly empty folder is reported as unknown instead of guessed | M1 | M |
| AC-01.5 | Tomas corrects a wrong classification in one reply | M1 | M |
| AC-01.6 | The fast scan leaves the project untouched; purpose signal guide limits the scan to 40 files | M1 | M + S |
| AC-02.1 | Every archetype profile is a complete, balanced weighting; the resolver would accept every profile; weights adding up to 101; incomplete or out-of-range outline (8 cases) | M1, M2 | S + E |
| AC-02.2 | Every changed weight comes with a reason tied to the project | M1 | M |
| AC-02.3 | The database-backend profile favours reliability and data; a reliability-critical service (manual) | M1 | S + M |
| AC-02.4 | The web-frontend profile puts accessibility first; a public website (manual) | M1 | S + M |
| AC-02.5 | WS-2 built-in starting weights; subfolder starting weights; an unknown project keeps the starting weights (manual) | WS, M2, M1 | E + M |
| AC-02.6 | Priya adjusts a proposed weight before saving | M1 | M |
| AC-03.1 | WS-1 (passes validation); every profile accepted; hand-edited config validation; schema parity | WS, M1, M2, IC | E |
| AC-03.2 | WS-1 (identical bytes); the fingerprint identifies the config; a different proposal is never saved; built-in config equals the example byte for byte | WS, M2, IC | E |
| AC-03.3 | 101; outline; not a config; unbalanced save with a fingerprint; damaged config higher up; read-only folder | M2 | E |
| AC-03.4 | An existing config is never replaced without Priya's go-ahead | M2 | E |
| AC-03.5 | WS-3 Kenji's billing override | WS | E |
| AC-03.6 | WS-1 (nothing else changed); read-only folder | WS, M2 | E |
| AC-04.1 | Priya sees exactly which values would change; a note is shown as removed; the overwrite question (manual) | M3 | E + M |
| AC-04.2 | Without the go-ahead the June config stays; only an explicit yes (manual outline) | M3 | E + M |
| AC-04.3 | Confirming replaces the config; a replacement is refused if the proposal changed | M3 | E |
| AC-04.4 | The check reports nothing to do; confirming an identical proposal leaves the file untouched | M3 | E |
| AC-04.5 | A broken current config is reported (x2) | M3 | E |
| AC-05.1 | The evidence mode comes only from the argument, clear wording, or the prompt | M4 | M |
| AC-05.2 | The skill guide warns that a full review writes a report; Kenji is warned (manual) | M4 | S + M |
| AC-05.3 | A review finding appears in a reason; a skipped domain is lowered | M4 | M |
| AC-05.4 | A failed domain review does not stop the proposal; a narrowed-scope review is not used | M4 | M |
| AC-05.5 | A full review writes only the report and the config | M4 | M |
| AC-06.1 | A payment service gets stricter thresholds | M5 | M |
| AC-06.2 | A security cutoff outside 1 to 10 is rejected (0, 11); stricter bands accepted | M5 | E |
| AC-06.3 | Stricter bands accepted; bands with a gap or overlap rejected (3 cases) | M5 | E |
| AC-06.4 | An ordinary project keeps the starting thresholds | M5 | M |

Coverage: 32 of 32 ACs are mapped. 18 have an executable check, 2 more have a partial static check (AC-01.3, AC-01.6), and 12 are manual only (agent judgment: 01.1, 01.2, 01.4, 01.5, 02.2, 02.6, 05.1, 05.3, 05.4, 05.5, 06.1, 06.4).

Also covered: FR-4, FR-6, FR-7, FR-8, BR-1..BR-6, NFR-1, NFR-3, NFR-4, ADR-007..ADR-011, and the three anchor-guard regressions from data-models section 6.3 (M2 `@regression`: starting weights, default set-up, folder outside the project).

## Manual / agent-eval procedure

The `@manual` scenarios run against the six DISCUSS fixtures (ledgerd, jeffbaileyblog, homelab-cli, geo-notes, fieldnotes, paygate), built as throwaway git repos. Procedure per scenario: invoke `/fitness-config-init` in a fresh session, answer the prompts as the scenario states, and record the transcript, the tool calls (file-read count for AC-01.6) and `git status`. Outcomes go into `tests/functional-tests.md`, a DELIVER housekeeping item from architecture-design 9.2. An agent-eval harness can replay the same Given/When/Then later; the Gherkin is written so the Then lines are checkable from a transcript.

## RED classification (pre-DELIVER gate)

Run with `FCI_RUN_PENDING=1`: 53 failed, 2 passed, 32 skipped (manual).

| Class | Count | Evidence |
|---|---|---|
| MISSING_FUNCTIONALITY: new `init` flags absent | 38 | `unrecognized arguments: --from --dry-run` / `--dry-run` asserted through the status token |
| MISSING_FUNCTIONALITY: skill files absent | 9 | `... not found at skills/fitness-config-init/... (not yet delivered)` |
| MISSING_FUNCTIONALITY: audit glob misses the new skill | 2 | `audit -> exit 0` on a checkout whose guide has an inline weight table or a direct read |
| MISSING_FUNCTIONALITY: stricter validator | 2 | hand-edited config crashes (`TypeError` traceback) and isn't named; schema parity: resolver accepts `version: 2`, unknown domain, 3-number band, string range |
| DEFECT reproduced: anchor walk | 2 | default set-up seeds the stray `accessibility 40`; `init --path ../ledgerd-archive` exits 0 and writes outside the project |
| GUARD (green by design) | 2 | example config still validates; security-only override still validates (ADR-008 backward compatibility) |
| IMPORT_ERROR / FIXTURE_BROKEN / wrong assertion | **0** | |

## Implementation order for DELIVER

Remove `@skip` from one scenario at a time, in this order. Each numbered step is one RED, GREEN, COMMIT cycle or a small batch.

1. **WS-1** (enabled): `--from - --dry-run` with create-only completeness and canonical rendering, the fingerprint, `--expect` exclusive create, and the anchor guard for target == cwd.
2. M2 "fingerprint identifies exactly the config", then IC "built-in config equals the example byte for byte"
3. WS-2 starting weights (`init --path T --dry-run`, `Baseline-Source`), then M2 subfolder starting weights
4. M2 anchor regressions: starting weights, default set-up, folder outside the project (exit 2)
5. M2 rejections: 101, the flaw outline (8), not a config, unbalanced save, then the IC schema parity (needs `jsonschema` installed)
6. M2 hand-edited validation (ADR-008 names, no crash), then the IC compatibility guards
7. M2 reviewed-proposal guarantees: mismatch, missing fingerprint, existing file refused, damaged chain, read-only folder
8. WS-3 billing override chain
9. **Skill files**: `SKILL.md`, `references/purpose-profiles.md`, `references/purpose-signals.md`, then M1 static checks, M4 static check, the IC audit scenarios (extend the audit glob), and the manual M1 agent evals
10. **R1 (US-04)**: M3 diff, identical, `--force` replace, malformed current file, unknown-key removal, replace mismatch, then the M3 manual evals
11. **R2 (US-05)**: M4 manual evals (no resolver change)
12. **R3 (US-06)**: M5 contiguity rule, cutoff range, then the M5 manual evals

Planned unit tests (inner loop, crafter-owned): `tests/unit/fitness_config/test_write_gate.py` (verify and rollback via an injected writer, concurrent-create race), plus the pure renderer, diff, fingerprint and completeness rules next to `test_validator.py`.
