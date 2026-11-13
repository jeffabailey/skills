# Determinism Report

**Skills:** 24 measured  ·  **Window:** last 30 days, all projects (169 sessions)  ·  **Baseline:** 2026-11-13T17:36:51Z, `docs/determinism-baseline.json`

## Baseline

Use cost, mean per run, top ten by total (measured; tokens are chars / 4; cost-eq weights tokens by price):

| Skill | Runs | API calls | Output tok | Tool-result tok | Cost-eq tok | Subagent cost-eq | Total cost-eq (all runs) | Own-script calls | Ad hoc Bash | Inline code | Failed calls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| review-full | 4 | 11.8 | 8,544 | 2,949 | 320,997 | 3,567,423 | 15,553,681 | 3 | 7 | 0 | 0 |
| ai-sanitize | 43 | 8 | 11,423 | 2,922 | 179,610 | 80,931 | 11,203,251 | 11 | 253 | 18 | 8 |
| deslop-rust | 3 | 24.7 | 29,467 | 28,328 | 644,979 | 1,530,054 | 6,525,100 | 6 | 66 | 6 | 2 |
| review-algorithms | 3 | 28.3 | 26,600 | 47,626 | 683,946 | 0 | 2,051,838 | 0 | 83 | 2 | 1 |
| review-testing | 4 | 31.5 | 11,582 | 24,405 | 495,992 | 0 | 1,983,969 | 0 | 116 | 4 | 3 |
| review-data | 3 | 37.3 | 9,476 | 36,587 | 624,209 | 0 | 1,872,628 | 0 | 105 | 5 | 3 |
| review-process | 6 | 18.3 | 8,840 | 18,810 | 297,052 | 0 | 1,782,314 | 11 | 98 | 0 | 9 |
| review-reliability | 4 | 25.8 | 11,929 | 20,959 | 426,299 | 0 | 1,705,196 | 0 | 94 | 6 | 6 |
| review-maintainability | 5 | 20.4 | 10,767 | 17,738 | 325,638 | 0 | 1,628,189 | 15 | 78 | 0 | 3 |
| review-security | 4 | 23.5 | 14,335 | 17,497 | 395,184 | 0 | 1,580,735 | 0 | 89 | 0 | 3 |

Load cost, ten largest bodies (measured):

| Skill | Description (every session) | Body (every run) | References (on demand) | Scripts | Recipe blocks | Data-step hints |
|---|---|---|---|---|---|---|
| deslop-python | 266 | 5,152 | 2,832 in 1 | 4 | 2 | 11 |
| review-usability | 172 | 4,315 | 13,317 in 3 | 0 | 2 | 6 |
| deslop-rust | 238 | 3,552 | 1,432 in 1 | 4 | 1 | 10 |
| fitness-config-init | 152 | 3,242 | 2,566 in 2 | 0 | 0 | 14 |
| review-accessibility | 181 | 2,869 | 42,360 in 3 | 1 | 0 | 8 |
| review-process | 131 | 2,769 | 48,104 in 3 | 1 | 0 | 8 |
| review-maintainability | 168 | 2,763 | 11,254 in 3 | 1 | 0 | 9 |
| review-testing | 113 | 2,752 | 22,783 in 3 | 0 | 0 | 13 |
| review-reliability | 156 | 2,746 | 56,546 in 3 | 0 | 0 | 8 |
| ai-sanitize | 198 | 2,742 | 7,521 in 3 | 2 | 0 | 6 |

- review-full is first: 15.6M cost-eq in 4 runs, and 92% of that is in the subagents it starts (3.57M per run), which run the ten domain review skills.
- ai-sanitize is second by volume (43 runs), not by price: 180k per run. Most of its runs are inside the article loop in `skills-writing`.
- The ten domain review skills cost 300k to 680k per run. Almost every API call in them is a shell command typed by hand (about 800 by-hand calls), and most of those calls read code, which is judgment.
- No runs in the window, static evidence only: agent-hygiene, fitness-config-init, review-jit-test-gen, review-usability.
- review-agent-memory collectors: no memory records a trap in a target skill. The repeated command sequences are inline programs (`python3 -` three times in a row, 3 sessions), which matches candidates 5 and 8.

