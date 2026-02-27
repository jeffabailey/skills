# Software Testing Fitness Report

## Summary

**Overall fitness score: 4.5 / 10**

This repository is a **skills meta-project** -- it defines structured review workflows (SKILL.md files and checklists) that AI agents use to analyze other codebases. The executable code consists of two shell test scripts (`tests/workflow-tests.sh`, `tests/skill-structure-tests.sh`), one Python configuration script (`.github/scripts/engine-config.py`), and CI workflow YAML. The `tests/` directory also contains **documentation-based test plans** (trigger tests and functional tests in markdown) that are designed for manual execution with the `claude` CLI.

Since the last review, the project has added a `pr-checks.yml` workflow that runs automated shell tests on every PR and push to main. This is a significant improvement over the prior state (no automated test execution at all). However, the 132+ trigger scenarios and 32+ functional scenarios in markdown remain manual-only, and there is still no coverage tooling, no performance testing, and no machine-parseable test output.

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Test Pyramid Balance | 5/10 | 99 automated shell assertions in CI (unit-like) but no integration or E2E automation; 164+ manual-only scenarios |
| Test Quality | 6/10 | Shell tests are deterministic and independent with clear naming; fail output lacks expected-vs-actual for most assertions |
| Coverage Strategy | 3/10 | No coverage tool; automated tests cover only structure/config, not skill behavior |
| Performance Testing | 1/10 | No load tests, benchmarks, or performance requirements |
| Debugging Support | 4/10 | Shell fail() helper has optional "got:" output but most assertions do not use it; no structured logging |
| CI Integration | 7/10 | 4 parallel CI jobs on every PR; tests block merge; no flaky-test tracking or test result reporting |

---

## Detailed Findings

### Test Pyramid Balance (5/10)

**Evidence:**

Automated tests (run in CI):
- `tests/skill-structure-tests.sh` -- 59 assertions across 4 test sections: directory existence (13), SKILL.md existence + frontmatter (26), checklist existence (10), report path convention (10)
- `tests/workflow-tests.sh` -- 40 assertions across 8 test sections: file structure (6), engine config outputs (18 = 3 engines x 5 keys + 3 engine_id checks), clean headers (2), multi-engine support (4), legacy patterns (2), act parsing (5), triggers (2), prompt (2)
- `.github/workflows/pr-checks.yml:29-46` -- `workflow-validation` job validates engine-config.py syntax and outputs programmatically (separate from the shell tests)
- `.github/workflows/pr-checks.yml:62-69` -- `skill-structure` job runs `skill-structure-tests.sh`
- `.github/workflows/pr-checks.yml:48-60` -- `workflow-tests` job runs `workflow-tests.sh`

Manual-only tests (documented in markdown, never executed by CI):
- `tests/trigger-tests.md` -- 13 skills x ~8 trigger phrases each = ~132 trigger scenarios
- `tests/functional-tests.md` -- 32 functional scenarios across 13 skills using Given/When/Then
- `README.md:199-257` -- documents the manual test protocol

**Test distribution:**
- **Unit-like (automated):** 99 structural assertions -- file existence, frontmatter presence, grep pattern matching, engine config output validation. Fast, deterministic, run in CI.
- **Integration-like (manual):** Trigger tests (does the right skill activate?) and functional tests (does the skill produce correct structured output?). Require `claude` CLI execution against a target project.
- **E2E (automated but separate):** `fitness-review.yml` runs full agent-based review weekly. This tests the pipeline, not the skills themselves.

**Strengths:**
- Automated tests cover the structural contract: every skill has a directory, SKILL.md with frontmatter, checklist (where applicable), and correct report path reference.
- Engine config validation catches regressions in the multi-engine configuration -- all 3 engines tested for all required output keys.
- Clear separation between structural validation (automated) and behavioral validation (manual).
- All 13 skills have both trigger and functional test documentation.

