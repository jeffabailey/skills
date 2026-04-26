# Walking Skeleton — fitness-config-per-directory

**Wave**: DISTILL
**Date**: 2026-04-25
**Persona**: Quinn (nw-acceptance-designer)

## Strategy declaration (Dim 9 — WS Boundary Proof)

**Strategy: C (Real Services)** — real filesystem in `tmp_path`, real
`python3 scripts/fitness-config.py` subprocess invocation. No in-memory
doubles, no mocks, no fakes at the acceptance layer.

This matches DESIGN ADR-006 (modular library with dependency inversion at
the I/O boundary) — the only impure boundary is the filesystem reader,
and the cheapest way to exercise it faithfully is the real filesystem
under pytest's per-test temporary directory.

## The walking skeleton

**Title**: "Devin previews module-specific weights for a Postgres review target"

**Why this scenario**:

1. **User-centric (Dim 5)**. Title describes Devin's goal ("preview
   module-specific weights"). Then steps describe Devin's observations
   (effective weights at 30 and 20, override named first, total sums to
   100). A non-technical stakeholder confirms "yes, that is what users
   need."

2. **Minimal end-to-end** (Dim 9d). Touches walk-up + deep-merge + reporter +
   CLI in one invocation. Forces software-crafter to wire all four
   modules in DELIVER's first iteration. If any module is stubbed, the
   skeleton fails.

3. **Real I/O proof** (Dim 9c). Tagged `@real-io @adapter-integration`.
   The scenario writes real `fitness-config.json` files to a real
   directory, invokes the real CLI as a real subprocess, and asserts on
   real stdout. If we replaced `_read_config` with an in-memory stub, the
   skeleton would still need to traverse the real filesystem to find
   files, so the test would fail. The litmus test passes: deleting the
   real adapter makes this skeleton fail.

## Why one walking skeleton, not 2-3

The DELIVER orchestrator template recommends 2-5 skeletons per feature;
test-design-mandates says 2-3 is typical. We use ONE for two reasons:

1. The driving port is one CLI script. The user's mental model has one
   primary verb (`show --path`) for the demo-able outcome. Other CLI
   verbs (`validate`, `init`) are supportive — `validate` is exercised
   by the error-handling milestone; `init` is exercised by milestone-6.
   Forcing additional skeletons would create artificial scenarios that
   replicate what milestone scenarios already cover.

2. Strategy C (real-services) makes every milestone scenario implicitly
   E2E. There is no separate "fast" tier with mocks — every test
   exercises the real CLI + real filesystem. The walking skeleton's
   distinction is only that it remains UNSKIPPED while the others are
   gated behind `@skip` for one-at-a-time DELIVER.

## Adapter coverage matrix (Dim 9c)

| Adapter | Real-I/O scenario coverage |
|---------|----------------------------|
| Filesystem reader (`_read_config`) | walking-skeleton + every milestone scenario tagged `@real-io` |
| CLI subprocess (driving port) | walking-skeleton + every milestone scenario tagged `@real-io` |
| (No other adapters in this feature.) | |

ADR-006 declares the filesystem as the only impure boundary. There are no
network, database, message-queue, or external-service adapters. The single
adapter is comprehensively covered.

## Unskip order for DELIVER

The software-crafter unskips scenarios in this sequence:

| # | Feature file | Scenarios | Rationale |
|---|--------------|-----------|-----------|
| 0 | walking-skeleton.feature | 1 | Already active. Drives Feature 0 build (the resolver wiring + show command). |
| 1 | milestone-1-walk-up-discovery.feature | 5 | Walk-up is the foundation. Adds depth coverage (file vs dir input, walk-past-empty-dir, missing-config fallback, missing-everywhere fallback, determinism). |
| 2 | milestone-2-deep-merge.feature | 5 | Deep-merge semantics. Adds partial-override, full-override, status-threshold and security-config merging, fail-closed precondition. |
| 3 | milestone-3-provenance.feature | 5 | Show-output rendering. Adds source-chain phrasing variants, all-10-domains line, descending-weight ordering, byte-identical determinism. |
| 4 | milestone-5-backward-compat.feature | 5 | NFR-3 guard rails. Each existing CLI invocation pattern preserved. Run before error scenarios to lock the legacy contract. |
| 5 | milestone-6-init-helper.feature | 4 | Init helper. Depends on resolver-driven seeding from root. |
| 6 | milestone-4-error-handling.feature | 11 | All error / boundary / failure paths. Run after happy-path is solid. |
| 7 | integration-checkpoints.feature | 8 | Cross-cutting contracts (broad-scope ADR-005, perf, JSON sentinel block, CLI mutual exclusion, US-08 audit). |

Total: 44 scenarios over 8 unskip iterations.

## Demo-ability

A 30-second stakeholder demo: Devin runs

```bash
cd <repo>
mkdir -p infrastructure/modules/postgresql
echo '{"version":1,"weights":{"data":30,"reliability":20,...}}' > infrastructure/modules/postgresql/fitness-config.json
touch infrastructure/modules/postgresql/main.tf
python3 scripts/fitness-config.py show --path infrastructure/modules/postgresql/main.tf
```

The output names both files, lists the merged weights with `data=30
reliability=20`, and prints `total 100 OK`. The stakeholder sees:

> "When I drop a config in my Postgres module and run show on a file
> inside it, the tool tells me the override won, the merged weights are
> 100, and exactly which two files contributed."

That sentence IS the user value. The skeleton scenario asserts on
exactly that observable output.
