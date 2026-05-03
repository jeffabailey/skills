<!-- markdownlint-disable MD024 -->

# User Stories: fitness-config-per-directory

## US-01: Walk-Up Resolver Finds Nearest Config

### Problem
Devin Park is an infrastructure engineer who maintains a homelab repo with 12 Terraform modules under `infrastructure/modules/`. He wants `infrastructure/modules/postgresql/fitness-config.json` to apply when he reviews `infrastructure/modules/postgresql/main.tf`, without telling the tool explicitly which config to use. Today, only the repo-root `fitness-config.json` is read, so module-specific priorities are ignored.

### Who
- Infrastructure engineer | maintains multiple modules in one repo | wants per-module priorities applied automatically based on review target path

### Solution
Add a config resolver that walks up from a review target path (file or directory) toward the repo root, returning the first directory containing a `fitness-config.json`. If none is found before the repo root, the root config is used. If no root config either, built-in defaults apply.

### Domain Examples

#### 1: Happy Path — Devin reviews postgresql/main.tf
Devin runs a review with `--path infrastructure/modules/postgresql/main.tf`. The resolver walks up: `postgresql/main.tf` (file, skip) → `postgresql/` (has `fitness-config.json`, stop). Override is `infrastructure/modules/postgresql/fitness-config.json`. Root is `fitness-config.json`. Source chain: [override, root].

#### 2: Edge Case — nested file under override
Devin runs a review with `--path infrastructure/modules/postgresql/scripts/migrate.sh`. The resolver walks up: `scripts/migrate.sh` (skip) → `scripts/` (no config) → `postgresql/` (has config, stop). Same override applies as Example 1.

#### 3: Edge Case — no override exists
Devin runs a review with `--path infrastructure/modules/networking/main.tf`. The resolver walks up: `main.tf` (skip) → `networking/` (no config) → `modules/` (no config) → `infrastructure/` (no config) → repo root (has `fitness-config.json`, stop). Source chain: [root only].

### UAT Scenarios (BDD)

#### Scenario: Resolver finds nearest config when target is a file in the override directory
Given the repo has `fitness-config.json` at the root with default weights
And `infrastructure/modules/postgresql/fitness-config.json` exists with `data=30, reliability=20`
When Devin runs `fitness-config.py show --path infrastructure/modules/postgresql/main.tf`
Then the source chain lists `infrastructure/modules/postgresql/fitness-config.json` first and root second
And the effective weights show `data=30` and `reliability=20` from the override

#### Scenario: Resolver walks past intermediate directories without configs
Given `infrastructure/modules/postgresql/fitness-config.json` exists
And `infrastructure/modules/postgresql/scripts/` has no `fitness-config.json`
When Devin runs `fitness-config.py show --path infrastructure/modules/postgresql/scripts/migrate.sh`
Then the source chain still lists `infrastructure/modules/postgresql/fitness-config.json` first
And the output explains it found this by walking up from the input path

#### Scenario: Resolver falls back to root when no override is found
Given `fitness-config.json` exists at the root
And no `fitness-config.json` exists anywhere under `infrastructure/modules/networking/`
When Devin runs `fitness-config.py show --path infrastructure/modules/networking/main.tf`
Then the source chain lists only `fitness-config.json` (root)
And the effective weights match the root config exactly

#### Scenario: Resolver falls back to defaults when no config exists at all
Given the repo has no `fitness-config.json` anywhere
When Devin runs `fitness-config.py show --path infrastructure/modules/networking/main.tf`
Then the source chain is empty (`built-in defaults`)
And the effective weights match `DEFAULT_WEIGHTS` defined in `fitness-config.py`

### Acceptance Criteria
- [ ] Resolver returns the nearest `fitness-config.json` ancestor for any input path
- [ ] Resolver handles file inputs (walks from parent dir) and directory inputs equivalently
- [ ] Resolver returns `[child, root]` chain when both exist; `[root]` when only root exists; `[]` (defaults) when neither exists
- [ ] Resolver completes in under 100ms for paths up to 10 levels deep in a 10k-file repo (NFR-1)
- [ ] Resolver is deterministic across invocations and machines for identical input (NFR-2)

