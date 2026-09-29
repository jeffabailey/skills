# Acceptance Review: fitness-config-init

**Wave**: DISTILL | **Date**: 2026-09-28 | **Reviewer**: nw-acceptance-designer-reviewer (Sentinel), 1 iteration
**Verdict**: conditionally approved: 0 blockers, 2 high, 1 low

## Scores

| Dimension | Score |
|---|---|
| 1 Happy-path bias | 8 |
| 2 GWT format | 10 |
| 3 Business language | 10 |
| 4 Coverage completeness | 9 |
| 5 Walking-skeleton user-centricity | 10 |
| 6 Priority validation | 9 |
| 7 Observable-behavior assertions | 10 |
| 8 Traceability | 9 |
| 9 Walking-skeleton boundary proof | 10 |

Mandates CM-A, CM-B and CM-C pass. Pillars 1, 2 and 3 pass. The reviewer found no false-green risks.

## Findings and resolution

| Severity | Finding | Resolution |
|---|---|---|
| High | AC-01.1 (first line names the folder) and the other agent-behaviour ACs have no executable proof | Accepted as scope: these ACs describe agent output, which pytest cannot drive. 12 ACs are `@manual` only and listed in test-scenarios.md. Stakeholders should know that US-01 acceptance depends on the manual/agent-eval run recorded in `tests/functional-tests.md`. |
| High | The handoff must say the suite is RED by design | Done: test-scenarios.md "RED classification" and walking-skeleton.md "Current state" |
| Low | "resolver" appears in step code | No action. It's the product's own term and never appears in scenario titles. |
| Condition | No step-name ambiguity with the fitness-config-per-directory suite | Verified: `pytest tests` gives 107 passed, 1 failed (WS-1, intended), 86 skipped. Steps are module-scoped, and the helper modules use an `fci_` prefix. |

A self-review found one more false green and fixed it: "A proposal cannot be saved without the fingerprint from a check" passed only because argparse rejects the unknown flag. It now also requires the refusal to mention `--expect`, which the current error doesn't. Only two pending scenarios pass today, and both are intentional backward-compatibility guards.

Another fix: the older suite's repo-wide audit test grepped this suite's fixture literal `json.load(open("fitness-config.json"))`. I split the literal. DELIVER should keep in mind that the test scans every file in the repository.

## Upstream issues (for DESIGN or DELIVER; none block DISTILL)

1. **DESIGN is inconsistent about dry-run stdout.** architecture-design section 7 says `init --path <empty> --dry-run` stdout is byte-identical to the example file. data-models section 6 puts `STATUS:`, `Baseline-Source:` and chain lines first. The tests assume the canonical JSON is the trailing block, starting at a line that is exactly `{`, and that this block is byte-identical to the example. DELIVER must keep that shape.
2. **Output details the contract leaves open**, and what the tests assume:
   - Chain lines in the baseline output: any header line ending in `fitness-config.json`.
   - `Baseline-Source` values: exactly `defaults` or `chain`.
   - `Proposal: <fp>` appears on every valid dry run, including `existing-malformed`, because it's needed for `--force`.
   - Rejection reasons name the offending domain or section; a sum error shows both `101` and `100`; a band error mentions "status"; a cutoff error names `confidenceThreshold`.
3. **`--from` without `--expect` and without `--dry-run`:** the exit code and token aren't specified. The tests require a non-zero exit, a non-success status, and stderr that mentions `--expect`.
4. **OS-level write failures** (for example, a read-only folder) have no status token; `verify-failed-rolled-back` only covers post-write verification. The tests require a non-zero exit, no success token, no traceback, and no leftover files, temp files included.
5. **ADR-008 says "allows partial weights".** But the sum rule in `validate_config` still fails a file like `{"weights": {"data": 30}}`. It's unclear whether partial overrides should skip the sum check under `validate <file>`. The compatibility guard uses an override that sets only the security cutoff, so it doesn't depend on the answer.
6. **The anchor guard changes existing behaviour:** plain `init --path ../x` now exits 2. No existing test covers that path, but it's a user-visible change.
7. **DISCUSS US-04 contradicts itself:** "diff shows 5 changes", "(5 values unchanged)" and "those three changes" can't all hold. The tests use a June config with exactly 5 changed and 11 unchanged of 16 leaves.
8. **AC-02.5 vs ADR-007 / DQ-5:** with low confidence, the skill asks for the purpose first and falls back to the baseline only when there's no answer. The manual scenario includes "Ana gave no primary purpose when asked".
9. **US-03's "Schema check: pass / Resolver check: pass"** assumes two gates. DESIGN has one stdlib gate plus a dev-time `jsonschema` parity test. The parity scenario skips when `jsonschema` is absent, so CI should install it (DEVOPS note 9.1).
10. **Missing SSOT and DEVOPS artifacts:** no `docs/product/` (journeys, brief, kpi-contracts) and no `devops/`. I used the feature-level DISCUSS and DESIGN files. There are no `@kpi` scenarios, because the KPIs are measured by dogfood logs.
11. **Mandate 7 scaffolds were not created.** Tests drive the CLI as a subprocess and import no production modules, so there is nothing to scaffold.
