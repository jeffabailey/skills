# Testing Review Scoring Rubric

Hand-maintained scoring rubric. sync-wisdom does not regenerate this file.

Score each dimension against the anchors below. Pick the band whose description best fits the evidence, then move up or down one point within it for strengths or gaps the anchor does not mention. Thresholds come from `checklist.md`; when the two disagree, fix `checklist.md`.

## Severity

| Severity | Definition | Testing examples |
|----------|------------|------------------|
| CRITICAL | A shipped defect in money, security, or data loss is likely to reach users undetected, or the suite reports green while not running. | Payment or auth code with zero tests; CI test job that always exits 0 (`|| true`, `continue-on-error: true` on the only test step). |
| HIGH | Core behavior can regress without any test failing, or the suite is untrusted. | The main business logic module has no tests; a test file whose assertions never run (no `assert`/`expect`); tests that call real external APIs. |
| MEDIUM | A real gap that raises regression risk but has a workaround or partial cover. | No coverage tool or threshold; a bug fix commit without a regression test; unit and slow tests in one CI stage with no timeout. |
| LOW | Hygiene that slows diagnosis or maintenance. | Vague test names (`test1`); `assertNotNull`-only checks on minor helpers; no single-test rerun documented. |

Calibrate severity to the project's purpose. An untested core in a personal CLI is HIGH, not CRITICAL, unless it handles money, credentials, or user data it can destroy.

## Dimensions

### 1. Test Pyramid Balance

Count tests with the native collector (see SKILL.md step 3), not by counting files.

- **9-10**: Unit, integration, and E2E (or CLI/acceptance) levels all present; roughly 70/20/10 or a justified variant; full unit run under 5 minutes; slow tests separated.
- **7-8**: Two or three levels present, base is unit-heavy, minor skew (for example acceptance tests near parity with unit tests but the whole suite still runs fast).
- **5-6**: One level dominates in a way that costs speed or confidence (inverted pyramid, or unit-only for code whose risk is in integration), or tests at one level are disguised as another.
- **3-4**: Only a handful of tests at one level covering a small fraction of modules.
- **1-2**: No tests, or only scaffold tests (a generated `hello`/doctest example).

### 2. Test Quality

- **9-10**: Behavior-describing names, Arrange-Act-Assert structure, specific assertions with negative cases, isolated state (tmp dirs, fixtures), no wall-clock, network, unseeded randomness, or `sleep()`.
- **7-8**: Mostly the above; a few broad assertions or shared fixtures that could leak state.
- **5-6**: Mixed: several tests assert only non-null or truthiness, some order dependence or real I/O, names partly generic.
- **3-4**: Tests largely smoke-level (call and check it did not crash); tests private internals or duplicate production logic.
- **1-2**: No meaningful assertions, or no tests to judge. Score 1 when nothing exists; 2 when only a scaffold exists.

### 3. Coverage Strategy

Includes the QA-process checks from checklist section 6 that concern what gets tested: definition of done requiring tests, regression tests for bug fixes, learning from failures.

- **9-10**: Coverage tool configured with a meaningful threshold enforced in CI; critical paths (auth, money, validation, error handling) tested with boundaries; bug-fix commits add regression tests.
- **7-8**: Critical paths and edge cases tested; coverage measured but not enforced, or enforced with no tool but obvious path coverage.
- **5-6**: Happy paths of main modules tested; no coverage tool; error paths and boundaries thin; at least one fix shipped without a regression test.
- **3-4**: Most source modules have no tests; the critical module is among them.
- **1-2**: No coverage of the core logic at all.

### 4. Performance Testing

Applicability depends on purpose (see N/A below).

- **9-10**: Load or benchmark tests for critical operations with percentile targets, baselines, and CI regression gates.
- **7-8**: Benchmarks or load scripts exist and run on a schedule or before release; targets documented.
- **5-6**: Ad hoc benchmarks or documented targets, not automated.
- **3-4**: Performance matters (service, hot path, large-input tool) but nothing measures it; only an implicit guard such as a CI job timeout.
- **1-2**: Performance is a stated requirement or a known problem and there is no measurement.

### 5. Debugging Support

For services: structured logging, correlation IDs, error context. For libraries and CLIs: error messages with context (what, which input, why), readable test failure output, single-test rerun, test-data factories.

- **9-10**: Failures and errors carry full context; tests print expected vs actual and the failing input; reproduction helpers or factories exist; services have structured logs with correlation IDs.
- **7-8**: Good error context and test diagnostics; one gap (no factories, or logs unstructured in a service).
- **5-6**: Errors name what failed but not the input or cause; tests rely on bare `assert` with no message in custom harnesses.
- **3-4**: Swallowed exceptions or bare `except`/empty `catch` in the code under test; failures need a debugger to understand.
- **1-2**: Errors are silent or discarded and there is no test harness output to diagnose from.

### 6. CI Integration

Includes the QA-process checks from checklist section 6 that concern feedback loops: required checks, pre-commit/local test scripts, flaky-test handling, PR template test requirements.

- **9-10**: Tests run on every PR as a required check, fast stage first, parallel or split where large, timeouts set, flaky tests tracked, results summarized in the PR.
- **7-8**: Tests run on every PR with timeouts; minor gaps (no result summary, some test files not wired into CI, duplicate runs).
- **5-6**: CI runs tests only on push to main or only some suites; failures do not block merges; no timeouts.
- **3-4**: CI exists but does not run tests (lint/build only), or test step is allowed to fail.
- **1-2**: No CI configuration. Score 1 when tests also are not runnable with one documented command; 2 when a local test command exists.

## Not applicable (N/A)

Mark a dimension `N/A — <reason>` only when there is nothing in scope to evaluate, not when something is missing. Missing is a low score; out of scope is N/A.

- Performance Testing is N/A for a small CLI, library, or script tool with no performance requirement, no hot loop over large inputs, and no service surface. It is NOT N/A for a web service, data pipeline, or tool whose README promises speed or processes large files.
- Debugging Support is never N/A for code with tests or error paths; it shifts to the CLI/library criteria above.
- A review scoped to a subset (for example, only `tests/`) may mark CI Integration N/A if the user excluded CI config; say so.

When every dimension but one is N/A, say that the review is too narrow to give a meaningful overall and still report the remaining score.

## Citing evidence for an absence

An absence finding has no line. Cite where the thing should be and how you checked:

- `Location: .github/workflows/ (none); no .gitlab-ci.yml, Jenkinsfile, or .circleci/ at repo root`
- `Location: go/ (no *_test.go); go test -list . reported "no test files"`
- `Location: pyproject.toml:14 [tool.pytest.ini_options] has no --cov; grep -rn "cov" .github/ returned nothing`

Absence findings still need confidence >= 7: you must have searched the places the convention puts them.

## Overall score

- Overall = mean of the scored (non-N/A) dimensions, rounded to one decimal. State which dimensions were averaged.
- If any CRITICAL finding exists, cap the overall at 4.0 and say the cap applied.
- Status bands: a score at or above `statusThresholds.healthy[0]` is Healthy, at or above `statusThresholds.needsAttention[0]` is Needs Attention, anything lower is Critical (defaults 8 / 5 when the resolver gives none). Only the lower bounds count, so a fractional score such as 7.5 is Needs Attention, never a gap; review-full uses the same rule.
