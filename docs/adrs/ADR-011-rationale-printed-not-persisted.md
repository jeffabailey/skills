# ADR-011: Rationale Is Printed in the Summary, Not Persisted

**Status**: Accepted
**Date**: 2026-09-28
**Wave**: DESIGN, fitness-config-init
**Persona**: Morgan (nw-solution-architect)

## Context

Every changed value gets a one-line, evidence-citing reason (FR-5). JSON has no comments. DQ-1 asked where the rationale lives. The user decided: printed summary only.

## Decision

The rationale table (key, baseline, proposed, reason or "(unchanged)") is printed in the proposal and repeated in the final summary. The written `fitness-config.json` contains only schema keys in canonical form. There is no sidecar file and no `$comment` key; the canonical renderer drops unknown keys, and the diff shows them as removals.

## Alternatives Considered

- **Sidecar `fitness-config.rationale.md`**: durable memory of why. Rejected because it is a second written file (NFR-1), goes stale on hand edits, and is not read by any tool.
- **`$comment` key in the JSON**: co-located with the values. Rejected because the per-directory deep merge drops it, it diverges from the example file's shape, and it breaks byte parity with the canonical form.

## Consequences

- Positive: one file written; the config stays byte-comparable with the example and the resolver's canonical form.
- Negative: the "why" is lost after the session unless the user copies it (for example, into a commit message). The summary ends with a one-line suggestion to paste the table into the commit message.
