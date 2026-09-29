<!-- markdownlint-disable MD024 -->

# User Stories: fitness-config-init

## System Constraints

- The deliverable is one skill, `skills/fitness-config-init/SKILL.md`, plus optional `references/`. It follows the sibling skill layout and frontmatter (`name`, `description` with trigger phrases, `## Workflow`).
- The skill never hardcodes default weights in its prose. The baseline comes from a single source (DQ-3), consistent with ADR-002 / FR-7 of fitness-config-per-directory.
- The written file must be consumable by the existing resolver unchanged (`fitness-config.py show|validate --path`), including in subfolders where it acts as an override.
- No runtime dependencies beyond the Python 3 stdlib (D-10 of fitness-config-per-directory).
- Every story carries `job_id: J-FCI-01`. The job statement is in `requirements.md`. The registry `docs/product/jobs.yaml` is absent; see DQ-8.

Baseline weights used in the examples (identical to `fitness-config.example.json` today): architecture 14, security 14, reliability 10, testing 10, performance 10, algorithms 10, data 10, accessibility 8, process 8, maintainability 6.

---

## US-01: Classify project purpose from a fast scan

`job_id: J-FCI-01` | Release: Walking Skeleton | MoSCoW: Must

### Elevator Pitch

- **Before**: Priya opens `ledgerd` and has no idea which fitness domains matter most. The only starting point is a generic example file.
- **After**: Priya invokes `/fitness-config-init` in `ledgerd`, accepts the default mode, and sees `Purpose: database-backed service (no UI) | Confidence: high`. Below that is a list of evidence paths (`go.mod: pgx/v5`, `migrations/ (42 .sql)`, `deploy/k8s/statefulset.yaml`).
- **Decision enabled**: Priya confirms the purpose or corrects it before any weights are proposed.

### Problem

Priya Raman maintains `ledgerd`, a Postgres-backed ledger service with no UI. She wants reviews to focus on what matters, but nothing today says what her project *is* in fitness terms. She would have to reason it out herself for all ten domains.

### Who

- Maintainer adopting fitness reviews | invokes the skill from the project root | wants a quick, credible read of the project before trusting any numbers

### Solution

The skill starts by naming the target folder and offering the evidence mode, with fast as the default. It reads purpose signals and reports the purpose, the confidence, and cited evidence.

### Domain Examples

#### 1: Happy path: ledgerd

`go.mod` lists `pgx/v5` and `golang-migrate`. `migrations/` holds 42 `.sql` files. `deploy/k8s/statefulset.yaml` has a PodDisruptionBudget. There are no `.html`, `.tsx`, or `.css` files. Result: "database-backed service (no UI)", confidence high.

#### 2: Edge: jeffbaileyblog

This is a Hugo site. The evidence is `hugo.toml`, `content/` with 180 posts, `layouts/`, and `.github/workflows/deploy.yml` publishing to GitHub Pages. Result: "public web frontend (static site)", confidence high.

#### 3: Boundary: empty idea folder

Ana Lima runs the skill in `~/scratch/geo-notes`, which contains only a README saying "TODO". Result: "unknown", confidence low, with the message "Not enough evidence; I'll propose baseline values."

### UAT Scenarios (BDD)

#### Scenario: Maintainer sees what the skill thinks the project is, and why

Given Priya is in `/Users/priya/src/ledgerd`, which contains go.mod with pgx/v5, 42 migrations, and a StatefulSet
When she invokes fitness-config-init and accepts the default mode
Then she sees the purpose "database-backed service (no UI)" with confidence "high"
And each evidence line names a path that exists in ledgerd

#### Scenario: Fast scan is the default evidence mode

Given Jeff invokes fitness-config-init in jeffbaileyblog without naming a mode
When he presses Enter at the mode prompt
Then the evidence header reads "fast scan"
And no review-full pass is started

#### Scenario: Sparse folder is reported as unknown instead of guessed