The candidate numbers below use the per-skill figures from a measurement taken 17 minutes before this baseline; run counts differ by at most one.

## Candidates


All savings are estimates. Total: about 2.6M cost-eq per 30 days, which is about 5% of the measured 54M. That sum counts some work twice, because review-full's subagent cost includes runs of the domain skills. The method is `references/patterns.md` section 6: by-hand calls per run, halved because parallel commands share one API call, minus one call for the new script, priced at the skill's own cost per API call.

| # | Skill | Step → script | Evidence | Est. savings / 30 days | Effort | Confidence |
|---|-------|---------------|----------|------------------------|--------|------------|
| 1 | ai-sanitize | `Detect` greps and cluster count → new `scan-tells.py` | 28 × `grep -niE` in 27 runs, 13 × `grep -nE` in 10, 10 × `grep -n -i` in 10; 141 calls hold a `grep`, in 42 of 43 runs | ~590k cost-eq | M | 8/10 |
| 2 | review-process | git history, tags, layout → extend `git-evidence.sh` | 34 calls hold git history commands (`git log`, `show`, `tag`), in 6 of 6 runs, beside 11 calls of the script | ~276k cost-eq | S | 8/10 |
| 3 | 10 review skills, review-full | scope inventory and applicability facts → ship and extend `scripts/review-context.py` (moved from `.github/scripts/`) | 284 calls hold `ls`/`find`/`wc`/`git ls-files`, in 35 of 36 runs; 19 do nothing else | ~1.0M cost-eq (300k direct + ~700k in review-full subagents) | M | 6/10 |
| 4 | 10 review skills | report self-check → new `scripts/check-report.py` | "Self-check" step in all ten; `sed -i` fixes after the report in 7 runs; a checker written at run time in 1 run | ~300k cost-eq | M | 5/10 |
| 5 | review-agent-memory | sizes and savings arithmetic → extend `collect_sources.py` | 11 inline programs in 4 of 4 runs; `wc -c` by hand in 4 of 4 runs | ~139k cost-eq | M | 6/10 |
| 6 | review-security, review-reliability | workflow, Dockerfile, compose facts and scanner run → new `scripts/ci-facts.py` | `command -v` loop in 3 of 3 security runs; 69 search-only calls in 8 runs; 6 inline programs in 1 reliability run | ~106k cost-eq | M | 6/10 |
| 7 | review-maintainability | import fan-in and cycles → call `import_graph.py`; smell counts → extend `metrics.py` | `grep -c` in 5 of 5 runs, `grep -rln` in 4 of 5, beside 15 calls of `metrics.py` | ~80k cost-eq | S | 6/10 |
| 8 | deslop-rust | programs written at run time → one more script (content not yet known) | 11 inline programs in 2 of 2 runs, beside 6 calls of the 4 scripts | ~94k cost-eq | M | 5/10 |
| 9 | review-testing | test counts per level → new `count-tests.py` | `grep -c` in 4 of 4 runs; 8 inline programs in 3 of 4 runs | ~31k cost-eq | M | 7/10 |

### 1. ai-sanitize: Detect greps and the cluster count

- **Now:** Step 3 (`SKILL.md:61-68`) tells the model to run the `Detect` hints, record each hit, and count hits by category against the cluster rule (0 to 2 isolated, 3 or more in one view). Step 5 (`SKILL.md:86`) tells it to run the greps again. The references hold 32 `Detect` lines (prose 5, ui 24, graphics 3), each a regex the model types again. Measured: 51 grep-first calls in the baseline; 141 calls that hold a `grep` in 42 of 43 runs; 30 inline programs in 14 runs; `md5` by hand in 13 runs to prove that report mode changed nothing.
- **Script:** `scripts/scan-tells.py <target...> [--before <original>]`. It reads the `Detect` patterns from the three references (one source, no second list), picks the medium from the file type, and prints `file:line  rule-id  matched phrase` (capped), then hits per category and per section, and the cluster verdict input ("3+ in one section: yes/no"). With `--before` it prints which hits are gone and which are new, and "unchanged" when the files are the same. About 300 to 500 tokens for one article.
- **Stays with the model:** the removal test and the reason test for each hit, the read for tells that no grep finds (`SKILL.md:63`), every rewrite, and the project-rules search in step 2.
- **Savings estimate:** 141 calls ÷ 43 runs = 3.3 calls per run; halved = 1.64; minus 1 = 0.64 calls. Cost per call = 174,140 ÷ 7.9 = 22,043. 0.64 × 22,043 ≈ 14.1k cost-eq per run × 42 runs ≈ 590k per 30 days. Inside that figure: about 150 to 600 output tokens of typed regex per run. A part of each run belongs to the calling skill, so the true saving can be lower.
- **Verify:** a unit test beside `tests/unit/test_survival_check.py` with a fixture that has a known hit count per rule, an empty file, and a file with no hits. In `compare`, ai-sanitize "Ad hoc Bash" and "Inline code" per run should fall and "Own-script calls" should rise.

