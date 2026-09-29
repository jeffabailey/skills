# Evolution: fitness-config-init

**Date**: 2026-09-29
**Feature ID**: fitness-config-init
**Branch**: `feat/fitness-config-init` (23 commits ahead of `91110fd` at handoff, plus this record)
**Status**: DELIVER complete; committed locally. Not pushed and no PR opened (user decision).

---

## Executive Summary

Shipped the `fitness-config-init` skill (`skills/fitness-config-init/`). It inspects a project, classifies its primary purpose, optionally runs `review-full` for extra evidence, and proposes a purpose-tuned `fitness-config.json`. The agent never writes the file itself. It pipes the proposal on stdin to the resolver's reviewed-proposal write gate (`init --path T --from - --dry-run`, then `--expect <fingerprint>` and optionally `--force`). The gate validates the proposal strictly, shows a value diff against any existing file, refuses to overwrite without confirmation, creates or replaces atomically, re-verifies against the merged root chain and rolls back on mismatch.

Business context: before this feature every tuned config was hand-edited from `fitness-config.example.json` (KPI-1 baseline 0%). The skill aims for 80% or more of runs to be accepted with at most one manual adjustment, with 100% of written files passing `validate` and zero unconfirmed overwrites as guardrails.

Along the way the single-file resolver (`scripts/fitness-config.py`, about 800 LOC) was split into the `scripts/fitness_config/` package (9 modules, 1,356 LOC) per ADR-012, closing the ADR-004 follow-up from fitness-config-per-directory. `scripts/fitness-config.py` remains as a 29-line entry stub.

---

## Six-Wave Timeline

| Wave | Persona | Status | Notes |
|------|---------|--------|-------|
| DISCOVER / DIVERGE | — | Skipped | Brownfield. The JTBD phase was skipped by instruction; job J-FCI-01 was inferred (DQ-8). |
| DISCUSS | Luna (`nw-product-owner`) | Complete | 6 stories, 1 bounded context, 5 outcome KPIs, journey YAML plus visual and a derived `.feature` file. |
| DESIGN | Morgan (`nw-solution-architect`) | Complete | 4 design docs, ADR-007..011. Conditionally approved for DISTILL. |
| DEVOPS | — | Skipped as a wave | CI change delivered as roadmap step 02-03 (pytest with `jsonschema`, resolver audit on PRs). |
| DISTILL | Quinn (`nw-acceptance-designer`) | Complete | Walking skeleton plus focused scenarios; 12 agent-behaviour ACs are `@manual`. Conditionally approved: 0 blockers, 2 high, 1 low. |
| DELIVER | `nw-functional-software-crafter` | Complete | 11 roadmap steps, 4 refactor levels, ADR-012 package split, 1 orchestrator fix, mutation testing at 95.6%. |

---

## Key Decisions

User decisions (pre-answered for DESIGN and DELIVER):

| Decision | Outcome |
|---|---|
| Weight derivation | Purpose profiles plus bounded judgment: each weight may move at most ±4 from its profile (ADR-007). |
| Rationale | Printed to the user only, never persisted in the config (ADR-011). |
| Full-review evidence | Used only to judge which domains apply, not to set scores. |
| Validation | Extend the existing stdlib validator, strict mode; no new runtime dependency. `jsonschema` is a dev-time parity check only (ADR-008). |
| Dry-run output | Header lines (`STATUS:`, `Baseline-Source:`, chain, `Proposal:`) first, then a canonical JSON block starting at a line that is exactly `{`. |
| Overrides | Partial weight overrides allowed; the merged chain must sum to 100. |
| Paradigm | Functional: pure core, I/O behind a `ConfigFile` port (ADR-006 style). |
| Package split | `scripts/fitness_config/` package (ADR-012), superseding the single-file stance of ADR-004. |
| Finish | Commit locally only; no push, no PR. |

Architectural decisions: baseline is the parent chain merged over defaults, anchored at the git top-level or cwd (ADR-009); every write goes through one deterministic, fingerprint-checked, create-only-unless-`--force` gate with verify and rollback (ADR-010).

---

## Roadmap Steps and Commit Hashes

