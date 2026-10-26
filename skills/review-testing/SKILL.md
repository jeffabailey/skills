---
name: review-testing
description: Analyzes a codebase for software testing fitness, producing scores (1-10) across test pyramid balance, test quality, coverage strategy, performance testing, debugging support, and CI integration. Use when the user says /review:review-testing, requests a test quality review, asks about testing strategy, wants test pyramid analysis, asks about QA practices, or needs testing fitness scores before shipping. Only reports findings with confidence >= 7/10.
---

# Software Testing Fitness Review

Analyze the codebase (or specified files/modules) for software testing fitness. Evaluate test quality, coverage strategy, pyramid balance, and testing infrastructure using evidence from test files, the code they test, CI configuration, and production support tooling.

Reference: [Fundamentals of Software Testing](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-testing/) — see also [Fundamentals of Software Quality Assurance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-quality-assurance/) and [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

- `references/rubric.md` is the scoring source: severity table, 1-10 anchors per dimension, N/A rules, how to cite an absence, and the overall-score formula. Read it first; it is short. Scores are only repeatable if every run uses the same anchors.
- `references/checklist.md` is what to check during the workflow steps. Its section 6 (QA Process) has no dimension of its own: its feedback-loop checks score under CI Integration and its regression and definition-of-done checks under Coverage Strategy.
- `references/wisdom.md` is optional background, generated from the two Fundamentals articles. It has no rubrics. Grep it by heading for a specific question (for example `grep -n '^### ' references/wisdom.md`); never read it whole.

## Configuration

Invoke the resolver CLI to obtain effective weights and thresholds for the review target. Never load `fitness-config.json` directly.

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py" show --path <target>
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; the resolver ships two levels up in the plugin's `scripts/`. If your agent does not expand the variable, substitute the directory containing this `SKILL.md`.

Where `<target>` is the file or directory under review. The CLI walks up to discover any module override and merges it with the root config. Include the `Config:` and `Effective weights:` lines from the resolver output within the first 10 lines of the final report as the provenance trail (AC-03.1, AC-08.2). The `effective` object inside the JSON block delimited by `<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->` / `<!-- END_EFFECTIVE_CONFIG_JSON -->` carries weights, status thresholds, security, and scoring for any programmatic needs.

## Workflow

1. **Load the rubric** — Read `references/rubric.md`, then skim `references/checklist.md`. Run the resolver and keep its `Config:` and `Effective weights:` lines.

2. **Scope and inventory** — Decide the target and identify what kind of project it is (service, library, CLI, script collection, polyglot). Find, per language:
   - Test files and runners: `*_test.go` (go test), `test/*.exs` + `mix.exs` (ExUnit), `*Tests.csproj` / `[Fact]` / `[Test]` (xUnit/NUnit, dotnet test), `test_*.py` / `pytest.ini` / `pyproject.toml` (pytest), `*.test.ts` / `jest.config` / `vitest.config` / `.mocharc`, `phpunit.xml`, `*.feature` (BDD), shell test harnesses.
   - CI: `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/`; pre-commit hooks; coverage config.
   - The source under test: the main modules each test file should cover.

   Skip build and data artifacts: `_build/`, `deps/`, `bin/`, `obj/`, `target/`, `node_modules/`, `.venv/`, `dist/`, generated code, and large data or output files (anything over ~1 MB, `*.txt` dumps, fixtures you do not need to read). They are not tests even when "test" appears in the path, and reading them wastes the budget.

3. **Decide applicability** — Using the inventory and the N/A rules in `rubric.md`, decide which of the six dimensions apply. Mark the rest `N/A — <reason>` now so later steps do not invent evidence for them. A missing practice is a low score, not N/A.

4. **Map the test pyramid** — Count tests with the native collector, because file counts miss parametrized cases and multi-test files:
   - Python: `pytest --collect-only -q` (last line gives the total; add `-m <marker>` or a path to split levels)
   - Go: `go test -list . ./...`
   - Elixir: `mix test --trace` (or count `test "` blocks if deps cannot be fetched)
   - .NET: `dotnet test --list-tests`
   - JS/TS: `npx jest --listTests` / `npx vitest list`; otherwise count `it(`/`test(` calls

   Run collectors read-only and offline where possible. If a collector cannot run (missing toolchain, no network), count by grep and say so in the evidence. Classify counts into unit, integration, and E2E/acceptance, and record the suite's run time if you ran it.

5. **Evaluate test quality** — Read a representative sample at each level against checklist section 2.

6. **Assess coverage against the code** — Read the source under test, not only the tests. List the core functions and which have tests. When you read untested code, note concrete defects or risky branches you can see (an empty result when a regex has no capture group, an unchecked error return, an off-by-one). Remediations must name these functions and behaviors, so the user gets "add a test for `parseArgs` rejecting a missing path" rather than "add more tests". Check git history for bug-fix commits without regression tests when `.git` is available.

7. **Review performance testing** — If applicable, search for load and benchmark tooling (k6, JMeter, Gatling, Locust, Artillery, `go test -bench`, `pytest-benchmark`, BenchmarkDotNet, Benchee) and stated performance requirements.

8. **Inspect debugging support** — Use the service or CLI/library criteria in `rubric.md` that fit the project type.

9. **Audit CI test integration** — Read CI files to confirm tests run on pull requests, with timeouts, and that every test suite found in step 2 is wired in. Apply checklist sections 6 and 7.

10. **Score** — Score each applicable dimension against the `rubric.md` anchors with file:line evidence (or an absence citation in the rubric's format). Compute the overall per the rubric.

11. **Self-check, then write the report** — Before writing, confirm:
    - every cited file:line uses a repo-relative path (not a bare filename), exists, and says what the finding claims;
    - every finding has confidence >= 7;
    - the overall equals the mean of the scored dimensions (and the CRITICAL cap, if any);
    - no secret values are reproduced; refer to secrets by file:line only.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line, or, for an absence, to the place it should be and the search that came up empty?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

Severity levels (CRITICAL, HIGH, MEDIUM, LOW) and their testing examples are defined in `references/rubric.md`. Calibrate to the project's purpose: an untested personal CLI is not a CRITICAL risk the way an untested payment path is.

## Scoring Dimensions (1-10 each)

Anchors for each band are in `references/rubric.md`.

1. **Test Pyramid Balance** — Ratio of unit to integration to E2E tests, pyramid shape, execution time distribution
2. **Test Quality** — Naming conventions, assertion quality, test independence, determinism, behavior vs. implementation verification
3. **Coverage Strategy** — Coverage tooling and thresholds, critical path coverage, boundary value testing, regression tests, definition of done
4. **Performance Testing** — Load testing tools, performance requirements, benchmarks, regression detection (often N/A for small CLIs and libraries)
5. **Debugging Support** — Error context, test failure output, reproduction helpers; structured logging and correlation IDs for services
6. **CI Integration** — Automated test execution on PRs, required checks, stage separation, timeouts, flaky test handling, local feedback loops

## Empty or near-empty suites

When a project has no tests or only a scaffold, the report is still useful if it is short and specific:
- Say plainly which languages or modules have zero tests and how you checked (collector output or the absence citation).
- Score from the low anchors; do not award points for practices that cannot exist yet (for example, Test Quality cannot exceed 2 with no real tests).
- Spend the effort on step 6: the action items should be a starter plan naming the first functions to test, the cases each needs, and the one command that will run them, ordered by where a bug would hurt most.

## Output Format

Write the report to `docs/testing-review.md` at the root of the repository that contains the target, unless the user gives a path. For a review scoped to a subdirectory or file set, write `docs/testing-review-<scope-slug>.md` (for example `docs/testing-review-scripts.md`) so a scoped run does not replace the whole-repo report.

```markdown
# Software Testing Fitness Report

**Target:** <path(s) or scope reviewed; project type>
Config: <copied from resolver output>
Effective weights: <copied from resolver output>

## Direct Answer

(Only when the user asked a specific question. Answer it in 2-4 sentences before the scores.)

## Summary

Overall fitness score: X.X / 10 — <status band> (mean of <list of scored dimensions>; <CRITICAL cap applied / not applied>)

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Test Pyramid Balance | X/10 | ... |
| Test Quality | X/10 | ... |
| Coverage Strategy | X/10 | ... |
| Performance Testing | X/10 or N/A — reason | ... |
| Debugging Support | X/10 | ... |
| CI Integration | X/10 | ... |

Test inventory: <counts per level and per language, and the command used for each>

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line (or absence citation per rubric.md)
- **Description:** What the issue is and why it matters.
- **Evidence:** The specific code pattern found.
- **Impact:** What could go wrong in production.
- **Remediation:** Concrete fix naming the function or behavior to test and the cases to cover.

(repeat for each finding, ordered by severity)

### Test Pyramid Balance (X/10)
**Evidence:** [collector output, counts per level, execution time]
**Strengths:** ...
**Gaps:** ...

(repeat for each dimension; for N/A dimensions, one line giving the reason)

## Action Items (up to 5, by impact)

1. [SEVERITY] Description naming the function/file to change -- file:line
2. ...

## Reference

Checks from `review-testing/references/checklist.md`; scores from `review-testing/references/rubric.md`. Based on [Fundamentals of Software Testing](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-testing/) and [Fundamentals of Software Quality Assurance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-quality-assurance/).
```
