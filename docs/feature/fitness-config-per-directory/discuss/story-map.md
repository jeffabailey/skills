# Story Map: fitness-config-per-directory

## User: Devin Park, infrastructure engineer maintaining a multi-module repo
## Goal: Apply per-module fitness review weights by dropping fitness-config.json into a subdirectory

## Backbone

| Author override config | Resolve config for path | Run review with override | Trust the report |
|------------------------|------------------------|--------------------------|------------------|
| Initialize per-dir override (`fitness-config.py init --path <dir>`) | Walk up from target to find nearest config | Review skills read effective config (not root) | Report header names config sources |
| Validate override sums to 100 after merge | Merge child over root | Skipped domains (weight=0) excluded from review | Effective weights inline in header |
| Update existing override | Surface schema version mismatches | Weighted average uses effective weights | `show` output matches review output |

---

## Walking Skeleton

The thinnest end-to-end slice that proves the override mechanism works at all:

1. Author override: place a `fitness-config.json` in a subdirectory (manual, no init helper)
2. Resolve config: walk up from a target path, find nearest config, merge with root
3. Run review: review-full reads the effective merged config (not root)
4. Trust report: report header line names `Config: <child path> (merged with root)` and lists effective weights

**Skeleton tasks** (one per backbone activity):
- WS-A: Manual placement of override (no new tooling required)
- WS-B: `fitness-config.py show --path <target>` displays merged config + source chain
- WS-C: At least one domain skill (e.g., review-full orchestrator) reads from resolver output instead of raw root JSON
- WS-D: review-full report header includes Config: line and Effective weights: line

This is the minimum to deliver Devin's outcome. Without any one of these four, the journey breaks.

---

## Release 1 (Walking Skeleton): "Devin can override weights for one module and trust the result"

**Target outcome KPI**: Devin runs review-full on `infrastructure/modules/postgresql/`, sees module-specific weights applied (verified in report header), and the overall score reflects the override.

Tasks included:
- WS-A: Manual override placement (documentation only)
- WS-B: `show --path` subcommand
- WS-C: Single resolver call from review-full
- WS-D: Report header config provenance lines

Rationale: this validates the riskiest assumption — that the resolver can be the single source of truth and that the report header proves which config was used. Without this, every later release is built on a guess.

---

## Release 2: "Devin can confidently author and validate overrides"

**Target outcome KPI**: 90% of override authoring attempts result in a valid sum-to-100 config on first commit, because validation happens before review runs.

Tasks included:
- `fitness-config.py validate --path <dir>` validates effective merged config (not just file)
- `fitness-config.py init --path <dir>` scaffolds an override (with comments noting which keys are inherited from root)
- Error messages name both config files involved
- Schema version mismatch detection (DQ-3)

Rationale: walking skeleton proves the mechanism works. This release reduces the foot-gun rate so adoption sticks.

---

## Release 3: "Coverage extends to all domain skills, not just review-full"

**Target outcome KPI**: 100% of domain skills (`review-architecture`, `review-security`, etc.) honor the per-directory override when invoked with a subtree scope.

Tasks included:
- Each `review-<domain>` SKILL.md updated to call resolver
- Per-domain reports include same Config: header line as review-full
- Functional tests in `tests/functional-tests.md` extended to cover overrides per domain

Rationale: prevents partial coverage where review-full respects overrides but `review-security` doesn't. Without this, Devin will hit confusing inconsistencies.

---

## Future / Out of Scope (Won't Have for v1)

- Multiple overrides in one tree (e.g., postgresql/scripts/ has its own override on top of postgresql/) — DQ-5
- Glob-based config discovery
- Explicit `--config <path>` flag (power-user escape hatch)
- Full-replacement merge mode (alternative to deep-merge)
- Cross-version migration tooling

---

## Scope Assessment: PASS

- Story count: 6-7 stories across 3 releases (well under 10)
- Bounded contexts touched: 2 (config tooling in `scripts/`, review skills in `src/`)
- Walking skeleton integration points: 3 (resolver, review-full orchestrator, report writer)
- Estimated effort: 4-6 days total across releases
- Right-sized for a single delivery cycle