### 2. review-process: finish `git-evidence.sh`

- **Now:** Step 4 (`SKILL.md:41`) runs the script, and all 6 runs did (11 calls). The model then typed git commands again in every run: 34 calls hold git history commands such as `git log`, `git show`, and `git tag` (6 of 6 runs), `git tag` in 5 of 6, `ls -a` in 6 of 6, `git ls-files` in 5 of 6. The script prints no tags, no changelog facts, and no top-level layout. `SKILL.md:42-44` also keeps three fallback commands that repeat what the script does (473 characters, about 118 tokens in every run).
- **Script:** extend `skills/review-process/scripts/git-evidence.sh` with three sections: `== releases ==` (tag count, newest tag and date, tag style, CHANGELOG present and its newest heading), `== top level ==` (entries with type), and `== manifests ==` (each manifest with its lockfile, per module). Add `--verify <sha>...` so the self-check "every `commit <sha>` resolves" is one call. About 150 more tokens of output.
- **Stays with the model:** the scores, which vague subjects matter, and whether a missing artifact is a defect for this project.
- **Savings estimate:** 34 calls ÷ 6 runs = 5.7; halved = 2.83; the script is already called, so no call is added. Cost per call = 297,052 ÷ 18.3 = 16,232. 2.83 × 16,232 ≈ 46k per run × 6 runs ≈ 276k per 30 days. Measured separately after the change: body −118 tokens when lines 42-44 become one sentence.
- **Verify:** add cases to `tests/unit/test_git_evidence.py` (a repo with tags, one without, a shallow clone). In `compare`, review-process "Ad hoc Bash" per run should fall from 16.3 and the body should fall by about 118 tokens. The 9 failed calls in 6 runs are a count to watch, not tokens.

### 3. Review skills: one scope inventory, shipped with the plugin

- **Now:** each domain skill finds its scope by hand: test files, runners, and CI (`review-testing/SKILL.md:36-41`), handlers, manifests, workflows, Dockerfiles (`review-security/SKILL.md:36`), compose, manifests, `*.tf` (`review-reliability/SKILL.md:43`), schemas and migrations (`review-data/SKILL.md:36`), hot-path entry points (`review-performance/SKILL.md:50-55`). Measured across the ten skills: 284 by-hand calls hold `ls`, `find`, `wc`, or `git ls-files` (35 of 36 runs); 19 calls do nothing else. review-full then starts ten subagents that each repeat this on the same tree.
- **Script:** the repo already has `scripts/review-context.py` (moved from `.github/scripts/`) (117 lines, tested in `tests/unit/test_review_context.py`). It prints the tracked-file count and whether the data and accessibility domains apply, but only CI uses it. Move it to `scripts/` beside `fitness-config.py`, so the plugin ships it, and extend it: files and lines per language, test files per runner, CI files, Dockerfiles and compose files, IaC, migrations and schemas, manifests and lockfiles, with build and vendor directories skipped. About 300 to 500 tokens. review-full runs it one time and gives the output to each subagent.
- **Stays with the model:** which dimensions are N/A and why, where the hot paths are, and what to read.
- **Savings estimate:** inventory-only calls 19 ÷ 35 = 0.54 per run. Mixed calls (284 − 19) ÷ 35 = 7.6; halved = 3.8; I credit one quarter to inventory = 0.95 (assumption). 0.54 + 0.95 − 1 for the script = 0.49 calls. Cost per call across the ten skills = 15,484,159 ÷ 894 = 17,320. 0.49 × 17,320 ≈ 8.5k per run × 35 runs ≈ 300k per 30 days. Inside review-full: its subagents cost 3,567,423 cost-eq per run. If the one shared inventory and the resolver output in the prompt remove 1 of about 27 calls in each of ten domain agents, that is 10 × 17,320 ≈ 173k per run × 4 runs ≈ 700k per 30 days (assumption: 1 call per agent). Total ≈ 1.0M.
- **Verify:** extend `tests/unit/test_review_context.py` with a fixture tree that has a known count per category. In `compare`, "Ad hoc Bash" per run should fall for the ten skills; the ten bodies should not grow.

