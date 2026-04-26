# Test Scenarios — fitness-config-per-directory

**Wave**: DISTILL
**Date**: 2026-04-25
**Persona**: Quinn (nw-acceptance-designer)
**Feature**: fitness-config-per-directory

## Scope

Acceptance tests covering 8 user stories (US-01..US-08) against the driving
port `python3 scripts/fitness-config.py {show,validate,init} --path <target>`.

Walking-skeleton + 6 milestone files + 1 integration-checkpoints file.
All scenarios except the walking skeleton begin with `@skip` so DELIVER
can unskip one at a time per Outside-In TDD.

---

## Scenario inventory

| Feature file | Total | Active | Skipped | Tags |
|--------------|-------|--------|---------|------|
| `walking-skeleton.feature` | 1 | 1 | 0 | `@walking-skeleton @real-io @adapter-integration` |
| `milestone-1-walk-up-discovery.feature` | 5 | 0 | 5 | `@US-01 @milestone-1 @real-io` |
| `milestone-2-deep-merge.feature` | 5 | 0 | 5 | `@US-02 @milestone-2 @real-io` |
| `milestone-3-provenance.feature` | 5 | 0 | 5 | `@US-03 @US-04 @milestone-3 @real-io` |
| `milestone-4-error-handling.feature` | 11 | 0 | 11 | `@US-02 @US-05 @US-07 @milestone-4 @real-io` (mix `@infrastructure-failure`) |
| `milestone-5-backward-compat.feature` | 5 | 0 | 5 | `@US-04 @US-05 @US-06 @milestone-5 @backward-compat` |
| `milestone-6-init-helper.feature` | 4 | 0 | 4 | `@US-06 @milestone-6 @real-io` (1 `@infrastructure-failure`) |
| `integration-checkpoints.feature` | 8 | 0 | 8 | `@milestone-integration @real-io` (mix `@cli-contract @perf @property @ADR-005`) |
| **Total** | **44** | **1** | **43** | |

### Error / edge-case coverage

| Category | Count | % of total |
|----------|-------|------------|
| Happy path / success | 16 | 36% |
| Error / boundary / failure | 19 | 43% |
| Property / determinism / perf | 4 | 9% |
| Backward-compat | 5 | 12% |

**Error path ratio: 43%** — exceeds the 40% mandate threshold (Dim 1).

---

## AC trace matrix

Every AC-1..AC-39 maps to at least one scenario. Multiple ACs may map
to a single scenario; multiple scenarios may exercise a single AC.

