# Tool recipes and pitfalls

## Contents
- cargo-nextest
- cargo-llvm-cov
- cargo-mutants
- Scoping a large project
- Pitfalls

## cargo-nextest

- Test identity is `binary-id` + test name. Unit tests in a library have binary id `<crate>`; each `tests/foo.rs` file is `<crate>::foo`. Filtersets: `binary_id(cartcalc::integration) & test(=full_checkout_flow)`.
- List tests as JSON: `cargo nextest list --message-format json` (`rust-suites.<id>.testcases`).
- JUnit timings without editing the project's `.config/nextest.toml`: `--tool-config-file "deslop-rust:$PWD/<file>"` (the path must be absolute) with a `[profile.default.junit] path = "junit.xml"` block; output lands in `target/nextest/default/junit.xml`. If the project has its own `default` profile with JUnit, reuse it.
- Find flaky tests (don't recommend deleting flaky tests as "redundant"; fix or flag them): `cargo nextest run --retries 2` and look for `FLAKY`.
- Slow-test threshold: `cargo nextest run --tool-config-file ...` with `slow-timeout = "1s"` in the profile prints `SLOW` lines.

## cargo-llvm-cov

- Whole-suite summary: `cargo llvm-cov nextest --summary-only`. Text with uncovered lines: `cargo llvm-cov nextest --text --show-missing-lines`.
- One test: `cargo llvm-cov nextest --lcov --output-path one.lcov -E 'binary_id(X) & test(=Y)'`. Profile data is cleaned between runs by default, so each run measures only that test. The instrumented build is reused, so per-test runs after the first are cheap.
- Branch coverage needs nightly: `cargo +nightly llvm-cov nextest --branch`. Use it when line coverage is identical but the tests differ by which arm of an `if`/`match` they take.
- `tests/`, `benches/`, `examples/` are excluded from the report by default. Inline `#[cfg(test)]` modules are not; `coverage_overlap.py` strips them so a test's own body doesn't count as "unique coverage".
- Doctest coverage needs nightly and `--doctests`; usually skip it and just run `cargo test --doc`.

## cargo-mutants

- `--test-tool nextest` runs each mutant under nextest. Everything after `--` goes to `cargo nextest run`, which is how to simulate removing tests: `-- -E 'not (test(=a) | test(=b))'`.
- `-- --no-fail-fast` runs every test against every mutant, so each mutant log names every test that failed. `kill_matrix.py` reads those logs; with fail-fast on, only the first failing test shows up and the matrix would be wrong.
- `-o <dir>` writes `<dir>/mutants.out/`; the directory must exist. A second run to the same dir renames the old one to `mutants.out.old`, so give baseline, simulation, and after runs separate dirs.
- Results: `caught.txt`, `missed.txt`, `timeout.txt`, `unviable.txt`, and `outcomes.json` (structured; `mutants_compare.py` reads it).
- `-f <file>` / `-e <file>` include or exclude files; `-F <regex>` / `-E <regex>` filter mutant names; `-p <pkg>` limits packages; `--in-diff <patch>` tests only mutants in changed lines (useful for verifying a junk-code deletion did not touch live code, not for test-only changes).
- `-j N` runs N mutants in parallel, each in its own copy of the tree. 4 is a sane default; memory, not CPU, is usually the limit for big workspaces.
- `--timeout` / `--timeout-multiplier`: mutants that cause infinite loops become `Timeout`, which cargo-mutants reports separately from caught and missed; `mutants_compare.py` treats a change from caught to timeout as a lost kill, since a timeout is slower and flakier evidence.
- Code the project marks `#[mutants::skip]` or excludes in `.cargo/mutants.toml` is out of scope; respect it.
- **Equivalent mutants**: some missed mutants can't be caught because they don't change behavior (for example, `>` to `>=` where the boundary values give the same result). Don't report those as test gaps; say "equivalent mutant" and why.

## Scoping a large project

Mutation testing cost is roughly `mutants × suite time ÷ jobs`. Before a full run:

1. `cargo mutants --list | wc -l` and the nextest wall time give the estimate.
2. If it is too large, audit one package or a few files at a time (`-p`, `-f`), and say in the report which scope the mutation evidence covers.
3. Speed up the suite first if one or two tests dominate the JUnit times; fixing the slowest test makes every later mutation run cheaper. Ask before doing that, since it is a change.
4. `--shard k/n` splits a run across machines or CI jobs.

## Pitfalls

- **Features.** Tests behind `#[cfg(feature = "...")]` don't run without the feature. Use the same feature set CI uses for all three tools, or tests will look dead that aren't.
- **Platform cfgs.** `#[cfg(target_os = ...)]` tests only run on that platform; don't call them dead.
- **`#[ignore]` tests** are skipped by default and by this audit's tools. List them in the report separately; ask whether they still run anywhere (`--run-ignored all`).
- **Property tests** (`proptest`, `quickcheck`) cover input spaces, not lines. One property test can look subsumed by line coverage while it is the only thing catching overflow and boundary bugs. Rely on mutation simulation, not coverage, for these.
- **Snapshot tests** (`insta`) assert a whole output; they look weak (one assert) but aren't.
- **Regression tests** whose name or comment cites an issue, a CVE, or an incident stay unless the user says otherwise: mark them High risk even with zero lost kills, because the mutation catalog may not reproduce the original bug.
- **Doc tests** are part of the public contract and documentation; never recommend removing one for redundancy.
- **Same lines, different outcome**: two tests that exercise the same lines but check `true` vs `false`, `Ok` vs `Err`, or empty vs non-empty are a parameterization candidate at most, never duplicates.
