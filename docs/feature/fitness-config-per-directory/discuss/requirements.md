# Requirements: fitness-config-per-directory

## Business Capability
Enable developers maintaining multi-module repositories to apply module-specific fitness review weights without forking the review skills or maintaining multiple root configs.

## Feature Goal
Allow a `fitness-config.json` placed in a subdirectory to override the root `fitness-config.json` for reviews scoped to that subtree, with deterministic discovery, deterministic merging, and visible provenance in every report.

## In Scope (v1)
- Walk-up discovery from review target path to nearest `fitness-config.json` ancestor
- Deep-merge of child override on top of root config (per top-level key, per domain weight)
- Effective-config validation: merged weights must sum to 100
- `fitness-config.py show --path <target>` subcommand displaying source chain and effective config
- `fitness-config.py validate --path <dir>` validating effective merged config (not just file)
- Report header lines naming config source chain and effective weights inline
- Schema version compatibility check between root and child

## Out of Scope (v1, may revisit)
- Multiple stacked overrides in one path (postgresql/ AND postgresql/scripts/) — DQ-5
- Explicit `--config <path>` flag for arbitrary config locations
- Glob-based discovery
- Full-replacement merge mode (vs deep-merge) — DQ-2
- Migration tooling between schema versions

## Functional Requirements

### FR-1: Config Discovery via Walk-Up
The resolver SHALL walk up from a review target path (file or directory) toward the repo root, returning the first directory containing a `fitness-config.json`. If none is found, the resolver SHALL fall back to the repo root config (if present), or to built-in defaults.

### FR-2: Deep-Merge Semantics
When both a child and a root config exist, the resolver SHALL produce an effective config by deep-merging child over root: child top-level keys (`weights`, `statusThresholds`, `security`, `scoring`) replace corresponding root keys, but within `weights`, only domain keys present in the child are overridden — root values are preserved for omitted domains. (Final merge mode subject to DESIGN confirmation.)

### FR-3: Effective Weights Sum Validation
The effective merged weights SHALL sum to 100 (within 0.01 tolerance). Any deviation SHALL produce a validation error naming both config files and offering remediation guidance.

### FR-4: Show Subcommand
`fitness-config.py show --path <target>` SHALL display: the resolved config source chain (in precedence order), the effective merged weights as a table, the merged status thresholds, security config, and scoring ranges, and a sum-line confirming totals.

### FR-5: Validate Subcommand on Effective Config
`fitness-config.py validate --path <dir>` SHALL validate the effective merged config (not just the file at `<dir>/fitness-config.json`). Validation SHALL fail if: the effective merged weights do not sum to 100; any config in the chain has malformed JSON; the schema versions of root and child differ.

### FR-6: Report Header Provenance
Every fitness review report (whether from `review-full` or any individual `review-<domain>`) SHALL include a header section (within the first 10 lines) naming: scope, config source chain, and effective weights inline. Without this, the override is invisible.

### FR-7: Single Resolver Source of Truth
All review skills SHALL obtain their effective config via the resolver. No skill SHALL read raw `fitness-config.json` from the repo root and use it directly when a subtree scope is specified.

### FR-8: Schema Version Compatibility
The resolver SHALL refuse to merge when root and child specify different `version` values, exiting with an error that names both files and their versions.

## Non-Functional Requirements

### NFR-1: Performance — resolver overhead
Resolver execution (walk-up + parse + merge + validate) SHALL complete in under 100 ms for repos up to 10,000 files. Measurement: invoke `fitness-config.py show --path <deep nested file>` 10 times in a 10k-file repo, average wall-clock time.

### NFR-2: Determinism
Given the same target path and the same set of `fitness-config.json` files in the repo, resolver output (source chain + effective config) SHALL be byte-identical across invocations and across machines.

### NFR-3: Backward Compatibility
Repos without any subdirectory `fitness-config.json` SHALL behave identically to today (root config used; no observable change). Validation: existing `tests/functional-tests.md` continues to pass without modification.

### NFR-4: Failure Mode — fail closed
If validation fails (sum != 100, schema mismatch, malformed JSON), the resolver SHALL exit non-zero before any review domain runs. No review SHALL proceed using a partially-validated or fallback config without explicit user opt-in.

### NFR-5: Cross-Platform
Resolver SHALL work on macOS, Linux, and Windows using only Python 3.6+ standard library (consistent with existing `scripts/fitness-config.py`).

## Business Rules

### BR-1: Effective Weight Sum
The merged effective weights MUST sum to 100. This rule applies to the merged config, not the override file in isolation. A partial override that adds new domain weights without zeroing equivalents elsewhere is invalid.

### BR-2: Schema Version Lock
Within a single repo, all `fitness-config.json` files MUST declare the same schema version. Mixed versions are an error, not a warning, to prevent silent surprises.

### BR-3: Override Discovery is Walk-Up Only (v1)
The first `fitness-config.json` found while walking up from the review target wins. The resolver SHALL NOT consider sibling directories, glob matches, or environment variables as sources in v1.

### BR-4: Provenance Always Visible
A review report without the Config: and Effective weights: header lines is a defect, regardless of whether an override was actually applied.

### BR-5: Resolver as Single Source of Truth
Skills MUST NOT directly load `fitness-config.json` files. All config access goes through the resolver, ensuring consistent merge semantics and provenance reporting.

## Glossary (Ubiquitous Language)

| Term | Definition |
|------|-----------|
| Root config | `fitness-config.json` at the repo root |
| Override config | `fitness-config.json` in a subdirectory |
| Effective config | Result of merging override over root, used by all scorers |
| Source chain | Ordered list of config files contributing to the effective config (highest precedence first) |
| Walk-up | Discovery algorithm: start from review target, ascend parent directories until first `fitness-config.json` is found |
| Review target path | The path passed to a review skill (file or directory); seed for walk-up |
| Review scope | The subtree being reviewed (often equals review target path) |
| Provenance | Header lines in the report naming the source chain and effective weights |

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Skills read root config directly, bypassing resolver (FR-7 violation) | Medium | High | Audit/lint step: grep for direct JSON reads of `fitness-config.json` in any `src/review-*/SKILL.md`; require resolver call in PR template |
| Walk-up picks wrong config when target is a symlink | Low | Medium | Resolver uses real path resolution; documented in error messages |
| Users author overrides with wrong sum, get blocked, give up | Medium | High | Init helper (US-06) seeds with sane sum-100 weights; validate subcommand provides clear remediation |
| Per-domain SKILLs roll out at different paces, creating inconsistency | Medium | Medium | Functional test gate: all `review-<domain>` skills must pass override-aware tests before marking R3 done |
| Schema version drift between repo branches (some have v1, some v2 child configs) | Low | Medium | Schema version mismatch is hard error; no silent coercion |

## Dependencies

- Existing `scripts/fitness-config.py` — extended, not replaced
- Existing `fitness-config.schema.json` — unchanged for v1 (no schema additions; same shape applies to override files)
- Existing `src/review-*/SKILL.md` files — must be updated in R3 to call resolver
- Existing `tests/functional-tests.md` — extended in R3 to cover override scenarios

No external service or third-party dependencies.

## Stakeholders

| Group | Need |
|-------|------|
| Infrastructure engineers (Devin persona) | Module-specific weights without forking skills |
| Skill maintainers (Jeff, repo owner) | Single resolver implementation; no per-skill config logic to maintain |
| CI/CD users (GitHub Agentic Workflows, Claude Code Action) | Backward compatibility — no override means no behavior change |
| New users / first-time installers | Discoverability — `init --path` and `show --path` make the feature visible without reading docs |