### 4. Review skills: a gate for the report self-check

- **Now:** all ten domain skills end with "Self-check, then write" (`review-testing/SKILL.md:66-70`, `review-algorithms/SKILL.md:58-63`, `review-performance/SKILL.md:65-69`, `review-process/SKILL.md:52`, `review-security/SKILL.md:63`, and the same step in the other five). Most of it is fact: each cited path exists and is repo-relative, the line number is inside the file, each commit resolves, each finding states a confidence of 7 or more, and the overall equals the mean of the scored dimensions with the CRITICAL cap at 4.0. Signs that the model does this by hand: `sed -i` on the report in 7 runs (maintainability 3, architecture 2, performance 2), `python3 -c` in 2 performance runs, and a `check.py` written at run time in 1 testing run.
- **Script:** `scripts/check-report.py <report.md> [--repo <root>]`. It prints one line per failure (`missing path`, `line 412 > 380 lines`, `overall 7.4 != mean 7.2`, `finding 3: no confidence`), then each citation with the first 100 characters of the cited line, so the model can confirm every claim from one output. Exit 0 or 1. `review-full/scripts/overall.py` already does the weighted overall for review-full; this covers the unweighted mean in the domain reports.
- **Stays with the model:** whether the cited line says what the finding claims, the scores, and the severities.
- **Savings estimate:** assumption: the self-check now takes about 1.5 calls per run and the script takes 1, so 0.5 calls saved. 0.5 × 17,320 ≈ 8.7k per run × 35 runs ≈ 300k per 30 days. The transcripts do not show which reads belong to the self-check, hence confidence 5. The stronger reason is correct reports: line numbers and the overall are checked the same way every time.
- **Verify:** unit tests with three fixture reports (clean, a wrong line number, a wrong mean). In `compare`, "Inline code" should go to 0 for review-testing and review-performance.

### 5. review-agent-memory: sizes and arithmetic from the collectors

- **Now:** all 4 runs called the two collectors (13 calls) and all 4 also wrote programs: 11 inline `python3 -c` calls, `wc -c` by hand in 4 of 4 runs, `ls` in 4 of 4, and 7 failed calls. The skill asks for token estimates and savings arithmetic (`SKILL.md:59`), and the collectors do not print every size the findings cite.
- **Script:** extend `collect_sources.py` (and `mine_transcripts.py` if needed) to print the size in tokens of every file it lists, and add `--size <path>...` for the files a finding names. Before writing it, watch one run to see what the inline programs compute; the transcripts show that they exist, not what they do.
- **Stays with the model:** which signals are findings, the fix for each, and the ranking.
- **Savings estimate:** 11 inline calls ÷ 4 runs = 2.75; halved = 1.38; no call is added. Cost per call = 341,909 ÷ 13.5 = 25,327. 1.38 × 25,327 ≈ 34.8k per run × 4 runs ≈ 139k per 30 days.
- **Verify:** a fixture project with known file sizes in the collector's tests. In `compare`, review-agent-memory "Inline code" should fall from 7 toward 0.

### 6. review-security and review-reliability: CI and container facts

