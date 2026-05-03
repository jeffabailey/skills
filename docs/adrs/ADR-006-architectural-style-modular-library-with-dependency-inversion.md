# ADR-006: Architectural Style — Modular Library with Dependency Inversion at the I/O Boundary

**Status**: Accepted
**Date**: 2026-04-25
**Wave**: DESIGN — fitness-config-per-directory
**Persona**: Morgan (nw-solution-architect)

## Context

The feature adds a config resolver, merger, validator, and reporter to the existing `scripts/fitness-config.py`. We need an architectural style that:

- Makes the core logic (resolver/merger/validator/reporter) trivially unit-testable without filesystem fixtures.
- Keeps the I/O boundary explicit so test substitution is straightforward.
- Works at ~300 LOC of Python without imposing class-hierarchy ceremony.
- Aligns with the existing procedural-functional shape of `scripts/fitness-config.py`.
- Gives a clear answer to "where does the resolver call go" for skill prompts and CLI commands.

Style options surveyed (from `architectural-styles-tradeoffs.md`):
- Layered / N-tier
- Hexagonal / Clean / Onion (DIP-based)
- Modular monolith
- Vertical slice
- Pipe and filter
- Microservices
- Event-driven / CQRS

## Decision

**Adopt a modular library with dependency inversion at the I/O boundary** — a hexagonal-lite style scaled appropriately for ~300 LOC of Python.

Specifics:
- **Core (pure functions)**: resolver orchestration, merger, validator, reporter. No filesystem access. No CLI access. No global state.
- **Driving port**: CLI command functions (`cmd_validate`, `cmd_init`, `cmd_show`). Translate user input to core function calls; translate core output to stdout/exit codes.
- **Driven port**: filesystem reader (`_read_config(path) -> dict | None`). The resolver accepts the reader as a parameter (default = real filesystem reader); tests pass an in-memory map.
- **No explicit `Protocol` or ABC classes**: the "port" is just a callable signature. Python's duck typing makes formal interface declarations unnecessary at this scale.
- **Single-file implementation in v1** (per ADR-004), with comment-banner-separated logical groupings. Future package split possible.

This is the same pattern family as Hexagonal / Clean / Onion (inward-pointing dependencies, ports for I/O isolation), expressed in Python idioms appropriate for the project size.

## Alternatives Considered

### Alternative A — Layered architecture (rejected)
- **Pros**: Familiar; simple top-to-bottom dependency direction.
- **Cons**: Doesn't naturally express the test-substitution boundary. A "data access layer" abstraction would be one function (`_read_config`) — calling it a "layer" is overkill. No clear win over the modular-library approach.
- **Verdict**: Rejected. The modular-library / hexagonal-lite naming better reflects the actual structure.

### Alternative B — Pure procedural script (no internal boundaries) (rejected)
- **Pros**: Simplest; least ceremony.
- **Cons**: Resolver tests need real filesystem fixtures (slow, brittle, harder to write). Refactoring becomes risky because internal structure is implicit. Solo maintainer benefits from the small explicit boundary.
- **Verdict**: Rejected. The cost of the I/O boundary parameter is one extra function argument; the benefit (testability) is large.

### Alternative C — Full-blown Hexagonal with `abc.ABC` ports and adapter classes (rejected)
- **Pros**: Formal, explicit, statically checkable.
- **Cons**: For ~300 LOC of stdlib Python, this is ceremony with no payoff. Class hierarchy adds reading overhead. Python's duck typing already provides the substitution capability without the ABC.
- **Verdict**: Rejected. Too heavy for the scale.

### Alternative D — Vertical slice (per-CLI-subcommand modules) (rejected)
- **Pros**: Per-feature organization.
- **Cons**: Each CLI subcommand would have its own resolver/merger copy or its own import path; defeats BR-5 (single source of truth for merge semantics). The cross-cutting concern (resolver) dominates over per-feature variation.
- **Verdict**: Rejected.

### Alternative E — Pipe and filter (rejected)
- **Pros**: Could model resolver -> merger -> validator -> reporter as a pipeline.
- **Cons**: The "pipeline" is a single linear call chain that is naturally expressed as nested function calls. Pipe-and-filter is for systems with reorderable independent stages; we have a fixed sequence with shared structured state.
- **Verdict**: Rejected.

## Consequences

### Positive
- Pure functions for merger/validator/reporter are unit-testable without any filesystem mocking.
- The single I/O boundary (`_read_config`) is substitutable via parameter for resolver tests.
- The CLI is a thin shell: argument parsing + dispatch + exit code. No business logic, so CLI tests can focus on I/O contract (exit codes, stdout shape) rather than algorithm correctness.
- Aligns with the existing `scripts/fitness-config.py` style (procedural-functional with pure data transforms).
- Natural fit with the ISO 25010 quality priorities for this feature: testability, maintainability, determinism dominate.

### Negative / Trade-offs
- The "ports and adapters" vocabulary is overkill for one I/O point. We use it loosely as a conceptual frame, not as a strict naming convention. Risk: a reader unfamiliar with the project might expect formal `Port` classes; mitigated by `architecture-design.md` explicitly naming the style "modular library with dependency inversion at the I/O boundary, hexagonal-lite in spirit, no formal Port/Adapter classes."
- Without formal `Protocol` classes, IDE/static-analysis support for the reader-substitution pattern is weaker. Mitigated by type hints (`Callable[[Path], dict | None]`) and small surface area (one substitution point).

### Follow-ups
- Architecture enforcement via grep audit (`architecture-design.md` section 11) implements BR-5/FR-7 — the only architectural rule that matters for this feature.
- DELIVER wave (software-crafter): write unit tests for merger/validator/reporter as pure functions; write resolver tests using an in-memory reader fixture; write end-to-end CLI tests using `subprocess` or `pytest`'s `CliRunner` equivalent for argparse.
- If the file grows past ~600 LOC, revisit ADR-004 (single file vs package) and consider import-linter for explicit contracts. The architectural style choice would not change.
