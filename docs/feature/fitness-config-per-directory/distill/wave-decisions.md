# Wave Decisions: DISTILL — fitness-config-per-directory

**Wave**: DISTILL
**Date**: 2026-04-25
**Persona**: Quinn (nw-acceptance-designer)
**Feature**: fitness-config-per-directory

---

## Configuration Used

| Setting | Value |
|---------|-------|
| Model | inherit |
| Test type | core |
| Test framework | pytest-bdd |
| Integration approach | real-services (real filesystem in pytest tmp_path; real CLI subprocess) |
| Infrastructure testing | false (DEVOPS wave skipped — pure tooling feature) |
| Interactive | low (auto mode) |
| Output format | gherkin |
| Output directories | `tests/acceptance/fitness-config-per-directory/` + `docs/feature/fitness-config-per-directory/distill/` |

---

## Phases Executed

- Phase 1: Skill loading (bdd-methodology, test-design-mandates, ad-critique-dimensions)
- Phase 2: Prior wave consultation (DISCUSS + DESIGN; DEVOPS skipped intentionally)
- Phase 3: Scenario design (walking skeleton + 6 milestones + integration checkpoints)
- Phase 4: Test infrastructure (conftest.py + 2 step modules)
- Phase 5: AC trace matrix
- Phase 6: Self-review against ad-critique-dimensions (9 dimensions)
- Phase 7: Handoff package preparation

---

## Prior Wave Artifact Checklist

DISCUSS:
- [x] `docs/feature/fitness-config-per-directory/discuss/requirements.md`
- [x] `docs/feature/fitness-config-per-directory/discuss/user-stories.md`
- [x] `docs/feature/fitness-config-per-directory/discuss/acceptance-criteria.md`
- [x] `docs/feature/fitness-config-per-directory/discuss/journey-fitness-config-per-directory.feature`
- [x] `docs/feature/fitness-config-per-directory/discuss/shared-artifacts-registry.md`

DESIGN:
- [x] `docs/feature/fitness-config-per-directory/design/wave-decisions.md`
- [x] `docs/feature/fitness-config-per-directory/design/architecture-design.md`
- [x] `docs/feature/fitness-config-per-directory/design/component-boundaries.md`
- [x] `docs/feature/fitness-config-per-directory/design/data-models.md`
- [x] `docs/adrs/ADR-001..ADR-006`

DEVOPS:
- [⊘] `docs/feature/fitness-config-per-directory/devops/environments.yaml` — wave skipped per orchestrator config (`infrastructure_testing: false`). Per critique-dimensions Dim 8 Check B fallback, default environments are clean/with-pre-commit/with-stale-config; only the `clean` environment is meaningful for a pure config-resolver feature, and tmp_path provides exactly that.

---

## Key Decisions

### D-1: Strategy C (real services) for the walking skeleton and all milestone scenarios

The driving port is the `fitness-config.py` CLI; the only adapter is the
filesystem reader. tmp_path gives every scenario an isolated real
filesystem. Real Python subprocess invocation gives a faithful CLI
contract test. No in-memory doubles, no mocks — the cost of real I/O is
negligible (the entire suite is filesystem-bound, but each scenario
operates on at most ~10 small files).

### D-2: Single walking skeleton, not 2-3

Rationale documented in `walking-skeleton.md`. Summary: one CLI script,
one primary user verb (`show --path`), one demo-able outcome. Additional
skeletons would duplicate milestone scenarios.

### D-3: 7 feature files mapped to milestones for one-at-a-time DELIVER

| File | Milestone | Driving story family |
|------|-----------|----------------------|
| walking-skeleton.feature | 0 | E2E user value (US-01+US-02+US-04) |
| milestone-1-walk-up-discovery.feature | 1 | US-01 |
| milestone-2-deep-merge.feature | 2 | US-02 (happy paths) |
| milestone-3-provenance.feature | 3 | US-03 + US-04 |
| milestone-4-error-handling.feature | 4 | US-02 errors + US-05 + US-07 + adapter failures |
| milestone-5-backward-compat.feature | 5 | NFR-3 + US-04/05/06 legacy paths |
| milestone-6-init-helper.feature | 6 | US-06 |
| integration-checkpoints.feature | 7 | ADR-005 broad-scope, US-08 audit, perf, determinism, CLI mutex, JSON-block contract |