- **Now:** review-security step 4 (`SKILL.md:40-45`) is a recipe: check each scanner with `command -v`, then run what exists. The model typed that loop in 3 of 3 runs. Step 6 (`SKILL.md:49`) runs four fixed greps from `references/checklist.md:227-230` (expression injection, `pull_request_target`, permissions, action pinning). review-reliability step 5 (`SKILL.md:52-56`) asks for `timeout-minutes` on every job in every workflow, pinned actions and images, healthchecks, restart policy, and limits. Measured: 69 search-only calls in 8 runs (security 39, reliability 30) and 6 inline programs in 1 reliability run.
- **Script:** `scripts/ci-facts.py <target>`. Per workflow job: `timeout-minutes`, `permissions`, `concurrency`, each `uses:` and whether it is pinned to a SHA, `pull_request_target`, and `${{ github.event.* }}` inside `run:`. Per Dockerfile: `USER`, `:latest` bases, `ENV` names that look like secrets (names only). Per compose service: image pin, healthcheck, restart, limits. It also runs the installed scanners (gitleaks with `--redact`, zizmor or actionlint, pip-audit or osv-scanner) and prints counts and `file:line`, never values. Standard library only; a small YAML reader for these keys, or line patterns marked approximate.
- **Stays with the model:** whether an input is attacker-controlled, whether a missing timeout matters for that job, and every severity.
- **Savings estimate:** security: 39 ÷ 4 = 9.75 search-only calls per run; one quarter credited to these fixed checks = 2.4 (assumption); halved = 1.2; plus 1 scanner call; minus 1 = 1.2 calls × 16,541 ≈ 19.8k × 3 runs ≈ 60k. Reliability: 30 ÷ 4 = 7.5; one quarter = 1.9; halved = 0.94; plus inline 6 ÷ 4 ÷ 2 = 0.75; minus 1 = 0.69 calls × 16,523 ≈ 11.4k × 4 runs ≈ 46k. Total ≈ 106k per 30 days. A per-job check is also a fact that a reader misses easily, so this helps correctness more than cost.
- **Verify:** fixture workflows (a job with no timeout, an unpinned action, an injected expression), a Dockerfile, and a compose file with known answers. In `compare`, "Ad hoc Bash" per run should fall for both skills and review-reliability "Inline code" should go to 0.

### 7. review-maintainability: use the scripts that exist

- **Now:** step 8 (`SKILL.md:55`) says "Trace imports: fan-in per module, cycles" by hand. `skills/review-architecture/scripts/import_graph.py` prints exactly that. Steps 7 and 9 (`SKILL.md:53`, `:57`) ask for TODOs with no issue reference, duplicated blocks, commented-out code, and smells per 1,000 non-blank lines. `metrics.py` prints the markers and `nonblank_loc`, but not these counts. Measured: `metrics.py` ran 15 times in 5 runs, and the model still typed `grep -c` in 5 of 5 runs and `grep -rln` in 4 of 5.
- **Script:** (a) call `../review-architecture/scripts/import_graph.py` in step 8; no new code. (b) extend `metrics.py`: mark each TODO that has no issue reference, count commented-out code lines, and print the per-1,000-line rates.
- **Stays with the model:** cognitive complexity, naming, whether a long function hurts, and which smells are real.
- **Savings estimate:** 22 search-only calls ÷ 5 runs = 4.4; half credited to these counts = 2.2 (assumption); halved = 1.1; the graph script adds a call and the `metrics.py` change adds none, so about 1.0 call. 1.0 × 15,963 ≈ 16k per run × 5 runs ≈ 80k per 30 days.
- **Verify:** add cases to `tests/unit/test_metrics.py` (a TODO with and without an issue reference, a known rate). In `compare`, review-maintainability "Ad hoc Bash" per run should fall from 15.6.

### 8. deslop-rust: the programs the model writes in every run

- **Now:** the skill has four scripts and called them 6 times in 2 runs. Both runs also wrote programs: 11 inline `python3 -` calls, plus 61 calls that hold a `grep`. The transcripts do not show what the programs compute. The likely steps are the totals in Phase 3 (`SKILL.md:149`, "Totals if all items are approved") and reading tool output that the four scripts do not parse.
- **Script:** not named yet. Watch one run, then give the program a file in `skills/deslop-rust/scripts/` (or a subcommand of `kill_matrix.py`), tested like the others. deslop-python shares three of the four scripts, so the same gap can be there.
- **Stays with the model:** the classification of each test and what to remove.
- **Savings estimate:** 11 ÷ 2 = 5.5 inline calls per run; halved = 2.75; minus 1 = 1.75. Cost per call = 722,529 ÷ 27 = 26,760. 1.75 × 26,760 ≈ 46.8k per run × 2 runs ≈ 94k per 30 days.
- **Verify:** a test with a small fixture of tool output. In `compare`, deslop-rust "Inline code" should fall from 5 to 0.

