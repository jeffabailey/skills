---
name: deslop-python
description: "Audits a Python project for junk tests, dead code, and unused dependencies using evidence from pytest (per-test timings), pytest-cov (per-test coverage contexts), mutmut (which mutations the suite kills, and which kills a test removal would lose), plus ruff, ty, vulture, radon, deptry, jscpd, and import-linter. It installs any of these tools that are missing, writes a prioritized report (file and test, problem, evidence, recommended optimization, estimated time savings, risk), changes no test or source file until the user approves, then applies only the approved items and verifies them against the original test results and mutation results. Use when the user says /deslop-python, wants to clean up, slim down, dedupe, or speed up a pytest suite, asks which Python tests are redundant, weak, slow, shadowed, or safe to delete, wants to parameterize tests or consolidate fixtures, asks for a mutation-testing or coverage-overlap review of a Python project, or wants dead Python code or unused dependencies found and removed, even if they don't name the tools."
user-invocable: true
argument-hint: "[path] [--package NAME] [--paths GLOB] - project to audit; defaults to the current Python project"
metadata:
  version: "1.0.0"
---

# deslop-python

Slop in a test suite is tests that cost time and attention but don't protect anything the rest of the suite doesn't already protect. Deciding that a test is slop takes evidence, not a vibe: two tests can look the same and check different edge cases, and a test can execute every line and still miss a real bug. The tools give the evidence:

| Tool | Question it answers |
|---|---|
| `pytest` (+ `--junitxml`, `--durations`) | How long does each test take, and how much of that is fixture setup? |
| `pytest-cov` (`--cov-context=test`) | Which production lines does each test execute? Which lines does no test execute? |
| `mutmut` (+ `scripts/kill_matrix.py`) | Which small injected bugs does the suite kill, and which kills go away if we drop a test? |
| `ruff` | Unused imports and variables, shadowed test functions (F811), blind `pytest.raises(Exception)`, commented-out code |
| `ty` | Type errors; a baseline so refactors don't add new ones |
| `vulture` | Functions, classes, and variables nothing references |
| `radon` | Complexity: branching logic inside tests, complex production code that hides surviving mutants |
| `deptry` | Declared dependencies nothing imports, imports nothing declares |
| `jscpd` | Copy-pasted blocks in tests (fixture and parameterization candidates) and in source |
| `import-linter` | The project's architecture contracts still hold after the changes |
| `pytest-benchmark` | Benchmarks that run in the normal suite; before/after speed of benchmarked code |

Mutation results are the strongest evidence. Coverage overlap and the static tools only nominate candidates: a test is redundant when removing it loses **zero mutation kills** and its assertions are already made elsewhere, not just when its lines are executed elsewhere.

## The mission

Perform a comprehensive Python test-suite optimization audit. Identify:

1. Duplicate and semantically equivalent tests.
2. Tests with overlapping coverage.
3. Excessively verbose tests that could be parameterized.
4. Repeated setup, teardown, and fixture construction.
5. Weak assertions and tests that don't verify meaningful outcomes.
6. Tests that validate implementation details instead of contracts.
7. Slow tests and unnecessary integration-test overhead.
8. Tests that provide no independent regression protection.
9. Opportunities to consolidate tests without losing edge-case coverage.

Also flag **junk production code**: functions nothing calls and no test executes, unused imports, commented-out code, copy-pasted blocks, and dependencies nothing imports.

Produce a prioritized report, then **stop**. Don't edit, delete, or move any test or source file during the audit. Making changes waits for the user's approval of specific report items, and every change is verified against the original suite and the original mutation results.

The approval gate exists because "redundant" is a judgment the user owns: a test may document a contract, guard a past incident, or be required by a reviewer. If the request already says "just delete the junk", still deliver the report first and ask which items to apply; it costs one round-trip and prevents silently losing a guard nobody knew mattered.

## Working files

Keep every artifact under `.deslop-python/` in the project root (call it `$W`). mutmut also writes `mutants/` in the project root. Hide both from git locally, without editing the project's `.gitignore`:

