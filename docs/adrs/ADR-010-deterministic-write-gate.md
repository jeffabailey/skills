# ADR-010: A Deterministic Write Gate in the Resolver; the Agent Never Writes the Config

**Status**: Accepted
**Date**: 2026-09-28
**Wave**: DESIGN, fitness-config-init
**Persona**: Morgan (nw-solution-architect)

## Context

Correctness and safety are the top quality attributes. The requirements say: write only after validation (FR-6, BR-5); on an existing file, show a value-level diff and overwrite only on explicit yes (FR-7, BR-4); write nothing when the proposal is identical; the written file equals the reviewed proposal (registry HIGH risk); canonical key order and formatting (NFR-3); no other file touched (NFR-1). If an agent performs these steps with its own file tools, each one is enforced only by prose. They are also invisible to pytest, so the most important ACs could be verified only by manual functional tests.

## Decision

Extend `fitness-config.py init --path <target>` (the existing seed verb) with:

- `--dry-run`: print the baseline (ADR-009).
- `--from -`: read a proposal from stdin, so no temp file lands in the project. With `--dry-run`, it validates (ADR-008 plus completeness), renders canonical bytes, prints the fingerprint (12 hex characters of SHA-256) and the diff against the existing file, and writes nothing.
- `--expect <fp>`: required for any write. The gate recomputes the fingerprint and refuses on mismatch, which guarantees the written bytes are the ones the user reviewed.
- `--force`: required to replace an existing file. Without it, the gate uses exclusive create and reports `refused-exists`.

The write sequence: pre-check the ancestor chain (existing functions), treat an object-equal existing file as `unchanged` (no write), otherwise write a temp file in the target directory and `os.replace` it. Post-write verification re-reads the bytes, compares the fingerprint, and runs `validate_effective` on the new chain. On any failure it restores the prior bytes (or removes the new file). No backup file is kept (NFR-1); the diff plus git is the recovery path.

The agent asks the confirm question and passes `--force` only after `y`/`yes`. The status contract is in data-models.md section 6.

## Alternatives Considered

- **Agent validates a temp file with `validate <tmp>`, then writes with its own tools**: the smallest Python change. Rejected because key order, identical detection, overwrite refusal, and "written == validated" all rest on prose; the temp file lands in the project or in a host-specific scratch dir; and none of it is testable in pytest.
- **New standalone script `scripts/fitness-config-write.py`**: keeps the resolver file smaller. Rejected by ADR-004 alternative D (two CLIs to locate and keep in sync). It would also duplicate the chain and validation functions or import a hyphenated module.
- **New top-level verb `write`/`apply` instead of `init` flags**: clearer name. Rejected, narrowly, because `init --path` already means "create this folder's config and refuse to overwrite". Extending it keeps one creation path and reuses its seed logic. This is the weakest-held choice here; renaming is cheap during DELIVER if the flags read poorly.
- **Keep a `.bak` of the replaced file**: easy undo. Rejected because it creates a second changed path (NFR-1, AC-03.6); git history and the displayed diff cover recovery.

## Consequences

- Positive: every safety AC is enforced in code and testable with pytest and `tmp_path`; agent differences cannot corrupt a config; the proposal-to-disk integrity is cryptographically checked (not a security control; it detects drift).
- Trade-off accepted for a single maintainer: more pytest surface to maintain, in exchange for zero unconfirmed overwrites being provable rather than asserted. The write-gate tests are the critical path for DELIVER.
- Negative: about 150 more lines in a resolver already past ADR-004's 600-LOC threshold (about 930 today). **Follow-up**: open an ADR proposing the `scripts/fitness_config/` package split (with a thin `fitness-config.py` wrapper) after this feature ships.
- Negative: the agent must pass the same JSON twice (dry-run, then write). The fingerprint turns a mismatch into a safe refusal rather than a wrong write.