### Outcome KPIs
- **Who**: Infrastructure engineers running reviews on subtrees within multi-module repos
- **Does what**: Implicitly applies the nearest module's `fitness-config.json` without specifying it
- **By how much**: 100% of review-target paths under an override directory pick up that override
- **Measured by**: Resolver unit tests + integration test: assert source chain for 5 representative target paths
- **Baseline**: 0% (overrides do not exist today)

### Technical Notes
- Resolver lives in `scripts/fitness-config.py`, extending the existing `load()`/`merge_defaults()` functions
- Walk-up MUST stop at the repo root (detected via `.git` presence, or filesystem root, whichever first)
- Use `Path.resolve()` to handle symlinks consistently

### Dependencies
- Existing `scripts/fitness-config.py` (modified)
- None blocking

---

## US-02: Effective Config Merge with Validation

### Problem
Devin's override config might only redefine a few weights. Today's resolver doesn't merge — it would either fully replace or ignore the file. Devin wants to express "I care more about data, leave the rest as root defaults" without restating all 10 weights, AND he wants the tool to refuse a merge that produces invalid total weights.

### Who
- Infrastructure engineer | wants minimal-diff override configs | expects clear errors when the merged result is invalid

### Solution
Resolver deep-merges child over root: top-level keys (`weights`, `statusThresholds`, `security`, `scoring`) and within `weights`, per-domain keys. Validates the merged effective weights sum to 100 (within 0.01). On validation failure, surfaces both files and offers two concrete fixes.

### Domain Examples

#### 1: Happy Path — partial override, valid merge
Root has all 10 weights summing to 100. `postgresql/fitness-config.json` redefines `data=30, reliability=20, performance=6, algorithms=4, accessibility=0, process=1, maintainability=1` (sum of overridden = 62). Root architecture=14, security=14, testing=10 contribute 38. Merged total = 100. Valid.

#### 2: Edge Case — full override
`postgresql/fitness-config.json` redefines all 10 weights summing to 100. Merge result equals override exactly. Valid.

#### 3: Error — merged total != 100
`postgresql/fitness-config.json` redefines all 10 weights but they sum to 95. Validation fails. Error names both files and offers fixes.

### UAT Scenarios (BDD)

#### Scenario: Partial override merges with root values for unspecified domains
Given root config has `architecture=14, security=14, reliability=10, testing=10, performance=10, algorithms=10, data=10, accessibility=8, process=8, maintainability=6` (sum=100)
And child config redefines only `data=30, reliability=20, performance=6, algorithms=4, accessibility=0, process=1, maintainability=1` (sum=62)
When the resolver merges child over root
Then the effective weights are `architecture=14, security=14, testing=10` (from root) and `data=30, reliability=20, performance=6, algorithms=4, accessibility=0, process=1, maintainability=1` (from child)
And the effective sum is 100
And validation passes

#### Scenario: Full override replaces every root weight
Given child config defines all 10 weights summing to 100
When the resolver merges child over root
Then every effective weight comes from the child config
And validation passes

#### Scenario: Merged weights do not sum to 100 — validation fails
Given root config sums to 100
And child config redefines all 10 weights summing to 95
When Devin runs `fitness-config.py validate --path infrastructure/modules/postgresql/`
Then exit code is 1
And the error names both `infrastructure/modules/postgresql/fitness-config.json` and `fitness-config.json`
And the error states `Effective weights sum to 95, must sum to 100`
And the error offers two fixes: adjust override weights, or use full-replacement mode
And no fitness review proceeds

#### Scenario: Other top-level keys merge independently
Given root config defines `statusThresholds.healthy = [8,10]`
And child config defines `security.confidenceThreshold = 9` but does NOT redefine statusThresholds
When the resolver merges child over root
Then effective `statusThresholds.healthy` is `[8,10]` from root
And effective `security.confidenceThreshold` is 9 from child

### Acceptance Criteria
- [ ] Deep-merge applied per top-level key, per domain weight
- [ ] Effective weights sum validation runs after merge and fails with exit code 1 if total != 100 (within 0.01)
- [ ] Error message names BOTH files in the chain
- [ ] Error message offers actionable remediation
- [ ] Merge result for non-weight keys (`statusThresholds`, `security`, `scoring`) follows same per-key override rule
- [ ] No silent fallback to root config on validation failure (NFR-4)

