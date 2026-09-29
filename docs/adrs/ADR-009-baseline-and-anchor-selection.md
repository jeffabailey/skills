# ADR-009: Baseline Comes from the Resolver Seed, Anchored at the Repository Root

**Status**: Accepted
**Date**: 2026-09-28
**Wave**: DESIGN, fitness-config-init
**Persona**: Morgan (nw-solution-architect)

## Context

"Changed from the baseline" decides which values need a reason (FR-5) and what the default column shows. Two copies of the defaults exist: `DEFAULT_*` in the resolver and `fitness-config.example.json`, identical today (HIGH risk in the shared-artifacts registry). In a subfolder, the meaningful baseline is what already applies there. The user accepted DQ-3's lean: built-in defaults at the repo root, the parent's merged config in a subfolder.

`build_seed_config` already computes exactly this, but the only way to reach it is `init --path`, which writes. The resolver stops walking at `cwd`. `cmd_init_path` starts from the target's parent, so when target == cwd the walk passes above cwd and can read unrelated ancestor configs (latent defect).

## Decision

1. The **anchor** is `git -C <target> rev-parse --show-toplevel`, or the target itself when git is absent or the target is not in a repo. The skill runs every resolver call with cwd = anchor.
2. The **baseline** is `init --path <target> --dry-run`, which prints `build_seed_config` of the chain strictly between the anchor and the target's parent, plus `Baseline-Source`. Target == anchor gives an empty chain and the built-in defaults. The walk never goes above the anchor (this fixes the latent defect for the existing `init --path` too).
3. The skill never hardcodes default weights and never reads the example file for the baseline, except in degraded mode (resolver unreachable), where the output is labeled `example file (degraded)`.
4. A parity test asserts that the canonical rendering of `DEFAULT_*` is byte-identical to `fitness-config.example.json`.

## Alternatives Considered

- **Example file as the baseline**: human-visible. Rejected because it is a second source of truth that the resolver never reads; a drift would make "default" mean different things in the skill and in reviews.
- **Baseline = the existing target file when present**: shows the delta from "what I have". Rejected as the baseline because it makes rationale relative to possibly-unexplained past tuning. The existing file is instead the left side of the US-04 diff, which already shows that delta.
- **Anchor = agent session cwd (what review-full uses)**: consistent with review-full. Rejected because a user running from `services/billing` would never see the root config, so the override notice (US-03 example 2) would be impossible.
- **Walk for `.git` in Python (ADR-001 text)**: no git dependency. Rejected because it duplicates git, mishandles worktrees and submodules, and changes resolver semantics for every consumer.

## Consequences

- Positive: a single source of truth; subfolder proposals are relative to what already applies; the latent walk-above-anchor defect is fixed.
- Negative: a review-full started from a subfolder session anchors differently from this skill's summary chain. The summary states which anchor was used when target ≠ anchor.
- Negative: without git, ancestor configs are not considered. The skill says so explicitly.
