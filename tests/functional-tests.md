# Functional Tests

Verify each skill produces correct, useful output.

## Test Protocol

For each test scenario:
1. Clone a test repository (or use the skills repo itself)
2. Run the skill
3. Verify the output matches expected structure
4. Verify findings are real (no false positives)
5. Verify file:line references are accurate

## review-architecture

### Test: Scores are produced for all dimensions

**Given:** A codebase with at least 5 source files
**When:** Run `/review:review-architecture`
**Then:**
- Report contains scores (1-10) for: Coupling, Cohesion, Layering, Modularity, Naming, API Design, Maintainability
- Each score has at least one file:line evidence citation
- Scores below 6 generate action items

### Test: Detects circular dependencies

**Given:** Module A imports B, B imports A
**When:** Run `/review:review-architecture`
**Then:** Coupling score reflects the circular dependency with specific file references

### Test: Detects poor naming

**Given:** Code with single-letter variables, generic names like `data`, `temp`, `process()`
**When:** Run `/review:review-architecture`
**Then:** Naming score reflects issues with specific examples

## review-security

### Test: High-confidence findings only

**Given:** Code with an obvious SQL injection (string concatenation in query)
**When:** Run `/review:review-security`
**Then:**
- Finding is reported with HIGH severity
- Confidence is 8/10 or higher
- File:line reference points to the vulnerable code
- Remediation suggests parameterized queries

### Test: No false positives for safe patterns

**Given:** Code using parameterized queries, proper auth middleware, bcrypt hashing
**When:** Run `/review:review-security`
**Then:** No findings for these safe patterns

### Test: Privacy checks work

**Given:** Code that logs user email addresses
**When:** Run `/review:review-security`
**Then:** Data Protection finding about PII in logs

## review-reliability

### Test: Detects missing observability

**Given:** A service with no logging, no metrics, no health checks
**When:** Run `/review:review-reliability`
**Then:**
- Observability score is low (1-3)
- Specific recommendations for what to instrument
- References golden signals framework

### Test: Detects missing timeouts

**Given:** HTTP client calls without timeout configuration
**When:** Run `/review:review-reliability`
**Then:** Timeout/Retry Hygiene score reflects the gap

## review-testing

### Test: Detects inverted test pyramid

**Given:** Project with 50 E2E tests, 5 unit tests
**When:** Run `/review:review-testing`
**Then:**
- Test Pyramid Balance score is low
- Recommends adding unit tests
- Identifies which functions lack unit coverage

### Test: Detects test quality issues

**Given:** Tests with no assertions, tests named "test1", "test2"
**When:** Run `/review:review-testing`
**Then:** Test Quality score reflects naming and assertion issues

## review-performance

### Test: Detects N+1 queries

**Given:** ORM code that queries in a loop
**When:** Run `/review:review-performance`
**Then:**
- Database Design score reflects the N+1 pattern
- Specific file:line reference to the loop

### Test: Detects quadratic algorithms

**Given:** Nested loops over the same collection
**When:** Run `/review:review-performance`
**Then:** Algorithmic Efficiency score flags O(n^2) with evidence

## review-algorithms

### Test: Detects wrong data structure choice

**Given:** Code using a list for frequent lookups by key (linear scan instead of hash map)
**When:** Run `/review:review-algorithms`
**Then:**
- Data Structure Selection score reflects the mismatch
- Specific file:line reference to the list-based lookup
- Recommends hash map or set

### Test: Detects race conditions

**Given:** Shared mutable state accessed from multiple threads without synchronization
**When:** Run `/review:review-algorithms`
**Then:**
- Concurrency Safety score is low
- Specific file:line reference to the unprotected shared state
- Recommends synchronization or concurrent data structures

### Test: Detects edge case gaps

**Given:** Function that divides by a parameter without checking for zero
**When:** Run `/review:review-algorithms`
**Then:** Edge Case Handling score reflects the missing guard

## review-data

### Test: Detects missing foreign keys

**Given:** Database schema with related tables but no foreign key constraints
**When:** Run `/review:review-data`
**Then:**
- Data Integrity score reflects the gap
- Specific file:line reference to the table definitions
- Recommends adding foreign key constraints

### Test: Detects unsafe migrations

**Given:** Migration that adds a NOT NULL column without a default value
**When:** Run `/review:review-data`
**Then:**
- Migration Safety score reflects the risk
- Recommends add column, backfill, then add constraint pattern

### Test: Detects schema issues