### Outcome KPIs
- **Who**: Override authors (infrastructure engineers maintaining module configs)
- **Does what**: Author valid overrides on the first commit attempt
- **By how much**: 90% first-attempt success rate (measured via validate exit codes in repo PR history once feature ships)
- **Measured by**: Telemetry on `validate` invocations in CI; ratio of pass-on-first-run vs. fail-then-retry
- **Baseline**: N/A (feature does not exist today)

### Technical Notes
- Extend existing `merge_defaults()` to take a chain of dicts, deep-merge in precedence order
- Validation function must operate on the merged config, not on the override file alone
- Reuse `validate_config()` existing logic; add new path-walking entry point

### Dependencies
- US-01 (resolver walk-up must produce the chain that this story merges)

---

## US-03: Report Header Names Config Sources and Effective Weights

### Problem
Even with a working resolver and merger, Devin can't trust the review unless he can SEE which config was applied. Today's reports name only the scope. If override silently fails to apply, Devin reads scores assuming module-specific weights when actually root weights were used.

### Who
- Anyone reading a fitness review report — Devin, peers, CI consumers
- Needs visible proof of which config and weights drove the scores

### Solution
Every fitness review report (review-full and per-domain) includes a header section within the first 10 lines naming: scope, config source chain, and effective weights inline. The values come from the same resolver call that drove scoring, ensuring no drift.

### Domain Examples

#### 1: Happy Path — override applied, header reflects it
Report header lines: `Scope: infrastructure/modules/postgresql/`, `Config: infrastructure/modules/postgresql/fitness-config.json (merged with root)`, `Effective weights: data=30 reliability=20 architecture=14 security=14 testing=10 performance=6 algorithms=4 accessibility=0 process=1 maintainability=1`.

#### 2: Edge Case — root only, no override
Header lines: `Scope: infrastructure/modules/networking/`, `Config: fitness-config.json`, `Effective weights: <root weights>`.

#### 3: Edge Case — defaults only, no config files anywhere
Header lines: `Scope: <path>`, `Config: built-in defaults (no fitness-config.json found)`, `Effective weights: <DEFAULT_WEIGHTS>`.

### UAT Scenarios (BDD)

#### Scenario: Report header proves override was applied
Given `infrastructure/modules/postgresql/fitness-config.json` exists with `data=30`
When Devin runs `review-full` scoped to `infrastructure/modules/postgresql/`
Then the first 10 lines of the report contain `Config: infrastructure/modules/postgresql/fitness-config.json (merged with root)`
And the first 10 lines contain `Effective weights: data=30 reliability=20 architecture=14 security=14 testing=10 performance=6 algorithms=4 accessibility=0 process=1 maintainability=1`
And those values match the resolver output for the same path

#### Scenario: Report header on root-scoped review names only the root config
Given root `fitness-config.json` exists
And subtree overrides exist but the review is scoped to repo root
When Devin runs `review-full` at the repo root
Then the report header shows `Config: fitness-config.json`
And the header does not name any subtree override
And a footnote/note explains "subtree overrides apply only when review scope is within their directory"

#### Scenario: Report header when no config exists
Given no `fitness-config.json` exists anywhere in the repo
When Devin runs `review-full`
Then the report header shows `Config: built-in defaults (no fitness-config.json found)`
And the effective weights match `DEFAULT_WEIGHTS`

### Acceptance Criteria
- [ ] Header section appears within the first 10 lines of every fitness report
- [ ] Header names the scope, the config source chain, and effective weights inline
- [ ] Header values are produced from the resolver output that drove scoring (no recomputation, no hardcoding)
- [ ] When source chain has 1 entry (root only), header reads `Config: <path>` (no "merged with..." suffix)
- [ ] When source chain has 2 entries, header reads `Config: <child path> (merged with root)`
- [ ] When source chain is empty, header reads `Config: built-in defaults (no fitness-config.json found)`
- [ ] On root-scoped reviews, header includes a note that subtree overrides do not apply

