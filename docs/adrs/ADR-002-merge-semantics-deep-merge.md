# ADR-002: Merge Semantics — Deep-Merge per Top-Level Key, per Domain Weight

**Status**: Accepted
**Date**: 2026-04-25
**Wave**: DESIGN — fitness-config-per-directory
**Persona**: Morgan (nw-solution-architect)

## Context

When both root and child `fitness-config.json` exist, the resolver must combine them into a single effective config. The merge rule directly affects authoring ergonomics and validation semantics:

- A **deep merge** lets the override file restate only the values that differ. Easy to author; minimal diff.
- A **full replacement** (override entirely supersedes root for any top-level key it touches) is simpler to reason about but forces overrides to restate every weight even when only one differs.
- A **mode flag** (`mergeMode: "deep" | "replace"`) lets the user pick per file, but doubles the validation surface and complicates authoring guidance.

Quality attributes:
- **Authoring ergonomics** (KPI 3 first-attempt success): minimum-diff overrides reduce errors.
- **Predictability**: user must know what their override will produce without trial-and-error.
- **Validation correctness**: BR-1 says effective weights must sum to 100 — the validator runs on the merged result.

## Decision

**v1 uses deep-merge per top-level key, per domain weight.** No mode flag. No alternative merge mode.

Concrete rules:

| Top-level key | Merge granularity |
|---------------|-------------------|
| `weights` | Per-domain key (`weights.data`, `weights.architecture`, etc.) |
| `statusThresholds` | Per-range-name key (`healthy`, `needsAttention`, `critical`); whole array replaces if present |
| `security` | Per-inner-key (`confidenceThreshold` etc.); replaced if present |
| `scoring` | Per-inner-key (`goodRange`, `badRange`); whole array replaces if present |
| `version` | From the highest-precedence chain entry that has it; chain consistency checked separately by validator |

Within `weights`: if the override sets `data=30` and `reliability=20`, only those two domains change. The remaining 8 domains are inherited from the root (or from `DEFAULT_WEIGHTS` if the chain is rooted in defaults).

The merged effective `weights` MUST sum to 100 within 0.01 tolerance (BR-1). Validation runs after merge, not on the override file in isolation. A partial override that happens to sum to less than 100 in isolation is fine, as long as the merge with root brings the total to 100.

## Alternatives Considered

### Alternative A — Full replacement (rejected for default)
- **Pros**: Easy to reason about — "the override file IS the config". No "hidden" inheritance.
- **Cons**: Every override restates every weight even when only one differs. High authoring friction. Adoption barrier.
- **Quality-attribute trade-off**: Predictability (+) vs authoring ergonomics (-). KPI 3 (90% first-attempt validity) is harder to hit if the user must remember all 10 domains.
- **Verdict**: Rejected as default. Every full-replacement use case is expressible by listing all 10 weights in the override (the file format does not forbid this) — so "full replacement" is a SUBSET of deep-merge behavior, not an alternative requiring its own mode.

### Alternative B — `mergeMode` flag in override (rejected for v1)
- **Pros**: Caller picks per file. Explicit intent.
- **Cons**: Doubles authoring guidance ("when do I use replace vs deep?"); doubles validation logic; doubles the test matrix; new schema field requires schema bump or `additionalProperties: true` (which weakens schema enforcement).
- **Verdict**: Deferred. If a user demonstrates a need for replace-mode, add it in v2 with its own ADR.

### Alternative C — Shallow merge per top-level key (rejected)
- **Pros**: Simpler than deep-merge.
- **Cons**: Override that contains `weights: {data: 30}` would replace the ENTIRE root `weights` object — leaving 9 of 10 domains undefined. Effective sum would be 30, validation would fail, user would be forced to restate all 10. Worst of both worlds (footgun + forced full restatement).
- **Verdict**: Rejected.

### Alternative D — Deep-merge with arrays-merge-by-index (rejected)
- **Pros**: Could merge `statusThresholds.healthy: [8, 10]` with `[9]` -> `[9, 10]`.
- **Cons**: Unintuitive (does index 0 win or merge?); edge cases multiply; nobody asked for this.
- **Verdict**: Rejected. Arrays in this schema are semantically unitary (a [min, max] range), so whole-array replacement is the right default.

## Consequences

### Positive
- Override files can be tiny (3-5 lines) when the user only wants to change one weight.
- Authoring ergonomics align with KPI 3 (90% first-attempt success): less to remember, less to mistype.
- Validation runs on the merged result, so a partial override that produces sum=100 is valid even though the override alone sums to 62.
- No new schema fields; existing schema applies unchanged to override files.
- Deterministic: same merge inputs always produce same output (NFR-2). Sorted-key iteration in the merger guards against pre-3.7 dict-ordering surprises.

### Negative / Trade-offs
- A user who WANTS full replacement (so the override file is self-contained) must list all 10 weights. This is the natural cost of choosing deep-merge as the default. Documentation should note this.
- A subtle override (e.g., `accessibility: 0`) that the user forgot they wrote will be applied silently. Mitigated by the report header (US-03) showing every effective weight inline — invisible overrides are immediately visible in every review.

### Follow-ups
- Functional test for partial override + valid merged sum.
- Functional test for partial override + invalid merged sum -> validation fails with both files named (AC-02.4).
- `init --path` seeds with all 10 weights from the root effective config so the first-time author has a valid starting point.
- DELIVER-wave documentation: `fitness-config.example.json` plus a new `fitness-config.partial-override.example.json` showing minimum-diff style.
