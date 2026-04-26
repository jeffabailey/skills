# Acceptance Criteria: fitness-config-per-directory

This document consolidates the testable acceptance criteria from each user story in `user-stories.md`. Every AC corresponds to one or more Gherkin scenarios in `journey-fitness-config-per-directory.feature`.

Format: each AC is observable, automatable, and traceable to a UAT scenario.

## US-01: Walk-Up Resolver

| AC-ID | Criterion | Verification |
|-------|-----------|--------------|
| AC-01.1 | Resolver returns `[child, root]` when both exist | UAT: "Resolver finds nearest config when target is a file in the override directory" |
| AC-01.2 | Resolver walks past intermediate directories without configs | UAT: "Resolver walks past intermediate directories without configs" |
| AC-01.3 | Resolver returns `[root]` when no override exists in target's ancestors | UAT: "Resolver falls back to root when no override is found" |
| AC-01.4 | Resolver returns `[]` (built-in defaults) when no config exists | UAT: "Resolver falls back to defaults when no config exists at all" |
| AC-01.5 | Resolver completes < 100ms for paths up to 10 levels deep in 10k-file repo | NFR-1 perf test |
| AC-01.6 | Resolver output is byte-identical across machines for same input | NFR-2 determinism test |

## US-02: Effective Config Merge & Validation

| AC-ID | Criterion | Verification |
|-------|-----------|--------------|
| AC-02.1 | Partial override merges with root for unspecified domains | UAT: "Partial override merges with root values for unspecified domains" |
| AC-02.2 | Full override replaces every root weight | UAT: "Full override replaces every root weight" |
| AC-02.3 | Effective weights summing != 100 produces validation failure with exit code 1 | UAT: "Merged weights do not sum to 100 — validation fails" |
| AC-02.4 | Error message names BOTH files in the chain | Same UAT |
| AC-02.5 | Error message offers two concrete fixes (adjust weights, full-replacement mode) | Same UAT |
| AC-02.6 | Other top-level keys (statusThresholds, security, scoring) merge per-key | UAT: "Other top-level keys merge independently" |
| AC-02.7 | No silent fallback to root config on validation failure | NFR-4 fail-closed test |

## US-03: Report Header Provenance

| AC-ID | Criterion | Verification |
|-------|-----------|--------------|
| AC-03.1 | Header section appears within first 10 lines of every report | Grep test on generated reports |
| AC-03.2 | Header values match resolver output (no drift) | Integration test: capture resolver output and report header for same path, assert byte-identical |
| AC-03.3 | Source chain with 2 entries renders as `Config: <child> (merged with root)` | UAT: "Report header proves override was applied" |
| AC-03.4 | Source chain with 1 entry (root only) renders as `Config: <path>` | UAT: "Report header on root-scoped review names only the root config" |
| AC-03.5 | Empty source chain renders as `Config: built-in defaults (no fitness-config.json found)` | UAT: "Report header when no config exists" |
| AC-03.6 | Effective weights line lists all 10 domains | UAT: "Report header proves override was applied" |
| AC-03.7 | Root-scoped review with subtree overrides existing includes a footnote/note | UAT: "Report header on root-scoped review names only the root config" |

## US-04: Show Subcommand

| AC-ID | Criterion | Verification |
|-------|-----------|--------------|
| AC-04.1 | `show --path <file>` prints source chain in precedence order | UAT: "Show subcommand previews override" |
| AC-04.2 | `show --path` prints effective weights as a table | Same UAT |
| AC-04.3 | `show --path` prints sum-line confirming totals | Same UAT |
| AC-04.4 | `show --path` exits 0 on success | All show UATs |
| AC-04.5 | Existing `show` (no --path) preserved | Backward-compat regression test |
| AC-04.6 | `show --path` median execution under 1 second | Perf test in functional suite |

## US-05: Validate Subcommand

| AC-ID | Criterion | Verification |
|-------|-----------|--------------|
| AC-05.1 | `validate --path <dir>` resolves and validates effective merged config | UAT: "Validate passes when effective merged config is valid" |
| AC-05.2 | Validate failure exits non-zero | UAT: "Validate fails when effective merged sum is wrong" |
| AC-05.3 | Validate error names all files in chain | Same UAT |
| AC-05.4 | Validate error offers actionable remediation | Same UAT |
| AC-05.5 | Schema version mismatch produces hard error | UAT: "Validate fails on schema version mismatch" |
| AC-05.6 | Existing `validate` (no --path) preserved | UAT: "Validate without --path preserves existing behavior" |

## US-06: Init Helper

| AC-ID | Criterion | Verification |
|-------|-----------|--------------|
| AC-06.1 | `init --path <dir>` creates `<dir>/fitness-config.json` seeded from root | UAT: "Init creates a scaffold from current root effective config" |
| AC-06.2 | Generated file passes `validate --path <dir>` immediately | Same UAT |
| AC-06.3 | Init refuses to overwrite existing file | UAT: "Init refuses to overwrite existing override" |
| AC-06.4 | Init falls back to DEFAULT_WEIGHTS when no root exists | UAT: "Init with no root falls back to defaults" |
| AC-06.5 | Existing `init` (no --path) preserved | Regression test |

## US-07: Schema Version Mismatch

| AC-ID | Criterion | Verification |
|-------|-----------|--------------|
| AC-07.1 | Matching versions across chain merge successfully | UAT: "Matching versions merge successfully" |
| AC-07.2 | Child version newer than root produces hard error | UAT: "Child version newer than root" |
| AC-07.3 | Child version older than root produces hard error | UAT: "Child version older than root" |
| AC-07.4 | Error names all files and their declared versions | Both error UATs |
| AC-07.5 | Error states supported version | Both error UATs |

## US-08: All Domain Skills Honor Override

| AC-ID | Criterion | Verification |
|-------|-----------|--------------|
| AC-08.1 | Every `review-<domain>` skill documents calling the resolver in its SKILL.md | Documentation review |
| AC-08.2 | Every per-domain report includes Config: and Effective weights: header lines | Functional test grep over per-domain report outputs |
| AC-08.3 | Functional tests include at least one override-aware scenario per skill | Test plan review |
| AC-08.4 | No skill bypasses resolver to read raw config (lint/grep gate) | CI lint step: grep for `fitness-config.json` direct loads outside `scripts/fitness-config.py` |

## Cross-Cutting (NFRs)

| AC-ID | Criterion | Verification |
|-------|-----------|--------------|
| AC-NFR-1 | Resolver overhead < 100 ms in 10k-file repo | Benchmark in functional tests |
| AC-NFR-2 | Resolver output deterministic across runs and machines | Run resolver twice, assert byte-identical |
| AC-NFR-3 | Backward compatibility: repos with no overrides behave identically | Run existing functional tests unchanged |
| AC-NFR-4 | Fail-closed on validation failure (no review proceeds) | Test deliberate-invalid configs, assert no review output produced |
| AC-NFR-5 | Cross-platform (macOS, Linux, Windows) | CI matrix |