```bash
mkdir -p .deslop-python
for p in .deslop-python/ mutants/; do grep -qxF "$p" .git/info/exclude 2>/dev/null || echo "$p" >> .git/info/exclude; done
```

Use `${CLAUDE_SKILL_DIR}` for this skill's directory; if your agent does not expand it, use the directory holding this SKILL.md. Run the scripts that import `coverage` or run pytest (`coverage_overlap.py`, `kill_matrix.py`) with the project's interpreter, `uv run python ...`.

## Phase 0: Preflight and install

1. Find the project: the path the user gave, else the nearest `pyproject.toml` (or `setup.cfg`/`setup.py`). Note the layout (`src/<pkg>` or `<pkg>/`), the import package name, and where the tests are.
2. Check the tree: `git status --porcelain`. If there are uncommitted changes, say so; the verification later compares against this starting point, so record `git rev-parse HEAD` and keep a copy of the diff if the user wants to continue anyway.
3. Check each tool and install only what is missing. These go into the project's dev dependencies, so the install changes `pyproject.toml` and `uv.lock`; tell the user that before you run it, and list it in the report as a setup change they can keep or revert:

   ```bash
   missing=""
   for t in ruff ty vulture radon deptry pytest pytest-cov mutmut pytest-benchmark import-linter; do
     uv pip show "$t" >/dev/null 2>&1 || missing="$missing $t"
   done
   [ -n "$missing" ] && uv add --dev $missing
   jscpd --version >/dev/null 2>&1 || npm install -g jscpd
   ```

   If the project doesn't use uv (no `uv.lock`, managed by Poetry, Hatch, or plain pip), don't convert it: ask, and meanwhile run the standalone analyzers through `uvx` (`uvx ruff`, `uvx vulture`, `uvx radon`, `uvx deptry`, `uvx ty`) and install the pytest plugins into the project's own environment its usual way. If `npm install -g` is not allowed, `npx -y jscpd` works. If an install fails, report it and continue with the evidence the remaining tools give; say in the report which evidence is missing.
4. Run the suite once: `uv run pytest -q` with the project's usual flags (markers, `-n auto` if it uses xdist). If it fails, stop and report: an audit on a red suite has no baseline to protect.

## Phase 1: Collect the baseline evidence

Read `references/tool-recipes.md` for exact flags, how to scope large projects, and known pitfalls (mutmut caching, `mutants/` in test collection, deptry first-party detection, vulture false positives). Pass `--ignore=mutants` to every pytest run once `mutants/` exists: it holds a copy of the tests, and pytest otherwise collects both copies and fails with "import file mismatch".

1. **Timings.** Rank tests, then split the slow ones into setup, call, and teardown, because in Python the time often sits in a fixture, not the test:

   ```bash
   uv run pytest -q --ignore=mutants --junitxml=.deslop-python/junit.xml --durations=25 --durations-min=0.05
   python3 "${CLAUDE_SKILL_DIR}/scripts/pytest_timings.py" .deslop-python/junit.xml --top 25
   ```

2. **Per-test coverage overlap.** One run with test contexts records which test executes each line. The script reports identical-coverage groups, strict subsets, unique lines per test, and production lines no test executes:

   ```bash
   COVERAGE_FILE=.deslop-python/coverage uv run pytest -q --ignore=mutants \
     --cov=<package> --cov-context=test --cov-branch --cov-report=
   uv run python "${CLAUDE_SKILL_DIR}/scripts/coverage_overlap.py" .deslop-python/coverage
   ```