### 9. review-testing: count the tests

- **Now:** step 4 (`SKILL.md:45-52`) lists a collector command per language and a grep fallback, then asks for counts per level. The model typed `grep -c` in 4 of 4 runs and wrote 8 inline programs in 3 of 4 runs.
- **Script:** `skills/review-testing/scripts/count-tests.py <target>`. It finds the runners, runs each collector read-only when the toolchain is there, falls back to a pattern count and says so, and prints tests per runner and per directory with a first guess at the level from path names. About 200 tokens.
- **Stays with the model:** the final unit, integration, and E2E split when the paths do not show it, and whether the pyramid is healthy.
- **Savings estimate:** inline 8 ÷ 4 = 2 calls plus about 1 count call per run = 3; halved = 1.5; minus 1 = 0.5. 0.5 × 15,746 ≈ 7.9k per run × 4 runs ≈ 31k per 30 days. The main reason is the same counts in every run.
- **Verify:** fixture projects for pytest and one brace language with a known test count, and a run with the toolchain missing. In `compare`, review-testing "Inline code" should fall from 4.

## Not candidates

- **Reading code in the review skills** (330 calls that read files, in 36 runs): this is the judgment input. A script cannot choose what to read.
- **review-algorithms**: its by-hand work is edge-input probes (steps 6 and 7), which change with every target. Only candidates 3 and 4 apply to it.
- **review-data, review-performance, review-architecture, review-accessibility**: no step of their own passed the test. Candidates 3 and 4 apply. review-architecture and review-accessibility already call their scripts.
- **Resolver calls** (`fitness-config.py show`): 66 calls in about 32 runs where 32 are expected (review-testing 11 in 4 runs, review-reliability 12 in 4). The transcripts do not show the cause (a call per target, a failed first call, or a repeat for the report header). Watch one run before any change. If each extra call is its own API call, this is up to about 590k cost-eq per 30 days (34 × 17,320).
- **review-full**: already scripted (`overall.py`, 3 calls in 3 runs, 0 inline programs). Its cost is the ten subagents. Candidate 3 lowers that a little; the rest is a design question (how many domains to start), not a script.
- **version-skills**: already scripted (6 script calls in 5 runs). The inline programs are in 1 run only.
- **ask-why**: all judgment. The by-hand commands (`gh run view`, `git show`) change with each question.
- **generate-commit** (1 run), **review-apply** (1 run), **deslop-python** (1 run): each has recipe blocks (`generate-commit/SKILL.md:16`, `:105`; `review-apply/SKILL.md:176`; `deslop-python/SKILL.md:67`, `:100`). One run is too little to rank. Per-run estimate only: one entry point in place of a 4 to 10 command block saves 1 to 2 calls. No usage data for a 30-day number.
- **No runs in the window, static evidence only:** agent-hygiene, fitness-config-init, review-jit-test-gen, review-usability. Two static notes for later: the agent-hygiene inventory (`SKILL.md:22-31`) is what `review-agent-memory/scripts/collect_sources.py` already prints, and review-usability has two recipe blocks (`SKILL.md:22`, 12 commands; `SKILL.md:39`, 5 commands).
- **Large review checklists read whole** (item 5 of `docs/agent-memory-review.md`): a section index is a loading fix, not a script.
- **the-deterministic-maker**: its 4 runs are test runs of this skill. No candidate.
- **Out of scope:** `.agents/skills/find-skills` is vendored and pinned in `skills-lock.json`.

## After

All nine candidates were applied on 2026-11-13. Compared with `docs/determinism-baseline.json`.

### Load cost (measured)