Given Ana's `~/scratch/geo-notes` contains only a README with the text "TODO"
When she invokes fitness-config-init
Then the purpose is "unknown" with confidence "low"
And she is told baseline values will be proposed

#### Scenario: Maintainer corrects a wrong classification

Given the skill classified Tomas's `homelab-cli` as "library"
When Tomas replies "it's a CLI tool"
Then the purpose used for the proposal is "CLI tool"

#### Scenario: Fast scan leaves the project untouched

Given Priya's ledgerd working tree is clean in git
When the fast scan finishes
Then `git status` in ledgerd still shows a clean tree

### Acceptance Criteria

- [ ] The first output line names the target folder
- [ ] With no mode given, the evidence mode is fast and review-full is not invoked
- [ ] Output includes the purpose, a confidence of high, medium, or low, and at least one evidence line per claim, each naming an existing path
- [ ] A folder with no manifests and no source files yields purpose "unknown", confidence "low"
- [ ] A one-line user correction replaces the classified purpose
- [ ] The fast scan modifies no files, runs no project code, and reads at most 40 files

### Outcome KPIs

- **Who**: maintainers running the skill | **Does what**: accept the classified purpose without correcting it | **By how much**: 80% or more of runs across 10 dogfood repos | **Measured by**: dogfood log (repo, classified purpose, corrected y/n) | **Baseline**: none (no classification exists today)

### Technical Notes

- Purpose categories: database-backed service, public web frontend, CLI tool, data pipeline, library, mixed, unknown. DESIGN may refine the list (DQ-4, DQ-5).
- Evidence sources are read-only file reads. No build or test commands.

### Dependencies

- None

---

## US-02: Propose purpose-tuned weights with a reason for each change

`job_id: J-FCI-01` | Release: Walking Skeleton | MoSCoW: Must

### Elevator Pitch

- **Before**: Priya copies the example file. Accessibility stays at 8 on a service with no UI, and reliability stays at 10 on a system whose downtime loses ledger writes.
- **After**: The skill shows a table of domain, default, proposed, and why. The row `reliability 10 -> 18: StatefulSet + PDB; downtime loses ledger writes` appears, the total is 100, and unchanged rows are marked "(unchanged)".
- **Decision enabled**: Priya accepts the weights or asks for a specific change before anything is written.

### Problem

Priya knows reliability and data matter most for `ledgerd`, but rebalancing ten weights to exactly 100 by hand is fiddly. Six months from now she won't remember why she chose 18.

### Who

- Same maintainer, after US-01 | wants weights that match the purpose | needs the reasoning to trust the numbers and explain them to reviewers

### Solution

From the purpose and evidence, the skill proposes all ten weights summing to 100. Each changed value gets one line of reasoning that cites evidence. Where the rationale is persisted is DQ-1.

### Domain Examples

#### 1: Happy path: ledgerd

Proposed: reliability 18, data 18, security 14, architecture 10, testing 10, performance 10, algorithms 8, process 6, maintainability 5, accessibility 1. The total is 100. Seven values changed, and each has a reason.

#### 2: Edge: jeffbaileyblog

Proposed: accessibility 18, performance 14, process 12, maintainability 12, security 10, architecture 10, testing 8, reliability 8, data 4, algorithms 4. Example reason: "accessibility 8 -> 18: public site, 180 posts read by the general public."

#### 3: Boundary: geo-notes (unknown purpose)

All ten weights equal the baseline. There are no rationale rows. The message reads "Kept baseline: not enough evidence to tune."

### UAT Scenarios (BDD)

#### Scenario: Reliability-critical service gets reliability and data weighted up

Given ledgerd was classified "database-backed service (no UI)" with high confidence
When the skill proposes weights
Then reliability and data are each higher than their baseline of 10
And accessibility is lower than its baseline of 8
And the ten weights sum to exactly 100

#### Scenario: Every changed weight comes with a reason tied to the project