### Outcome KPIs
- **Who**: Anyone reading a fitness report
- **Does what**: Identifies which config was applied without reading scoring logic
- **By how much**: 100% of reports include the Config: and Effective weights: header lines
- **Measured by**: Functional test grep over generated reports; CI gate
- **Baseline**: 0% (feature does not exist today)

### Technical Notes
- The report writer (in `review-full` orchestrator and each `review-<domain>`) calls the resolver once and uses its output for both scoring and header lines
- Inline weights line ordered by descending weight, ties broken alphabetically, for readability
- Skipped domains (weight=0) included in the header line for transparency

### Dependencies
- US-01 (resolver chain available)
- US-02 (effective weights available)

---

## US-04: Show Subcommand Displays Resolved Config

### Problem
Before running a review, Devin wants to preview which config will apply. Without a preview, he runs the review, sees an unexpected score, and has to dig to figure out which config was used. He needs a fast way to dry-run the config resolution.

### Who
- Override authors and review consumers
- Want to verify config resolution without running a full review

### Solution
Add `fitness-config.py show --path <target>` subcommand that prints: source chain (in precedence order), effective weights as a table, effective non-weight settings, and a sum-line confirming totals. No review is run.

### Domain Examples

#### 1: Happy Path — preview override before review
Devin runs `fitness-config.py show --path infrastructure/modules/postgresql/main.tf`. Output lists override and root, displays merged weights table, prints `total 100 OK`.

#### 2: Edge Case — preview at a path under no override
Devin runs `fitness-config.py show --path infrastructure/modules/networking/main.tf`. Output lists only root config, displays root weights, prints `total 100 OK`.

#### 3: Edge Case — preview when nothing exists
Devin runs `fitness-config.py show --path /tmp/empty-repo/some-file`. Output shows `built-in defaults (no fitness-config.json found)` and `DEFAULT_WEIGHTS` table.

### UAT Scenarios (BDD)

#### Scenario: Show subcommand previews override
Given `infrastructure/modules/postgresql/fitness-config.json` exists
When Devin runs `fitness-config.py show --path infrastructure/modules/postgresql/main.tf`
Then exit code is 0
And output lists both config files in precedence order (override first, root second)
And output displays the effective weights as a table with one row per domain
And output displays `total 100 OK` (or the actual effective sum followed by status)

#### Scenario: Show subcommand previews root-only resolution
Given root `fitness-config.json` exists
And no overrides exist
When Devin runs `fitness-config.py show --path src/somefile.py`
Then exit code is 0
And output lists only the root config
And output displays the root weights as a table

#### Scenario: Show subcommand previews built-in defaults
Given the repo has no `fitness-config.json` anywhere
When Devin runs `fitness-config.py show --path .`
Then exit code is 0
And output shows `built-in defaults (no fitness-config.json found)`
And output displays `DEFAULT_WEIGHTS` as a table

### Acceptance Criteria
- [ ] `show` accepts `--path <target>` (file or directory)
- [ ] `show` calls the resolver once and renders its output as a human-readable table
- [ ] Source chain printed in precedence order (override before root)
- [ ] Effective weights table includes all 10 domains
- [ ] Sum-line shows total and OK/error status
- [ ] Existing `show` (no `--path`) behavior preserved for backward compatibility (NFR-3)

### Outcome KPIs
- **Who**: Override authors verifying config before running review
- **Does what**: Previews effective config without running a full review
- **By how much**: Median preview time < 1 second; preview adoption (separate from validate) tracked via CLI invocation telemetry if available
- **Measured by**: Time `show --path` execution in functional tests; track existence of preview-before-review pattern in user docs
- **Baseline**: 0% (feature does not exist today)

### Technical Notes
- Reuse existing `cmd_show()` in `scripts/fitness-config.py`, add `--path` argparse argument
- Preserve existing argument-less behavior (current default `fitness-config.json`)
- Output format matches the TUI mockup in `journey-fitness-config-per-directory-visual.md`

### Dependencies
- US-01, US-02 (resolver and merge must exist)

---

## US-05: Validate Subcommand Checks Effective Merged Config

