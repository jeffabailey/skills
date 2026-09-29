# ADR-012: Split the Resolver into a `scripts/fitness_config/` Package

**Status**: Accepted
**Date**: 2026-09-29
**Wave**: DELIVER (refactoring pass), fitness-config-init
**Supersedes**: ADR-004's single-file decision. ADR-004's CLI contract still holds.

## Context

ADR-004 kept the resolver in one file, `scripts/fitness-config.py`, and set about 600 lines as the point to split it into a package. The file passed that point during fitness-config-per-directory (about 800 lines). ADR-010 then added the write gate and planned this split as a follow-up once fitness-config-init shipped. At the end of fitness-config-init DELIVER, the file had 1404 lines and eight responsibilities: defaults, chain resolution, validation, rendering, the write gate, filesystem adapters, the CI audit and the CLI. They were separated only by comment banners.

At that size the single file had three costs:

- Readers had to scroll past unrelated groups to follow one flow, such as the write gate.
- Unit tests loaded the file through `importlib.util.spec_from_file_location`, because its hyphenated name cannot be imported.
- Nothing in the file's structure showed that the pure functions must not call the filesystem.

The user chose to split the package during the DELIVER refactoring pass, not in a later feature.

## Decision

Split the logic into a stdlib-only package beside the script, with one module per responsibility:

| Module | Owns | Depends on |
|---|---|---|
| `model.py` | `DEFAULT_*`, `SECTION_DEFAULTS`, `CONFIG_FILENAME`, `SUPPORTED_SCHEMA_VERSION`, `WEIGHTS_SUM_TOLERANCE` | nothing |
| `resolution.py` | walk-up chain, anchored chain (ADR-009), deep merge (ADR-002), effective and seed configs | model |
| `validation.py` | schema versions (ADR-003), effective sum, strict per-file rules and completeness (ADR-008) | model |
| `render.py` | `show --path` report, canonical bytes, fingerprint, value diff | model |
| `write_gate.py` | `GateStatus`, `GateOutcome`, the `ConfigFile` port, `check_proposal`, `save_reviewed_proposal` (ADR-010) | resolution, render, validation |
| `adapters.py` | config reads, the `ConfigFile` adapter over a real file (temp file, fsync, link or replace) | write_gate (port types only) |
| `audit.py` | the `audit` CI gate | nothing |
| `cli.py` | argparse, the `cmd_*` verbs, printing, exit codes | everything above |

Dependencies point inward. `cli` is the only module that prints or chooses exit codes. `adapters` is the only module that writes files. `model`, `resolution`, `validation`, `render` and `write_gate` do no I/O. The exceptions are the path probes in `walk_up_chain_with_status` and calls made through the injected `ConfigFile` port.

`scripts/fitness-config.py` stays as the public entry point. It is a thin stub that puts its own directory on `sys.path`, found through `__file__` rather than the working directory, and calls `fitness_config.cli.main()`. Skills (`${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py`), CI (`python3 scripts/fitness-config.py validate|init|audit`) and the acceptance tests (which run it as a subprocess) keep working unchanged. Unit tests import the package modules directly.

The runtime floor is Python 3.10, as declared in `pyproject.toml`. The script header used to claim 3.6+, which was out of date.

## Alternatives Considered

- **Keep the single file and raise ADR-004's threshold.** This costs nothing now, but the three problems above remain and keep getting worse. Rejected.
- **Rename the script to `scripts/fitness_config.py` (an importable module) and add a wrapper.** This fixes imports but still leaves 1400 lines in one module. Rejected.
- **Add `import-linter` to enforce the dependency rule.** ADR-004 and ADR-006 considered it. It is a new dev dependency for eight modules, and the rule is simple enough to check in review. Deferred.

## Consequences

- Positive: each responsibility fits on a screen. The largest module, `cli.py`, has about 340 lines, and the largest function has 30 lines, down from 81. The dependency direction is visible in the imports.
- Positive: unit tests import `fitness_config.<module>` with no `importlib` workaround. The `tests/unit/fitness_config/_loader.py` helper only adds `scripts/` to `sys.path`.
- Positive: shipping is unchanged. The plugin (`.claude-plugin/marketplace.json`, `"source": "./"`) ships the whole repository. `scripts/install-skills.sh` symlinks `skills/*` back to the repository, so `${CLAUDE_SKILL_DIR}/../../scripts/` resolves to the real `scripts/` folder and finds the package. No install step copies the script by itself.
- Negative: the package must stay beside `scripts/fitness-config.py`. Copying the script alone breaks it with an `ImportError` at startup, not with wrong results. The README structure section lists both.
- Neutral: BR-5 enforcement is unchanged. The `audit` verb still scans skill prose. The repository-wide "no direct `fitness-config.json` reads" test still exempts only `scripts/fitness-config.py`, and the package modules pass it: they read configs only through `adapters.read_config`, and no line pairs `json.load` or `open` with the file name.