Given the ledgerd proposal changes 7 of 10 weights
When Priya reads the proposal table
Then there are exactly 7 reasons
And each reason cites a path or finding from the evidence list

#### Scenario: Public website gets accessibility weighted up

Given jeffbaileyblog was classified "public web frontend (static site)"
When the skill proposes weights
Then accessibility is the highest weight
And data is lower than its baseline of 10

#### Scenario: Unknown project keeps baseline weights

Given geo-notes was classified "unknown" with low confidence
When the skill proposes weights
Then all ten weights equal the baseline
And no rationale rows are shown

#### Scenario: Maintainer adjusts a proposed weight before writing

Given the ledgerd proposal has performance 10
When Priya says "performance 12, take it from architecture"
Then the revised proposal shows performance 12 and architecture 8
And the total is still 100

### Acceptance Criteria

- [ ] The proposal contains exactly the 10 schema domains, each an integer from 0 to 100, summing to 100
- [ ] The number of reasons equals the number of values that differ from the baseline, and each reason cites an evidence path or finding
- [ ] A database-backed service with no UI has reliability and data above the baseline and accessibility below it
- [ ] A public web frontend has accessibility as its highest weight
- [ ] An unknown or low-confidence purpose yields baseline weights and zero reasons
- [ ] A user adjustment is applied and the total re-balanced to 100 before the proposal is final

### Outcome KPIs

- **Who**: maintainers running the skill | **Does what**: accept proposed weights with at most 1 manual adjustment | **By how much**: 80% or more of runs | **Measured by**: dogfood log (adjustments per run) | **Baseline**: 0% (today every tuned config is hand-edited)

### Technical Notes

- Purpose-to-weights mapping is DQ-4 (profiles vs judgment, floor for no-surface domains).
- Rationale persistence is DQ-1. The printed table is mandatory in every option.
- The skill must not hardcode baseline weights in its prose (System Constraints).

### Dependencies

- US-01

---

## US-03: Write only a valid config, never over an existing one

`job_id: J-FCI-01` | Release: Walking Skeleton | MoSCoW: Must

### Elevator Pitch

- **Before**: A hand-edited config with weights summing to 101 makes the resolver fail the next time `review-full` runs.
- **After**: The skill prints `Schema check: pass`, `Resolver check: pass`, `Wrote /Users/priya/src/ledgerd/fitness-config.json`, and then the `Config:` line from `fitness-config.py show --path`.
- **Decision enabled**: Priya runs `review-full` knowing it will use these weights.

### Problem

A config that doesn't validate breaks every later review. A config silently written over an existing one destroys someone's tuning. Both failures surface later and far from their cause.

### Who

- Same maintainer | expects the file on disk to be correct and wants any prior work preserved

### Solution

The skill checks the proposal against the schema and the resolver validator. It writes `<folder>/fitness-config.json` only when both pass and no file exists yet. Then it shows the resolver chain. If a file exists, the skeleton refuses to overwrite and prints the proposal; US-04 adds diff and confirm.

### Domain Examples

#### 1: Happy path: ledgerd, no prior config

Both checks pass, and the file is written. The chain shows `Config: fitness-config.json`.

#### 2: Edge: subfolder override

Kenji runs the skill in `fieldnotes/services/billing`, and `fieldnotes/fitness-config.json` already exists. The file is written, and he sees "This is an override of fieldnotes/fitness-config.json. It applies to reviews scoped to services/billing; root-scope reviews use the root config (ADR-005)."

#### 3: Error: invalid proposal

After an adjustment the weights sum to 101. The skill prints "Not written. Proposed weights sum to 101 (must be 100)." along with the proposal, and no file appears.

### UAT Scenarios (BDD)

#### Scenario: Valid config is written to a project that had none

Given ledgerd has no fitness-config.json
And the accepted proposal passes the schema and resolver checks
When the skill writes the config
Then `/Users/priya/src/ledgerd/fitness-config.json` exists
And running `fitness-config.py validate --path .` in ledgerd reports it valid
And its contents equal the accepted proposal