### Problem
Today's `validate` subcommand checks one file in isolation. With overrides, an override file alone might not sum to 100 (intentional, with partial overrides). Devin needs a validator that checks the EFFECTIVE merged config, not the override file alone.

### Who
- Override authors writing or editing module configs
- CI/CD pipelines verifying configs before review runs

### Solution
Extend `fitness-config.py validate` to accept `--path <dir>`. It resolves the effective config for that path (using US-01) and validates the merged result. Exits non-zero on any failure (sum != 100, schema mismatch, malformed JSON, etc.) with errors that name all files in the chain.

### Domain Examples

#### 1: Happy Path — partial override merges to valid sum
Override redefines 7 of 10 weights summing to 62. Root contributes 38 from the other 3. Effective sum = 100. `validate --path` exits 0.

#### 2: Error — partial override leaves merged sum at 95
Override redefines 7 weights summing to 57 (root contributes 38 = total 95). `validate --path` exits 1 with explicit message.

#### 3: Error — schema version mismatch
Root `version=1`, child `version=2`. `validate --path` exits 1 with message naming both files and their versions.

### UAT Scenarios (BDD)

#### Scenario: Validate passes when effective merged config is valid
Given root config sums to 100
And child config has a partial override producing effective sum 100 after merge
When Devin runs `fitness-config.py validate --path infrastructure/modules/postgresql/`
Then exit code is 0
And output confirms `Effective merged config valid: total 100 OK`

#### Scenario: Validate fails when effective merged sum is wrong
Given root config sums to 100
And child config produces effective sum 95 after merge
When Devin runs `fitness-config.py validate --path infrastructure/modules/postgresql/`
Then exit code is 1
And the error names both `infrastructure/modules/postgresql/fitness-config.json` and `fitness-config.json`
And the error states `Effective weights sum to 95, must sum to 100`
And the error offers fixes: adjust override weights OR use full-replacement mode

#### Scenario: Validate fails on schema version mismatch
Given root `fitness-config.json` has `version: 1`
And `infrastructure/modules/postgresql/fitness-config.json` has `version: 2`
When Devin runs `fitness-config.py validate --path infrastructure/modules/postgresql/`
Then exit code is 1
And the error names both files and their versions
And the error states which version is supported

#### Scenario: Validate without --path preserves existing behavior
Given root `fitness-config.json` exists and is valid
When Devin runs `fitness-config.py validate` (no --path)
Then exit code is 0
And output reads `Valid: fitness-config.json`

### Acceptance Criteria
- [ ] `validate --path <dir>` resolves and validates the effective merged config
- [ ] Validation failures exit with non-zero code (NFR-4)
- [ ] Error messages name all files involved in the chain
- [ ] Error messages offer actionable remediation
- [ ] Schema version mismatch produces a hard error
- [ ] Existing `validate` (no --path) behavior preserved (NFR-3)

