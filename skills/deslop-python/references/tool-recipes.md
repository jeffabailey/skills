# Tool recipes and pitfalls

## Contents
- pytest and pytest-cov
- mutmut
- Static tools (ruff, ty, vulture, radon, deptry, jscpd, import-linter)
- pytest-benchmark
- Scoping a large project
- Pitfalls

## pytest and pytest-cov

- Test identity is the node id: `tests/test_core.py::test_name`, `tests/test_core.py::TestCart::test_add`, `...::test_parse[case-1]`. `kill_matrix.py --remove` takes node ids or bare names.
- `--junitxml=<file>` gives per-test time (setup + call + teardown). `--durations=N --durations-min=S` splits phases; a big `setup` number points at a fixture, so fix the fixture, not each test.
- `--cov=<package> --cov-context=test` records the test that executed each line. `--cov-report=` (empty) skips the terminal table. Set `COVERAGE_FILE` to keep the data file in `.deslop-python/` instead of `.coverage` in the root.
- `--cov-branch` adds branch arcs to the data; use `coverage report --show-missing` with it when line coverage is identical but tests take different arms of an `if`.
- Find flaky tests (don't recommend deleting flaky tests as "redundant"; fix or flag them): rerun the suspicious test a few times: `for i in 1 2 3 4 5; do uv run pytest -q --ignore=mutants <node>; done`.
- Skips and xfails: `pytest -rsxX` lists them. An `XPASS` means an `xfail` now passes: the mark is stale.

## mutmut

- mutmut 3 needs no config for a `src/` or `lib/` layout or a package directory named after the project; otherwise it needs `[tool.mutmut] source_paths = [...]` in `pyproject.toml`. Adding that is a project change: tell the user, or put it in only for the run and restore the file. `paths_to_mutate` and `tests_dir` are old names (it warns).
- It copies the project into `mutants/`, records which tests execute each function (`mutants/mutmut-stats.json`), and runs only those tests for each mutant, with `pytest -x`.
- Results: `mutmut results` (one line per mutant that is not killed), `mutmut show <key>` (the diff), `mutants/**/<file>.meta` (`exit_code_by_key`; 1 or 3 killed, 0 survived, 33 no tests, 36 timeout, 37 caught by type check). `mutants_compare.py snapshot` copies these.
- `--max-children N` sets parallelism. Memory, not CPU, is usually the limit.
- `mutmut run <glob>` runs only matching mutant names, for example `"cartcalc.core.x_parse_qty*"`.
- Mark code to leave alone with `# pragma: no mutate` on the line; respect existing ones.
- Config options that matter here: `pytest_add_cli_args` (extra pytest flags for every run; pass the same flags to `kill_matrix.py --pytest-arg`), `pytest_add_cli_args_test_selection` (which tests to run), `do_not_mutate` (globs to skip), `also_copy` (extra files the tests need in `mutants/`).
- mutmut needs `fork`; on Windows run it under WSL.
- **"Expected keys (e.g.): [...]" / "failed to collect stats"** with every mutant `not checked`: the tests import the code under a different module name than its path. mutmut names mutants after the file path below `src/` (or the project root), so a package that tests import as `fitness_config` after a `sys.path.insert(0, "scripts")` gets mutant names starting `scripts.fitness_config` that no test ever triggers. Files with hyphens (`engine-config.py`) loaded with `importlib.util.spec_from_file_location` can't be matched at all. Don't restructure the user's project for the audit. In a scratch copy outside the repo (`cp -r` or `tar`), move the package under `src/` and leave a symlink at the old path (`mkdir src && mv scripts/pkg src/ && ln -s ../src/pkg scripts/pkg`), then run mutmut there. Report path-loaded scripts as "not mutation-tested" in the scope line.
- **Tests that run the code as a subprocess** (`subprocess.run([sys.executable, "scripts/tool.py", ...], cwd=tmp_path)`) crash under mutmut: the child inherits `MUTANT_UNDER_TEST`, and mutmut's trampoline then looks for its config in the child's working directory and raises `FileNotFoundError: Could not figure out where the code to mutate is`. Leave those tests out of the mutation run (`pytest_add_cli_args_test_selection = ["tests", "--ignore=tests/test_cli.py"]`), say so in the scope line, and note that code reached only through subprocesses shows as `no tests`. Code reached only that way is itself a gap worth reporting: an in-process test calling `main([...])` makes it testable.
- **`also_copy` with a single file** fails with `FileNotFoundError: mutants/<dir>/<file>` when the parent directory doesn't exist yet. `mkdir -p mutants/<dir>` after `rm -rf mutants`, or list the directory instead of the file.
- **Hypothesis makes kills random.** A property test kills a mutant only when it happens to generate the input that exposes it, so the same mutant can be killed in the baseline and survive afterwards with no test changed. Pin the seed for every mutation run with `pytest_add_cli_args = ["--hypothesis-seed=0"]` (and `kill_matrix.py --pytest-arg=--hypothesis-seed=0`). If a lost kill in `mutants_compare.py diff` belongs to a property test you didn't touch, rerun that mutant a few times (`MUTANT_UNDER_TEST=<key>` + pytest in `mutants/`) before calling it a regression.
- **Kill matrix cost**: `kill_matrix.py` reruns each killed mutant in a new pytest process, so expect roughly `killed mutants × (pytest start-up + covering tests' time) ÷ jobs`. On a 1,500-mutant project with hypothesis tests that was most of an hour before per-mutant timeouts; the script now times each rerun out at 10s + 5× its tests' baseline time. Scope with `mutmut run "<module glob>"` first when the estimate is large.
- **Equivalent mutants**: some survivors can't be killed because they don't change behavior (for example, `x <= 0` to `x < 1` for integers). Don't report those as test gaps; say "equivalent mutant" and why.

## Static tools

- **ruff**: `ruff check --no-fix --output-format concise --select <codes> .` Useful codes: `F401` unused import (but `__init__.py` re-exports are deliberate when listed in `__all__`), `F811` redefinition (a shadowed test never runs), `F841` unused variable, `ERA001` commented-out code, `ARG` unused arguments (an unused fixture parameter still runs the fixture), `B017` and `PT011` broad `pytest.raises`, `PT006`/`PT007` parametrize style, `PT018` composite asserts, `SIM`, `C901` complexity. Use `--statistics` for counts.
- **ty**: `ty check` (whole project) or `ty check <paths>`. It is pre-1.0; diagnostics change between versions, so compare before and after with the same version rather than treating the count as absolute.
- **vulture**: `vulture <src> tests --min-confidence 60`. 100% confidence is near-certain (unreachable code, unused imports); 60% includes functions and attributes found only by name, so expect false positives for framework hooks, `__all__` exports, dynamic `getattr`, and pytest fixtures used only by name. `--make-whitelist` shows the false positives the project can record; don't add a whitelist file during the audit.
- **radon**: `radon cc -s <paths>` (cyclomatic complexity per function, `-n C` for C and worse), `radon mi -s <src>` (maintainability index), `radon raw` (line counts, for the "lines removed" total).
- **deptry**: `deptry . --known-first-party <package>`. Codes: `DEP001` imported but not declared, `DEP002` declared but not imported, `DEP003` transitive import, `DEP004` dev dependency used in production code. Without `--known-first-party`, deptry can report the project's own package as `DEP003` in some layouts. Dependencies used only as CLI tools, pytest plugins, or entry-point plugins look unused to deptry; check before calling them junk.
- **jscpd**: `jscpd --min-tokens 30 --pattern "**/*.py" --ignore "**/.venv/**,**/mutants/**" --reporters json,console --output <dir> .` The JSON report (`jscpd-report.json`) lists each clone's files and line ranges. In `tests/`, clones are fixture or parametrize candidates; in source, they are refactoring candidates (report them, don't merge production code unless approved).
- **import-linter**: `lint-imports` reads `[tool.importlinter]` in `pyproject.toml` or `.importlinter`. Contract types: `forbidden`, `layers`, `independence`. Run before and after; a contract that was kept must stay kept. To try a contract without editing the project, write it to `.deslop-python/importlinter.ini` and run `lint-imports --config .deslop-python/importlinter.ini`.