**Gaps:**
- **Bottom-heavy pyramid:** 100% of automated tests are structural/unit-like. Zero automated integration tests verify that skills produce correct output when invoked.
- 164+ manual scenarios represent the vast majority of testing intent but are never executed by CI.
- No automated test verifies skill behavior -- a skill could have a completely broken workflow section and still pass all CI checks as long as its file structure is correct.
- No execution-time data; test suite completes in under 5 seconds (observed locally), but this covers only structural checks.

---

### Test Quality (6/10)

**Evidence:**

Shell test quality (`tests/workflow-tests.sh`, `tests/skill-structure-tests.sh`):
- `workflow-tests.sh:10-11` -- Custom `pass()` and `fail()` functions with optional "got:" diagnostic output
- `workflow-tests.sh:18-22` -- File existence checks with clear pass/fail descriptions (e.g., "fitness-review.yml exists")
- `workflow-tests.sh:71-92` -- Engine config output validation iterates engines and keys systematically
- `skill-structure-tests.sh:32-43` -- SKILL.md existence and frontmatter checks for every skill in the SKILLS array
- `skill-structure-tests.sh:12-15` -- SKILLS array serves as the authoritative skill list for structure tests

Markdown test quality (`tests/functional-tests.md`, `tests/trigger-tests.md`):
- `functional-tests.md:16-24` -- Given/When/Then with specific expected outputs: "Report contains scores (1-10) for: Coupling, Cohesion, Layering, Modularity, Naming, API Design, Maintainability"
- `functional-tests.md:80-88` -- "Detects inverted test pyramid" scenario with concrete preconditions ("50 E2E tests, 5 unit tests") and expected behavior
- `trigger-tests.md:53-66` -- "Should trigger" and "Should NOT trigger" phrases for review-testing, including negative case for "Generate tests" (belongs to review-jit-test-gen)

**Strengths:**
- Shell test names are descriptive and behavior-focused: "fitness-review.yml exists", "engine-config.py outputs engine_id=claude", "No hardcoded engine_id in YAML" -- readable as failure documentation.
- Tests are deterministic: all assertions use file existence checks (`-f`, `-d`, `-x`) or `grep -q` pattern matching. No wall-clock time, no network calls, no randomness.
- Tests are independent: each assertion checks one condition, no shared mutable state, no ordering dependencies.
- Functional test scenarios follow strict Given/When/Then with one behavior per scenario.
- Each test verifies one specific behavior (not multiple unrelated assertions per test case).

**Gaps:**
- **Most assertions lack expected-vs-actual output:** `workflow-tests.sh:73-77` shows the only place that captures "got:" output (engine_id validation). All other `grep -q` failures produce only "FAIL: description" with no indication of what was actually found. Example: `workflow-tests.sh:97-101` -- if `gh-aw-metadata` is found, the output is just "FAIL: gh-aw-metadata still present" with no context about where it was found.
- `skill-structure-tests.sh:35-39` -- frontmatter check uses `head -1 | grep -q "^---"` but on failure says only "FAIL: review-X/SKILL.md missing frontmatter" without showing what the first line actually is.
- No negative test cases in shell scripts (no tests that verify the scripts correctly fail on bad input).
- No test for the `fail()` function itself or the exit code behavior (`tests/workflow-tests.sh:198-200`).
- Markdown tests have no executable assertions -- all verification is human judgment.

---

### Coverage Strategy (3/10)

**Evidence:**
- No `pytest.ini`, `jest.config`, `vitest.config`, `.nycrc`, `pyproject.toml`, `tox.ini`, `Makefile`, or any coverage configuration found anywhere in the repository.
- No `package.json` or `requirements.txt` with test/coverage dependencies.
- `.github/workflows/pr-checks.yml` -- 4 CI jobs but no coverage collection or reporting step.
- `engine-config.py` -- 367 lines of Python with zero unit tests. Only validated by CI running it with `--engine claude|copilot|codex` and checking output keys.

