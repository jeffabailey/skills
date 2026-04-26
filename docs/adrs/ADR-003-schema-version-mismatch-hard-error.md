# ADR-003: Schema Version Mismatch is a Hard Error

**Status**: Accepted
**Date**: 2026-04-25
**Wave**: DESIGN — fitness-config-per-directory
**Persona**: Morgan (nw-solution-architect)

## Context

The `fitness-config.schema.json` declares `"version": { "const": 1 }`. Every config file declares `"version": 1`. When v2 ships in the future, root and child configs in the same repo could declare different versions during a transition period.

The resolver must decide what to do when the chain contains files with mismatched `version` values. Three approaches:

1. **Hard error** — fail fast; refuse to merge; require user to fix.
2. **Warn-and-proceed** — log a warning; treat the higher-version file as authoritative; continue.
3. **Use-child / use-root override** — silent precedence rule.

Quality attributes:
- **Determinism (NFR-2)**: same chain -> same outcome.
- **Fail-closed (NFR-4)**: validation failures must block reviews, not produce silent fallbacks.
- **Correctness**: a v2 config might use a schema field absent from v1; merging across versions could produce nonsense.
- **Maintainer trust**: users must trust that "review ran successfully" means "the config they expected was applied".

## Decision

**Schema version mismatch is a hard error.** The resolver:

1. Reads `version` from every config in the chain.
2. If any two values differ, returns `valid=False` with an error message naming all files involved, the version each declares, and the supported version.
3. Exits the CLI with code 1 before any review work is dispatched.

The resolver does NOT attempt automatic migration, downgrade, or coercion. The user must update one or both files to a consistent version.

## Alternatives Considered

### Alternative A — Warn-and-proceed (rejected)
- **Pros**: Less disruptive during version transitions; review still runs.
- **Cons**: Defeats the purpose of versioning. A warning in CLI output is easy to miss; the user runs the review, sees a score, and never realizes the override was ignored or partially applied. Violates NFR-4 (fail-closed). Violates BR-4 (provenance always visible — and version mismatch IS a provenance failure).
- **Verdict**: Rejected.

### Alternative B — Use higher version, ignore lower (rejected)
- **Pros**: Reasonable-sounding default.
- **Cons**: Silent. The user does not know the lower-version file was ignored. May be wrong: maybe the user is in the middle of upgrading the root and forgot the child. Maybe the higher version drops a key the lower version relied on.
- **Verdict**: Rejected.

### Alternative C — Use lower version, attempt merge (rejected)
- **Pros**: Conservative.
- **Cons**: Loses information. If the higher version uses a field absent from the lower schema, that field is silently discarded.
- **Verdict**: Rejected.

### Alternative D — Configurable behavior via flag (rejected)
- **Pros**: User chooses.
- **Cons**: Yet another knob. Most users will not configure it; default behavior dominates.
- **Verdict**: Rejected. If a future version of this feature needs configurable handling (e.g., during a planned migration), add it then.

## Consequences

### Positive
- Surfaces version drift immediately and unambiguously. The user sees both files and both versions in the error message.
- Aligns with NFR-4 (fail-closed) and BR-4 (provenance visible).
- Forces explicit action when the schema evolves — preventing silent semantic drift across a multi-branch repo.
- Simple to implement and test (compare version values; emit error if not all equal).

### Negative / Trade-offs
- During a future v1->v2 migration, every override file must be updated before the root, OR a migration tool must be provided. Mitigation: when v2 is designed, plan the migration as part of that work; document migration procedure in the ADR for v2.
- A typo (`"version": 11` instead of `"version": 1`) produces an obscure-looking error. Mitigation: error message includes "supported version: 1" so the typo is obvious.

### Follow-ups
- Functional test: deliberate v1/v2 mismatch -> exit code 1, both files named (AC-07.4), supported version stated (AC-07.5).
- Documentation: when (or if) v2 is introduced, write a companion ADR for the migration strategy and reference this ADR.
- The validator emits the version-mismatch error BEFORE attempting merge. Order matters: do not partially merge then bail.