| Skill | Version | Description | Body | References | Scripts | Recipe blocks | Data-step hints | Body tokens / 30 days (projected) |
|---|---|---|---|---|---|---|---|---|
| ai-sanitize | 1.0.0 → 1.1.0 | 198 | 2,742 → 2,738 (-4) | 7,521 → 7,589 (+68) | 2 → 3 (+1) | 0 | 6 → 4 (-2) | -172 |
| deslop-rust | 1.0.0 → 1.1.0 | 238 | 3,552 | 1,432 → 1,460 (+28) | 4 → 5 (+1) | 1 | 10 → 8 (-2) | +0 |
| review-accessibility | 1.0.1 → 1.1.0 | 181 | 2,869 → 2,868 (-1) | 42,360 | 1 | 0 | 8 → 7 (-1) | -1 |
| review-agent-memory | 1.0.0 → 1.1.0 | 288 | 2,048 → 2,045 (-3) | 2,380 → 2,438 (+58) | 2 | 0 | 5 → 4 (-1) | -12 |
| review-algorithms | 1.0.0 → 1.1.0 | 165 | 2,684 | 52,146 | 0 | 0 | 9 | +0 |
| review-architecture | 1.0.2 → 1.1.0 | 146 | 2,600 | 26,216 | 1 | 0 | 12 → 10 (-2) | +0 |
| review-data | 1.0.0 → 1.1.0 | 140 | 2,519 → 2,509 (-10) | 32,918 | 0 | 0 | 8 → 6 (-2) | -30 |
| review-full | 1.0.2 → 1.1.0 | 88 | 2,481 → 2,658 (+177) | 0 | 1 | 0 | 6 | +708 |
| review-maintainability | 1.0.1 → 1.1.0 | 168 | 2,763 → 2,762 (-1) | 11,254 | 1 | 0 | 9 | -5 |
| review-performance | 1.0.0 → 1.1.0 | 148 | 2,494 → 2,492 (-2) | 27,908 | 0 | 0 | 10 → 8 (-2) | -6 |
| review-process | 1.0.0 → 1.1.0 | 131 | 2,769 → 2,724 (-45) | 48,104 | 1 | 0 | 8 → 5 (-3) | -270 |
| review-reliability | 1.0.0 → 1.1.0 | 156 | 2,746 → 2,736 (-10) | 56,546 | 0 | 0 | 8 → 6 (-2) | -40 |
| review-security | 1.0.0 → 1.1.0 | 141 | 2,631 → 2,620 (-11) | 26,469 | 0 | 0 | 9 → 7 (-2) | -44 |
| review-testing | 1.0.0 → 1.1.0 | 113 | 2,752 → 2,631 (-121) | 22,783 | 0 → 1 (+1) | 0 | 13 → 9 (-4) | -484 |
| the-deterministic-maker | 1.0.0 → 1.0.1 | 264 | 2,319 | 1,824 | 1 | 0 | 5 | +0 |

The projection is the body change times the run rate before the change.

Other skills: 9 unchanged.

### Use cost (not measured yet)

No skill has been used in its new version. `compare` lists a few "runs since" for ai-sanitize, review-full, and review-maintainability; those are the agents that made these edits reading the SKILL.md files, or sessions that ran the old version, so they are not evidence. Run `compare` again after real use.

### Applied items

| Item | Measured now | Estimated per 30 days (from Candidates) |
|------|--------------|------------------------------------------|
| 1. ai-sanitize → `scan-tells.py` | body 2,742 → 2,738 tokens; script prints ~111 tokens for one file, ~676 capped for a tree; 11 tests | ~590k cost-eq |
| 2. review-process → `git-evidence.sh` sections and `--verify` | body 2,769 → 2,724; script output 1,246 → 1,565 tokens on this repo; 14 new tests | ~276k |
| 3. scope inventory → `scripts/review-context.py --inventory`, passed by review-full to each subagent with the resolved config | prints ~360 tokens; review-full body 2,481 → 2,658 (+177); ten domain bodies flat or smaller; 5 new tests | ~1.0M (700k of it assumes one call fewer per subagent) |
| 4. self-check → `scripts/check-report.py` | prints 200 to 960 tokens per report; 12 tests | ~300k |
| 5. review-agent-memory → `--size`, `--estimate` | body 2,048 → 2,045; `--size` ~160 tokens, `--estimate` ~71; 9 tests | ~139k |
| 6. security and reliability → `scripts/ci-facts.py` | prints ~366 tokens; 8 tests; only actionlint ran as a real scanner | ~106k |
| 7. review-maintainability → `import_graph.py` call, `metrics.py` counts | `metrics.py` output 8,019 → 7,338 chars; 6 new tests | ~80k |
| 8. deslop-rust → `suite_scan.py` (`scan`, `totals`) | body unchanged; ~220 tokens on one crate; 11 tests | ~94k |
| 9. review-testing → `count-tests.py` | body 2,752 → 2,631; prints ~342 tokens; 10 tests | ~31k |