**What is covered (automated):**
- Skill directory structure: 13/13 skills checked for directory, SKILL.md, frontmatter
- Checklist existence: 10/10 domain skills checked for `references/checklist.md`
- Report path convention: 10/10 domain skills checked for correct `docs/<domain>-review.md` reference in SKILL.md
- Engine config outputs: 3 engines x 5 output keys = 15 output validations
- Workflow YAML: file existence, clean headers, multi-engine support, triggers, prompt reference
- YAML syntax: `yaml.safe_load()` validation of fitness-review.yml
- Python syntax: `ast.parse()` validation of engine-config.py

**What is NOT covered (no tests at all):**
- `engine-config.py` -- `write_outputs()` function logic (heredoc threshold, GITHUB_OUTPUT file writing, key sorting): `engine-config.py:315-351`
- `engine-config.py` -- `_domains()` deduplication and sorting logic: `engine-config.py:135-136`
- `engine-config.py` -- CLI command string assembly (CLAUDE_AGENT_CLI, COPILOT_AGENT_CLI, etc.): `engine-config.py:157-228`
- `engine-config.py` -- Domain allowlist completeness and correctness: `engine-config.py:89-132`
- Skill behavior: no automated test verifies that any skill produces correct output when invoked
- Report format: no test validates report structure (required sections, score table format, action item format)
- Trigger behavior: no automated test verifies skills activate on expected phrases
- Error paths: no test for what happens when engine-config.py receives an invalid engine name (argparse handles it, but this is not tested)

**Critical paths without dedicated test coverage:**
- `engine-config.py` handles secrets (API key names, secret env vars): `engine-config.py:243-244,268-269,292-293` -- no test validates these are correct strings
- `engine-config.py` permission model (`bypassPermissions`, `--allow-all-tools`): `engine-config.py:163,175` -- no test validates these security-critical strings
- YAML workflow correctness: only validated by `yaml.safe_load()` (syntax) and pattern greps, not by schema validation

**Strengths:**
- The 99 automated assertions do cover the structural contract comprehensively -- if a skill directory is missing or a SKILL.md lacks frontmatter, CI catches it.
- `pr-checks.yml:30` validates engine-config.py Python syntax so broken Python cannot merge.
- `pr-checks.yml:45-46` validates workflow YAML syntax.

**Gaps:**
- No coverage tool is configured.
- No coverage thresholds in CI.
- No boundary value testing (empty inputs, missing files, malformed YAML).
- No regression tests linked to bug fixes.
- The 367-line `engine-config.py` is the most complex executable in the repo and has zero unit tests for its logic (only integration-style output validation).

---

### Performance Testing (1/10)

**Evidence:**
- Grep for k6, JMeter, Gatling, Locust, Artillery, benchmark: zero matches in any executable or configuration file. Matches appear only in the skill definitions (review-testing and review-reliability checklists that describe what to look for in other codebases).
- No performance requirements documented for the shell test suite execution time, engine-config.py execution time, or CI pipeline total duration.
- No baseline measurements for workflow execution time.
- `.github/workflows/fitness-review.yml:983` -- detection job has `timeout-minutes: 10` but this is a resource limit, not a performance test.
- No `timeout-minutes` on any job in `pr-checks.yml`.

**Strengths:**
- N/A -- performance testing does not meaningfully apply to a documentation/skills project with sub-second test execution.

**Gaps:**
- No benchmarks for `engine-config.py` output generation (likely sub-millisecond, but not measured).
- No CI pipeline duration targets -- no way to detect if a change makes CI slower.
- No `timeout-minutes` on pr-checks.yml jobs, so hung tests could block the pipeline indefinitely.
- No documented expectations for fitness-review workflow execution time per engine.

**Mitigating context:** This is a meta-project with no runtime services and fast-executing shell scripts. Performance testing is genuinely low priority. The score reflects absence per the checklist, not that performance testing is critically needed here.

---

### Debugging Support (4/10)

**Evidence:**

