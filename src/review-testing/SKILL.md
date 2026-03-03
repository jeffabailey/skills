---
name: review-testing
description: Analyzes a codebase for software testing fitness, producing scores (1-10) across test pyramid balance, test quality, coverage strategy, performance testing, debugging support, and CI integration. Use when the user says /review:review-testing, requests a test quality review, asks about testing strategy, wants test pyramid analysis, asks about QA practices, or needs testing fitness scores before shipping. Only reports findings with confidence >= 7/10.
---

# Software Testing Fitness Review

Analyze the codebase (or specified files/modules) for software testing fitness. Evaluate test quality, coverage strategy, pyramid balance, and testing infrastructure using evidence from test files, CI configuration, and production support tooling.

Reference: [Fundamentals of Software Testing](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-testing/) — see also [Fundamentals of Software Quality Assurance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-quality-assurance/) and [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

For detailed scoring rubrics, severity definitions, what-good-looks-like / what-bad-looks-like criteria, and domain expertise, read `references/wisdom.md` before scoring. That file is auto-generated from:

- [Fundamentals of Software Testing](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-testing/)
- [Fundamentals of Software Quality Assurance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-quality-assurance/)

Use the wisdom reference when evaluating code and assigning dimension scores.

## Workflow

1. **Read domain knowledge** — Read `references/wisdom.md` to load scoring rubrics, thresholds, and severity definitions.

2. **Discover test infrastructure** — Use Glob to find test files (patterns like `*test*`, `*spec*`, `__tests__`), test configuration (jest.config, pytest.ini, vitest.config, .mocharc, phpunit.xml), CI pipeline files (.github/workflows, .gitlab-ci, Jenkinsfile), and coverage configuration (.nycrc, coverage settings in config files).

3. **Map the test pyramid** — Classify discovered tests into unit, integration, and end-to-end categories. Count tests at each level. Apply the rubrics/thresholds from the wisdom reference to evaluate whether the ratio matches the recommended pyramid shape.

4. **Evaluate test quality** — Read a representative sample of test files at each pyramid level. Apply the rubrics/thresholds from the wisdom reference for naming conventions, assertion quality, test independence, structure, and behavior vs. implementation verification.

5. **Assess coverage strategy** — Check for coverage configuration, coverage thresholds, and which code paths are tested. Apply the rubrics/thresholds from the wisdom reference to determine whether critical paths have dedicated tests and whether boundary values and edge cases are covered.

6. **Review performance testing** — Search for load testing configuration (k6, JMeter, Gatling, Locust, Artillery), benchmark tests, performance regression detection, and performance requirements. Apply the rubrics/thresholds from the wisdom reference.

7. **Inspect debugging support** — Evaluate structured logging, correlation ID propagation, stack trace quality, error context preservation, and reproduction support. Apply the rubrics/thresholds from the wisdom reference.

8. **Audit CI test integration** — Read CI configuration files to verify tests run on pull requests. Apply the rubrics/thresholds from the wisdom reference for parallel execution, test splitting, fast feedback loops, flaky test handling, and test result reporting.

9. **Score each dimension** with file:line evidence, using the rubrics from `references/wisdom.md`.

10. **Produce the report** with scores, evidence, and prioritized action items.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

For severity level definitions (CRITICAL, HIGH, MEDIUM, LOW) with domain-specific examples, consult `references/wisdom.md`.

## Scoring Dimensions (1-10 each)

Dimensions to score (detailed rubrics including what-to-check, what-good-looks-like, and what-bad-looks-like are in `references/wisdom.md`):

1. **Test Pyramid Balance** — Ratio of unit to integration to E2E tests, pyramid shape, execution time distribution
2. **Test Quality** — Naming conventions, assertion quality, test independence, determinism, behavior vs. implementation verification
3. **Coverage Strategy** — Coverage tooling and thresholds, critical path coverage, boundary value testing, regression tests
4. **Performance Testing** — Load testing tools, performance requirements, benchmarks, regression detection, realistic scenarios
5. **Debugging Support** — Structured logging, correlation IDs, error context, test failure output, reproduction helpers
6. **CI Integration** — Automated test execution on PRs, stage separation, parallelization, flaky test handling, result reporting

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

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line
- **Description:** What the issue is and why it matters.
- **Evidence:** The specific code pattern found.
- **Impact:** What could go wrong in production.
- **Remediation:** Concrete fix with code example or specific steps.

(repeat for each finding, ordered by severity)

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

## Reference

Based on [Fundamentals of Software Testing](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-testing/), [Fundamentals of Software Quality Assurance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-quality-assurance/), and guidance from https://jeffbailey.us/categories/fundamentals/
```

Refer to the testing checklist at `review-testing/references/checklist.md` for detailed checks within each dimension.