#### Scenario: Invalid proposal is never written

Given an accepted proposal whose weights sum to 101
When the skill reaches the write step
Then no fitness-config.json is created
And the message states the weights sum to 101 and must be 100

#### Scenario: Existing config is not overwritten in the walking skeleton

Given ledgerd already has a fitness-config.json
When the skill reaches the write step without diff support
Then the existing file is byte-identical to before
And the proposal is printed for manual use

#### Scenario: Config in a subfolder is announced as an override

Given `fieldnotes/fitness-config.json` exists and Kenji runs the skill in `fieldnotes/services/billing`
When the config is written
Then the summary shows the resolver chain with the new file as the override and the root file as root
And it states that root-scope reviews use only the root config

### Acceptance Criteria

- [ ] The written file passes `fitness-config.py validate --path <folder>` and conforms to `fitness-config.schema.json`
- [ ] The written file parses to the same object as the accepted proposal, with key order following the example and 2-space indentation
- [ ] When either check fails, no file is created and the failure reason is shown
- [ ] An existing `fitness-config.json` is never modified by this story
- [ ] After writing, the resolver's `Config:` line for the folder is shown; under an ancestor config, the override notice is shown
- [ ] No other file in the project is created or changed

### Outcome KPIs

- **Who**: maintainers who ran the skill | **Does what**: run review-full afterward without a config error | **By how much**: 100% of skill-written files pass `validate` | **Measured by**: functional test and dogfood log | **Baseline**: unknown; hand-edited configs are unmeasured

### Technical Notes

- The resolver is at `${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py` (review-full convention).
- Validation mechanics before writing are DQ-6. The schema alone cannot enforce the sum. The resolver alone does not check weight key names or bounds.
- The baseline for a subfolder is DQ-3.

### Dependencies

- US-02
- Existing `scripts/fitness-config.py validate|show --path`, which has shipped (fitness-config-per-directory)

---

## US-04: Review a diff before replacing an existing config

`job_id: J-FCI-01` | Release: R1 | MoSCoW: Must

### Elevator Pitch

- **Before**: When `ledgerd` already has a config, the skeleton only prints a proposal. Priya has to merge it by hand.
- **After**: The skill prints per-value changes (`weights.reliability 12 -> 18`, and so on), then `(5 values unchanged)`, then `Overwrite /Users/priya/src/ledgerd/fitness-config.json? [y/N]`.
- **Decision enabled**: Priya keeps her current config or replaces it, knowing exactly what changes.

### Problem

Priya tuned `ledgerd`'s config in June. She wants a fresh proposal but fears losing a deliberate choice, such as accessibility 4.

### Who

- A maintainer with an existing config | re-running the skill after the project changed | protective of past decisions

### Solution

When a config exists, the skill shows a value-level diff and asks for confirmation, defaulting to No. It writes only on `y`/`yes`.

### Domain Examples

#### 1: Happy path: accept

ledgerd has reliability 12, data 12, and accessibility 4. The diff shows 5 changes. Priya types `y`, and the file is replaced and validated.

#### 2: Edge: identical

Jeff re-runs the skill on jeffbaileyblog, and the proposal equals the current file. The skill prints "No changes; fitness-config.json already matches." and nothing is written.

#### 3: Error: malformed existing file

`homelab-cli/fitness-config.json` has a trailing comma. The skill prints "Current file is not valid JSON; cannot diff by value," shows the proposal, and still asks before overwriting.

### UAT Scenarios (BDD)

#### Scenario: Maintainer sees exactly which values would change

Given ledgerd's current config has reliability 12, data 12, accessibility 4
When the proposal has reliability 18, data 18, accessibility 1
Then the diff lists those three changes with old and new values
And it states how many values are unchanged

#### Scenario: Declining keeps the current config

Given the overwrite prompt is shown for ledgerd
When Priya answers "n" or just presses Enter
Then fitness-config.json is byte-identical to before