| Step | Title | Commit |
|------|-------|--------|
| (setup) | DISCUSS, DESIGN, DISTILL artifacts and approved roadmap | `4f9ac16` |
| 01-01 | Walking skeleton: reviewed proposal saved byte-for-byte into ledgerd | `1227255` |
| 01-02 | Fingerprint identity and canonical defaults parity with the example | `2cc0338` |
| 01-03 | Anchor-guarded starting weights and anchor regressions | `a4f3e82` |
| 01-04 | Strict validator, proposal rejections and schema parity | `dbfc8c5` |
| 02-01 | Reviewed-proposal guarantees with verify and rollback | `8d628eb` |
| 02-02 | Override announced against the root config chain | `b08e41e` |
| 02-03 | CI runs pytest with jsonschema and the resolver audit | `0956f6e` |
| 03-01 | Skill guide, purpose references and audit coverage | `5c714ed` |
| 03-02 | List fitness-config-init across bundle docs and plugin metadata | `d5225e0` |
| 04-01 | Review before replace: value diff, unchanged and confirmed `--force` | `562a68a` |
| 04-02 | Full-review evidence in the skill and contiguous threshold rules | `60b9c6d` |

### Refactor Pass

| Pass | Title | Commit |
|------|-------|--------|
| Split | Resolver split into the `fitness_config` package | `9ae2dea` |
| L1 | Readability across the resolver package | `ef50699` |
| L2 | Complexity in cli, render, validation and audit | `0c90ce4` |
| L3 | Exit codes and printing kept in the CLI shell | `089c99d` |
| L4 | One home for the write gate's status codes | `8896196` |
| ADR | ADR-012 records the package split | `19c32d8` |

### Review Fixes and Mutation Testing

| Item | Commit |
|------|--------|
| Refuse unreadable input and non-folder targets without a traceback | `60d446d` |
| Close gaps found by mutation testing | `363f5ab` |
| Pin CLI and validation behaviour mutants exposed | `96c6fac` |
| Unknown weight domain in a proposal reported once | `31dfd0d` |
| Mutation report | `9c92dd3` |

**Total**: 23 commits since `91110fd`; 77 files changed, +9,328 / -967.

---

## Quality Gates

| Gate | Result |
|---|---|
| Roadmap review | Approved before DELIVER (`4f9ac16`). |
| DES integrity | `verify_deliver_integrity`: all 11 steps have complete DES traces (55 phase events). |
| Adversarial review (Phase 4) | Approved by the reviewer. The orchestrator then found 4 defects the reviewer missed, all fixed in `60d446d`: a traceback on non-UTF-8 input, a folder named `fitness-config.json` at the target, a file passed as the target folder, and duplicate JSON keys being accepted silently. |
| Mutation testing (Phase 5) | cosmic-ray 8.7.0 over 9 modules: 87.1% on the first run, 95.6% (1,187 of 1,242) after 105 real gaps were closed. All 55 survivors are equivalent or benign. Every module is above 80%. |
| Test suite | `uv run pytest tests -q`: 241 passed, 32 skipped (the skips are the `@manual` agent-eval scenarios). |
| DISTILL review | Conditionally approved: 0 blockers, 2 high (manual ACs accepted as scope; RED-by-design handoff note added), 1 low. |

---

## Outcome KPI Mapping

From `docs/feature/fitness-config-init/discuss/outcome-kpis.md`:

| KPI | Target | Closed By |
|-----|--------|-----------|
| KPI-1 (North Star) | 80% or more of runs accepted with at most 1 adjustment | Skill guide and purpose references (03-01); measured by dogfood log over 10 repos. Not yet measured. |
| KPI-2 (guardrail) | 100% of skill-written files pass `validate` | Write gate plus strict validator (01-04, 02-01, 02-02); automated. |
| KPI-3 (guardrail) | 0 unconfirmed overwrites | Create-only save, fingerprint, value diff and `--force` (01-01, 04-01); automated. |
| KPI-4 | Full mode at least 10 points above fast mode | 04-02; dogfood log. Not yet measured. |
| KPI-5 | 80% or more classifications accepted | 03-01; dogfood log. Not yet measured. |

KPI-1, KPI-4 and KPI-5 depend on the dogfood log and the manual agent-eval run, neither of which has happened yet.

---

