# ATDD Infrastructure Policy

Per `nw-distill` § Project Infrastructure Policy. One file per project. Apply-if-exists; write-if-absent; rewrite with `--policy=fresh`. Git history is the audit trail.

Bootstrapped by DISTILL for `fitness-config-init` (2026-09-28) from the conventions already used by `tests/acceptance/fitness-config-per-directory/` (Strategy C, real services).

## Driving
| Port | Mechanism | Note |
|---|---|---|
| Resolver CLI (`scripts/fitness-config.py`) | real subprocess (`sys.executable`), cwd = project anchor under `tmp_path`, stdin for proposals | clean env: PATH, HOME, LANG only |
| Agent skill (`skills/*/SKILL.md` executed by an agent host) | not executable under pytest: static artifact checks + `@manual` agent-eval scenarios | recorded in `tests/functional-tests.md` |

## Driven internal (real)
| Port | Mechanism | Note |
|---|---|---|
| Filesystem (config chain, write gate) | real files under pytest `tmp_path` | read-only folders via chmod; skipped when running as root |
| `git` CLI (anchor lookup) | not used by the resolver; the skill resolves the anchor and passes cwd | acceptance tests set cwd = anchor directly |

## Driven external / non-deterministic (fake)
| Port | Fake | Note |
|---|---|---|
| review-full skill (full mode) | none at pytest level; `@manual` agent-eval with injected domain failure | resolver has no dependency on it |
| `jsonschema` (dev-only parity check) | real library when installed; `pytest.importorskip` otherwise | `@requires_external` |
