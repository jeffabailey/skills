---
name: deslop-rust
description: "Audits a Rust crate or workspace for junk tests and dead code using evidence from cargo-nextest (per-test timings), cargo-llvm-cov (per-test coverage overlap), and cargo-mutants (which mutations the suite catches, and which kills a test removal would lose). It installs any of these tools that are missing, writes a prioritized report (file and test, problem, evidence, recommended optimization, estimated time savings, risk), changes nothing until the user approves, then applies only the approved items and verifies them against the original test results and mutation results. Use when the user says /deslop-rust, wants to clean up, slim down, dedupe, or speed up a Rust test suite, asks which Rust tests are redundant, weak, slow, or safe to delete, wants to parameterize or consolidate Rust tests, asks for a mutation-testing or coverage-overlap review of a Rust project, or wants dead Rust code found and removed, even if they don't name the tools."
user-invocable: true
argument-hint: "[path] [--package NAME] [--files GLOB] - crate or workspace to audit; defaults to the current Cargo project"
metadata:
  version: "1.0.0"
---

# deslop-rust

Slop in a test suite is tests that cost time and attention but don't protect anything the rest of the suite doesn't already protect. Deciding that a test is slop takes evidence, not a vibe: two tests can look the same and check different edge cases, and a test can cover every line and still miss a real bug. Three tools give the evidence:

| Tool | Question it answers |
|---|---|
| `cargo-nextest` | How long does each test take? (JUnit timings, parallel runs) |
| `cargo-llvm-cov` | Which production lines does each test reach? Which lines does no test reach? |
| `cargo-mutants` | Which small injected bugs does the suite catch, and which catches go away if we drop a test? |

Mutation results are the strongest evidence. Coverage overlap only nominates candidates: a test is redundant when removing it loses **zero mutation kills** and its assertions are already made elsewhere, not just when its lines are covered elsewhere.

## The mission

Perform a comprehensive Rust test-suite optimization audit. Identify:

1. Duplicate and semantically equivalent tests.
2. Tests with overlapping coverage.
3. Excessively verbose tests that could be parameterized.
4. Repeated setup, teardown, and fixture construction.
5. Weak assertions and tests that don't verify meaningful outcomes.
6. Tests that validate implementation details instead of contracts.
7. Slow tests and unnecessary integration-test overhead.
8. Tests that provide no independent regression protection.
9. Opportunities to consolidate tests without losing edge-case coverage.

Also flag **junk production code**: functions no test reaches and nothing calls (dead code), as evidenced by uncovered lines, mutants that survive because nothing executes them, and `#[allow(dead_code)]` items with no references.

Produce a prioritized report, then **stop**. Don't edit, delete, or move any test or source file during the audit. Making changes waits for the user's approval of specific report items, and every change is verified against the original suite and the original mutation results.

The approval gate exists because "redundant" is a judgment the user owns: a test may document a contract, guard a past incident, or be required by a reviewer. If the request already says "just delete the junk", still deliver the report first and ask which items to apply; it costs one round-trip and prevents silently losing a guard nobody knew mattered.

## Working files

Keep every artifact under `target/deslop-rust/` in the project (call it `$W`). `target/` is already ignored by Cargo projects, so the audit leaves `git status` clean. Use `${CLAUDE_SKILL_DIR}` for this skill's directory; if your agent does not expand it, use the directory holding this SKILL.md.

## Phase 0: Preflight and install

1. Find the project: the path the user gave, else the nearest `Cargo.toml`. Note whether it is a workspace (`[workspace]`) and which packages are in scope.
2. Check the tree: `git status --porcelain`. If there are uncommitted changes, say so; the verification later compares against this starting point, so record `git rev-parse HEAD` and keep a copy of the diff if the user wants to continue anyway.
3. Check each tool and install only what is missing. Tell the user what you are installing; these are user-level Cargo installs (into `~/.cargo/bin`), which is how Cargo subcommands work, so they are shared by every project:

   ```bash
   cargo nextest --version  || cargo install cargo-nextest --locked
   cargo llvm-cov --version || cargo install cargo-llvm-cov --locked
   cargo mutants --version  || cargo install --locked cargo-mutants
   rustup component list --installed | grep -q llvm-tools || rustup component add llvm-tools-preview
   ```

   If `cargo binstall` is available, `cargo binstall -y <tool>` is much faster than building from source. If an install fails (no network, pinned toolchain), report it and continue with the evidence the remaining tools give; say in the report which evidence is missing.
