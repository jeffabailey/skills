# Acceptance Criteria: fitness-config-init

This is an index view. The authoritative criteria live in each story in `user-stories.md`. Every AC below is checked by an observable result: output text, file existence, file bytes, or a resolver exit code.

| AC | Story | Criterion | Verified by |
|---|---|---|---|
| AC-01.1 | US-01 | The first output line names the target folder | Output line 1 |
| AC-01.2 | US-01 | With no mode given, the mode is fast and review-full is not invoked | Transcript: no review-full invocation |
| AC-01.3 | US-01 | Purpose, confidence (high, medium, or low), and evidence lines are shown, each naming an existing path | Every cited path exists |
| AC-01.4 | US-01 | A folder with no manifests or source yields purpose "unknown", confidence "low" | geo-notes fixture |
| AC-01.5 | US-01 | A user correction replaces the purpose | Proposal header shows the corrected purpose |
| AC-01.6 | US-01 | The fast scan changes no files, runs no project code, and reads at most 40 files | `git status` clean; transcript tool calls |
| AC-02.1 | US-02 | Exactly 10 schema domains, integers from 0 to 100, summing to 100 | Parse the proposal |
| AC-02.2 | US-02 | Number of reasons = number of values changed from the baseline; each cites evidence | Count and compare |
| AC-02.3 | US-02 | DB service with no UI: reliability and data above the baseline, accessibility below it | ledgerd fixture |
| AC-02.4 | US-02 | Public web frontend: accessibility is the highest weight | jeffbaileyblog fixture |
| AC-02.5 | US-02 | Unknown or low confidence: baseline weights and zero reasons | geo-notes fixture |
| AC-02.6 | US-02 | A user adjustment is applied and re-balanced to 100 | Revised proposal |
| AC-03.1 | US-03 | The written file passes `fitness-config.py validate --path <folder>` and the schema | Exit code 0 plus schema check |
| AC-03.2 | US-03 | The written file equals the accepted proposal, with example key order and 2-space indentation | Byte and object comparison |
| AC-03.3 | US-03 | When a check fails, no file is created and the reason is shown | File absent; message present |
| AC-03.4 | US-03 | An existing config is never modified (skeleton) | Hash before and after |
| AC-03.5 | US-03 | The resolver `Config:` line is shown; the override notice appears under an ancestor config | fieldnotes/services/billing fixture |
| AC-03.6 | US-03 | No other project file is created or changed | `git status` shows only `fitness-config.json` |
| AC-04.1 | US-04 | The diff lists every changed leaf as `path old -> new` plus an unchanged count | ledgerd fixture with prior config |
| AC-04.2 | US-04 | Only `y`/`yes` (case-insensitive) overwrites; anything else leaves the bytes identical | Hash before and after for inputs `n`, empty, `nope` |
| AC-04.3 | US-04 | On confirm, the file equals the diffed proposal and passes both checks | Comparison plus validate |
| AC-04.4 | US-04 | An identical proposal causes no write | mtime unchanged |
| AC-04.5 | US-04 | A malformed current file triggers a notice and still requires confirmation | homelab-cli fixture |
| AC-05.1 | US-05 | Full mode only via the prompt or the `full` argument | Transcript |
| AC-05.2 | US-05 | `docs/fitness-report.md` is disclosed and confirmed before review-full runs | Output order |
| AC-05.3 | US-05 | A changed domain with a review-full finding or skip has a reason citing it | fieldnotes / ledgerd fixtures |
| AC-05.4 | US-05 | One failed domain review is reported and the proposal still completes | Injected failure |
| AC-05.5 | US-05 | Only `docs/fitness-report.md` and `fitness-config.json` are written | `git status` |
| AC-06.1 | US-06 | Each threshold change carries a reason | paygate fixture |
| AC-06.2 | US-06 | `security.confidenceThreshold` stays within 1-10 | Parse |
| AC-06.3 | US-06 | Status bands are contiguous and non-overlapping over 1-10 | Range check |
| AC-06.4 | US-06 | No stakes signal means the three sections equal the baseline | jeffbaileyblog fixture |

Fixtures for DISTILL (all realistic, minimal):

- `ledgerd`: a Go service with pgx, 42 migrations, and a k8s StatefulSet with a PDB
- `jeffbaileyblog`: a Hugo site with content/, layouts/, and a Pages deploy workflow
- `homelab-cli`: a Go CLI with cobra and goreleaser
- `geo-notes`: a README containing "TODO"
- `fieldnotes`: a Rails app with Postgres and public views, plus a root config and a `services/billing` subfolder
- `paygate`: a webhook service with a Stripe/Adyen SDK
