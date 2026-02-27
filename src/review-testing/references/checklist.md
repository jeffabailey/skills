# Software Testing Fitness Checklist

Detailed checklist for reviewing code against software testing, quality assurance, performance testing, and debugging fundamentals. Use alongside the review-testing skill to systematically evaluate each dimension.

---

## 1. Test Pyramid Balance

### Test Distribution
- [ ] **Count tests at each level** -- Tally unit, integration, and E2E tests. A healthy ratio is roughly 70% unit, 20% integration, 10% E2E. Significant deviation warrants investigation.
- [ ] **Identify an inverted pyramid** -- If E2E or integration tests outnumber unit tests, the suite will be slow and brittle. Look for test directories named `e2e/`, `integration/`, `functional/` that contain more files than `unit/` or co-located `*_test` files.
- [ ] **Identify a bottom-only pyramid** -- If only unit tests exist and no integration or E2E tests are present, components may pass in isolation but fail when connected. Check for absence of test fixtures that start databases, HTTP servers, or service containers.
- [ ] **Check that each level tests the right scope** -- Unit tests should test individual functions and logic branches. Integration tests should test API endpoints, database queries, and service-to-service calls. E2E tests should test complete user journeys.
- [ ] **Verify E2E tests are targeted** -- E2E tests should cover critical user journeys (signup, login, checkout, core workflow) not trivial behaviors that unit tests can handle. Each E2E test should justify its cost in execution time.

### Execution Time
- [ ] **Measure unit test execution time** -- Unit tests should complete in under 5 minutes for the full suite. If they take longer, look for tests that make network calls, hit databases, or use excessive `sleep()`.
- [ ] **Verify slow tests are separated** -- Integration and E2E tests should run in a separate CI stage from unit tests so fast feedback is not blocked by slow tests.
- [ ] **Check for tests that are integration tests disguised as unit tests** -- A "unit test" that requires a database connection, starts an HTTP server, or reads from the filesystem is actually an integration test and should be classified and run accordingly.

Source: [Fundamentals of Software Testing -- The Testing Pyramid](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-testing/)

---

## 2. Test Quality

### Naming and Readability
- [ ] **Test names describe behavior** -- Look for names like `test_premium_user_gets_10_percent_discount` rather than `test1`, `testUser`, or `it works`. A test name should tell you what is broken when it fails.
- [ ] **Tests follow Arrange-Act-Assert** -- Each test has three visible sections: set up data (Arrange), call the code under test (Act), and verify results (Assert). Look for test bodies that mix setup and assertion without clear separation.
- [ ] **Each test verifies one behavior** -- A test with five unrelated assertions is testing five things. When it fails, you cannot tell which behavior broke. Split into separate tests.

### Independence and Determinism
- [ ] **Tests do not depend on execution order** -- Search for tests that rely on state left by a previous test (shared database rows, global variables, class-level mutable state). Each test should set up its own state and clean up after itself.
- [ ] **Tests do not use wall clock time** -- Look for `time.time()`, `Date.now()`, `System.currentTimeMillis()` in test assertions. These cause flaky failures when tests run slower than expected. Inject a clock or freeze time instead.
- [ ] **Tests do not make real network calls** -- Tests that call real external APIs fail when the API is down, rate-limited, or slow. Mock or stub external dependencies at the HTTP boundary.
- [ ] **Tests do not use unseeded randomness** -- Random test data without a fixed seed produces different inputs each run, making failures non-reproducible. Use seeded random generators or fixed test data.
- [ ] **Tests do not use `sleep()` for synchronization** -- `sleep(2)` to wait for an async operation is flaky and slow. Use explicit waiting mechanisms (polling with timeout, event signals, or test-specific hooks).

