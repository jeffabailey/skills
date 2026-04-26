# ADR-004: Resolver Lives in `scripts/fitness-config.py` as a Single File

**Status**: Accepted
**Date**: 2026-04-25
**Wave**: DESIGN — fitness-config-per-directory
**Persona**: Morgan (nw-solution-architect)

## Context

The resolver, merger, validator, and reporter together form a small library (~300 LOC of Python). They must be:

- Reachable by every consumer (CLI, future Python tests, and indirectly by every `review-*/SKILL.md` via the CLI shell invocation).
- The single source of truth for effective config (BR-5 / FR-7).
- Maintainable by a solo developer.

Three reasonable layouts:

1. **Single file** — keep `scripts/fitness-config.py` as today; add the new functions inside it.
2. **Package** — split into `scripts/fitness_config/{__init__.py, resolver.py, merger.py, validator.py, reporter.py}`.
3. **Embedded in skill prompts** — copy resolver logic into each `SKILL.md` so the agent can run it inline.

Quality attributes:
- **Maintainability (solo dev)**: fewer files to navigate is better at this scale.
- **Single-source-of-truth (BR-5)**: only ONE place reads `fitness-config.json`.
- **Testability**: pure functions must be importable from a test file.
- **Backward compatibility**: today's invocation `python3 scripts/fitness-config.py validate` must still work.

## Decision

**v1 keeps `scripts/fitness-config.py` as a single file.** The new resolver, merger, validator, and reporter functions live inside it as logical groupings (function clusters with comment-banner separators), not as separate modules.

Skill prompts (`src/review-*/SKILL.md`, `.github/fitness-review-prompt.md`) call the script as a CLI subprocess: `python3 <skills>/scripts/fitness-config.py show --path <target>`. They do NOT import functions from the script and do NOT inline resolver logic.

The internal logical groupings inside the script are:

```text
# === Defaults =============================================
DEFAULT_WEIGHTS, DEFAULT_STATUS, ...

# === I/O Boundary =========================================
def _read_config(path): ...

# === Resolver =============================================
def resolve_effective_config(target_path, *, reader=_read_config): ...
def _walk_up_chain(start_dir, reader): ...

# === Merger ===============================================
def deep_merge_chain(chain, defaults): ...

# === Validator ============================================
def validate_effective(effective, raw_configs, source_chain): ...
def validate_config(data): ...   # legacy, kept for backward compat

# === Reporter =============================================
def render_show_output(result): ...
def render_header_lines(result, scope): ...
def render_validation_error(result): ...
def render_inline_weights(weights): ...

# === CLI Commands =========================================
def cmd_validate(...): ...
def cmd_init(...): ...
def cmd_show(...): ...

# === Entry point ==========================================
def main(): ...
```

Future work: if the file grows past ~600 LOC OR a second consumer (a non-CLI Python entry point) emerges, split into `scripts/fitness_config/` package and adopt `import-linter` for explicit dependency contracts.

## Alternatives Considered

### Alternative A — Package layout from the start (rejected for v1)
- **Pros**: Clean module boundaries; per-module test files; `import-linter` enforces architecture rules formally.
- **Cons**: 5 files for ~300 LOC; navigation overhead; existing `python3 scripts/fitness-config.py validate` invocation pattern keeps working only if `scripts/fitness-config.py` is preserved as a thin wrapper. More moving parts for solo maintainer.
- **Quality-attribute trade-off**: Maintainability (-) vs formal enforcement (+). At this scale, comment banners + a grep audit step provide enforcement equivalent to import-linter for far less ceremony.
- **Verdict**: Defer until size or complexity justifies the split.

### Alternative B — Embed resolver in each SKILL.md (rejected)
- **Pros**: No subprocess call; no JSON parsing in the agent.
- **Cons**: Massively violates BR-5 (single source of truth). 11 SKILL.md files would each need their own copy of the resolver logic, and they would drift. The agent (Claude Code, Copilot, Codex) is good at following instructions but cannot reliably reproduce the same merge logic across 11 prompts deterministically. NFR-2 (determinism) would be impossible to guarantee.
- **Verdict**: Rejected outright. This would be the worst possible architectural choice.

### Alternative C — Resolver as a Python library installed via pip (rejected)
- **Pros**: Reusable across repos.
- **Cons**: Adds packaging burden; the resolver is intrinsically tied to this skills repo's schema; no other repo has reason to consume it.
- **Verdict**: Rejected. YAGNI.

### Alternative D — Separate `scripts/fitness_resolver.py` file alongside the existing script (rejected)
- **Pros**: Splits new code from old.
- **Cons**: Two scripts to maintain; users now need to know which to call when; CLI entry point becomes ambiguous; no clear win over either single-file or package layouts.
- **Verdict**: Rejected.

## Consequences

### Positive
- One file to navigate for the entire feature. Solo maintainer reads it top-to-bottom.
- Backward-compatible CLI invocation: `python3 scripts/fitness-config.py validate` works unchanged.
- Clear logical groupings via comment banners give the same conceptual structure as a package without the file-count cost.
- Testable: a `tests/test_fitness_config.py` can `from scripts.fitness_config import ...` (with a small `sys.path` shim) and unit-test pure functions.
- Compatible with the BR-5 enforcement: `grep "json\.load.*fitness-config\.json"` outside this script catches violations.

### Negative / Trade-offs
- ~600 LOC is the soft size threshold beyond which a single file becomes unwieldy. We are starting at ~150 today and adding ~150 more; we should be at ~300, well under the threshold.
- Pytest import gymnastics: `scripts/fitness-config.py` has a hyphen in its filename, which is not a legal Python identifier, so direct `import scripts.fitness-config` fails. Mitigation: tests can either use `importlib` (`importlib.import_module("scripts.fitness-config")`) or rename the file to `scripts/fitness_config.py` with a wrapper script `scripts/fitness-config.py` that calls it. Software-crafter decides during DELIVER. (Prefer the second option.)

### Follow-ups
- During DELIVER, consider renaming `scripts/fitness-config.py` to `scripts/fitness_config.py` with a tiny wrapper at `scripts/fitness-config.py` that re-exports `main()` for backward-compat, OR using `importlib` in tests. This is a tactical choice for software-crafter, not a design decision.
- If the file crosses 600 LOC, open a follow-up ADR proposing the package split.
- CI grep audit step (per `architecture-design.md` section 11) implements BR-5 / FR-7 enforcement.