### Outcome KPIs
- **Who**: Override authors and CI pipelines
- **Does what**: Catches invalid configs before any review runs
- **By how much**: 100% of invalid effective configs detected at validate time (zero false-negatives in test corpus)
- **Measured by**: Functional tests with deliberately broken configs; assert `validate --path` exits 1 for each
- **Baseline**: 0% (today's validator only checks single file)

### Technical Notes
- Reuse `validate_config()` after merge step
- Add explicit schema version comparison between chain entries
- Error messages must reference real file paths from the chain, not generic placeholders

### Dependencies
- US-01, US-02

---

## US-06: Init Helper Scaffolds an Override Config

### Problem
Devin doesn't want to copy-paste 10 domain weights every time he creates a new module override. He wants a scaffold command that generates an override skeleton with comments explaining which keys are inherited from root and which are overridden.

### Who
- New override authors (someone creating their first module override)
- Existing maintainers adding overrides to new modules

### Solution
Extend `fitness-config.py init` to accept `--path <dir>`. It writes a `fitness-config.json` in `<dir>` pre-populated with the current root effective weights and a comment block (or sibling `.md` doc since JSON has no comments) explaining how to customize.

### Domain Examples

#### 1: Happy Path — scaffold a fresh override
Devin runs `fitness-config.py init --path infrastructure/modules/redis/`. The command creates `infrastructure/modules/redis/fitness-config.json` containing all 10 weights from the root config (so it's valid out of the box). A sibling note (or extra field in the JSON) explains how to redefine weights.

#### 2: Edge Case — target already has a config
Devin runs `init --path infrastructure/modules/postgresql/` (which already has a config). Command exits non-zero with `Error: <path>/fitness-config.json already exists`, matching existing `init` behavior.

#### 3: Edge Case — no root config to seed from
Devin runs `init --path some/dir/` in a repo with no root `fitness-config.json`. Command writes the override using `DEFAULT_WEIGHTS` and adds a note that no root was found.

### UAT Scenarios (BDD)

#### Scenario: Init creates a scaffold from current root effective config
Given root `fitness-config.json` exists with the default weights
And `infrastructure/modules/redis/` has no `fitness-config.json`
When Devin runs `fitness-config.py init --path infrastructure/modules/redis/`
Then `infrastructure/modules/redis/fitness-config.json` is created
And it contains all 10 domain weights matching the root values
And `fitness-config.py validate --path infrastructure/modules/redis/` passes
And output names the new file path

#### Scenario: Init refuses to overwrite existing override
Given `infrastructure/modules/postgresql/fitness-config.json` already exists
When Devin runs `fitness-config.py init --path infrastructure/modules/postgresql/`
Then exit code is non-zero
And the error states `<path>/fitness-config.json already exists`
And the existing file is unchanged

#### Scenario: Init with no root falls back to defaults
Given no root `fitness-config.json` exists
When Devin runs `fitness-config.py init --path some/dir/`
Then `some/dir/fitness-config.json` is created
And it contains `DEFAULT_WEIGHTS`
And output notes that no root config was found and defaults were used

### Acceptance Criteria
- [ ] `init --path <dir>` creates `<dir>/fitness-config.json` with current root effective weights as starting point
- [ ] If no root exists, falls back to `DEFAULT_WEIGHTS`
- [ ] Refuses to overwrite an existing file (existing behavior preserved)
- [ ] Generated file passes `validate --path <dir>` immediately
- [ ] Existing `init` (no --path) preserved (NFR-3)

### Outcome KPIs
- **Who**: First-time override authors
- **Does what**: Scaffolds an override without manual JSON editing
- **By how much**: Time-to-first-valid-override under 60 seconds (run init, edit one weight, run validate, all passing)
- **Measured by**: Manual UX test on fresh persona walkthrough
- **Baseline**: N/A (feature does not exist today)

### Technical Notes
- Reuse existing `cmd_init()` in `scripts/fitness-config.py`
- For seeding, call `merge_defaults({})` against the root file (or use `DEFAULT_WEIGHTS` if no root)
- Consider adding a `_comment` field at the top of the JSON for inheritance notes (JSON allows extra fields not in schema's `additionalProperties: false` — confirm in DESIGN if schema needs adjustment)

### Dependencies
- US-01 (for resolver to seed from root)
- US-02 (for "passes validate immediately" guarantee)

---

## US-07: Schema Version Mismatch Produces Clear Error

### Problem
If two different `fitness-config.json` files in the same repo declare different schema versions, the merge result is undefined. Devin needs a hard error, not a silent assumption.

### Who
- Anyone running validate or a review when configs in the chain have mismatched versions

### Solution
Resolver compares `version` between root and child. Mismatch → error with both files named, their versions stated, and the supported version printed.

### Domain Examples

#### 1: Happy Path — both versions match
Root `version=1`, child `version=1`. Merge proceeds.

#### 2: Error — child uses newer version
Root `version=1`, child `version=2`. Resolver errors. Devin sees: "Cannot merge: root has version 1, infrastructure/modules/postgresql/fitness-config.json has version 2. Supported version: 1."

#### 3: Error — child uses older version
Root `version=2`, child `version=1`. Resolver errors with same shape, identifying the older child.

### UAT Scenarios (BDD)

#### Scenario: Matching versions merge successfully
Given root and child both declare `version: 1`
When the resolver runs
Then merging proceeds without error

#### Scenario: Child version newer than root
Given root has `version: 1`
And child has `version: 2`
When Devin runs `fitness-config.py validate --path <dir>`
Then exit code is 1
And the error names both files and their versions
And the error states the supported version (1)

#### Scenario: Child version older than root
Given root has `version: 2`
And child has `version: 1`
When Devin runs `fitness-config.py validate --path <dir>`
Then exit code is 1
And the error names both files and their versions
And the error suggests upgrading the child config

### Acceptance Criteria
- [ ] Resolver reads `version` from every config in the chain
- [ ] Mismatch produces non-zero exit code before any merge attempted
- [ ] Error names all files and their declared versions
- [ ] Error names the supported version (currently 1)

### Outcome KPIs
- **Who**: Maintainers across branches/forks where schema versions might drift
- **Does what**: Surfaces version mismatches as hard errors instead of silent merges
- **By how much**: 100% of mismatched chains detected at validate/review time
- **Measured by**: Functional test with deliberate version mismatch; assert exit code 1
- **Baseline**: 0% (today's validator does not check across files)

### Technical Notes
- Schema version is currently a `const: 1` in `fitness-config.schema.json`
- When a future v2 ships, this story's logic is the migration gate

### Dependencies
- US-01

---

## US-08: All Domain Skills Honor the Override

### Problem
If only `review-full` honors overrides but `review-security` (run individually) doesn't, Devin will hit confusing inconsistencies. Per-domain coverage must be complete.

### Who
- Anyone running an individual `review-<domain>` skill on a subtree

### Solution
Update every `src/review-*/SKILL.md` to call the resolver for its review target. Each skill's report includes the same Config: header lines as review-full.

### Domain Examples

#### 1: Happy Path — review-security on a postgresql module
Devin runs `review-security` scoped to `infrastructure/modules/postgresql/`. The skill's report header shows `Config: infrastructure/modules/postgresql/fitness-config.json (merged with root)` and `Effective weights: data=30 ...`. Even though review-security only scores security dimensions, the header still names effective weights for transparency.

#### 2: Edge Case — review-data on a path with no override
Devin runs `review-data` scoped to `src/some-utility/`. Report header names only the root config.

#### 3: Edge Case — review-data on a path under an accessibility=0 override
Override sets `accessibility=0` (skipped) but `review-data` doesn't care about accessibility. Review proceeds normally, report header names the override.

### UAT Scenarios (BDD)

#### Scenario: review-security on a path with override shows the override in header
Given `infrastructure/modules/postgresql/fitness-config.json` exists
When Devin runs `review-security` scoped to `infrastructure/modules/postgresql/`
Then the security review report's header names the override config
And the header shows the effective weights inline

#### Scenario: All review-<domain> skills produce a Config header line
Given a repo with multiple modules, some with overrides, some without
When Devin runs each `review-<domain>` skill on each module
Then every report's header includes a `Config:` line
And the line correctly names the chain for that scope

#### Scenario: Functional tests cover override-aware behavior per domain
Given the test plan in `tests/functional-tests.md`
When CI runs the test suite
Then there is at least one override-aware scenario per domain skill
And all such scenarios pass

### Acceptance Criteria
- [ ] Every `src/review-*/SKILL.md` documents calling the resolver
- [ ] Every per-domain report includes the Config: and Effective weights: header lines (matching US-03)
- [ ] `tests/functional-tests.md` has at least one override-aware scenario per skill
- [ ] No skill bypasses the resolver to read raw config (FR-7, BR-5)

### Outcome KPIs
- **Who**: Per-domain skill users (anyone running review-architecture, review-security, etc. directly)
- **Does what**: Sees the same override applied as review-full would
- **By how much**: 100% of `review-<domain>` skills honor overrides on subtree-scoped invocations
- **Measured by**: Functional test gate — all per-domain skills must pass override-aware tests
- **Baseline**: 0% (today's per-domain skills don't load fitness-config consistently)

### Technical Notes
- This is the largest story by surface area but mostly mechanical
- Linter/grep audit: no `json.load` of `fitness-config.json` outside the resolver

### Dependencies
- US-01, US-02, US-03 (resolver, merge, header pattern)
