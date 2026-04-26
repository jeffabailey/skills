# ADR-005: Broad-Scope Reviews Use Only the Root Config

**Status**: Accepted
**Date**: 2026-04-25
**Wave**: DESIGN — fitness-config-per-directory
**Persona**: Morgan (nw-solution-architect)

## Context

DQ-5 from the DISCUSS wave: when a review's target path is at or above the location of one or more override configs, what config(s) apply?

Three concrete scenarios illustrate the question:

1. **Review at repo root, with a `infrastructure/modules/postgresql/fitness-config.json` override present.** Walk-up from the root reaches no override; only root config applies. (Easy case.)
2. **Review of `infrastructure/modules/`, with overrides in `infrastructure/modules/postgresql/`, `infrastructure/modules/networking/`, and `infrastructure/modules/redis/`.** Multiple downstream overrides exist. Which applies? Or do we apply none, or all, or merge them?
3. **Review of `infrastructure/modules/postgresql/scripts/`, where `infrastructure/modules/postgresql/fitness-config.json` exists.** This is just a deeper case of walk-up — already covered by ADR-001.

Scenario 2 is the genuinely ambiguous case.

Quality attributes:
- **Predictability**: user must know in advance which config applies for a given scope.
- **Determinism (NFR-2)**: same scope -> same config.
- **Provenance (BR-4)**: report header must accurately name the applied config.
- **Implementation simplicity**: more sophisticated rules require more test cases.

## Decision

**v1: When the review target path is AT OR ABOVE the location of any override, the resolver returns only the root config (or built-in defaults if no root exists). Subtree overrides are ignored when the review scope is broader than the override's directory.**

Concretely:

| Review target | Walk-up result |
|---------------|----------------|
| `<repo>/` (repo root) | `[<repo>/fitness-config.json]` if root exists, else `[]` |
| `infrastructure/modules/` | `[<repo>/fitness-config.json]` if root exists, else `[]` (postgresql/networking/redis overrides are NOT collected) |
| `infrastructure/modules/postgresql/` | `[<...>/postgresql/fitness-config.json, <repo>/fitness-config.json]` |
| `infrastructure/modules/postgresql/scripts/migrate.sh` | Same as above (walks up to postgresql/) |

The walk-up algorithm (ADR-001) naturally produces this behavior: it only ascends parents of the target, never descends into siblings or subdirectories of the target. So scenario 2 is not a special case in the implementation — it falls out of the walk-up rule.

The report header for a broad-scope review includes a footnote (per AC-03.7):
> "Subtree overrides apply only when the review scope is within their directory. Modules with their own fitness-config.json: <list of paths discovered separately for documentation, not used in scoring>."

Producing that footnote requires a separate (cheap, opt-in) directory enumeration that is OUT OF SCOPE for v1's resolver. The skill prompt may produce the list via its own filesystem inspection if and when it wants to display the footnote; the resolver itself does not return it.

## Alternatives Considered

### Alternative A — Per-file resolution within broad scope (rejected)
- **Concept**: For a review of `infrastructure/modules/`, the resolver returns a MAP from each reviewed file to its effective config. Each file gets its own walk-up resolution; scoring is per-file with per-file weights; an aggregated overall score is then computed.
- **Pros**: Most accurate; every file gets the priorities its module specifies.
- **Cons**: Massive complexity increase. The resolver returns a structure, not a single config. The aggregator must compute a meaningful "overall" score across files weighted by potentially-different weights. The report header has to render N config lines, not one. Impossible to fit in v1 scope.
- **Quality-attribute trade-off**: Correctness (++) vs simplicity (--). Adoption (-) because users will not understand a report with mixed weights.
- **Verdict**: Rejected for v1. Reasonable v3+ feature once the basic mechanism has proven valuable.

### Alternative B — Use the root config but EMIT WARNINGS naming all sub-overrides (rejected)
- **Pros**: User aware that overrides exist but were not used.
- **Cons**: Warnings clutter output; user has no actionable response (the warning is informational only). The report header footnote (per AC-03.7) covers the same need with less noise.
- **Verdict**: Rejected. Footnote is the right channel.

### Alternative C — Refuse to run broad-scope reviews when overrides exist below (rejected)
- **Pros**: Forces user to choose a specific module to review.
- **Cons**: Breaks the obvious use case "run review-full at the repo root". Hostile UX.
- **Verdict**: Rejected.

### Alternative D — Merge ALL overrides found in the subtree into a single effective config (rejected)
- **Pros**: Some semblance of using the override information.
- **Cons**: Merge order is arbitrary (alphabetical? depth-first?). Result is meaningless because the overrides reflect priorities specific to their respective modules — combining `postgresql`'s `data=30` with `networking`'s `security=30` produces a config nobody asked for. Violates predictability.
- **Verdict**: Rejected.

## Consequences

### Positive
- Walk-up algorithm (ADR-001) covers all cases without special handling. Implementation is minimal.
- Predictable: the user can always answer "which config applies" by tracing the walk-up from their target path.
- Compatible with the report header footnote (AC-03.7) for transparency.
- Backward compatible: `review-full` at repo root behaves exactly like today (NFR-3).

### Negative / Trade-offs
- A user who runs `review-full` at the repo root with overrides scattered in subtrees gets a "generic" review. Mitigation: the report header footnote names the discovered overrides and explains they were not applied; user can re-run scoped to a specific module if they want module-specific weights.
- The discovered-overrides list (for the footnote) is computed outside the resolver. This is a tiny duplication of "find all fitness-config.json files in the subtree" logic, but it is opt-in and used only for documentation in the report header.

### Follow-ups
- Skill prompt for `review-full` (in DELIVER) includes the footnote-generation step: enumerate `fitness-config.json` files within the review scope (excluding the chain returned by the resolver) and list them in a "Subtree overrides not applied" footnote.
- v2+ candidate: per-file resolution within broad scope (Alternative A). Re-evaluate after v1 ships and adoption data exists.
- Functional test: review at repo root with sub-overrides present -> source chain contains only root; report includes the footnote.
- Documentation: README and SETUP.md note "subtree overrides apply only when review scope is within their directory."