Unskip order documented in `walking-skeleton.md`.

### D-4: tmp_path real-filesystem fixture; no fixture parametrization across environments

Mandate 4 (Pure Function Extraction Before Fixtures) compliance: DESIGN
already extracted resolver/merger/validator/reporter as pure functions
(ADR-006). The only impure boundary is `_read_config`. Acceptance tests
exercise the CLI subprocess (driving port) and need exactly ONE
filesystem environment per scenario — tmp_path provides it. DELIVER
inner-loop unit tests exercise the pure functions directly, with no
fixture at all.

### D-5: All non-skeleton scenarios start with @skip

Outside-In TDD policy: enable one acceptance test at a time, drive the
inner loop until it passes, commit, repeat. The walking skeleton stays
active to drive the initial wiring. Software-crafter unskips milestone
scenarios in the order documented.

### D-6: Real-CLI subprocess via `repo.run(...)` — never import resolver internals

Mandate 1 (Hexagonal Boundary Enforcement) compliance: tests invoke the
driving port. The CLI's stdout/stderr/exit-code triple is the contract.
Every step method delegates to `repo.run("show"|"validate"|"init", ...)`.
Zero step imports any function from `scripts/fitness-config.py`.

### D-7: AC-08.1 documentation review and AC-NFR-5 cross-platform are out of acceptance scope

AC-08.1 is "every review-*/SKILL.md documents the resolver call" — a
documentation-review check, not a behavioral test. DELIVER inner loop
covers it.

AC-NFR-5 is "macOS, Linux, Windows" — same scenarios, different OSes.
Handled by CI matrix configuration in DELIVER, not by additional
acceptance scenarios.

All other 37 ACs (AC-01.x..AC-08.4 minus AC-08.1, plus AC-NFR-1..4) trace
to at least one scenario.

---

## Hexagonal Boundary Enforcement (CM-A evidence)

```
$ grep -rn "from scripts" tests/acceptance/fitness-config-per-directory/
(zero matches)

$ grep -rn "import scripts" tests/acceptance/fitness-config-per-directory/
(zero matches)
```

Every step's CLI invocation goes through `RepoTree.run(...)` -> `subprocess.run([...])`.

---

## Business Language Purity (CM-B evidence)

```
$ grep -rEn "(database|REST|HTTP/[0-9]|controller|service\.|endpoint|api\.|status code)" \
    tests/acceptance/fitness-config-per-directory/*.feature
(zero matches)
```

Two domain-language usages of "JSON" and "exit status" justified in
`acceptance-review.md` Dim 3.

---

## Walking Skeleton + Focused Scenario Counts (CM-C evidence)

| Type | Count |
|------|-------|
| Walking skeletons (user-value E2E, active) | 1 |
| Focused scenarios (skipped, DELIVER unskips one at a time) | 43 |
| **Total** | **44** |

Ratio (1 skeleton : 43 focused) reflects Strategy C: every focused
scenario is also E2E since there are no test-double tiers. The skeleton's
distinction is its activation status, not its real-I/O posture.

---

## Pure Function Extraction Inventory (CM-D evidence)

Per DESIGN ADR-006, the impure boundary is isolated to one function:

| Function | Purity | Adapter boundary |
|----------|--------|------------------|
| `_read_config(Path) -> dict \| None` | IMPURE (only impure component) | Filesystem |
| `walk_up_chain(target_path) -> list[Path]` | Pure | n/a |
| `deep_merge_chain(chain, defaults) -> dict` | Pure | n/a |
| `validate_effective(effective, raw_configs, source_chain) -> list[str]` | Pure | n/a |
| `render_show_output(result) -> str` | Pure | n/a |
| `render_header_lines(result, scope) -> str` | Pure | n/a |
| `render_validation_error(result) -> str` | Pure | n/a |
| `render_inline_weights(effective_weights) -> str` | Pure | n/a |
| `resolve_effective_config(target_path, *, reader) -> ResolutionResult` | Pure (parameterized on reader) | n/a |

Acceptance tests exercise the CLI driving port (impure top of the call
graph). DELIVER inner-loop unit tests cover each pure function directly.
Fixture parametrization across environments is NOT needed because the
single adapter has exactly one runtime mode (real filesystem under
tmp_path).

---

## Self-Review Outcome (Dim 1-9)