### Assertion Quality
- [ ] **Assertions are specific** -- `assertEqual(result.total, 42.00)` is specific. `assertNotNull(result)` and `assertTrue(result != nil)` tell you nothing about correctness. Check that assertions verify the actual expected value.
- [ ] **Negative assertions exist** -- Tests should verify not just that good input produces good output, but that bad input produces the correct error. Look for `assertRaises`, `expect(...).toThrow()`, or equivalent.
- [ ] **No tests without assertions** -- A test that calls a function without checking the result is coverage theater. Search for test functions with no `assert`, `expect`, or `should` statements.

### Anti-Pattern Detection
- [ ] **Tests do not test private methods** -- Tests calling `_private_method()` or accessing internal fields like `obj._internal_state` break on any refactoring. Tests should use the public API.
- [ ] **Tests do not assert on call counts** -- `verify(mock.save).calledExactly(3)` couples the test to how many times an internal method is called, not whether the behavior is correct. Assert on outcomes instead.
- [ ] **Tests do not duplicate production logic** -- If a test reimplements the calculation it is testing (`expected = price * 0.9; assert result == expected`), it tests nothing. Use hardcoded expected values derived from requirements.
- [ ] **Tests do not ignore exceptions** -- Look for `try/except: pass` or empty catch blocks in tests. Swallowed exceptions hide real failures.

Source: [Fundamentals of Software Testing -- Test Design Principles](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-testing/), [Fundamentals of Software Testing -- Common Testing Mistakes](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-testing/)

---

## 3. Coverage Strategy

### Critical Path Coverage
- [ ] **Authentication and authorization paths have tests** -- Login, logout, session management, permission checks, role-based access, and token validation must be tested. Check for tests that verify unauthorized access is denied, not just that authorized access works.
- [ ] **Payment and financial logic has tests** -- Any code that calculates prices, applies discounts, processes payments, or handles refunds needs comprehensive tests including edge cases (zero amounts, negative values, currency rounding, tax calculations).
- [ ] **Data validation has tests** -- Input validation functions should be tested with valid input, invalid input, boundary values, empty input, null/undefined, and excessively long input.
- [ ] **Error handling paths have tests** -- Tests exist for what happens when a database query fails, an external API returns an error, a file is not found, or a timeout occurs. Not just happy paths.

### Boundary Value Testing
- [ ] **Zero and empty values are tested** -- Empty strings, empty arrays, zero quantities, null/undefined values. These are the most common sources of production bugs.
- [ ] **Maximum and minimum values are tested** -- Integer overflow boundaries, string length limits, collection size limits, date range boundaries.
- [ ] **Off-by-one boundaries are tested** -- For any range check (0..10), test the values at 0, 1, 9, 10, and 11. The boundaries are where bugs hide.
- [ ] **Concurrent access is tested** -- If code can be called by multiple threads or requests simultaneously, tests verify it handles concurrent access correctly (no race conditions, no duplicate processing).

### Regression Testing
- [ ] **Bug fixes include a regression test** -- When a bug is fixed, a test is added that reproduces the original failure. This prevents the bug from being reintroduced. Check git history for bug-fix commits that include test additions.
- [ ] **Regression test names reference the bug** -- Test names like `test_checkout_handles_zero_quantity_bug_1234` link the test to the original issue, making it clear why the test exists.
- [ ] **Previously broken scenarios are part of the permanent suite** -- Regression tests are not deleted after the fix ships. They remain as guardrails.

### Coverage Tooling
- [ ] **Coverage tool is configured** -- Check for coverage configuration (nyc, istanbul, coverage.py, JaCoCo, SimpleCov) in the project.
- [ ] **Coverage thresholds are enforced in CI** -- Coverage minimums block merges when critical code loses coverage. The threshold is meaningful (not 0% or a number that never triggers).
- [ ] **Coverage targets critical code, not everything** -- Trivial code (simple getters, data containers, generated code) is excluded from coverage targets. Coverage effort focuses on code where being wrong is expensive.
- [ ] **Coverage is reviewed, not just collected** -- Coverage reports are part of the code review process. New code without tests is flagged during review.

