# Technology Stack: fitness-config-init

No new technology. Everything below already exists in the repo or the Python standard library.

| Layer | Choice | License | Rationale | Alternatives rejected |
|---|---|---|---|---|
| Skill format | Agent Skills `SKILL.md` + `references/*.md` | n/a (open format) | Same packaging as the sibling skills; works in the Claude Code plugin and the Agent Plugin | Slash-command file (not portable to Agent Plugin hosts); standalone Python wizard (cannot do evidence judgment) |
| Deterministic logic | Python 3 stdlib (`json`, `hashlib`, `os.replace`, `tempfile`, `argparse`, `pathlib`) in `scripts/fitness-config.py` | PSF | Already the resolver runtime; D-10 forbids new runtime deps; ADR-004 single file | New `scripts/fitness-config-init.py` (a second CLI to locate and keep in sync, rejected by ADR-004 alt. D); shell + `jq` (not on Windows by default) |
| Schema validation at runtime | Extended stdlib `validate_config` (ADR-008) | PSF | One gate, no dependency | `jsonschema` at runtime (new dependency; unavailable in many agent sandboxes) |
| Schema parity check | `jsonschema` (optional, dev/CI only; test skips when absent) | MIT | Proves the stdlib validator never accepts what the schema rejects | Hand-maintained duplicate assertions only (drift goes undetected) |
| Tests | pytest (existing `tests/unit`, `tests/acceptance` layout, `pyproject.toml` config) | MIT | Already used for the resolver | unittest (inconsistent with the existing suite) |
| Repo anchor | `git rev-parse --show-toplevel` (optional) | GPL-2.0 (tool invocation only, not linked) | Matches how users think of "repo root"; read-only | Walk for `.git` in Python (duplicates git; misses worktrees and submodules) |
| Architecture enforcement | Existing `fitness-config.py audit` verb (extended glob) + pytest fitness tests | n/a | ADR-004/006 chose grep audit over import-linter at this scale | import-linter (single file; nothing to contract) |

Runtime floor: whatever the resolver already requires. The header says 3.6+, but it already uses `dataclasses` (3.7+), so that header claim is stale doc debt. The additions must not raise the floor further.
