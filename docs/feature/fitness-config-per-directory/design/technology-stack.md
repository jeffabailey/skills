# Technology Stack — fitness-config-per-directory

**Wave**: DESIGN
**Date**: 2026-04-25

This feature adds no new runtime dependencies. The choices below cover (1) what we keep, (2) what we explicitly reject, and (3) what we recommend for delivery-time test/lint tooling.

---

## 1. Runtime stack (kept)

| Component | Version | License | Rationale | Alternatives considered |
|-----------|---------|---------|-----------|-------------------------|
| Python | 3.6+ | PSF License (OSS) | Already in use by `scripts/fitness-config.py`; matches NFR-5 (cross-platform: macOS, Linux, Windows); stdlib-only path keeps install footprint zero | Node.js / Bash — both rejected: existing script is Python; switching would be a rewrite for no benefit |
| `json` (stdlib) | bundled | PSF | Already used; lossless round-trip of fitness-config files | `simplejson`, `orjson` — rejected: external deps; perf is not a constraint at this scale |
| `pathlib.Path` (stdlib) | bundled | PSF | Already used; correct cross-platform path semantics including symlink resolution | `os.path` — works but `pathlib` already chosen and gives us `.resolve()` for free |
| `argparse` (stdlib) | bundled | PSF | Already used; sufficient for adding `--path` flag to existing subcommands | `click`, `typer` — rejected: external deps; current arg surface is small enough |
| `sys` (stdlib) | bundled | PSF | Already used for stderr and exit codes | n/a |

**Total new runtime dependencies: 0.**

---

## 2. Schema (kept, not modified for v1)

| Artifact | Decision |
|---------|----------|
| `fitness-config.schema.json` | Unchanged. The same schema applies to root and override files. No `mergeMode` field added in v1 (deferred — see ADR-002). The schema's `additionalProperties: false` on the root and `weights` already prevents typos in keys, which is enough validation for override files. |
| `fitness-config.example.json` | Unchanged for v1. A new `fitness-config.override.example.json` may be added in DELIVER as a partial-override sample, but it is not architecturally required. |

We deliberately do NOT introduce runtime JSON Schema validation (e.g., `jsonschema` package). The existing `validate_config` function does manual checks for the small fixed set of constraints that matter (sum=100, version, confidence threshold range). Adding `jsonschema` would be a new dependency for marginal value at this scale.

---

## 3. Development / test tooling (recommended for DELIVER)

| Component | License | Why recommended |
|-----------|---------|----------------|
| `pytest` | MIT | De facto Python test framework; runs the pure-function unit tests for merge/validate/render and the CLI end-to-end tests. |
| `pytest-tmp_path` (built-in fixture) | MIT | Provides isolated temporary directories for walk-up integration tests. |
| `coverage` (optional) | Apache 2.0 | If line coverage gating is desired; not architecturally required. |

These are not yet in `requirements.txt` because the repo has no Python test suite today. DELIVER wave (software-crafter) decides whether to add a `requirements-dev.txt` or use `pip install pytest` ad-hoc in CI.

---

## 4. Architecture enforcement tooling

| Component | License | Recommendation |
|-----------|---------|----------------|
| `grep` (POSIX) | n/a | **Recommended for v1.** A single CI step greps for `json.load.*fitness-config\.json` outside `scripts/fitness-config.py` and fails the build if any match is found. Implements BR-5 / FR-7 enforcement with zero new tooling. |
| `import-linter` | BSD-2-Clause | Recommended only if `scripts/fitness-config.py` is later split into a `scripts/fitness_config/` package (per ADR-004 future work). Not needed for v1. |
| `pytest-archon` | MIT | Alternative to import-linter; pytest-native architecture rules. Same v2-only consideration. |

---

## 5. Explicitly rejected

| Technology | Why rejected |
|-----------|--------------|
| **TOML / YAML configs** | Schema is already JSON; users already know the shape; no benefit to switching format. |
| **Pydantic / dataclasses-json / msgspec** | Adds runtime dependency; existing manual validation in `validate_config` is sufficient and consistent with stdlib-only constraint. |
| **Click / Typer** | Adds runtime dependency; argparse is sufficient for ~5 flags. |
| **Plugin/entry-point system for config providers** | Resume-driven complexity. There is exactly one provider (the JSON file) and no roadmap for a second. |
| **Long-running config daemon** | Absurd for a local CLI; introduces operational burden. |
| **Watchdog-based config hot-reload** | The CLI runs to completion each call. No long-running state to invalidate. |
| **JSON Schema runtime validator (`jsonschema` package)** | Adds dependency; existing manual checks cover what matters; schema file is documentation for users, not runtime contract. |

---

## 6. Cross-platform notes (NFR-5)

| Concern | Handling |
|---------|----------|
| Path separators | `pathlib.Path` handles transparently. |
| Walk-up termination | Stop at filesystem root OR at first directory containing `.git/` (whichever comes first). On Windows, root is the drive letter. |
| Symlinks | `Path.resolve(strict=False)` canonicalizes before walking up — same target file produces same chain regardless of how the user navigates to it. |
| Line endings in JSON | `json` module is line-ending-agnostic for parsing; for `init` writes, use the platform default (no explicit `\n`-only override). |
| File encoding | `encoding="utf-8"` already used by existing `load`. Continue. |

---

## 7. Open source compliance

All chosen technologies are OSS under permissive licenses (PSF, MIT, BSD, Apache 2.0). No copyleft, no proprietary, no commercial-grade SaaS dependencies. Repository remains Unlicense (public domain) per existing license declaration.
