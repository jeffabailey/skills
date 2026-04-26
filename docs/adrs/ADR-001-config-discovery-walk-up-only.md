# ADR-001: Config Discovery — Walk-Up Only for v1

**Status**: Accepted
**Date**: 2026-04-25
**Wave**: DESIGN — fitness-config-per-directory
**Persona**: Morgan (nw-solution-architect)

## Context

Devin Park (and engineers like him) maintain multi-module repositories. Today only the repo-root `fitness-config.json` is read; module-specific priorities are ignored. We need a discovery mechanism that, given a review target path, locates the appropriate config(s) to apply.

Three discovery mechanisms are commonly used in CLI tooling:

1. **Walk-up (filesystem hierarchy traversal)** — like `.gitignore`, `.editorconfig`, `.git`. Start from target, ascend parent directories, find first match.
2. **Explicit flag** — `--config <path>` lets the user name an arbitrary file.
3. **Glob pattern** — config maps a path glob (e.g. `infrastructure/modules/*/`) to a config file.

Quality attributes that matter for discovery:
- **Predictability**: user must know which config will apply without reading source.
- **Determinism (NFR-2)**: same target path -> same chosen config across machines.
- **Backward compatibility (NFR-3)**: repos with no overrides behave identically to today.
- **Implementation simplicity**: solo developer; minimum cognitive surface.

## Decision

**v1 supports walk-up discovery only.** The resolver, given a review target path:

1. Canonicalizes the path via `Path.resolve(strict=False)`.
2. Starts at the parent directory if target is a file, else at the directory itself.
3. Ascends one parent at a time, checking each directory for `fitness-config.json`.
4. Stops at the first match, or at the directory containing `.git/`, or at the filesystem root, or after 64 levels (pathological-tree guard).
5. Returns the chain in walk order (deepest match first).

Walk-up applies to v1. v2 may add an explicit `--config <path>` flag if user feedback shows demand.

## Alternatives Considered

### Alternative A — Explicit `--config <path>` flag (rejected for v1)
- **Pros**: Power-user escape hatch; lets the same review be re-run with different configs without filesystem changes.
- **Cons**: Doesn't solve the primary use case (Devin wants implicit discovery from where he runs the review). Adds surface area for ambiguity (what if both `--path` and `--config` are given?). Solo-dev maintenance cost.
- **Verdict**: Defer to v2 if demand emerges. Walk-up alone covers all 8 user stories.

### Alternative B — Glob-based discovery (rejected)
- **Pros**: Most flexible; one root-level mapping file could route reviews of `infrastructure/modules/postgresql/*` to one config and `infrastructure/modules/networking/*` to another, even from a directory that has no override file of its own.
- **Cons**: Two sources of truth (the override file content + the glob mapping); harder to reason about; user must understand BOTH the glob match AND the merge rules. Filesystem walk-up is the de facto Unix idiom — every developer already understands it from `.gitignore`.
- **Verdict**: Rejected. Adds complexity without solving a problem that walk-up doesn't solve.

### Alternative C — Environment variable (`FITNESS_CONFIG_PATH`) (rejected)
- **Pros**: Easy CI override.
- **Cons**: Hidden input; review reproducibility depends on shell state; conflicts with the determinism quality attribute.
- **Verdict**: Rejected. CI can place a config file at the right path instead.

### Alternative D — Sibling-directory search (rejected)
- **Pros**: Could find configs across the tree (e.g. `infrastructure/configs/postgresql.json` for `infrastructure/modules/postgresql/`).
- **Cons**: Unbounded search space; ambiguous when multiple matches exist; not how `.gitignore` / `.editorconfig` work; violates user's mental model.
- **Verdict**: Rejected.

## Consequences

### Positive
- Matches Devin's mental model (he already understands `.gitignore` walk-up).
- Bounded performance: at most `depth` file reads per resolution (NFR-1 budget easy to meet).
- Deterministic: filesystem hierarchy is the only input; same input -> same output (NFR-2).
- Zero impact on repos without overrides: walk-up from any path still finds the root config and stops there (NFR-3).
- Trivially testable with in-memory filesystem fixtures: walk-up is a pure function of `(target_path, file_existence_map)`.

### Negative / Trade-offs
- Cannot route reviews to configs outside the target's ancestor chain. Mitigated by the fact that the override file is co-located with the module it governs — the natural place to put it.
- No way to share a config across modules without copying it (or symlinking). Mitigated by the fact that the root config provides shared defaults; per-module files only need to redefine differences.
- Symlink edge case: a symlink in the target's path could change which directory chain is walked. Mitigated by `Path.resolve(strict=False)` canonicalization before walk-up.

### Follow-ups
- Functional test: walk-up determinism check (run twice on same input, assert byte-identical chain).
- Functional test: pathological-tree guard fires at 64 levels with a clear error.
- Documentation: SETUP.md mentions "drop a `fitness-config.json` in any directory; reviews scoped to that subtree pick it up."