| AC | Scenario | Feature file |
|----|----------|--------------|
| AC-01.1 | "Devin previews resolution for a file directly inside an override directory" | milestone-1 |
| AC-01.2 | "Devin previews resolution for a file two levels below the override directory" | milestone-1 |
| AC-01.3 | "Devin previews resolution for a file under no override" | milestone-1 |
| AC-01.4 | "Devin previews resolution in a repo with no fitness-config.json anywhere" | milestone-1 |
| AC-01.5 | "Resolution stays under the 100ms budget for a 10-level deep target" | integration-checkpoints |
| AC-01.6 | "Devin gets the same resolved chain every time he previews the same target" + "Resolution is deterministic across consecutive runs" | milestone-1, integration-checkpoints |
| AC-02.1 | "A partial override only restates the weights Devin cares about" | milestone-2 |
| AC-02.2 | "A full override replaces every root weight" | milestone-2 |
| AC-02.3 | "Validate fails when the effective merged weights sum to less than 100" | milestone-4 |
| AC-02.4 | same scenario | milestone-4 |
| AC-02.5 | same scenario | milestone-4 |
| AC-02.6 | "Other top-level settings merge independently" + "A status threshold range is replaced as a whole" | milestone-2 |
| AC-02.7 | "A merge that produces an invalid total blocks the review chain entirely" + "Validate failure prevents any review from proceeding" | milestone-2, milestone-4 |
| AC-03.1 | (consumer-side: skill prompts embed header lines — verified via integration-checkpoints "per-domain review report includes the same Config and Effective weights lines") | integration-checkpoints |
| AC-03.2 | "Show output embeds a parseable JSON block" | integration-checkpoints |
| AC-03.3 | "Show output for a target inside an override directory names both files" | milestone-3 |
| AC-03.4 | "Show output for a target with no override names only the root config" | milestone-3 |
| AC-03.5 | "Show output when no fitness-config.json exists anywhere" | milestone-3 |
| AC-03.6 | "Show output lists all 10 domains" + "domains ordered by descending weight" | milestone-3 |
| AC-03.7 | "A review at the repo root with module overrides present uses only the root" | integration-checkpoints |
| AC-04.1 | "Show output for a target inside an override directory names both files" + walking-skeleton | milestone-3, walking-skeleton |
| AC-04.2 | same scenario | milestone-3 |
| AC-04.3 | same scenario | milestone-3 |
| AC-04.4 | same scenario | milestone-3 |
| AC-04.5 | "Show without --path still prints the root effective config merged with defaults" | milestone-5 |
| AC-04.6 | "Resolution stays under the 100ms budget" (perf budget covers preview latency) | integration-checkpoints |
| AC-05.1 | "Validate succeeds when a partial override merges to a valid total" | milestone-4 |
| AC-05.2 | "Validate fails when the effective merged weights sum to less than 100" | milestone-4 |
| AC-05.3 | same scenario | milestone-4 |
| AC-05.4 | same scenario | milestone-4 |
| AC-05.5 | "Child config declares a newer schema version than root" | milestone-4 |
| AC-05.6 | "Validate without --path preserves the legacy single-file behavior" + "Validate without --path still validates the single root file" | milestone-4, milestone-5 |
| AC-06.1 | "Init seeds a new module override from the current root effective config" | milestone-6 |
| AC-06.2 | same scenario (post-init validate) | milestone-6 |
| AC-06.3 | "Init refuses to overwrite an existing module override" | milestone-6 |
| AC-06.4 | "Init falls back to default weights when no root config exists" | milestone-6 |
| AC-06.5 | "Init without --path still creates a root config with default weights" | milestone-5 |
| AC-07.1 | "Matching schema versions across the chain validate successfully" | milestone-4 |
| AC-07.2 | "Child config declares a newer schema version than root" | milestone-4 |
| AC-07.3 | "Child config declares an older schema version than root" | milestone-4 |
| AC-07.4 | both v2/v1 mismatch scenarios | milestone-4 |
| AC-07.5 | both v2/v1 mismatch scenarios | milestone-4 |
| AC-08.1 | (DELIVER docs review — out of acceptance-test scope; tracked in DELIVER inner loop) | n/a |
| AC-08.2 | "A per-domain review report includes the same Config and Effective weights lines as a full review" | integration-checkpoints |
| AC-08.3 | (covered by full milestone-1..6 suite — every UAT in functional-tests.md gets a milestone scenario here) | (whole suite) |
| AC-08.4 | "No skill bypasses the resolver to read fitness-config.json directly" | integration-checkpoints |
| AC-NFR-1 | "Resolution stays under the 100ms budget" | integration-checkpoints |
| AC-NFR-2 | "Resolution is deterministic across consecutive runs" | integration-checkpoints |
| AC-NFR-3 | "A repo with no module overrides behaves identically to today" + all of milestone-5 | milestone-5 |
| AC-NFR-4 | "Validate failure prevents any review from proceeding" + walking-skeleton | milestone-4, walking-skeleton |
| AC-NFR-5 | (cross-platform; verified by CI matrix in DELIVER, not by acceptance-test design) | n/a |

**Coverage summary**: 39 functional + cross-cutting ACs traced. AC-08.1 is a
documentation-review check (does each `review-*/SKILL.md` mention the
resolver?) — out of scope for acceptance tests. AC-NFR-5 is a CI matrix
concern. All other ACs trace to at least one scenario.

---

## Story-to-scenario mapping (Dim 8 Check A)

| Story | Scenarios |
|-------|-----------|
| US-01 | walking-skeleton + 5 milestone-1 + 1 integration determinism |
| US-02 | walking-skeleton + 5 milestone-2 + 1 milestone-4 sum-fail + 1 milestone-4 perm-block |
| US-03 | 5 milestone-3 + AC-08.2 integration scenario |
| US-04 | walking-skeleton + 5 milestone-3 + 1 milestone-5 backward-compat |
| US-05 | 4 milestone-4 (validate effective + schema mismatch) + 1 milestone-5 backward-compat |
| US-06 | 4 milestone-6 + 1 milestone-5 backward-compat |
| US-07 | 3 milestone-4 (matching, newer, older) |
| US-08 | 2 integration-checkpoints (audit grep + per-domain header lines) |