## Lessons Learned

1. **Reviewer approval is not proof of robustness.** The adversarial reviewer approved code that still tracebacked on non-UTF-8 input and accepted duplicate keys. Hostile input probing by the orchestrator (odd bytes, wrong file types at the target path) found 4 defects in minutes. Keep a short "hostile input" checklist in the review prompt.
2. **Mutation testing earned its cost.** About 23 minutes of wall time found 105 real gaps, including an untested depth-cap boundary and CLI behaviour that only argparse was guarding. Filtering out annotation-only mutants (396) up front kept the run fast and the survivor list honest.
3. **Design contradictions surface in DISTILL.** The dry-run stdout shape and the US-04 change counts contradicted each other across DISCUSS and DESIGN. The tests pinned one reading. Several contract details (item 6 to 8 below) still drift between docs and code, so re-read the design docs against the code at the end of DELIVER.
4. **Split early when a threshold is already passed.** ADR-004's 600-LOC threshold was exceeded before this feature started. Doing the package split mid-DELIVER worked, but it added a refactor stream on top of the feature work.
5. **Agent-behaviour ACs need an eval harness.** 12 ACs (32 scenarios) cannot run in pytest, so US-01 sign-off still waits on a manual run.

---

## Open Follow-Ups

1. **Manual agent-eval scenarios not run.** 32 `@manual` scenarios (procedure in `tests/functional-tests.md`) have not been run. US-01 sign-off depends on them.
2. **Seed path skips the completeness check.** `init --path` without `--from` copies merged parent configs without the write-bound completeness check, so fractional parent weights would be inherited.
3. **Dry run checks only the proposal.** `init --dry-run` does not check the merged chain. A proposal that is invalid once merged is caught only at save time (and rolled back).
4. **Non-object JSON config (pre-existing, also in `91110fd`).** A file that is valid JSON but not an object passes `validate --path` as Valid, and legacy `show` crashes with `AttributeError`.
5. **Legacy command messages.** Legacy `validate <file>` prints a misleading second error line. Legacy `show` with an unreadable file prints the defaults and exits 0.
6. **Doc drift: chain pre-check order.** data-models §6.2 puts the chain pre-check after the fingerprint check; the code reads the chain first.
7. **Doc drift: value diff.** The unit-count rule in the value diff excludes `version`, and the `(absent)` marker is used. Neither is documented in data-models §6.1.
8. **Doc drift: ADR-001 and component-boundaries.** ADR-001 says the walk stops at `.git`, but the code stops at the cwd or anchor. component-boundaries mentions a `KNOWN_DOMAINS` constant that does not exist.
9. **Python 3.10 not tested locally.** Checked only via the ruff `py310` target; tests ran on 3.11 and 3.14.
10. **±4 bound and user-requested edits.** `purpose-profiles.md` lets a user-requested weight edit exceed the ±4 bound (an interpretation of ADR-007). Pending user confirmation.
11. **Hard links required for create.** The `os.link` create path fails on filesystems without hard links and reports `write-failed`.

---

## References

- DISCUSS: `docs/feature/fitness-config-init/discuss/wave-decisions.md`, `outcome-kpis.md`, `user-stories.md`
- DESIGN (migrated): `docs/architecture/fitness-config-init/` (`architecture-design.md`, `component-boundaries.md`, `technology-stack.md`, `data-models.md`)
- DISTILL: `docs/feature/fitness-config-init/distill/acceptance-review.md`; walking skeleton migrated to `docs/scenarios/fitness-config-init/walking-skeleton.md`
- UX journey (migrated): `docs/ux/fitness-config-init/`
- DELIVER plan: `docs/feature/fitness-config-init/deliver/roadmap.json` (11 steps, 4 phases)
- DELIVER trace: `docs/feature/fitness-config-init/deliver/execution-log.json` (55 phase events)
- Mutation report: `docs/feature/fitness-config-init/deliver/mutation/mutation-report.md`
- ADRs: `docs/adrs/ADR-007-purpose-profiles-with-bounded-judgment.md` … `docs/adrs/ADR-012-resolver-package-split.md`
- Skill: `skills/fitness-config-init/SKILL.md`, `references/purpose-profiles.md`, `references/purpose-signals.md`
