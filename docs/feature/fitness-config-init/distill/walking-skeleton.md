# Walking Skeleton: fitness-config-init

**Wave**: DISTILL | **Date**: 2026-09-28 | **Persona**: Quinn (nw-acceptance-designer)

## The user goal it proves

Priya reviewed a purpose-tuned weight proposal for `ledgerd`. The skeleton proves that proposal ends up on disk byte-for-byte as she saw it, that it's valid, and that her next review will use it. Nothing else in her project changes.

File: `tests/acceptance/fitness-config-init/walking-skeleton.feature`

| # | Scenario | State | Stories / ACs |
|---|---|---|---|
| WS-1 | Priya saves a reviewed database-service config into ledgerd, which had none | **enabled** (the only enabled scenario in the suite) | US-02, US-03; AC-03.1, AC-03.2, AC-03.6 |
| WS-2 | Priya sees the built-in starting weights for a project at its repository root | `@skip` | US-02; AC-02.5 |
| WS-3 | Kenji's billing config is announced as an override of the fieldnotes root config | `@skip` | US-03; AC-03.5 |

## The path WS-1 exercises

1. The Given sets up `ledgerd` under `tmp_path` with its go.mod, migrations, StatefulSet and README.
2. Then `init --path . --from - --dry-run` checks the proposal (from stdin): `STATUS: would-create`, `Proposal: <fp>`, and the canonical bytes.
3. The When saves it with `init --path . --from - --expect <fp>`: `STATUS: created`.
4. The Thens check that the file bytes equal the canonical bytes Priya saw and that the fingerprint matches. `validate --path .` and strict `validate fitness-config.json` both pass, `show --path .` prints `Config: fitness-config.json`, and the workspace state delta shows exactly one new file.

Driving adapter: the real CLI as a subprocess (cwd = anchor). Driven adapter: the real filesystem. No mocks.

## Why the agent half isn't in the skeleton

US-01 (classification) and the judgment part of US-02 happen inside the agent. pytest can't run them. They're covered by:

- static checks on `SKILL.md`, `references/purpose-profiles.md` and `references/purpose-signals.md` (milestone-1)
- `@manual` agent-eval scenarios run against the six DISCUSS fixtures

The skeleton therefore begins at the handoff point the design fixes (architecture-design section 4): the agent passes the proposal to the resolver on stdin. The skeleton's scope is that seam.

## Current state (RED, right reason)

```
AssertionError: expected status existing-malformed or unchanged or would-create or would-replace, got None
fitness-config.py init --path . --from - --dry-run -> exit 2
fitness-config.py: error: unrecognized arguments: --from --dry-run
```

Classification: MISSING_FUNCTIONALITY. The flags in data-models.md section 6 don't exist yet.

## Minimum DELIVER work to turn WS-1 green

- `init --path T --from - --dry-run`: strict validation plus completeness, canonical renderer, fingerprint, `STATUS: would-create`
- `init --path T --from - --expect FP`: exclusive create, then `STATUS: created`
- the anchor guard (target == cwd means an empty chain), so the check never reads above the project