Test failure diagnostics:
- `workflow-tests.sh:11` -- `fail()` function: `echo "  FAIL: $1"; if [ -n "${2:-}" ]; then echo "        got: $2"; fi` -- supports optional "got:" output
- `workflow-tests.sh:76-77` -- Only usage of "got:" diagnostic: `actual_id=$(echo "$ENGINE_OUTPUT" | grep "^engine_id=" | head -1); fail "..." "${actual_id:-<no engine_id line found>}"` -- captures what was actually found
- `skill-structure-tests.sh:10` -- Same `fail()` function but never invoked with the second argument in any assertion
- `skill-structure-tests.sh:35-39` -- Frontmatter check failure shows only "FAIL: review-X/SKILL.md missing frontmatter" -- does not show what the first line actually was
- `workflow-tests.sh:97-101` -- Pattern match failures (e.g., "gh-aw-metadata still present") do not show what was matched or where

Reproduction support:
- `tests/functional-tests.md:6-12` -- Test protocol provides 5-step reproduction guide: clone repo, run skill, verify structure, verify accuracy, verify evidence
- `README.md:199-257` -- Documents how to run each test category with example commands
- `.github/pull_request_template.md:14` -- PR checklist reminds to run workflow-tests.sh locally

Error context in engine-config.py:
- `engine-config.py:353-363` -- `main()` uses argparse with `choices` parameter, producing clear error messages for invalid engine names
- No try/except blocks in engine-config.py -- errors propagate with full stack traces

**Strengths:**
- `fail()` helper function exists and supports diagnostic output via optional second parameter.
- Functional test documentation provides clear reproduction steps.
- Shell tests can be run individually by name (standard bash execution -- `bash tests/workflow-tests.sh`).
- Pass/fail summary at end of each test script: `workflow-tests.sh:196-200`, `skill-structure-tests.sh:75-79`.
- Non-zero exit code on any failure (`exit 1`) makes CI integration reliable.

**Gaps:**
- **Expected-vs-actual output is rare:** Only 1 of 99 assertions (`workflow-tests.sh:76-77`) captures "got:" output. The remaining 98 assertions show only the failure description.
- No test fixtures or factories -- tests operate directly on the working directory.
- No structured logging in any executable (engine-config.py uses only `sys.stdout.write`).
- No correlation IDs or tracing (expected -- no runtime services in this repo).
- No invariant assertions or contracts in engine-config.py (e.g., no assertion that all ENGINES entries have the same set of keys).
- When `grep -q` fails in test scripts, there is no way to tell from the output what the file actually contained.

---

### CI Integration (7/10)

**Evidence:**
- `.github/workflows/pr-checks.yml:8-12` -- Triggers on `pull_request` to main and `push` to main
- `.github/workflows/pr-checks.yml:17-46` -- `workflow-validation` job: Python syntax check, engine-config output validation, YAML syntax check
- `.github/workflows/pr-checks.yml:48-60` -- `workflow-tests` job: runs `tests/workflow-tests.sh`
- `.github/workflows/pr-checks.yml:62-69` -- `skill-structure` job: runs `tests/skill-structure-tests.sh`
- `.github/workflows/pr-checks.yml:71-97` -- `markdown-links` job: verifies referenced files exist
- All 4 jobs run in parallel (no `needs:` dependencies between them).
- `.github/workflows/fitness-review.yml:10-11` -- Weekly schedule (`cron: "14 9 * * 0"`) + `workflow_dispatch` for fitness review.

**Strengths:**
- **Tests run on every PR and push to main** -- `.github/workflows/pr-checks.yml:8-12`. This is the foundational CI integration requirement.
- **4 parallel jobs** provide fast feedback -- workflow-validation, workflow-tests, skill-structure, and markdown-links all run concurrently.
- **Tests block merge on failure** -- PR checks are configured as required (per `.github/workflows/pr-checks.yml`). The `set -euo pipefail` in shell scripts and `exit 1` on failure ensure non-zero exit codes propagate.
- Shell test suite runs in under 5 seconds (observed locally), well under the 5-minute fast-feedback target.
- GitHub Actions SHA-pinned for all actions (`actions/checkout@de0fac...`, `actions/setup-python@a309ff...`) -- reliable, reproducible CI.