Source: [Fundamentals of Software Testing -- Test Coverage](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-testing/), [Fundamentals of Software Quality Assurance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-quality-assurance/)

---

## 4. Performance Testing

### Load Testing
- [ ] **Load test scripts exist** -- Check for files using k6, JMeter (.jmx), Gatling (.scala), Locust (locustfile.py), or Artillery (.yml). Their presence indicates intentional load testing.
- [ ] **Load tests model real user behavior** -- Test scenarios include realistic user flows (browse, add to cart, checkout) not just uniform GET requests to a single endpoint.
- [ ] **Load test data reflects production volumes** -- Test data includes realistic data sizes, distributions, and relationships. Small uniform test data hides performance problems.
- [ ] **Ramp-up patterns are defined** -- Load tests gradually increase load rather than slamming the system with full traffic instantly. Check for ramp-up configuration in test scripts.

### Performance Requirements
- [ ] **Response time targets are defined** -- Documentation or test scripts specify target response times using percentiles (P95 under 200ms) not averages.
- [ ] **Throughput targets are defined** -- Expected requests per second or concurrent user targets are documented and testable.
- [ ] **Error rate thresholds are defined** -- Acceptable error rates under load are specified (less than 0.1% under expected load).
- [ ] **Requirements distinguish load types** -- Different requirements for normal load, peak load, and degraded mode (when dependencies are slow).

### Benchmarks and Regression Detection
- [ ] **Benchmark tests exist for critical operations** -- Computationally expensive functions have benchmark tests that measure execution time.
- [ ] **Benchmarks compare against baselines** -- Performance results are compared to previous runs to detect regressions. Check for baseline files or comparison logic.
- [ ] **Performance tests run in CI** -- At minimum, lightweight benchmarks run on every commit. Full load tests run on a schedule or before releases.
- [ ] **Performance regression alerts exist** -- When benchmarks show degradation beyond a threshold, the build fails or an alert fires.

### Test Result Analysis
- [ ] **Results track percentiles, not just averages** -- Response time is measured at P50, P95, and P99. Averages hide tail latency that affects real users.
- [ ] **Results include resource utilization** -- CPU, memory, database connections, and thread pool usage are captured during tests, not just response times.
- [ ] **Bottleneck identification follows test execution** -- Test results are analyzed to identify which component (database, application, network) is the limiting factor.