**Given:** Table with all VARCHAR(255) columns including dates and numbers
**When:** Run `/review:review-data`
**Then:** Schema Design score is low with specific type recommendations

## review-accessibility

### Test: Detects missing alt text

**Given:** HTML with images lacking alt attributes
**When:** Run `/review:review-accessibility`
**Then:** Screen Reader Support score reflects the gap

### Test: Detects non-semantic HTML

**Given:** Clickable divs instead of buttons, missing form labels
**When:** Run `/review:review-accessibility`
**Then:** Semantic HTML score is low with specific elements cited

## review-process

### Test: Detects missing documentation

**Given:** Repo with no README or a minimal README
**When:** Run `/review:review-process`
**Then:** Documentation Quality score is low with specific suggestions

### Test: Detects stale dependencies

**Given:** package.json with dependencies 2+ major versions behind
**When:** Run `/review:review-process`
**Then:** Dependency Management score reflects staleness

## review-maintainability

### Test: Scores are produced for all dimensions

**Given:** A codebase with at least 5 source files
**When:** Run `/review:review-maintainability`
**Then:**
- Report contains scores (1-10) for: Structural Complexity, Comprehensibility, Technical Debt, Coupling/Dependency Depth, Code Smell Density
- Each score has at least one file:line evidence citation
- Report written to `docs/maintainability-review.md`

### Test: Detects high cyclomatic complexity

**Given:** Function with deeply nested conditionals (4+ levels)
**When:** Run `/review:review-maintainability`
**Then:** Structural Complexity score reflects the nesting with specific file:line reference

### Test: Detects code smells

**Given:** Code with duplicated blocks, god classes, or long methods
**When:** Run `/review:review-maintainability`
**Then:** Code Smell Density score is low with specific examples cited

## review-full

### Test: Produces unified report

**Given:** Any codebase
**When:** Run `/review:review-full`
**Then:**
- Report written to docs/fitness-report.md
- Contains overall score (weighted average)
- Contains all domain scores in table format
- Contains top 10 prioritized action items
- Each domain has detailed findings section

### Test: Skips accessibility for backend-only projects

**Given:** A Python/Go/Java project with no frontend files
**When:** Run `/review:review-full`
**Then:** Accessibility section notes "Skipped - no frontend code detected"

## review-jit-test-gen

### Test: Generates tests for changed code

**Given:** Modified Python/JS/TS file with a new function
**When:** Run `/review:review-jit-test-gen`
**Then:**
- Test file is created following project conventions
- Test covers the new function
- Test uses descriptive name
- Test passes when run

### Test: Doesn't duplicate existing tests

**Given:** File with changes that are already well-tested
**When:** Run `/review:review-jit-test-gen`
**Then:** Reports that existing coverage is sufficient, generates only gap-filling tests

## review-apply

### Test: Fetches and parses a fitness report issue

**Given:** An open GitHub issue with the `fitness-review` label containing a fitness report
**When:** Run `/review:review-apply` with the issue URL
**Then:**
- Action items are extracted and listed by priority
- Each item is classified as actionable or deferred
- User is presented with a triage for confirmation

### Test: Addresses actionable items

**Given:** A fitness report with actionable items referencing specific files
**When:** User confirms the triage
**Then:**
- Referenced files are read and modified
- Changes are minimal and targeted to the action item
- A summary of changes is produced

### Test: Closes the issue after completion

**Given:** All actionable items have been addressed from a GitHub issue source
**When:** Changes are complete
**Then:**
- A comment is posted to the issue with a summary
- The issue is closed with reason "completed"

### Test: Falls back to local file when no open issue exists

**Given:** No open GitHub issue with the `fitness-review` label, and `docs/fitness-report.md` exists with a valid fitness report
**When:** Run `/review:review-apply` with no arguments
**Then:**
- The local file is read as the report source
- Action items are extracted and triaged normally
- After completion, the summary is presented directly (no issue comment or close)

### Test: Reads a user-specified local file

**Given:** A fitness report at a non-default path (e.g., `reports/review.md`)
**When:** Run `/review:review-apply reports/review.md`
**Then:**
- The specified file is read as the report source
- Action items are extracted and triaged normally

## review-usability

### Test: Downloads the current article before scoring

**Given:** Network access to jeffbailey.us
**When:** Run `/review:review-usability` against any public URL
**Then:**
- The article's `llm.txt` is fetched to `${TMPDIR:-/tmp}/review-usability/` before any scoring
- The report header's "Rubric source" line names the live URL and fetch date

### Test: Falls back to the bundled copy when offline

