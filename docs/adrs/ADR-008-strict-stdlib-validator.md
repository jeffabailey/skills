# ADR-008: Extend the Stdlib Validator to Mirror the Schema

**Status**: Accepted
**Date**: 2026-09-28
**Wave**: DESIGN, fitness-config-init
**Persona**: Morgan (nw-solution-architect)

## Context

FR-4 and BR-5 require every written config to pass both `fitness-config.schema.json` and the resolver validator. The schema needs `jsonschema`, which is not stdlib and is rejected as a runtime dependency (D-10 of fitness-config-per-directory). Today `validate_config` checks only `version` is an int, the weights sum, and the `confidenceThreshold` range. It accepts unknown weight names, negative or over-100 weights, and booleans (`True` counts as 1), and it crashes on a non-numeric threshold. The user decided (DQ-6) to extend the stdlib validator to check weight names against the known domains and the 0-100 range, and to refuse to write when python3 is unavailable.

## Decision

1. `validate_config` additionally enforces: `version == 1`; weight keys ⊆ known domains (derived from `DEFAULT_WEIGHTS`, no second list); each weight numeric (not bool) in [0, 100]; `confidenceThreshold` numeric (not bool) in [1, 10] with no crash; `statusThresholds.*` and `scoring.*` arrays of exactly two numbers. It allows unknown top-level keys (as the schema does). It returns all violations as data (the CLI edge prints them), not just the first, and never raises. **Partial weights**: a file whose `weights` object leaves out any domain (for example `{"weights": {"data": 30}}`) is valid on its own; per-file validation checks the weights sum only when the file lists all 10 domains. Sum-to-100 is enforced on the merged config by `validate_effective`, so an override is judged by the effective weights it produces, not in isolation.
2. **Completeness rules** apply only to proposals headed for a write (ADR-010), on top of the item 1 rules (one shared violations function): all 10 domains present, integers only, sum exactly 100, all four sections present with only their known keys, and (from US-06) status bands contiguous and non-overlapping over 1-10 (BR-6).
3. A dev-time parity test runs the stdlib validator and `jsonschema` over a shared fixture corpus. The stdlib validator must reject everything the schema rejects. The test skips when `jsonschema` is not installed.
4. No python3 means the skill enters degraded mode: it prints the proposal and writes nothing.

## Alternatives Considered

- **Validate a temp file with `jsonschema` when available, stdlib otherwise**: uses the real schema. Rejected because behavior would depend on the environment (two different gates), and the temp file violates NFR-1 if placed in the project.
- **Agent checks the schema by reading it**: no code change. Rejected because LLM arithmetic and rule checking are exactly what BR-5 exists to guard against.
- **Leave `validate_config` alone; put all rules in a new write-only validator**: zero backward-compat risk. Rejected because `validate <file>` would keep accepting configs the schema rejects, which is the bug DQ-6 names, and two validators would drift.

## Consequences

- Positive: one stdlib gate that matches the schema, provably through the parity test; existing CLI users gain protection against typos such as `"securty": 14`.
- Negative: **behavior change** to `validate <file>`. Files the schema already rejected (unknown weight names, out-of-range values, version ≠ 1) now fail. This is acceptable because those files were already invalid per the published schema. CI's `validate fitness-config.example.json` and `init /tmp/...` steps must still pass.
- Negative: rules live twice (schema JSON and Python). The parity test is the mitigation.
