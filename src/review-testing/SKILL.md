---
name: review-testing
description: Analyzes a codebase for software testing fitness, producing scores (1-10) across test pyramid balance, test quality, coverage strategy, performance testing, debugging support, and CI integration. Use when the user says /review:review-testing, requests a test quality review, asks about testing strategy, wants test pyramid analysis, asks about QA practices, or needs testing fitness scores before shipping.
---

# Software Testing Fitness Review

Analyze the codebase (or specified files/modules) for software testing fitness. Evaluate test quality, coverage strategy, pyramid balance, and testing infrastructure using evidence from test files, CI configuration, and production support tooling.

## Workflow

1. **Discover test infrastructure** -- Use Glob to find test files (patterns like `*test*`, `*spec*`, `__tests__`), test configuration (jest.config, pytest.ini, vitest.config, .mocharc, phpunit.xml), CI pipeline files (.github/workflows, .gitlab-ci, Jenkinsfile), and coverage configuration (.nycrc, coverage settings in config files).

2. **Map the test pyramid** -- Classify discovered tests into unit, integration, and end-to-end categories. Count tests at each level. Identify the ratio and whether it matches the recommended pyramid shape (many unit tests, fewer integration tests, few E2E tests).

3. **Evaluate test quality** -- Read a representative sample of test files at each pyramid level. Check naming conventions, assertion quality, test independence, Arrange-Act-Assert structure, and whether tests verify behavior or implementation details.

4. **Assess coverage strategy** -- Check for coverage configuration, coverage thresholds, and which code paths are tested. Determine whether critical paths (money, security, user data, error handling) have dedicated tests. Look for boundary value testing and edge case coverage.

5. **Review performance testing** -- Search for load testing configuration (k6, JMeter, Gatling, Locust, Artillery), benchmark tests, performance regression detection, and performance requirements in documentation. Check whether performance metrics are defined and tracked.

6. **Inspect debugging support** -- Evaluate structured logging, correlation ID propagation, stack trace quality, error context preservation, and reproduction support (test helpers, fixture generators, seed scripts). Check whether failures produce actionable diagnostic information.

7. **Audit CI test integration** -- Read CI configuration files to verify tests run on pull requests, check for parallel test execution, test splitting, fast feedback loops, flaky test handling, and test result reporting.

8. **Score each dimension** with specific file:line evidence.

9. **Produce the report** with scores, evidence, and prioritized action items.

## Scoring Dimensions (1-10 each)

Evaluate and score each dimension with evidence from the code.

### 1. Test Pyramid Balance

What to check:
- Ratio of unit tests to integration tests to E2E tests
- Whether the pyramid is inverted (too many E2E tests, too few unit tests)
- Whether the pyramid is bottom-heavy (all unit tests, no integration or E2E coverage of critical user flows)
- Test execution time distribution across levels
- Whether each pyramid level tests the right things (units test logic, integrations test component interaction, E2E tests critical user journeys)

What good looks like (8-10):
- Clear pyramid shape: many fast unit tests, moderate integration tests, few targeted E2E tests
- Unit tests cover individual functions and logic branches
- Integration tests verify API endpoints, database interactions, and service communication
- E2E tests cover critical user journeys (signup, checkout, core workflows) and nothing trivial
- Test suite runs in under 5 minutes for unit tests, with slower tests separated

What bad looks like (1-3):
- Inverted pyramid: most tests are E2E or integration, few or no unit tests
- Only unit tests exist; no verification that components work together
- All tests at one level with no deliberate distribution
- E2E tests covering trivial behavior that unit tests should handle
- Test suite takes 30+ minutes because everything runs as integration tests

### 2. Test Quality