## pytest-benchmark

- `--benchmark-only` runs only benchmark tests; `--benchmark-skip` skips them. Benchmark tests in the default run are slow and usually assert nothing.
- Baseline and compare: `--benchmark-autosave --benchmark-storage=file://.deslop-python/bench`, then `--benchmark-compare --benchmark-storage=file://.deslop-python/bench`. `--benchmark-compare-fail=mean:10%` fails on a 10% slowdown.

## Scoping a large project

Mutation testing cost is roughly `mutants × tests per mutant × average test time ÷ children`; `kill_matrix.py` adds about one more pass over the killed mutants. Before a full run:

1. Run once on one module (`mutmut run "pkg.module.*"`) and use `mutmut print-time-estimates` to extrapolate.
2. If it is too large, audit one package or module at a time, and say in the report which scope the mutation evidence covers.
3. Speed up the suite first if one or two tests or fixtures dominate the JUnit times; every later mutation run gets cheaper. Ask before doing that, since it is a change.
4. For per-test coverage over thousands of tests, `--cov-context=test` still needs only one run, but the data file gets large; scope `--cov` to the package being audited.

## Pitfalls

- **`mutants/` and pytest collection.** `mutants/` contains a copy of `tests/`. Pass `--ignore=mutants` to every pytest run in the project root while it exists, or pytest fails with "import file mismatch".
- **mutmut caches results.** It keeps a mutant's old result while its function's source hash is unchanged, so deleting or weakening a test does not make it retest anything. `rm -rf mutants` before every run whose results you will compare.
- **Markers and options.** Tests behind markers (`-m slow`, `-m integration`) or `addopts` filters don't run by default. Use the same selection CI uses for all tools, or tests will look dead that aren't.
- **Platform and version skips.** `skipif(sys.platform ...)` or Python-version skips only run in some environments; don't call them dead.
- **Property tests** (`hypothesis`) cover input spaces, not lines. One property test can look subsumed by line coverage while it is the only thing catching boundary bugs. Rely on the kill matrix, not coverage, for these.
- **Snapshot tests** (`syrupy`, `inline-snapshot`) assert a whole output; they look weak (one assert) but aren't.
- **Regression tests** whose name, docstring, or comment cites an issue, a CVE, or an incident stay unless the user says otherwise: mark them High risk even with zero lost kills, because the mutation catalog may not reproduce the original bug.
- **Doctests** (`--doctest-modules`) are part of the documentation; never recommend removing one for redundancy.
- **Same lines, different outcome**: two tests that execute the same lines but check `True` vs `False`, raises vs returns, or empty vs non-empty are a parameterization candidate at most, never duplicates.
- **Shadowed tests** hide in plain sight: the suite passes, the count looks right, and one test body never runs. ruff F811 finds them.