Source: [Fundamentals of Software Performance Testing](https://jeffbailey.us/blog/2025/12/01/fundamentals-of-software-performance-testing/)

---

## 5. Debugging Support

### Structured Logging
- [ ] **Logging is structured** -- Log output uses a consistent format (JSON, key-value pairs) that can be parsed and searched. Not unstructured `console.log("error happened")`.
- [ ] **Log entries include context** -- Each log entry includes: timestamp, log level, request/correlation ID, operation name, and relevant identifiers (user_id, order_id).
- [ ] **Log levels are used correctly** -- ERROR for things that need attention, WARN for degraded behavior, INFO for significant events, DEBUG for diagnostic detail. Not everything at INFO or ERROR.
- [ ] **Sensitive data is not logged** -- Passwords, tokens, credit card numbers, and PII are redacted or excluded from logs. Check for logging of request bodies or headers that might contain secrets.

### Correlation and Tracing
- [ ] **Correlation IDs propagate across services** -- A request ID generated at the edge (API gateway, load balancer) is passed through all downstream service calls via headers and included in log entries.
- [ ] **Distributed traces are supported** -- OpenTelemetry, Jaeger, Zipkin, or equivalent tracing is configured to track request latency across service boundaries.
- [ ] **Error traces include the full call chain** -- When an error occurs in a downstream service, the upstream caller's logs include the correlation ID so the full path can be reconstructed.

### Error Context and Stack Traces
- [ ] **Errors preserve context** -- Exceptions include what was being attempted, what input was provided, and what failed. Not just "error occurred" or a bare exception type.
- [ ] **Stack traces are preserved across async boundaries** -- In async code, the original stack trace is not lost. Check for patterns that swallow stack traces (bare `raise`, `throw` without cause chaining).
- [ ] **Error handling does not swallow exceptions** -- Search for empty catch blocks (`catch (e) {}`, `except: pass`). Silent error swallowing makes bugs invisible.
- [ ] **Errors are categorized** -- Transient errors (network timeout, rate limit) are distinguished from permanent errors (invalid input, missing permission) because they require different handling.

### Test Failure Diagnostics
- [ ] **Test failures show expected vs actual** -- When a test fails, the output shows what was expected and what was received, not just "assertion failed".
- [ ] **Test failures include input context** -- For parameterized tests, the specific input that caused the failure is visible in the output.
- [ ] **Failed tests can be re-run individually** -- Test runner supports running a single test by name or path, enabling fast iteration during debugging.

### Reproduction Support
- [ ] **Factory functions or builders create test data** -- Shared factories produce test objects with sensible defaults and overridable fields, avoiding copy-paste of data setup across tests.
- [ ] **Seed scripts or fixtures exist for local development** -- Developers can populate a local database with representative data for manual debugging and exploration.
- [ ] **Failing scenarios can be captured as test cases** -- When a production bug is found, there is a clear path to write a minimal reproduction as a test (the codebase supports injecting dependencies and controlling inputs).

### Invariant Checking
- [ ] **Assertions or contracts guard module boundaries** -- Preconditions on function inputs and postconditions on outputs catch invalid state early rather than letting it propagate.
- [ ] **Invariants are expressed as testable expectations** -- Examples: "we never charge twice for the same order ID", "a request with an invalid token returns 401, not 500". These are encoded as tests.
- [ ] **Debug/development modes enable extra validation** -- Additional runtime checks (assertions, contract verification) can be enabled in development and test environments for early defect detection.

Source: [Fundamentals of Software Debugging](https://jeffbailey.us/blog/2025/12/25/fundamentals-of-software-debugging/), [Fundamentals of Software Debugging -- Observability](https://jeffbailey.us/blog/2025/12/25/fundamentals-of-software-debugging/)

---

## 6. QA Process

### Quality Assurance as a System
- [ ] **Quality is built into the process, not bolted on at the end** -- Tests, reviews, and checks happen during development, not in a separate "QA phase" after code is written. Check whether CI runs checks on every PR.
- [ ] **Definition of done includes tests** -- Pull request templates or contribution guides require tests for new features and bug fixes. Check PR templates for test requirements.
- [ ] **Code reviews include test review** -- Reviewers evaluate test quality alongside code quality. Check PR review comments for discussion of test coverage and test design.
- [ ] **Small, reviewable changes are the norm** -- Pull requests are focused and small (under 400 lines). Large PRs are harder to review and more likely to introduce untested behavior.

### Feedback Loops
- [ ] **Short feedback loops exist** -- Failing tests are detected within minutes, not hours or days. Check CI pipeline duration from push to test results.
- [ ] **Test failures block merges** -- CI is configured as a required check. Failing tests prevent merging, not just warn.
- [ ] **Flaky tests are treated as quality problems** -- Flaky tests have tracking issues and remediation plans, not silent retries. Check for retry configuration without corresponding flaky-test tracking.
- [ ] **Test suite trust is maintained** -- Developers run tests locally before pushing. Check for pre-commit hooks, local test scripts, or documentation encouraging local test runs.

### Learning from Failures
- [ ] **Bug reviews produce process improvements** -- After significant bugs, the team identifies what process change would have prevented or detected the issue earlier (not just "add more tests").
- [ ] **Incident postmortems include testing gaps** -- Postmortem documents examine whether existing tests should have caught the issue and what test would prevent recurrence.
- [ ] **Metrics track test effectiveness** -- Defect escape rate (bugs found in production that tests should have caught), test suite execution time, and flaky test count are monitored over time.

Source: [Fundamentals of Software Quality Assurance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-quality-assurance/)

---

## 7. CI Test Integration

### Pipeline Configuration
- [ ] **Tests run on every pull request** -- CI configuration triggers test execution on push and pull_request events. Check CI config files for trigger conditions.
- [ ] **Test stages are ordered by speed** -- Fast unit tests run first. If they fail, slower integration and E2E tests do not run. This provides the fastest possible feedback.
- [ ] **Tests run in parallel** -- Test execution is distributed across multiple workers or containers. Check for parallel configuration in CI (matrix strategy, test splitting, parallel workers).
- [ ] **Test timeouts are configured** -- CI jobs have timeout limits to prevent hung tests from blocking the pipeline indefinitely.

### Fast Feedback
- [ ] **Unit test feedback is under 5 minutes** -- From push to unit test results, developers wait no more than 5 minutes. Longer waits cause context switching.
- [ ] **Test results are summarized in PR** -- PR comments or checks show test counts, failures, and coverage changes without requiring developers to dig through logs.
- [ ] **Failed tests are clearly identified** -- Test failure output identifies the specific failing test, the assertion that failed, and the expected vs actual values. Not a wall of stack traces.

### Flaky Test Management
- [ ] **Flaky tests are identified and tracked** -- A mechanism exists to detect tests that pass and fail without code changes. Check for flaky test reports, quarantine directories, or skip-with-reason annotations.
- [ ] **Flaky tests are quarantined, not silently retried** -- Retrying failures hides flakiness. Quarantined tests are tracked for remediation and do not block other developers.
- [ ] **Flaky test trends are monitored** -- The number of flaky tests over time is tracked. An increasing trend indicates a testing infrastructure problem.

### Test Selection and Optimization
- [ ] **Affected test detection exists on large codebases** -- For repositories with thousands of tests, only tests affected by the changed files run on each PR. Check for test selection tooling or dependency analysis.
- [ ] **Test caching is used where appropriate** -- Unchanged test inputs produce cached results, avoiding redundant execution. Check for caching configuration in CI.
- [ ] **Expensive tests run on a schedule** -- Full E2E suites, load tests, and comprehensive integration tests run nightly or before releases, not on every commit.

Source: [Fundamentals of Software Testing -- Test Automation and CI](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-testing/), [Fundamentals of Software Quality Assurance -- Short Feedback Loops](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-quality-assurance/)

---

## Quick Reference: The Five Most Common Testing Problems

1. **Inverted test pyramid** -- Most tests are E2E or integration, few unit tests. Fix: extract logic into testable units, write focused unit tests, reserve E2E for critical journeys.
2. **Tests without assertions** -- Functions are called but results are never checked. Fix: add specific assertions that verify expected values, not just non-null checks.
3. **Flaky tests ignored** -- Intermittent failures are retried without investigation. Fix: quarantine flaky tests, fix root causes (time dependence, shared state, network calls), track trends.
4. **No tests on critical paths** -- Payment, auth, and security code has no test coverage. Fix: prioritize tests for code where being wrong is expensive (money, security, data loss).
5. **Slow test feedback** -- Tests take 30+ minutes, developers stop running them. Fix: separate fast and slow tests, parallelize execution, run unit tests first.

---

## Source Articles

- [Fundamentals of Software Testing](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-testing/)
- [Fundamentals of Software Quality Assurance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-quality-assurance/)
- [Fundamentals of Software Performance Testing](https://jeffbailey.us/blog/2025/12/01/fundamentals-of-software-performance-testing/)
- [Fundamentals of Software Debugging](https://jeffbailey.us/blog/2025/12/25/fundamentals-of-software-debugging/)
- [Jeff Bailey Fundamentals Series](https://jeffbailey.us/categories/fundamentals/)