**Given:** No network access to jeffbailey.us, but the target site is reachable (for example, a local build)
**When:** Run `/review:review-usability`
**Then:**
- The review still completes using `references/wisdom.md`
- The "Rubric source" line says fallback, so the reader knows the rubric may be older than the live article

### Test: Walks tasks instead of reading code

**Given:** A live URL and a browser automation tool
**When:** Run `/review:review-usability`
**Then:**
- 3 to 5 top tasks are listed and walked at desktop and phone widths
- Every finding cites a URL and an element or task step, not a file:line
- Report written to docs/usability-review.md with all five dimension scores

### Test: Does not guess without a browser

**Given:** A live URL and no browser automation tool
**When:** Run `/review:review-usability`
**Then:** Interaction-dependent checks appear under "Not Verified" rather than as passes or failures

### Test: Keeps recommendations proportionate

**Given:** A static personal blog with no forms or destructive actions
**When:** Run `/review:review-usability`
**Then:** Undo, confirmation, and bulk-operation checks are marked N/A and do not lower any score


### Test: Re-review tracks prior findings

**Given:** A previous usability report for the same site
**When:** Run `/review:review-usability` again after fixes
**Then:**
- The summary table has a "Prev" column
- A "Prior Findings" table gives each earlier finding a status (Fixed, Still present, Deferred, or Not verifiable here) with evidence
- The same top tasks are walked, and each fix is probed for regressions

## ai-sanitize

### Test: Rewrites prose tells without changing facts or voice

**Given:** A Markdown draft with emdashes, "Here's the kicker", an "It's not X, it's Y" line, a closing "Curious what others think?", and the author's own profanity
**When:** Run `/ai-sanitize draft.md`
**Then:**
- Every emdash, the kicker phrase, the contrast line, and the closing question are rewritten or removed
- The profanity, facts, numbers, code blocks, and links are unchanged
- The report lists each change with its `references/prose.md` item number

### Test: Strips a generated UI composition using existing tokens

**Given:** A React hero with a purple gradient blob, an uppercase eyebrow, pill buttons, glass cards, a pulsing "Active" badge, and a project `tailwind.config` with defined colors and radii
**When:** Run `/ai-sanitize src/components/Hero.tsx`
**Then:**
- The blob, eyebrow, glass, and constant "Active" badge are removed
- Remaining colors and radii come from the existing config; no new colors, fonts, or button variants appear
- The page is rendered (or marked not verified) at desktop and phone widths

### Test: Keeps intentional choices

**Given:** A project whose documented brand uses a purple gradient, and a status badge whose state changes
**When:** Run `/ai-sanitize`
**Then:** Both appear under "Kept on purpose" with the reason, and neither is edited

### Test: Report mode edits nothing

**Given:** Any target with tells
**When:** Run `/ai-sanitize report src/`
**Then:**
- `git status` shows no modified files
- The report has a "Proposed changes" table with location, tell, and fix

### Test: Verifies ASCII art and SVG by rendering

**Given:** A README with a hand-drawn ASCII banner that misspells the project name, and an SVG icon row with mixed stroke widths
**When:** Run `/ai-sanitize README.md assets/icons/`
**Then:**
- The banner is removed or regenerated with a real tool, and the fix is checked by rendering
- Icons are normalized to one stroke width and size, or the finding says not verified if rendering was unavailable

## fitness-config-init

These are the `@manual` agent-eval scenarios in `tests/acceptance/fitness-config-init/`. Pytest never runs them. The resolver side of the skill (validation, fingerprint, save, rollback) is covered by `uv run pytest tests`.

### Procedure

1. Build each fixture below as a throwaway git repo with one initial commit, so the working tree starts clean.
2. For each scenario, start a fresh agent session in the fixture and invoke `/fitness-config-init` with the arguments the scenario states. Answer the prompts as the scenario states.
3. Record the transcript, the tool calls (count the file reads for the 40-file fast-scan budget), and `git status` after the run.
4. Check each Then line of the scenario against the transcript and the files. Every cited evidence path must exist in the fixture.
5. Run `python3 scripts/fitness-config.py validate --path <fixture>` on any saved `fitness-config.json`.

### Fixtures

- `ledgerd`: a Go service with pgx, 42 migrations, and a k8s StatefulSet with a PDB
- `jeffbaileyblog`: a Hugo site with `content/`, `layouts/`, and a Pages deploy workflow
- `homelab-cli`: a Go CLI with cobra and goreleaser
- `geo-notes`: a README containing "TODO" and nothing else
- `fieldnotes`: a Rails app with Postgres and public views, plus a root `fitness-config.json` and a `services/billing` subfolder
- `paygate`: a webhook service with a Stripe or Adyen SDK

