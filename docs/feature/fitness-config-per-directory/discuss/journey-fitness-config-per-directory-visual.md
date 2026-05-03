# Journey: Per-Directory Fitness Config

**Persona**: Devin Park, infrastructure engineer maintaining a homelab repo with 12 Terraform modules. Each module has different priorities (postgresql cares about data integrity, logging cares about observability, networking cares about security). Devin currently runs `review-full` and gets the same generic weighting for every module — the postgresql review under-scores data issues because architecture and security dominate the weighting.

**Goal**: Drop a `fitness-config.json` into a module subdirectory so reviews scoped to that subtree apply module-specific weights.

## Emotional Arc: Confidence Building

| Stage | Feeling | Trigger |
|-------|---------|---------|
| Start | Mildly frustrated — generic weights miss what matters in this module | Sees fitness report, knows data integrity should weigh more |
| Middle | Cautiously optimistic — drops a config, runs review | Curious whether the right config got picked up |
| End | Confident — review output names the config that was applied, scores reflect priorities | Verifies in the report header |

**Key transition risk**: silent fallback to root config (user thinks override applied, it didn't). The journey must surface "which config was applied" loudly.

## Happy Path Flow

```
[Devin edits postgresql/fitness-config.json]
     |
     | Writes weights: data=30, reliability=20, security=14, ...
     |
     v
[Devin runs: review-full on postgresql/]
     |
     v
+-- Step 1: Tool resolves config -------------------------+
| Walks up from postgresql/ looking for fitness-config.json|
| Finds: postgresql/fitness-config.json                    |
| Validates schema, validates merged weights sum to 100    |
+----------------------------------------------------------+
     |
     | Feels: reassured (explicit "config-applied" line in output)
     v
+-- Step 2: Tool merges with root config ------------------+
| Deep-merge child over root                                |
| Effective config used for scoring                         |
+----------------------------------------------------------+
     |
     v
+-- Step 3: Review runs with effective weights ------------+
| Per-domain scores                                         |
| Weighted overall score using merged weights               |
+----------------------------------------------------------+
     |
     | Feels: confident (data domain ranked at top of action items)
     v
+-- Step 4: Report header shows which config was applied --+
| Lines 1-5 of report: scope, config source(s), effective  |
| weights summary table                                     |
+----------------------------------------------------------+
     |
     v
[Devin trusts the report — module-specific priorities reflected]
```

## TUI Mockups

### Step 1 output: config resolution (default verbosity)

```
$ python3 ~/.claude/skills/scripts/fitness-config.py show \
    --path infrastructure/modules/postgresql/main.tf

Resolved config for: infrastructure/modules/postgresql/main.tf

  config sources (in precedence order):
    1. infrastructure/modules/postgresql/fitness-config.json   (override)
    2. fitness-config.json                                     (root)

  effective weights (merged):
    data            30   (override)
    reliability     20   (override)
    architecture    14   (root)
    security        14   (root)
    testing         10   (root)
    performance      6   (override)
    algorithms       4   (override)
    accessibility    0   (override -- skipped)
    process          1   (override)
    maintainability  1   (override)
    -------------------
    total          100   OK

  effective thresholds, security, scoring: from root (no override)
```

### Step 3 output: review report header

```
+-- Project Fitness Report -----------------------------------+
| Date:  2026-04-25                                           |
| Scope: infrastructure/modules/postgresql/                   |
|                                                             |
| Config: postgresql/fitness-config.json (merged with root)   |
| Effective weights: data=30 reliability=20 architecture=14...|
|                                                             |
| Overall Score: 7.2 / 10                                     |
+-------------------------------------------------------------+
```

### Step 1 error: weights don't sum to 100 after merge

```
$ python3 ~/.claude/skills/scripts/fitness-config.py validate \
    --path infrastructure/modules/postgresql/

Error: Effective config has invalid weights

  Source: infrastructure/modules/postgresql/fitness-config.json
          merged with: fitness-config.json (root)

  Effective weights sum to 95, must sum to 100.

  The override redefined: data, reliability, performance,
  algorithms, accessibility, process, maintainability.
  The override left from root: architecture=14, security=14, testing=10.

  To fix:
    1. Adjust override weights so the merged total is 100, OR
    2. Set "weights": { ... } with all 10 domains in the override
       (full replacement, no merge with root weights).

  See: fitness-config.example.json
```

## Edge Case 1: Config Lookup Walks Past Subdirs

```
[Devin runs review on infrastructure/modules/postgresql/scripts/migrate.sh]
     |
     | (postgresql/scripts/ has no fitness-config.json)
     |
     v
[Tool walks up: scripts/ -> postgresql/ -> modules/ -> infrastructure/ -> root]
     |
     | Stops at first match: postgresql/fitness-config.json
     |
     v
[Same config used as if Devin reviewed postgresql/main.tf]
     |
     | Feels: predictable (lookup behavior matches their mental model
     |        of how .gitignore, .editorconfig, .git work)
```

Output banner makes the resolution visible:

```
Config: infrastructure/modules/postgresql/fitness-config.json (merged with root)
        Found by walking up from: infrastructure/modules/postgresql/scripts/migrate.sh
```

## Edge Case 2: Override Has Invalid Weight Sum

Documented under "Step 1 error" mockup above. Critical that the error message:
- Names BOTH config files involved
- Distinguishes override-defined vs root-inherited weights
- Offers two concrete fixes (adjust the override, or use full-replacement mode)
- Never silently falls back to root — that breaks user trust

## Out of Scope (DESIGN decides)

- Whether merge is deep-merge (assumed) vs. full-override per top-level key — see `wave-decisions.md`
- Whether discovery rule supports glob/multiple configs (only walk-up assumed for v1)
- How tool detects "review target path" when invoked without explicit path (probably CWD; DESIGN decides)
- Schema version mismatch behavior (root v1, child v2): assumed error, but exact UX is DESIGN's call

## Shared Artifacts (see registry)

- `effective_weights` — produced by config resolver, consumed by every domain scorer and report header
- `config_source_chain` — produced by resolver, consumed by report header and `show` subcommand
- `review_target_path` — produced by user invocation, consumed by resolver to seed walk-up