Every story has at least one scenario. No untraceable stories.

---

## Mandate compliance (CM-A/B/C/D)

### CM-A: Hexagonal boundary enforcement

All steps invoke the CLI subprocess via `repo.run("show"|"validate"|"init", ...)`.
No step imports resolver internals. The grep audit:

```
grep -rn "from scripts" tests/acceptance/fitness-config-per-directory/
grep -rn "import scripts" tests/acceptance/fitness-config-per-directory/
```

returns zero matches. The driving port is the CLI; tests respect the
hexagonal boundary.

### CM-B: Business language abstraction

Gherkin uses domain terms (root config, module override, effective
weights, source chain, preview, validate, initialize, schema version).
Technical terms `JSON`, `subprocess`, `argparse`, `stdout`, `exit code` appear in the
test infrastructure (conftest, step methods) but NOT in the .feature
files. The two exceptions surface as user-facing CLI vocabulary:

- "exits with success" / "exits with a non-zero status" — these are user-observable outcomes (the user runs a command in a shell; exit code IS the observable signal).
- "fenced effective-config JSON block" — appears in ONE integration-checkpoints scenario where the JSON contract IS the user-visible artifact (skill prompts parse it).

These are accepted as domain-meaningful given the CLI is the driving port.

### CM-C: User journey completeness

- Walking skeleton: Devin's complete preview-before-review journey.
- Each milestone scenario has Given (Devin's repo state), When (CLI command
  Devin runs), Then (what Devin observes — exit status, source chain,
  effective weights, error message).
- Error scenarios validate complete recovery journeys (error names files
  AND offers fixes AND blocks downstream review).

### CM-D: Pure-function extraction

The DESIGN wave already extracted resolver/merger/validator/reporter as
pure functions per ADR-006. Acceptance tests exercise the CLI driving
port (impure boundary). No fixture parametrization across environments
is needed — `tmp_path` provides one isolated real filesystem per scenario.

Pure-function inventory (from DESIGN):
- `walk_up_chain(target_path) -> list[Path]` — pure
- `deep_merge_chain(chain, defaults) -> dict` — pure
- `validate_effective(effective, raw_configs, source_chain) -> list[str]` — pure
- `render_show_output(result) -> str`, `render_header_lines(...)`, `render_validation_error(...)`, `render_inline_weights(...)` — pure
- `_read_config(path) -> dict | None` — IMPURE (the only adapter)

DELIVER inner-loop unit tests will cover each pure function directly with
table-driven inputs. Acceptance tests do not need to.

---

## Tag taxonomy

| Tag | Meaning |
|-----|---------|
| `@walking-skeleton` | The single end-to-end skeleton scenario |
| `@US-01..@US-08` | Story traceability |
| `@AC-XX.X` | Acceptance criterion traceability |
| `@milestone-1..6, @milestone-integration` | Milestone grouping for DELIVER unskip order |
| `@real-io` | Scenario uses real filesystem + real subprocess (no in-memory doubles) |
| `@adapter-integration` | Scenario specifically exercises an adapter wiring (subprocess + filesystem) |
| `@infrastructure-failure` | Adapter failure mode (malformed JSON, missing path, permission denied, depth exceeded) |
| `@property` | Property-shaped invariant (DELIVER may implement as property-based test) |
| `@perf` | Performance-budget assertion |
| `@cli-contract` | CLI argument/output contract scenarios |
| `@backward-compat` | NFR-3 backward compatibility |
| `@ADR-005` | Specifically validates ADR-005 (broad-scope uses only root) |
| `@skip` | Currently disabled — DELIVER unskips one at a time |

---

## DELIVER unskip order

See `walking-skeleton.md` for the rationale. Summary:

1. (active) walking-skeleton.feature
2. milestone-1 walk-up scenarios (5)
3. milestone-2 deep-merge scenarios (5)
4. milestone-3 provenance/show scenarios (5)
5. milestone-5 backward-compat scenarios (5)
6. milestone-6 init helper (4)
7. milestone-4 error handling (11)
8. integration-checkpoints (8) — last because they exercise full contract