### Test: Fast scan classifies without touching the project

**Given:** The `ledgerd` fixture with a clean working tree
**When:** Run `/fitness-config-init` with no arguments
**Then:**
- The first output line names the target folder
- The mode is fast and review-full is not invoked
- Purpose, confidence, and evidence lines are shown, and each evidence line names an existing path
- At most 40 files are read, no project code runs, and `git status` is clean before the save

### Test: Weights follow the project's purpose

**Given:** The `ledgerd` and `jeffbaileyblog` fixtures
**When:** Run `/fitness-config-init fast` in each
**Then:**
- The proposal has exactly 10 domains, integers from 0 to 100, summing to 100
- `ledgerd`: reliability and data are above the baseline and accessibility is below it
- `jeffbaileyblog`: accessibility is the highest weight
- The number of reasons equals the number of values changed from the baseline, and each reason cites evidence
- No value moves more than 4 from the matching profile

### Test: An unknown project keeps the starting weights

**Given:** The `geo-notes` fixture
**When:** Run `/fitness-config-init fast`
**Then:** Purpose is "unknown", confidence is "low", the weights equal the baseline, and there are zero reasons

### Test: Corrections and adjustments are applied

**Given:** Any fixture where the classification is wrong or medium confidence
**When:** Correct the purpose in one reply, then change one proposed weight
**Then:**
- A medium-confidence classification asks for the primary purpose before proposing
- The proposal header shows the corrected purpose
- The adjusted weight is applied and the rest re-balance to 100

### Test: Saving writes only the approved config

**Given:** The `homelab-cli` fixture with no config
**When:** Accept the proposal
**Then:**
- The written file passes `fitness-config.py validate` and the schema, and equals the accepted proposal with example key order and 2-space indentation
- `git status` shows only `fitness-config.json`
- The resolver `Config:` line is shown after the save

### Test: A subfolder save shows the inherited root config

**Given:** The `fieldnotes` fixture
**When:** Run `/fitness-config-init fast services/billing` and accept
**Then:** The output shows the resolver `Config:` line and the notice that the root config is overridden for this folder

### Test: Replacing an existing config needs an explicit yes

**Given:** The `ledgerd` fixture with a prior `fitness-config.json`, and the `homelab-cli` fixture with a malformed one
**When:** Run `/fitness-config-init` and answer the overwrite question with `n`, an empty reply, `nope`, then `yes`
**Then:**
- The diff lists every changed leaf as `path old -> new` plus an unchanged count, and the question names the file and defaults to no
- Only `y` or `yes` (any case) overwrites; the other replies leave the file bytes identical
- An identical proposal causes no write (mtime unchanged)
- The malformed file triggers a notice and still requires confirmation

### Test: Full mode discloses the report and uses its findings

**Given:** The `fieldnotes` fixture with a clean working tree
**When:** Run `/fitness-config-init full` and accept
**Then:**
- Full mode starts only from the `full` argument, clear wording, or the prompt
- The output names `docs/fitness-report.md` and asks for confirmation before review-full runs
- A changed domain with a review-full finding or skip has a reason citing it
- `git status` shows only `docs/fitness-report.md` and `fitness-config.json`

### Test: A failed domain review does not stop the proposal

**Given:** The `homelab-cli` fixture, with review-performance made to fail during the full review
**When:** Run `/fitness-config-init full`
**Then:** The output says the performance review failed, the performance value uses fast-scan evidence, and the proposal completes

### Test: Full mode on a dirty tree does not use a narrowed review

**Given:** The `fieldnotes` fixture with uncommitted changes, so review-full reports a scope of changed files instead of the `fieldnotes` folder
**When:** Run `/fitness-config-init full`
**Then:**
- The skill checks the report's `**Scope:**` line against the target folder
- It says review-full reviewed changes only and its results are not used
- The proposal uses fast-scan evidence

### Test: Thresholds tighten only with a stakes signal

**Given:** The `paygate` and `jeffbaileyblog` fixtures
**When:** Run `/fitness-config-init fast` in each
**Then:**
- `paygate`: each threshold change carries a reason, `security.confidenceThreshold` stays within 1-10, and status bands are contiguous and non-overlapping over 1-10
- `jeffbaileyblog`: the three threshold sections equal the baseline