#### Scenario: Confirming replaces the config with the reviewed proposal

Given the overwrite prompt is shown for ledgerd
When Priya answers "y"
Then fitness-config.json equals the proposal shown in the diff
And it passes `fitness-config.py validate --path .`

#### Scenario: Nothing to do when the proposal matches

Given jeffbaileyblog's config equals the new proposal
When the skill compares them
Then it reports no changes
And the file's modification time is unchanged

#### Scenario: Broken current file still needs confirmation

Given homelab-cli's fitness-config.json is not valid JSON
When the skill reaches the compare step
Then it says the current file cannot be diffed by value
And it asks before overwriting

### Acceptance Criteria

- [ ] The diff lists every changed leaf value as `path old -> new` plus a count of unchanged values
- [ ] Only `y` or `yes` (case-insensitive) overwrites; any other input, including empty input, leaves the file byte-identical
- [ ] On confirm, the written file equals the diffed proposal and passes both checks
- [ ] An identical proposal causes no write
- [ ] A malformed current file triggers a notice, and the overwrite still requires confirmation

### Outcome KPIs

- **Who**: maintainers with an existing config | **Does what**: re-run the skill and keep or replace their config with no lost edits | **By how much**: 0 unconfirmed overwrites; 60% or more of re-runs end in an accepted overwrite | **Measured by**: functional tests plus dogfood log | **Baseline**: the skeleton refuses 100% of the time

### Technical Notes

- The diff covers all top-level keys (weights, statusThresholds, security, scoring). Unknown keys in the current file are shown as removals.
- Consider a backup of the replaced file (DESIGN).

### Dependencies

- US-03

---

## US-05: Use a full review to sharpen the proposal

`job_id: J-FCI-01` | Release: R2 | MoSCoW: Should

### Elevator Pitch

- **Before**: A fast scan of `fieldnotes` (Rails app, Postgres, public pages) can't tell whether the public pages or the database dominate.
- **After**: Kenji runs `/fitness-config-init full`. After a notice that `docs/fitness-report.md` will be written, the review runs, and the proposal's reasons cite findings. For example: "data 10 -> 16: review-data found 3 unsafe migrations in db/migrate."
- **Decision enabled**: Kenji accepts weights grounded in actual review findings, not just file names.

### Problem

For mixed or unusual projects, file names alone underdetermine the purpose. Kenji Watanabe is willing to spend a slow full review to get weights he trusts.

### Who

- Maintainer of a mixed or ambiguous project | has time for a full review | wants the strongest evidence

### Solution

When the user picks full mode (at the prompt or as an argument), the skill discloses the side effect and then runs `review-full` on the folder. It uses domain presence, skipped domains, and findings as extra evidence. How scores map to weights is DQ-2.

### Domain Examples

#### 1: Happy path: fieldnotes

review-full scores all 10 domains. review-data finds 3 unsafe migrations. The proposal raises data, and its reason cites the finding.

#### 2: Edge: domain skipped

On ledgerd, review-full skips accessibility because there is no frontend code. The proposal cites "review-full skipped accessibility: no frontend files."

#### 3: Error: one domain fails

On homelab-cli, review-performance errors out. The skill says "performance: review failed, using fast-scan evidence" and continues.

### UAT Scenarios (BDD)

#### Scenario: Maintainer is warned before a full review writes a report

Given Kenji chooses the full review for fieldnotes
When the skill is about to start review-full
Then it states that docs/fitness-report.md will be written in fieldnotes
And it proceeds only after Kenji confirms

#### Scenario: Review findings appear in the reasons for changed weights

Given review-full on fieldnotes reported 3 unsafe migrations under review-data
When the skill proposes weights
Then the data reason cites that finding

#### Scenario: Skipped domain is lowered with the review as evidence

Given review-full on ledgerd skipped accessibility for lack of frontend files
When the skill proposes weights
Then the accessibility reason cites the skip

#### Scenario: A failed domain review does not stop the proposal

