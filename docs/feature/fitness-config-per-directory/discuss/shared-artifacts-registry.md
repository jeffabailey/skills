# Shared Artifacts Registry: fitness-config-per-directory

Every `${variable}` in journey mockups must trace to a single source of truth. This registry documents producers and consumers.

## Artifacts

### `review_target_path`

| Property | Value |
|----------|-------|
| Source of truth | User invocation (CLI argument, or CWD if not given) |
| Displayed as | `${review_target_path}` |
| Consumers | resolver walk-up, report header (Scope line), `show` subcommand banner |
| Owner | Top-level invocation parser (review-* skill or `fitness-config.py`) |
| Integration risk | HIGH — wrong path means resolver picks the wrong config |
| Validation | `show --path X` and `review-full --scope X` must produce same resolver result |

### `config_source_chain`

| Property | Value |
|----------|-------|
| Source of truth | Config resolver output (ordered list of file paths) |
| Displayed as | "Config: <child> (merged with root)" or "Config: fitness-config.json" |
| Consumers | report header (Config line), `show` subcommand banner, error messages on validation failures |
| Owner | Config resolver (in `scripts/fitness-config.py` per Luna's assumption) |
| Integration risk | HIGH — silent drift between what was used and what is reported breaks user trust |
| Validation | Report header chain MUST equal resolver output for the same target path |

### `effective_weights`

| Property | Value |
|----------|-------|
| Source of truth | Config resolver merge step |
| Displayed as | Table in `show` output, inline list in report header, weight applied per domain in scoring |
| Consumers | Every domain scorer, weighted-average calculator, report header, `show` output, validation messages |
| Owner | Config resolver (must be the *only* place that merges) |
| Integration risk | CRITICAL — if scorers reach for raw root weights instead of effective weights, override is silently ignored |
| Validation | `show` output, report header, and the weights actually used in scoring MUST be byte-identical for any given run |

### `effective_status_thresholds`, `effective_security_config`, `effective_scoring_ranges`

| Property | Value |
|----------|-------|
| Source of truth | Config resolver merge step |
| Displayed as | Used during status assignment (Healthy/Needs Attention/Critical), security confidence filter, scoring range labels |
| Consumers | Report status column, security skill confidence threshold, all skills' good/bad-range labels |
| Owner | Config resolver |
| Integration risk | MEDIUM — these are less prominent than weights, but if they drift, status colors and security findings will mismatch what user expects |
| Validation | Same as effective_weights — single resolver output, no recomputation downstream |

### Schema version

| Property | Value |
|----------|-------|
| Source of truth | `fitness-config.schema.json` (`version` const) |
| Displayed as | `"version": 1` in every config file |
| Consumers | Validator (root and child), error messages, future migration tooling |
| Owner | Schema file in repo root |
| Integration risk | MEDIUM — version drift between root and child configs (DQ-3) |
| Validation | Validator must read schema's `const` and compare to both config files' `version` field |

## Integration Validation Checks

Run these checks during DESIGN/DELIVER to confirm horizontal coherence:

1. **Resolver-as-single-source check**: grep for hardcoded weight reads across the codebase. Only the resolver should read `weights` from the JSON file. All consumers should call the resolver.
2. **Report-header-fidelity check**: produce a report with a non-trivial override; assert the header's effective-weights line equals the resolver output for the same path.
3. **Show-vs-review parity check**: run `show --path X` and `review-full --scope X`, capture both effective-weights outputs, assert byte-identical.
4. **Walk-up determinism check**: from a deep nested file, verify resolver picks the *nearest* `fitness-config.json` ancestor, not the root, when both exist.
5. **Validation-blocks-review check**: any validation failure (sum != 100, schema mismatch, malformed JSON) MUST exit non-zero before any review domain runs.

## Open Questions Affecting Artifacts

- DQ-2 (merge semantics) affects how `effective_weights` is computed. If merge mode is configurable per file, the resolver must surface the mode in `config_source_chain` ("merged with root" vs "replaces root").
- DQ-5 (broad scope crossing multiple overrides) affects whether `config_source_chain` can ever contain more than 2 entries.

These will be resolved in DESIGN. The artifact contracts (single source, no drift) hold regardless of how DESIGN answers them.