See `acceptance-review.md`. Approved.

```yaml
approval_status: "approved"
critical_issues_count: 0
high_issues_count: 0
low_issues_count: 2
```

The two low-severity notes are forwarded to DELIVER:

1. AC-03.1 (report-header presence) requires consumer-side changes in
   `review-*/SKILL.md` files — software-crafter integration-tests against
   real review commands close this loop.
2. AC-NFR-1 perf budget under real-subprocess invocation may be tight on
   slow CI runners — relax to internal-timing if needed.

---

## Definition of Done — DISTILL

| Criterion | Status |
|-----------|--------|
| All acceptance scenarios written with passing step definitions | YES — 44 scenarios across 8 feature files; 1 active, 43 @skip; all step parsers wired |
| Test pyramid complete (acceptance + planned unit test locations) | YES — acceptance suite under `tests/acceptance/fitness-config-per-directory/`; planned DELIVER unit-test location is alongside `scripts/fitness-config.py` (existing convention from `tests/test_engine_config.py`) |
| Peer review approved (critique-dimensions, 6+ dimensions) | YES — self-review approved; all 9 dimensions evaluated |
| Tests run in CI/CD pipeline | DEFERRED to DELIVER — software-crafter wires up `pytest tests/acceptance/fitness-config-per-directory/` into the existing CI; the walking skeleton MUST run green before DELIVER claims Feature 0 done |
| Story demonstrable to stakeholders from acceptance tests | YES — walking-skeleton.md documents the 30-second demo path |

---

## Handoff Package — Ready for DELIVER (nw-software-crafter)

**Artifacts produced:**

```
tests/acceptance/fitness-config-per-directory/
├── walking-skeleton.feature                  (1 active scenario)
├── milestone-1-walk-up-discovery.feature     (5 scenarios, all @skip)
├── milestone-2-deep-merge.feature            (5 scenarios, all @skip)
├── milestone-3-provenance.feature            (5 scenarios, all @skip)
├── milestone-4-error-handling.feature        (11 scenarios, all @skip)
├── milestone-5-backward-compat.feature       (5 scenarios, all @skip)
├── milestone-6-init-helper.feature           (4 scenarios, all @skip)
├── integration-checkpoints.feature           (8 scenarios, all @skip)
└── steps/
    ├── __init__.py
    ├── conftest.py                           (RepoTree fixture, run_cli helper, JSON parser)
    ├── config_resolution_steps.py            (walk-up, merge, show, backward-compat, integration)
    └── error_handling_steps.py               (validate, schema mismatch, malformed JSON, init helper)

docs/feature/fitness-config-per-directory/distill/
├── test-scenarios.md                         (full Gherkin index + AC trace matrix)
├── walking-skeleton.md                       (rationale + scope + unskip order)
├── acceptance-review.md                      (self-review against 9 dimensions)
└── wave-decisions.md                         (this file)
```

**Delivery gates for software-crafter:**

1. **Feature 0 (walking skeleton)** must run green before any milestone is unskipped. The walking skeleton failing is the entry signal for the inner loop — implement walk-up + deep-merge + show + reporter rendering enough to make it pass.
2. **One @skip removed at a time.** After each removal, drive the inner loop (unit tests on pure functions) until the acceptance scenario passes. Commit. Move to the next.
3. **Backward compatibility** (milestone-5) must be unskipped EARLY (after milestone-3) to lock the legacy CLI contract before error scenarios are exercised.
4. **AC-08.1** (every `review-*/SKILL.md` documents the resolver call) is not behaviorally testable from acceptance scenarios — DELIVER updates the skill prompts as part of the inner loop and documents the change in DELIVER's wave-decisions.
5. **AC-NFR-5** (cross-platform) is satisfied by running the suite on the existing CI matrix; no new acceptance scenario needed.

**Mandate compliance proven:**

- CM-A: zero internal imports (grep evidence above)
- CM-B: zero technical-jargon hits (grep evidence above)
- CM-C: 1 walking skeleton + 43 focused scenarios (counts above); 19/44 error paths (43%)
- CM-D: pure-function inventory documented (table above)

No blockers. No iteration 2 of self-review needed.

---

## Next Wave: DELIVER

Pass to `nw-software-crafter`. Drive Feature 0 from the walking skeleton.
Unskip milestones in the documented order.