3. **Static evidence.** Run all of these and keep their output in `$W`; none of them changes a file with these flags:

   ```bash
   uv run ruff check --no-fix --output-format concise \
     --select F401,F811,F841,ERA001,ARG,B017,PT,SIM,C901 . > .deslop-python/ruff.txt
   uv run ty check > .deslop-python/ty.txt 2>&1
   uv run vulture <src-dir> tests --min-confidence 60 > .deslop-python/vulture.txt
   uv run radon cc -s <src-dir> tests > .deslop-python/radon-cc.txt   # a test above A (1) has branches
   uv run radon mi -s <src-dir> > .deslop-python/radon-mi.txt
   uv run deptry . --known-first-party <package> > .deslop-python/deptry.txt 2>&1
   jscpd --min-tokens 30 --reporters json,console --output .deslop-python/jscpd \
     --ignore "**/.venv/**,**/mutants/**,**/.deslop-python/**" --pattern "**/*.py" . > .deslop-python/jscpd.txt
   uv run lint-imports > .deslop-python/lint-imports.txt 2>&1   # only if the project has contracts
   ```

   The `--select` list overrides the project's ruff config for this run only; it is evidence, not a lint gate. `--no-fix` matters because a project config with `fix = true` would otherwise edit files during the audit. If the project has no import-linter contracts, don't add config to it; note it as a gap only if the code has an obvious layering rule (for example, core modules importing the CLI or web layer).

4. **Mutation baseline.** Estimate cost first: mutants (`uv run mutmut run` prints the count; `mutmut print-time-estimates` after a first run) × baseline suite time ÷ `--max-children`. If that exceeds ~20 minutes, tell the user the estimate and scope it (see the recipes) before you run it.

   ```bash
   rm -rf mutants        # mutmut reuses old results while a function's source is unchanged
   uv run mutmut run --max-children 4 > .deslop-python/mutmut-run.log 2>&1
   uv run mutmut results > .deslop-python/mutmut-results.txt
   python3 "${CLAUDE_SKILL_DIR}/scripts/mutants_compare.py" snapshot .deslop-python/baseline
   uv run python "${CLAUDE_SKILL_DIR}/scripts/kill_matrix.py" --cache .deslop-python/kill_matrix.json
   ```

   mutmut runs pytest with `-x`, so its own results credit a killed mutant to at most one test. `kill_matrix.py` reruns each killed mutant against the tests that cover its function without `-x` and records every test that fails. It reports kills and unique kills per test, tests with identical kill sets, tests whose kills are a strict subset of another's, and tests that kill nothing. That is the main evidence for categories 1, 2, and 8. `mutmut show <mutant>` prints the diff of any mutant it names. Redirect `mutmut run` to a log: its progress line rewrites itself thousands of times.

   Keep `.deslop-python/baseline/` untouched; it is the yardstick for every later comparison.

5. **Benchmarks.** If any test takes the `benchmark` fixture, save a baseline: `uv run pytest --ignore=mutants --benchmark-only --benchmark-autosave --benchmark-storage=file://.deslop-python/bench`. Benchmarks that also run in the normal suite are slow-test candidates (category 7).

## Phase 2: Read the tests and classify

Tools nominate; reading confirms. For every nominated test, open the test and the code under test and decide which of the nine mission categories apply (or the junk-code category). Look at what each test *asserts*, not only what it executes:

- Same coverage + same assertions + same inputs → duplicate (category 1).
- Same coverage, different inputs or outcomes (`True` vs `False`, raises vs returns, empty vs non-empty) → **not** a duplicate; at most a parameterization candidate (3, 9).
- A group of tests that differ only by input and expected value, or a `for` loop of asserts inside one test → `@pytest.mark.parametrize` (3). A loop hides which case failed; parametrize reports each one.
- **Shadowed tests** (ruff F811): a second `def test_x` in the same module replaces the first, so the first never runs. Recommend renaming one so both run, never deleting either, and check what the hidden one asserts: it may hold a kill the suite lost without anyone noticing. Similarly, functions in test files that pytest won't collect (no `test_` prefix, a `Test` class with `__init__`) never run; vulture often lists them.
- `assert x`, `assert x is not None`, `isinstance` only, `assert mock.called`, `pytest.raises(Exception)` without `match=`, a call with no assertion, or `print` instead of assert → weak (5). The fix is usually to strengthen it to the exact value or exception type, not delete it.
- Asserts on `_private` attributes, `__dict__`, call order of internal helpers, `mock.patch` of the unit's own private methods with `assert_called_once_with` → implementation detail (6). Recommend asserting the public contract instead.
- `time.sleep`, real network, the real filesystem where `tmp_path` works, `subprocess` launching the CLI where calling `main()` works, a function-scoped fixture that builds something expensive and immutable, an `autouse` fixture doing heavy work for every test → slow or overhead (7). `--durations` shows whether the time is in setup.
- The same setup lines in many tests (jscpd clones in `tests/`, repeated `setUp` bodies) → fixture (4); recommend a fixture in the module or `conftest.py`, not a new dependency.
- Branching inside a test (radon complexity above 1 in `tests/`) usually means one test checks several cases → parameterize, or it means conditional asserts that sometimes check nothing.
- Code nothing calls (vulture, uncovered lines, mutmut `no tests` mutants, no hits from `grep -rn`) that is not public API → junk code. Check `__all__`, entry points in `pyproject.toml`, framework hooks (pytest fixtures and plugins, Django and Flask registrations, Click commands), and dynamic `getattr` dispatch before you call it dead. Names a published package exports may be used downstream; mark those High risk.
- deptry DEP002 (declared, never imported) → junk dependency. Check plugins loaded by entry point, CLI tools run in scripts or CI, and optional extras first.

### Prove "no independent regression protection" (category 8)

Check the whole set of tests you plan to recommend for removal against the kill matrix. This needs no new mutation run:

```bash
uv run python "${CLAUDE_SKILL_DIR}/scripts/kill_matrix.py" --cache .deslop-python/kill_matrix.json \
  --remove test_cart_total_again test_discount_runs tests/test_integration.py::test_full_checkout_flow_with_retry
```

It lists every mutant that only the removed tests kill, and exits 1 if there is one. Zero lost kills is the evidence that the set is safe to remove. If kills are lost, the output names the mutant and the test that alone kills it: move that test to "keep" or "merge into a parameterized test" and check again. Surviving mutants in the baseline are gaps the suite already has; report the important ones as gaps (a test to add), separate from removals.

An identical kill set is not proof of a duplicate. mutmut makes only a few mutants per function, so tests that check different things (`rejects_zero` and `accepts_42`) can kill the same few mutants. Read the assertions before you call two tests duplicates.

## Phase 3: The report

Write `.deslop-python/report.md` and show its contents in the chat. Rank by value ÷ risk: low-risk items with real savings first. Use this structure:

```markdown
# Python test-suite optimization audit: <project>

Baseline: <N> tests, <S>s summed test time, <W>s session time; mutants <killed>/<total> killed
(<survived> survived, <no tests> no tests, <timeout> timeout); <C>% line coverage. Commit <sha>.
Scope: <packages/paths>; evidence not collected: <none | which tool and why>.
Setup changes: <dev dependencies added to pyproject.toml/uv.lock, or none>.

## Prioritized findings

| # | File :: test | Category | Problem | Evidence | Recommended optimization | Est. time saved | Risk |
|---|---|---|---|---|---|---|---|
| 1 | tests/test_integration.py :: test_full_checkout_flow | 7 slow | sleeps 1.5s for a service that doesn't exist | junit 1.50s (50% of suite); kill matrix: 2 unique kills, so keep the test | delete the sleep | ~1.5s per run, ~65s per mutation run (43 tested mutants) | Low |

## Junk production code and dependencies
<item, evidence (vulture, uncovered lines, no-tests mutants, references, deptry), recommendation, risk>

## Gaps found (not removals)
<surviving mutants worth a new or stronger test; shadowed tests to rename; missing architecture contracts>

## Not recommended
<tests that looked redundant but hold unique kills or distinct edge cases, and why they stay>

## Totals if all items are approved
<tests removed / merged, seconds saved per run and per mutation run, lines removed, dependencies removed>
```

