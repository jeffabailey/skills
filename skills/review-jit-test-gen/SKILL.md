---
name: review-jit-test-gen
description: Generates just-in-time catching tests for changed code. Analyzes pending changes to find uncovered paths and writes focused tests that catch regressions at the moment of change. Use when the user says "generate tests", "jit tests", "test generation", "write tests for changes", or wants tests for recently modified code.
---

# JIT Test Generation

Generate focused tests for the code being changed right now, and prove each one would catch a regression in that change.

The JIT approach: write tests at the moment of change, when context is freshest and the risk of regression is highest. A test that passes on the change and also passes on the broken version catches nothing, so the core of this skill is Step 6: run the new tests against a broken version and show that at least one fails.

Background: `references/wisdom.md` (from [What Is Just-in-Time Catching Test Generation?](https://jeffbailey.us/blog/2026/02/14/what-is-just-in-time-catching-test-generation/)) explains catching versus hardening tests, mutants, and the "dodgy diff". Read its first two sections if the terms are new.

## Keep or Throw Away

`wisdom.md` describes catching tests as disposable: they are generated to fail on a buggy diff, and they never join the codebase. A user who asks for "tests for my changes" usually wants tests they can keep. This skill produces both kinds and treats them differently:

| Result of Step 6 | What it is | What to do |
|---|---|---|
| Passes on the change, fails on the parent or a mutant | Proven hardening test: it guards this change against future regressions | Keep it in the project's test tree (default) |
| Fails on the change itself | Weak catch: the change may have a bug, or the test misread the intent | Never commit it. Ask the user, in one line, "this used to do X, now it does Y; is that intended?" A "no" means the code has a bug: fix it, and the test becomes a keepable regression test. A "yes" means the test was wrong: delete it |
| Passes on both | Catches nothing for this change | Rewrite it to target a risk from Step 3, or delete it |

Why keep the proven ones: wisdom.md's "disposable" rule exists because large pipelines generate thousands of unreviewed tests per diff, and nobody can maintain them. Here a person asked for a few tests, reviews them, and each one is proven to fail on a real breakage, so it earns its maintenance cost.

Ask the user before writing when intent is unclear, for example when they say "jit tests" or "catching tests" (which suggests disposable), or when the repo has no test tree. Ask: "Keep the proven tests in the repo, or run them as throwaway catching tests and report only what they find?" In throwaway mode, write the tests to the scratch directory (see Output), or into the test tree only for the run, and remove them from the project afterwards.

## Workflow

### Step 1: Identify Changed Code

```bash
git diff --name-only HEAD          # staged and unstaged
git status --porcelain             # new untracked files too
```

If no changes exist, ask the user which files or commit range to target (for a range, the parent is the range's base instead of `HEAD`).

### Step 2: Read the Change and Its Existing Tests

For each changed source file:

1. Read the full file and the diff (`git diff HEAD -- <file>`).
2. Find existing tests. Grep for the module name, the changed function names, and the file path. Grep alone misses indirection, so also read the imports and fixtures of the test files nearest the code (loader helpers, `conftest.py`, test utilities that import by path). A test that runs a script by path (for example `bash scripts/foo.sh`) covers it too, as does a CI step that runs it.
3. Run the existing tests that touch the file against the change, and note whether they already fail on the parent (Step 6 does this). If they already catch the change, say so and generate only the gaps.

### Step 3: List Plausible Regressions First

Before writing any test, write down 3-5 concrete ways this change could be wrong or could later be broken. These are the mutants your tests must kill. Draw them from the diff itself:

- Reverting the change (the "dodgy diff": the parent is the first mutant)
- An off-by-one or flipped comparison in a changed condition
- A changed branch taken for the wrong inputs: boundary values, empty, null, zero, negative, fractional, unicode, paths with spaces
- An error path that now swallows or misreports a failure
- A side effect that runs twice, runs in the wrong place, or is not idempotent on a rerun
- A second caller or entry point that bypasses the changed code

Each test you write in Step 5 should name the regression it targets. Include this list in the report: it is the reader's quickest way to judge whether the tests cover the right risks.

### Step 4: Detect the Runner and Harness

Find out how this project really runs tests before writing any. Check, in this order, and stop when you have a command that runs the existing tests green:

1. CI config: `.github/workflows/*.yml`, `.gitlab-ci.yml`, `.circleci/config.yml`, `Jenkinsfile`. The command CI runs is the ground truth, including wrappers like `uv run`, `poetry run`, `npx`.
2. Project manifests: `pyproject.toml` (`[tool.pytest.ini_options]`, `[tool.uv]`, `uv.lock`), `package.json` `scripts.test`, `Makefile` / `justfile` test targets, `go.mod`, `Cargo.toml`, `tox.ini`, `noxfile.py`.
3. Existing test files: their framework and helpers. For shell code, look for `tests/*.sh` sourcing a shared harness (such as a `lib.sh` with `pass`/`fail`/`summarize`), `*.bats` files (bats-core), or `shunit2`.

Run the existing suite once with the detected command to confirm it works before adding anything. If the system interpreter lacks the framework (for example no `pytest` on the system `python3`), use the project's wrapper rather than installing packages globally.

### Step 5: Write the Tests

1. **Match conventions**: framework, file location, naming, import style (including loader indirection found in Step 2), and harness.
2. **Test behavior, not implementation**: assert on outputs, exit codes, and side effects.
3. **One behavior per test**: parametrize over cases (`pytest.mark.parametrize`, table-driven tests) instead of copying a test per input.
4. **Name the regression**: the test name or a one-line comment says which Step 3 risk it targets.
5. **Realistic data**: domain values, not "foo"/"bar".
6. **Isolate side effects**: scripts and functions that write files, touch `$HOME`, edit dotfiles, install, symlink, or call the network must run against fixtures, never against the user's real environment:
   - Create a temp dir (`mktemp -d`, `tmp_path`, `t.TempDir()`) and remove it in a `trap ... EXIT` or fixture teardown.
   - Point `HOME` (and `XDG_CONFIG_HOME`, `XDG_DATA_HOME` if used) at the temp dir for the run, and pass explicit target paths when the script accepts them.
   - Never run a no-argument "install to default location" mode outside a temp `HOME`.
   - Replace network calls and external services with stubs (a fake binary first on `PATH`, a mock, a local fixture).
7. **Rerun safety**: if the code mutates state, run it twice in the test and assert the second run leaves the same result. Rerun bugs are common and cheap to catch.

### Step 6: Prove the Tests Catch (Required)

A test only counts if it fails on a broken version. Do this for every new test file before reporting:

1. Run the new tests on the change. They must pass (or see the "fails on the change" row in Keep or Throw Away).
2. Run them on the parent: the changed source files as they are at `HEAD` (or the range base). Leave the new test files in place. At least one new test must fail.
3. If the change is new code with no parent (a new file or function), or the parent run cannot work, apply a hand-made mutant instead: one of the Step 3 regressions as a small patch to the changed lines. At least one new test must fail on it. Prefer two or more mutants when the change has several branches.
4. Restore the working tree and confirm `git diff` shows only the user's change plus your new tests.

The bundled script does steps 1-4 safely, restoring the files even on Ctrl-C:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/prove-catch.sh" --file path/to/changed.py -- uv run pytest tests/unit/test_new.py -q
bash "${CLAUDE_SKILL_DIR}/scripts/prove-catch.sh" --mutant /tmp/off-by-one.patch -- bash tests/new-tests.sh
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; if your agent does not expand it, use the directory containing this `SKILL.md`. Pass only source files to `--file`, never the new tests. Do not use `git stash` for this: it also stashes unrelated work and can conflict on pop.

If no test fails on any broken version, the tests catch nothing: go back to Step 3 and target a different regression. If you cannot make one fail, say so plainly in the report instead of claiming coverage.

Then run the full existing suite with the new tests added, to confirm no collateral breakage.

### Step 7: Wire Into CI

Check whether CI picks up the new test file automatically (pytest discovery, `go test ./...`) or lists test files by name (for example, one workflow step per `tests/*.sh`). If CI lists them by name, the new file never runs in CI until it is added: add the step, or, if CI config is out of scope for the user, name the exact line to add in the report.

## Output

Print the report in the conversation. If the user wants a file, or the report is long, also save it outside the repo so it never ends up in a commit: `${TMPDIR:-/tmp}/jit-tests/<repo-name>-<YYYYMMDD-HHMM>/report.md`, and tell the user the path. Throwaway catching tests go in the same directory. Kept tests go in the project's test tree.

For each changed file:

```markdown
## Tests for `path/to/changed-file.ext`

**Change:** [one line on what changed and why]
**Existing coverage:** [tests that touch this code, or "none"; whether they already fail on the parent]
**Plausible regressions:** [the Step 3 list, numbered]
**Runner:** `[exact command]` (from [CI file / pyproject / Makefile / ...])
**New tests:** [count] in `path/to/test-file.ext` (kept | throwaway)

**Catch proof:**
| Version | Passed | Failed |
|---|---|---|
| Change | N | 0 |
| Parent (`HEAD`) | N | M |
| Mutant: [regression #k, one line] | N | M |

**Full suite:** [N passed, 0 failed]
**CI:** [picked up automatically | added to <file> | needs this line in <file>: ...]

### Test: [descriptive name]
**Catches:** regression #k ([one line])
```

End with any weak catches (tests that failed on the change) as "used to X, now Y; intended?" questions, and any real bugs found while probing, even outside the diff.

## What Not to Generate

- Tests for trivial getters and setters
- Tests that duplicate existing coverage (check Step 2 first)
- Tests tied to implementation details (private names, call order, exact log wording) unless that is the behavior that changed
- Tests for generated or vendored code
- Tests for pure configuration data. A script or CI step that consumes config is code and can be tested