What to check:
- Test names describe the behavior being verified (not "test1", "testUser", "it works")
- Each test verifies one specific behavior, not multiple unrelated assertions
- Tests follow Arrange-Act-Assert or Given-When-Then structure
- Tests are independent: no shared mutable state, no ordering dependencies
- Tests are deterministic: no reliance on wall clock time, random values without seeds, or network calls without mocks
- Tests verify behavior (inputs/outputs/side effects) not implementation (private methods, internal state, call counts)
- Assertions are specific: `assertEqual(result, 42)` not just `assertNotNull(result)`

What good looks like (8-10):
- Test names read as behavior documentation: `test_premium_user_gets_10_percent_discount`
- Each test has a clear Arrange section, a single Act, and focused Assert
- Tests can run in any order and produce the same results
- Mocks replace external dependencies, not internal implementation
- Edge cases and error paths have dedicated tests
- Assertions verify exact expected values, not just truthiness

What bad looks like (1-3):
- Test names are `test1`, `test_user`, `it should work` with no behavior description
- Tests assert on multiple unrelated behaviors in a single function
- Tests depend on execution order or shared database state between tests
- Tests call private methods or assert on internal field names that break on refactoring
- Tests have no assertions (call the function but never check the result)
- Tests use `sleep()` or `time.time()` making them flaky across environments

### 3. Coverage Strategy

What to check:
- Whether coverage tooling is configured and thresholds are enforced
- Whether critical code paths have dedicated test coverage (payment processing, authentication, authorization, data validation)
- Whether boundary values and edge cases are tested (zero, negative, empty, null, max values)
- Whether error handling paths are tested (exceptions, timeouts, invalid input, missing data)
- Whether coverage targets high-risk code rather than chasing a percentage across everything
- Whether tests exist for bug fixes (regression tests that prevent reintroduction)

What good looks like (8-10):
- Coverage thresholds enforced in CI (not necessarily 100%, but meaningful thresholds on critical paths)
- Payment, auth, and security code has near-complete test coverage
- Edge cases are tested explicitly: empty inputs, boundary values, concurrent access
- Bug fixes include a regression test that reproduces the original bug
- Coverage reports are reviewed, not just collected
- Trivial code (simple getters, data containers) is intentionally excluded from coverage targets

What bad looks like (1-3):
- No coverage tooling configured
- Critical paths (auth, payments) have no tests or only happy-path tests
- No boundary value testing: only "normal" inputs tested
- No regression tests: bugs are fixed without tests to prevent recurrence
- Coverage theater: 90% coverage but tests have no assertions or only test trivial code
- Error paths are untested: no tests for what happens when dependencies fail

### 4. Performance Testing

What to check:
- Whether load testing tools are configured (k6, JMeter, Gatling, Locust, Artillery)
- Whether performance requirements are defined (response time targets, throughput goals, concurrent user targets)
- Whether benchmark tests exist for critical operations
- Whether performance regression detection is in place (comparing current results to baselines)
- Whether performance test scenarios reflect real user behavior (not synthetic uniform load)
- Whether test data volumes match production scale

What good looks like (8-10):
- Load test scripts exist for critical endpoints with defined performance requirements
- Performance requirements specify percentiles (P95, P99), not just averages
- Benchmarks run in CI and alert on regressions against baselines
- Test scenarios model realistic user flows with ramp-up patterns
- Test data reflects production volumes and distributions
- Results are analyzed, not just collected; bottleneck identification follows test execution

What bad looks like (1-3):
- No load testing tools or scripts anywhere in the repository
- No defined performance requirements or SLAs
- No benchmarks for computationally expensive operations
- Performance testing only happens manually before releases, if at all
- Test scenarios use uniform artificial load that does not reflect real traffic patterns
- Performance issues are discovered only when users complain in production

### 5. Debugging Support

What to check:
- Whether logging is structured (JSON, key-value) and searchable, not unstructured println/console.log
- Whether correlation IDs or request IDs propagate across service boundaries
- Whether errors preserve context (stack traces, input values, user/request identifiers)
- Whether test failures produce actionable output (clear failure messages showing expected vs actual)
- Whether reproduction helpers exist (seed scripts, fixture generators, factory functions)
- Whether the codebase has invariants expressed as assertions or contracts that catch invalid state early

