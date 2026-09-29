# ADR-007: Purpose Profiles with Bounded Agent Judgment

**Status**: Accepted
**Date**: 2026-09-28
**Wave**: DESIGN, fitness-config-init
**Persona**: Morgan (nw-solution-architect)

## Context

`fitness-config-init` must turn evidence about a project's purpose into 10 weights that sum to 100, with a cited reason for every value that differs from the baseline (FR-4, FR-5, BR-2). DISCUSS left open how the mapping works (DQ-4), how mixed purposes are handled (DQ-5), and how review-full scores feed in (DQ-2). The quality drivers are correctness (valid, explainable output), consistency across runs and agents, and maintainability for one maintainer. The user decided on profiles plus bounded adjustment, a floor of 1, an ask when confidence is not high, and applicability-only use of scores.

## Decision

1. `skills/fitness-config-init/references/purpose-profiles.md` holds one parseable table with six archetypes: `database-backend`, `web-frontend`, `cli-tool`, `library-sdk`, `data-pipeline`, `api-service`. Each row has 10 integer weights, each ≥ 1, summing to 100. The set comes from the purpose categories in US-01 and the six DISCUSS fixtures (ledgerd, jeffbaileyblog, homelab-cli, fieldnotes, paygate; geo-notes means unknown), with `api-service` split from `database-backend` because paygate-style services have no owned data store. New archetypes are added only when dogfood logs show repeated corrections to the same purpose.
2. The agent starts from the matching profile and may adjust any domain by at most ±4, and only with a cited evidence path or finding. The result must keep integers, the floor of 1, and a sum of 100. The bound limits the agent's own judgment, not the user: a change the user asks for explicitly is applied exactly, even beyond ±4, and its reason is marked as a user edit. The floor, integers and sum of 100 still apply, and the resolver's validator enforces them either way.
3. Confidence high means use the profile. Medium, or `mixed`, means ask the user for the primary purpose, then use that profile; mixed repos get a pointer to per-directory overrides, which the skill never creates. Low or `unknown` (with no answer) means the proposal equals the baseline and there are zero reasons (BR-3).
4. Full mode: review-full evidence changes **applicability only**. A skipped or absent domain moves toward the floor, and the reason cites the skip. Findings may be cited as reasons for moves the profile already made. A low score never raises a weight, because weights mean importance, not current health.
5. A pytest fitness test parses the table and enforces the invariants in (1). The resolver's strict validator stays the final gate for every proposal (ADR-008, ADR-010).

## Alternatives Considered

- **Pure agent judgment within guardrails (no profiles)**: needs no content maintenance. Rejected because proposals would vary across runs and hosts for the same evidence, and nothing could be regression-tested. That undermines the KPI of 80% or more accepted without correction.
- **Fixed profiles with no adjustment**: fully deterministic. Rejected because it cannot express project-specific evidence (for example, a CLI tool that also ships a TUI). Rationale would degrade to "because it is a CLI", which BR-2 treats as thin.
- **Blend profiles for mixed repos (weighted average by evidence share)**: automatic. Rejected because the blend weights are themselves unexplainable judgments, and the user is the better source for the primary purpose (DQ-5 lean).
- **Floor 0 for no-surface domains**: truthful for UI-less services. Rejected because review-full already redistributes skipped domains, and a 0 in the file hides the domain entirely if a UI appears later. A floor of 1 keeps it visible at negligible cost.
- **Scores raise weights for weak domains (DQ-2 alternative)**: tempting as "focus where it hurts". Rejected because it conflates importance with health, and it produces feedback loops: fixing a domain would lower its weight.

## Consequences

- Positive: reproducible starting points; rationale anchored to a named profile plus evidence; profile invariants are testable; numbers live in one reference file, never in SKILL.md (audit-compatible).
- Negative: six archetypes will not fit every project. The ±4 bound can feel restrictive, and users can still edit rows before writing (US-02). Profile numbers are content that needs occasional tuning from dogfood logs.
- Follow-up: DELIVER seeds the `database-backend` and `web-frontend` rows from the US-02 examples.