**Gaps:**
- **Documented tests not run in CI:** 132+ trigger scenarios and 32 functional scenarios in markdown are never executed by any CI job.
- **No test result reporting:** Shell scripts output plain text (`PASS`/`FAIL`). No JUnit XML, no TAP format, no GitHub Actions test summary annotations. Failures require reading raw logs.
- **No timeout-minutes on pr-checks.yml jobs:** If a test hangs (e.g., engine-config.py enters an infinite loop), the job would run until the GitHub Actions default timeout (6 hours).
- **No flaky test tracking or quarantine:** No mechanism to detect or track intermittent failures. The deterministic nature of file-existence tests makes this less risky, but there is no framework for future non-deterministic tests.
- **No test caching:** CI installs PyYAML (`pip install -q pyyaml`) on every run (`pr-checks.yml:46`). Minor optimization opportunity.
- **No affected-test detection:** All 4 jobs run on every PR regardless of which files changed. Acceptable for a small repo but not architected for scale.

---

## Top 5 Action Items (by impact)

1. **[HIGH] Add expected-vs-actual diagnostic output to all shell test assertions** -- `tests/workflow-tests.sh:11`, `tests/skill-structure-tests.sh:10`
   The `fail()` function supports a second argument for "got:" output, but only 1 of 99 assertions uses it (`workflow-tests.sh:76-77`). When a `grep -q` assertion fails, developers must manually inspect the file to understand what went wrong. Add the actual value (or relevant file content) to every `fail()` call. Severity: HIGH because poor failure diagnostics slow down debugging and increase time-to-fix.

2. **[HIGH] Add unit tests for engine-config.py logic** -- `.github/scripts/engine-config.py:315-367`
   The 367-line Python script is the most complex executable in the repo and handles security-critical configuration (API key names, permission models, CLI commands). Currently only validated by running it with 3 known-good inputs. Add pytest tests for: `write_outputs()` with heredoc threshold edge cases, `_domains()` deduplication, CLI command string assembly, invalid engine name handling, and GITHUB_OUTPUT file writing. Severity: HIGH because this script generates security-sensitive CI configuration.

3. **[HIGH] Add timeout-minutes to all pr-checks.yml jobs** -- `.github/workflows/pr-checks.yml:17-97`
   None of the 4 CI jobs have explicit timeout limits. A hung process would block the pipeline until GitHub's 6-hour default. Add `timeout-minutes: 5` to each job. Severity: HIGH because this is a reliability gap in the CI pipeline.

4. **[MEDIUM] Convert trigger tests to an executable script** -- `tests/trigger-tests.md`
   The 132+ trigger scenarios are well-structured and could be converted to a script that validates skill activation. Even a subset (1 positive + 1 negative phrase per skill = 26 checks) would provide regression detection for trigger behavior. This is the highest-impact gap: a skill's trigger could break without CI detecting it. Severity: MEDIUM because it requires `claude` CLI availability in CI which may have cost/infrastructure constraints.

5. **[MEDIUM] Add machine-parseable test output (TAP or JUnit)** -- `tests/workflow-tests.sh`, `tests/skill-structure-tests.sh`
   Shell test output is plain text with custom `PASS`/`FAIL` formatting. Converting to TAP format (minimal change: add `1..N` header, prefix with `ok`/`not ok`) would enable GitHub Actions test summary annotations and third-party test result aggregation. Severity: MEDIUM because current plain-text output works but does not integrate with CI test reporting features.

---

## Checklist Reference

See review-testing/references/checklist.md for the full testing checklist
derived from software testing, quality assurance, performance testing,
and debugging fundamentals.