4. Run the suite once: `cargo nextest run` (add the project's usual flags: `--workspace`, `--all-features`, or the features CI uses). If it fails, stop and report: an audit on a red suite has no baseline to protect.

## Phase 1: Collect the baseline evidence

Read `references/tool-recipes.md` for exact flags, how to scope large projects, and known pitfalls (doctests, features, timeouts).

1. **Timings.** Write `$W/nextest.toml` with a JUnit profile, run nextest with it, and rank tests:

   ```bash
   mkdir -p target/deslop-rust/{baseline,sim,after}   # cargo mutants -o needs the directory to exist
   printf '[profile.default.junit]\npath = "junit.xml"\n' > target/deslop-rust/nextest.toml
   cargo nextest run --tool-config-file "deslop-rust:$PWD/target/deslop-rust/nextest.toml"   # nextest requires an absolute path
   python3 "${CLAUDE_SKILL_DIR}/scripts/nextest_timings.py" target/nextest/default/junit.xml --top 25
   ```

2. **Per-test coverage overlap.** Measures each test alone and reports identical-coverage groups, strict subsets, tests with zero unique lines, and production lines no test reaches:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/coverage_overlap.py" --out target/deslop-rust/cov
   ```

   It runs one coverage pass per test. For suites over a few hundred tests, narrow it with `--filter '<nextest filterset>'` to the modules you are auditing, and say so in the report.

3. **Mutation baseline.** Estimate cost first: `cargo mutants --list | wc -l` mutants × the baseline test time ÷ jobs. If that exceeds ~20 minutes, tell the user the estimate and scope with `-f <file>` or `-p <package>` before you run it.

   ```bash
   cargo mutants --test-tool nextest -j 4 -o target/deslop-rust/baseline -- --no-fail-fast
   python3 "${CLAUDE_SKILL_DIR}/scripts/kill_matrix.py" target/deslop-rust/baseline/mutants.out
   ```

   `--no-fail-fast` makes every test run against every mutant, so the mutant logs show *each* test that catches a mutant, not only the first. `kill_matrix.py` turns those logs into a per-test kill matrix: kills and unique kills per test, tests with identical kill sets, tests whose kills are a strict subset of another's, and tests that kill nothing. That one run is the main evidence for categories 1, 2, and 8. Use `-j 2` when other work shares the machine.

   Keep `target/deslop-rust/baseline/mutants.out/` untouched; it is the yardstick for every later comparison.

4. **Doctests.** nextest does not run doctests. Run `cargo test --doc` too, and remember doctests can be the only guard for some behavior.

## Phase 2: Read the tests and classify

Tools nominate; reading confirms. For every nominated test, open the test and the code under test and decide which of the nine mission categories apply (or the junk-code category). Look at what each test *asserts*, not only what it executes:

- Same coverage + same assertions + same inputs → duplicate (category 1).
- Same coverage, different inputs or outcomes (true vs false return, error vs ok) → **not** a duplicate; at most a parameterization candidate (3, 9).
- Only `is_ok()`, `is_err()`, `let _ = f()`, `assert!(x > 0)` where an exact value is knowable, or no assertion at all → weak (5). The fix is usually to strengthen it, not delete it.
- Asserts on private layout, `#[doc(hidden)]` accessors, `Vec` capacity, internal ordering the API doesn't promise → implementation detail (6). Recommend asserting the public contract instead.
- `thread::sleep`, real network or filesystem where a fake would do, a full integration binary for a unit-level check → slow or overhead (7). Each `tests/*.rs` file is its own binary to link; many tiny ones add build and startup time.
- The same three lines of setup in many tests → fixture (4); recommend a helper function or builder, not a new dependency.
- Mutation-surviving code that nothing calls (`#[allow(dead_code)]`, no references from `grep -rn`, not `pub` API) → junk code. `pub` items may be used by downstream crates; mark those high risk.

### Prove "no independent regression protection" (category 8)

Check the whole set of tests you plan to recommend for removal against the kill matrix. This needs no new mutation run:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/kill_matrix.py" target/deslop-rust/baseline/mutants.out \
  --remove tests::cart_total_again tests::discount_runs full_checkout_flow_with_retry
```

It lists every mutant that only the removed tests catch, and exits 1 if there is one. Zero lost kills is the evidence that the set is safe to remove. If kills are lost, the output names the mutant and the test that alone catches it: move that test to "keep" or "merge into a parameterized test" and check again. Missed mutants in the baseline are gaps the suite already has; report the important ones as gaps (a test to add), separate from removals.

An identical kill set is not proof of a duplicate. cargo-mutants makes only a few mutants per function, so tests that check different things (`rejects_zero` and `accepts_42`) can catch the same few mutants. Read the assertions before you call two tests duplicates.

If the baseline was run with fail-fast (the script refuses those logs), or to confirm a large removal before you report it, simulate it directly: `cargo mutants --test-tool nextest -f <files> -o target/deslop-rust/sim -- -E 'not (test(=a) | test(=b))'`, then `mutants_compare.py` baseline against sim.

## Phase 3: The report

Write `target/deslop-rust/report.md` and show its contents in the chat. Rank by value ÷ risk: low-risk items with real savings first. Use this structure:

```markdown
# Rust test-suite optimization audit: <crate>

Baseline: <N> tests, <S>s summed test time, <W>s wall time; mutants <caught>/<total> caught
(<missed> missed, <timeout> timeout); <C>% line coverage. Commit <sha>.
Scope: <packages/files>; evidence not collected: <none | which tool and why>.

## Prioritized findings

| # | File :: test | Category | Problem | Evidence | Recommended optimization | Est. time saved | Risk |
|---|---|---|---|---|---|---|---|
| 1 | tests/integration.rs :: full_checkout_flow | 7 slow | sleeps 1.5s for a service that doesn't exist | junit 1.513s (47% of suite); kill matrix: 0 unique kills | delete the sleep | ~1.5s per run, ~78s per mutation run (52 mutants) | Low |

## Junk production code
<item, evidence (uncovered lines, missed mutants, references), recommendation, risk>

## Gaps found (not removals)
<surviving mutants worth a new or stronger test>

## Not recommended
<tests that looked redundant but hold unique kills or distinct edge cases, and why they stay>

## Totals if all items are approved
<tests removed / merged, seconds saved per run and per mutation run, lines removed>
```

Fill every column. **Evidence** names the tool and the number (timing, identical-coverage group, `kill_matrix.py` result, the line the weak assert is on). **Est. time saved** comes from the JUnit times of the tests removed or shortened; also give the per-mutation-run saving (seconds saved × mutants tested), because a slow test is paid once per mutant. Parameterizing saves code and maintenance more than seconds; say "~0s, -N lines" rather than inventing a number. **Risk**: Low = identical assertions or zero lost kills in the kill matrix; Medium = overlap is real but the test documents an edge case or contract that should move, not vanish; High = holds unique kills or unique lines, is public API, or names an issue or incident.

Then end with one direct question: which item numbers to apply (for example "all Low", "1-4 and 7", or "none"). Don't make changes in the same turn.

## Phase 4: Apply approved items

Apply only the approved numbers, one category at a time so a failure points at one kind of change:

- **Removing duplicates:** keep the clearest name; if the one you remove had a better name, rename the keeper.
- **Parameterizing:** use what the project already uses (`rstest`, `test-case`, a `macro_rules!`, or a table loop with a message naming the case: `assert_eq!(parse(input), want, "input {input:?}")`). Don't add a dev-dependency without asking. Keep every distinct input and expected value from the tests you fold in.
- **Weak assertions:** replace with the exact expected value. Run the test to confirm it passes; a failure means you found a bug, so stop and report it instead of loosening the assert.
- **Implementation-detail tests:** rewrite against the public contract, or remove if the contract is already asserted elsewhere with zero lost kills.
- **Slow tests:** remove pointless sleeps, swap real I/O for in-memory fakes, move unit-level checks out of `tests/` into `#[cfg(test)]` modules, or merge tiny integration binaries.
- **Junk code:** delete the item and its `#[allow(dead_code)]`; run `cargo build --all-targets` and `cargo clippy --all-targets` if the project uses Clippy.

## Phase 5: Verify against the original

Run all of these and put the numbers in a before/after table:

1. `cargo nextest run` (same flags as Phase 0) passes, plus `cargo test --doc`. The test count drops only by the removed tests; every remaining test name existed before or is an approved merge.
2. Mutation results: rerun the same scope as the baseline and compare:

   ```bash
   cargo mutants --test-tool nextest -j 4 -o target/deslop-rust/after -- --no-fail-fast
   python3 "${CLAUDE_SKILL_DIR}/scripts/mutants_compare.py" \
     target/deslop-rust/baseline/mutants.out target/deslop-rust/after/mutants.out
   ```

   It must exit 0 (no lost kills). Mutants listed as "only in baseline" must belong to approved junk-code deletions; anything else means production code changed and is a defect to fix.
3. Coverage: rerun `coverage_overlap.py` (or `cargo llvm-cov nextest --summary-only`) and confirm no production line that was covered before is uncovered now, apart from deleted junk code.
4. Timing: rerun the JUnit profile and report the summed test time and wall time before and after.

If any check fails, revert that item (`git checkout -- <file>` for that change only), say which item failed and why, and continue with the rest. End with the before/after table and the list of items applied, reverted, and still pending. Don't commit unless the user asks.