Fill every column. **Evidence** names the tool and the number (timing, identical-coverage group, `kill_matrix.py` result, the ruff or vulture line). **Est. time saved** comes from the JUnit times of the tests removed or shortened; also give the per-mutation-run saving (seconds saved × mutants whose covering tests include it), because a slow test is paid again for every mutant it covers. Parameterizing saves code and maintenance more than seconds; say "~0s, -N lines" rather than inventing a number. **Risk**: Low = identical assertions or zero lost kills in the kill matrix; Medium = overlap is real but the test documents an edge case or contract that should move, not vanish; High = holds unique kills or unique lines, is public API, or names an issue or incident.

Then end with one direct question: which item numbers to apply (for example "all Low", "1-4 and 7", or "none"). Don't make changes in the same turn.

## Phase 4: Apply approved items

Apply only the approved numbers, one category at a time so a failure points at one kind of change:

- **Removing duplicates:** keep the clearest name; if the one you remove had a better name, rename the keeper.
- **Parameterizing:** `@pytest.mark.parametrize` with readable `ids=` (or `pytest.param(..., id=...)`), keeping every distinct input and expected value from the tests you fold in. If the suite is `unittest`-style, use `self.subTest` instead of converting it to pytest unless the user asks.
- **Fixtures:** move repeated setup into a fixture in the module, or `conftest.py` when several modules share it. Widen fixture scope only for objects that tests don't mutate.
- **Weak assertions:** replace with the exact expected value or exception type (`pytest.raises(ValueError, match=...)`). Run the test to confirm it passes; a failure means you found a bug, so stop and report it instead of loosening the assert.
- **Shadowed tests:** rename so both run, then run them; a failure in the revived test is a finding to report, not a test to delete.
- **Implementation-detail tests:** rewrite against the public contract, or remove if the contract is already asserted elsewhere with zero lost kills.
- **Slow tests:** remove pointless sleeps, use `tmp_path` and `monkeypatch` instead of real I/O and clocks, call functions directly instead of through `subprocess`, mark benchmarks so the default run skips them the way the project already selects tests (a marker plus `-m "not benchmark"`, or `--benchmark-skip` in `addopts`).
- **Junk code and dependencies:** delete the item, then run `uv run ruff check`, `uv run ty check`, and `uv run vulture` again. Remove a dependency with `uv remove <name>`.

Don't add a new dev dependency or pytest plugin to make a change easier without asking.

## Phase 5: Verify against the original

Run all of these and put the numbers in a before/after table:

1. `uv run pytest -q --ignore=mutants` (same flags as Phase 0) passes. The test count drops only by the removed tests and rises only by revived shadowed tests or approved parametrize cases; every remaining test existed before or is an approved merge.
2. Mutation results: start fresh, rerun the same scope as the baseline, and compare:

   ```bash
   rm -rf mutants        # required: mutmut would reuse the baseline results for unchanged functions
   uv run mutmut run --max-children 4 > .deslop-python/mutmut-after.log 2>&1
   python3 "${CLAUDE_SKILL_DIR}/scripts/mutants_compare.py" snapshot .deslop-python/after
   python3 "${CLAUDE_SKILL_DIR}/scripts/mutants_compare.py" diff .deslop-python/baseline .deslop-python/after
   ```

   It must exit 0 (no lost kills). Mutants listed as "only in baseline" or functions listed as "changed" must belong to approved junk-code deletions; anything else means production code changed and is a defect to fix.
3. Coverage: rerun the Phase 1 coverage command and `coverage_overlap.py`; confirm no production line that was covered before is uncovered now, apart from deleted junk code.
4. Static: `ruff` (same `--select`), `ty check`, `vulture`, and `lint-imports` report no new findings; deptry reports no new issues.
5. Timing: rerun the JUnit command and report the summed test time and session time before and after. If there were benchmarks, `--benchmark-compare` against the saved baseline.

If any check fails, revert that item (`git checkout -- <file>` for that change only), say which item failed and why, and continue with the rest. End with the before/after table and the list of items applied, reverted, and still pending, plus a reminder of the setup changes from Phase 0 (dev dependencies added). Don't commit unless the user asks.