Limits:

- Candidates 5 and 8 were designed from the skill text, not from a watched run. Whether they replace the programs the model wrote at run time is unconfirmed.
- ai-sanitize: 51 `Detect` hints are now "by reading" and are not scanned; the split is a judgment call for the reference owner to review.
- review-testing: only pytest and Go use a collector; other runners get a labelled pattern count. Gherkin scenarios can be counted twice.
- No eval or live run of the changed skills was made.

To replace the estimates with measurements after the skills have been used:

```bash
python3 skills/the-deterministic-maker/scripts/measure_skills.py compare docs/determinism-baseline.json
```

## Measured after one run (2026-11-13)

One whole-repository run of review-full (eight domain subagents; data and accessibility skipped), one review-agent-memory report run, and one ai-sanitize report run on `README.md`. One run per skill, on this repo only, so treat each number as a single sample. The "before" means come from 3 to 6 runs on several repos.

| Skill | API calls per run | Ad hoc Bash per run | Cost-eq per run | Note |
|---|---|---|---|---|
| review-testing | 31.5 → 11 | 29 → 9 | 495,992 → 251,846 | |
| review-architecture | 29 → 11 | 23.7 → 10 | 492,607 → 291,014 | |
| review-reliability | 25.8 → 11 | 23.5 → 10 | 426,299 → 242,431 | |
| review-security | 23.5 → 11 | 22.2 → 12 | 395,184 → 240,431 | |
| review-process | 18.3 → 7 | 16.3 → 5 | 297,052 → 209,673 | |
| review-performance | 22.7 → 16 | 21 → 15 | 409,938 → 514,582 | cost rose: 68,643 tool-result tokens against 26,365 |
| review-algorithms | 28.3 → 30 | 27.7 → 19 | 683,946 → 1,586,323 | cost rose: it started a helper agent and reported 35 findings |
| review-agent-memory | 13.5 → 15 | 8.2 → 5 | 341,909 → 276,085 | |

Not usable as measurements: review-maintainability, review-full, and ai-sanitize each show two or three "runs since", and at least one of them is an editing agent that read the SKILL.md, so their means are mixed.

Sum over the eight domain runs: about 3.5M cost-eq before (sum of the means) and about 3.5M after. Six skills fell by 30% to 50%; review-algorithms and review-performance rose and cancelled that.

What the runs still did by hand (from each run's own list):

- Script-to-test mapping (testing, architecture, maintainability each built it with grep loops).
- Per-file line counts for source files; the inventory prints language totals only (testing, performance, algorithms).
- Eval fixtures are not marked in the inventory (maintainability, performance).
- Step-level timeouts, images pulled in `run:` steps, and unpinned installs in `run:` steps are not in `ci-facts.py` (reliability, security). review-testing and review-performance need CI facts and do not call it.
- `check-report.py` confirms a cited line exists but does not find line numbers; every run looked them up with grep.
- `metrics.py` prints no counts over the Severe thresholds and has no duplicate-block detection (maintainability).
- review-agent-memory: quotients and sums over the miner's totals, lists cut at the top 12, no since-date view, context stores the collector did not list.
- ai-sanitize `scan-tells.py`: skipped hints are not itemised, hits print without line context, the header counts all media, and it missed a contrast-framing line.

Defects the review found in the scripts added by this change (see `docs/algorithms-review.md`): `ci-facts.py:259-269` (checkout marked safe from the previous step), `review-context.py:62-67` (rules matched on the absolute path), `count-tests.py:149-152` (paths with a space dropped), `git-evidence.sh:106-117` (`via_pr_pct` from two windows), `measure_skills.py:510-511` (`--since` with a date only crashes), `measure_skills.py:717` (`compare` stops on a removed skill).