What good looks like (8-10):
- Structured logging with consistent fields: request_id, user_id, operation, duration, error
- Correlation IDs generated at the edge and propagated through all downstream calls
- Error messages include context: what was attempted, what input was provided, what failed
- Test failure output shows expected vs actual with enough context to diagnose without re-running
- Factory functions or builders create test data with sensible defaults and overrides
- Assertions or contracts check invariants at module boundaries

What bad looks like (1-3):
- Logging is unstructured `console.log("error")` with no context
- No request tracing; failures cannot be followed across services
- Errors swallowed silently with empty catch blocks or generic "something went wrong" messages
- Test failures show only "assertion failed" with no indication of expected vs actual values
- Test data is hardcoded in each test with no shared fixtures or factories
- No invariant checks; invalid state propagates silently until it causes a visible failure elsewhere

### 6. CI Integration

What to check:
- Whether tests run automatically on every pull request
- Whether test stages are separated (fast unit tests first, slower integration/E2E tests after)
- Whether parallel test execution is configured for faster feedback
- Whether flaky tests are tracked and quarantined (not just retried silently)
- Whether test results are reported clearly (summary in PR comments, failure details visible)
- Whether test selection or affected-test detection reduces unnecessary test execution on large codebases

What good looks like (8-10):
- Tests run on every PR and block merge on failure
- Unit tests run first (under 5 minutes) providing fast feedback; integration and E2E run after
- Tests run in parallel across workers or containers
- Flaky tests are quarantined with tracking issues, not silently retried
- Test results appear in PR summary with failure details and links to logs
- Selective test execution skips unaffected tests on large codebases

What bad looks like (1-3):
- No CI pipeline, or CI exists but does not run tests
- All tests run in a single sequential job taking 30+ minutes
- No parallel execution; feedback loop is too slow for developers to act on
- Flaky tests are retried 3 times with no tracking; intermittent failures are ignored
- Test failures produce wall-of-text logs with no summary or clear failure identification
- Every PR runs the full test suite regardless of which files changed

## Output Format

Write the report to `docs/testing-review.md` with this structure:

```markdown
# Software Testing Fitness Report

## Summary

Overall fitness score: X.X / 10 (average of dimensions)

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Test Pyramid Balance | X/10 | ... |
| Test Quality | X/10 | ... |
| Coverage Strategy | X/10 | ... |
| Performance Testing | X/10 | ... |
| Debugging Support | X/10 | ... |
| CI Integration | X/10 | ... |

## Detailed Findings

### Test Pyramid Balance (X/10)
**Evidence:** [specific files, test counts, execution times]
**Strengths:** ...
**Gaps:** ...

### Test Quality (X/10)
**Evidence:** [specific test files with line references showing patterns]
**Strengths:** ...
**Gaps:** ...

### Coverage Strategy (X/10)
**Evidence:** [coverage config, critical path test files, missing coverage areas]
**Strengths:** ...
**Gaps:** ...

### Performance Testing (X/10)
**Evidence:** [load test scripts, benchmark files, performance requirements]
**Strengths:** ...
**Gaps:** ...

### Debugging Support (X/10)
**Evidence:** [logging patterns, error handling, correlation ID usage]
**Strengths:** ...
**Gaps:** ...

### CI Integration (X/10)
**Evidence:** [CI config files, test stage configuration, parallelization]
**Strengths:** ...
**Gaps:** ...

## Top 5 Action Items (by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...
3. ...
4. ...
5. ...

## Checklist Reference

See review-testing/references/checklist.md for the full testing checklist
derived from software testing, quality assurance, performance testing,
and debugging fundamentals.
```

Refer to the testing checklist at `review-testing/references/checklist.md` for detailed checks within each dimension.
