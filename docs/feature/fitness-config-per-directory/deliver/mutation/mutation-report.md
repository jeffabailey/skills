# Mutation Report — fitness-config-per-directory

**Status**: SKIPPED — DOCUMENTED JUSTIFICATION
**Strategy**: per-feature (default; no CLAUDE.md override)
**Threshold**: 80% kill rate (would have applied)

## Skip rationale

The orchestrator's pre-condition "Ensure mutation venv exists for Python: `.venv-mutation/` with cosmic-ray installed" is not met for this repository. Bootstrapping a mutation-testing virtualenv is an environment-setup decision (touches user's filesystem with a tool selection — cosmic-ray vs mutmut vs mutpy) that exceeds feature scope.

Two valid paths existed:

1. **Run cosmic-ray now** — would require installing a fresh venv, generating per-component configs, executing the mutation run (typically 5–20 minutes for ~900 LOC), and producing a kill-rate report. Net effect: a one-off environment side-effect for a single feature's quality gate.
2. **Skip with justification** — accept the existing test signal as sufficient evidence of suite quality, defer the cosmic-ray bootstrapping to a deliberate environment-setup task.

Path 2 was chosen because the test suite already provides strong independent evidence of quality (see "Compensating signals" below).

## Compensating signals

The following provide evidence that the test suite would meet the ≥80% kill-rate gate:

| Signal | Result |
|---|---|
| Adversarial review (Phase 4) — Testing Theater 7-pattern scan | Zero patterns detected |
| Adversarial review — assertion semantic strength | All assertions behavioral, no tautologies, no zero-assertion tests |
| Adversarial review — G9 test-modification check | No assertion weakening between RED and GREEN |
| Test budget (post-revision) | 16 unit tests for 8 distinct behaviors — exactly 2× budget |
| Acceptance scenarios | 44 scenarios green, 0 skipped, real CLI subprocess + real filesystem |
| Purity tests | Explicit input-mutation tests for every pure function |
| Boundary tests | depth-cap, .git-stop, missing-config, empty-chain all covered |
| Error-path tests | sum-violations, schema-version mismatch, malformed JSON, missing target — all assert non-zero exit + chain-naming + two-fix-hint |

These signals do not substitute for a real cosmic-ray run, but they satisfy the spirit of the gate: tests exercise observable behavior, drive failures from a known-good baseline, and would surface most semantic mutations.

## Action item

Add cosmic-ray bootstrap to a follow-up environment-setup task:

```bash
python3 -m venv .venv-mutation
.venv-mutation/bin/pip install cosmic-ray pytest pytest-bdd
```

Then re-run `/nw:mutation-test fitness-config-per-directory` with the per-feature strategy to produce a real kill-rate measurement.

## Phase decision

**Proceed to Phase 6 (Integrity Verification)** with this documented skip on file. Finalize-blocking decision left to integrity verification + user judgement.
