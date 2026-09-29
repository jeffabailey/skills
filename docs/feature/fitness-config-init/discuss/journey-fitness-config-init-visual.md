# Journey: Tune a fitness config to what this project actually is

**Persona**: Priya Raman maintains `ledgerd`, a Postgres-backed double-entry ledger service with no UI, running on the homelab k3s cluster. She is about to run `review-full` for the first time.
**Goal**: Get a `fitness-config.json` whose weights match what matters for this project, without hand-editing ten numbers, and understand why each number changed.
**Arc**: Skeptical ("will it just give me defaults?") -> Engaged (sees its evidence and reasoning) -> Confident (valid file written, every change explained).

## Flow

```
 [1 Invoke]      [2 Choose mode]     [3 Gather evidence]   [4 Classify]      [5 Propose]        [6 Existing?]        [7 Validate+Write]   [8 Next step]
 /fitness-       fast (default)  --> README, manifests, --> purpose +     --> weights/thresh --> none: skip     --> schema + resolver --> "run review-full"
 config-init     | full review       dirs, deploy cfg      confidence        + rationale        exists: diff +      validate, then write   + resolver chain
                 v                   (+ review-full                          table              confirm y/N
                 warn: writes         scores if full)
                 docs/fitness-report.md
 Feels:  curious    in control          watching / trusting   "yes, that's it"  informed           careful, safe         relieved             confident
```

Emotional transitions: the one risky transition is step 6 (overwriting an existing file). It is buffered by a diff and an explicit confirm that defaults to No. Validation failures (step 7) never write a file. They are shown as "not written, here is why."

## Step mockups (agent chat output)

### Step 2: Choose evidence mode

```
fitness-config-init: /Users/priya/src/ledgerd

How much evidence should I gather?
  1. Fast purpose scan (default, about 1 min): README, manifests, directory layout, deploy config
  2. Full review: runs review-full (all 10 domains). Slower. Also writes docs/fitness-report.md
Choice [1]:
```

### Step 4: Purpose classification

```
Purpose: ${project_purpose}                     e.g. database-backed service (no UI)
Confidence: ${purpose_confidence}               high
Evidence (${evidence_mode} scan):
  - go.mod: pgx/v5, golang-migrate            -> relational database access
  - migrations/ (42 .sql files)               -> schema evolves in place
  - deploy/k8s/statefulset.yaml, PodDisruptionBudget -> long-running, availability-sensitive
  - no *.html/*.tsx/*.css                     -> no user-facing UI
```

### Step 5: Proposal with rationale

```
Proposed ${config_path}  (baseline: ${default_config_source})

Domain           default  proposed  why
reliability         10       18     StatefulSet + PDB: downtime loses ledger writes
data                10       18     42 migrations + pgx: integrity and migration safety dominate
architecture        14       10     single service, small surface
algorithms          10        8     CRUD plus balance math, no custom algorithms
process              8        6     single maintainer, no release train
maintainability      6        5     small codebase (about 6k LOC Go)
accessibility        8        1     no UI found; kept above 0 so API error text still gets a look
security            14       14     (unchanged)
testing             10       10     (unchanged)
performance         10       10     (unchanged)
                  ----     ----
total              100      100

statusThresholds, security.confidenceThreshold, scoring: unchanged from baseline
```

### Step 6: Existing file diff (only when one exists)

```
ledgerd already has fitness-config.json (edited 2026-06-02).

  weights.reliability      12 -> 18
  weights.data             12 -> 18
  weights.accessibility     4 -> 1
  weights.architecture     14 -> 10
  weights.process           8 -> 6
  (5 values unchanged)

Overwrite ${config_path}? [y/N]:
```

### Step 7-8: Validate, write, next step

```
Schema check     : pass (fitness-config.schema.json)
Resolver check   : pass (${validation_result})
Wrote ${config_path}

Resolver chain for this folder: ${resolution_chain}
Next: run review-full here. It will use these weights.
```

Error rendering (step 7 fails): `Not written. Proposed weights sum to 101 (must be 100).` followed by the proposal, so nothing on disk changes.