Given review-performance fails during the full review of homelab-cli
When the skill proposes weights
Then the performance value uses fast-scan evidence
And the output says the performance review failed

### Acceptance Criteria

- [ ] Full mode is selectable at the prompt or with the `full` argument; fast is never upgraded to full silently
- [ ] Before running, the skill names `docs/fitness-report.md` as a file that will be written and waits for confirmation
- [ ] At least one reason cites a review-full finding or skip whenever review-full produced one for a changed domain
- [ ] A single failed domain review is reported and does not abort the proposal
- [ ] No files other than `docs/fitness-report.md` and `fitness-config.json` are written in full mode

### Outcome KPIs

- **Who**: maintainers choosing full mode | **Does what**: accept proposals with no manual adjustment | **By how much**: 10 or more percentage points above the fast-mode acceptance rate | **Measured by**: dogfood log split by mode | **Baseline**: fast-mode rate from KPI-1

### Technical Notes

- Invokes `skills/review-full` as-is. No changes to review-full.
- Score semantics are DQ-2.

### Dependencies

- US-02
- `skills/review-full` (exists)

---

## US-06: Tune thresholds and security cutoff to purpose

`job_id: J-FCI-01` | Release: R3 | MoSCoW: Could

### Elevator Pitch

- **Before**: `paygate`, a payment webhook service, hides security findings below confidence 7. That is the same cutoff used by a static blog.
- **After**: The proposal includes `security.confidenceThreshold 7 -> 5: handles card-network webhooks; surface lower-confidence findings`, and `statusThresholds` shows healthy [9,10], needsAttention [6,8], critical [1,5].
- **Decision enabled**: Priya accepts stricter thresholds for a high-stakes service, or keeps the baseline.

### Problem

Weights say what matters. Thresholds say how strict to be. A payment service and a hobby blog should not share "healthy = 8+" or the same security-confidence cutoff.

### Who

- Maintainer of a high-stakes or low-stakes project | wants strictness proportional to risk

### Solution

The skill optionally proposes `statusThresholds`, `security.confidenceThreshold`, and `scoring` changes, each with a reason, keeping ranges contiguous (BR-6).

### Domain Examples

#### 1: Happy path: paygate

The confidence threshold goes from 7 to 5, and healthy is raised to [9,10], with reasons citing the payment webhooks.

#### 2: Edge: jeffbaileyblog

All thresholds stay at the baseline, with the message "no stakes signal to change thresholds."

#### 3: Error: range gap

A draft proposal of healthy [9,10] and needsAttention [5,7] leaves 8 uncovered. The skill must correct the gap before showing the proposal.

### UAT Scenarios (BDD)

#### Scenario: High-stakes service gets stricter thresholds with reasons

Given paygate was classified as a payment-handling service
When the skill proposes the config
Then security.confidenceThreshold is below the baseline of 7
And each changed threshold has a reason

#### Scenario: Ordinary project keeps baseline thresholds

Given jeffbaileyblog was classified "public web frontend (static site)"
When the skill proposes the config
Then statusThresholds, security, and scoring equal the baseline

#### Scenario: Status bands always cover every score from 1 to 10

Given any proposal that changes statusThresholds
When it is shown
Then the healthy, needsAttention, and critical ranges cover 1 to 10 with no gaps or overlaps

### Acceptance Criteria

- [ ] Threshold changes each carry a reason
- [ ] `security.confidenceThreshold` stays within 1-10
- [ ] The statusThresholds ranges are contiguous and non-overlapping over 1-10
- [ ] With no stakes signal, all three sections equal the baseline

### Outcome KPIs

- **Who**: maintainers of high-stakes services | **Does what**: keep proposed stricter thresholds without editing them | **By how much**: 70% or more | **Measured by**: dogfood log | **Baseline**: 0% (nobody tunes thresholds today)

### Technical Notes

- The resolver does not validate range contiguity. DESIGN decides whether to add that check (DQ-6).

### Dependencies

- US-02
