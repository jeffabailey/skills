# Process Review Scoring Rubric

Hand-maintained scoring rubric. sync-wisdom does not regenerate this file.

Score each dimension from what `scripts/git-evidence.sh` printed and what you read in the repo. Pick the highest band whose conditions all hold. When a repo sits between two bands, take the lower band's top score (for example 6, not 7).

## Severity

| Severity | Definition | Process examples |
|----------|------------|------------------|
| CRITICAL | The process is broken or misleading: a stated safeguard does not exist, or contributors cannot legally or practically take part. | README names a license and no LICENSE file exists in a repo published for outside use; secrets committed to history with no rotation note. |
| HIGH | A core safeguard is missing or never runs, or a newcomer cannot run the project without editing code. | The only CI workflow sits in `sub/.github/workflows/`, which GitHub never runs; code defaults point into `/Users/<name>/`; CONTRIBUTING requires PRs but most commits on main are direct pushes. |
| MEDIUM | A practice exists but is inconsistent or stale enough to mislead or slow contributors. | Conventional-commit rate 40-79% while CONTRIBUTING requires the convention; README points to paths that no longer exist. |
| LOW | Polish: the gap costs little today. | No CODE_OF_CONDUCT in a solo project; no status badge. |

Missing LICENSE when you cannot tell whether the repo is public (no remote, private clone): rate it HIGH and say it becomes CRITICAL once published. If the user asks about outside contributors, treat the repo as intended for publication.

## Dimension anchors

### 1. Documentation Quality
- **9-10:** README covers purpose, prerequisites, setup, usage, tests, contributing, license; every path it names exists; ADRs or design docs explain major choices; CONTRIBUTING.md present.
- **7-8:** README covers setup, usage, and tests; CONTRIBUTING present or linked; at most 1-2 stale references.
- **5-6:** README usable but missing two or more of setup/tests/contributing/license; or 3+ stale references (paths, commands, or claims that no longer match the repo); no design rationale anywhere.
- **3-4:** README is a title plus a paragraph, or mostly out of date; no contributor guidance.
- **1-2:** No README, or the README contradicts how the project actually runs.

### 2. Development Workflow
- **9-10:** CI at root `.github/workflows/` (or equivalent) runs tests and lint on every PR and blocks merge; branch strategy consistent; conventional-commit rate >= 80% with 0 vague subjects (when a convention is claimed).
- **7-8:** Root CI runs tests on push/PR; convention rate 60-79% or a few vague subjects; branch strategy evident in history.
- **5-6:** CI exists but runs only part of the checks (lint only, or tests not gating), or the convention rate is 40-59%.
- **3-4:** CI file exists but never runs (nested, disabled, or wrong trigger), or no CI and tests run only by hand; convention rate < 40% while one is claimed.
- **1-2:** No CI, no tests to run, no recognizable commit or branch practice.
- If no convention is claimed anywhere (CONTRIBUTING, README, commitlint config, PR template), judge messages on descriptiveness instead, not on Conventional Commits. A commit-message tool in the repo or a habit visible in history is not a claim. Repeated placeholder subjects (`repeated_subjects`) count as vague.

### 3. Code Review Practices
- **9-10:** >= 80% of changes on the default branch arrive via PR (merge commits or `(#N)` squash subjects); CODEOWNERS and a PR template exist; branch protection documented.
- **7-8:** 50-79% via PR, PR template or CODEOWNERS present.
- **5-6:** 20-49% via PR, or PRs used but no template, CODEOWNERS, or review guidance.
- **3-4:** < 20% via PR while the repo has several human authors or a written PR-required policy.
- **1-2:** No PRs, several human authors, and no review step at all.
- PR rate = `via_pr_pct` from git-evidence.sh. Bot PRs (Dependabot, Renovate, sync jobs) show automation, not human review; mention them but do not let them lift the band.
- Solo repos (one human author) replace the PR-rate bands above with these, because direct commits are normal in solo trunk-based work: **7-8** PR template, CODEOWNERS, and a review section in CONTRIBUTING all present; **5-6** one or two of them; **3-4** none of them. A solo repo reaches 9-10 only if PRs are also used. Flag direct pushes only when they contradict a written policy.

### 4. Dependency Management
- **9-10:** Every package manifest has a committed lockfile; automated updates (Dependabot/Renovate) configured; vulnerability scan in CI; license compliance noted.
- **7-8:** Lockfiles committed for every manifest; either update automation or scanning, not both.
- **5-6:** Lockfiles for some manifests only, or versions unbounded in places; no update automation.
- **3-4:** No lockfiles; floating versions (`*`, `latest`) in manifests.
- **1-2:** Dependencies undeclared (vendored copies or install instructions only in prose).
- In a monorepo, check each module's manifest. Credit per-module lockfiles; do not report "no lockfile" because the root has none.

### 5. Project Organization
- **9-10:** Layout matches the language's convention; entry points obvious; config separated from code with `.env.example` or documented defaults; `.gitignore` covers the stack; no build artifacts or large binaries tracked.
- **7-8:** Clear layout with one or two hygiene gaps (an IDE file, a missing `.env.example`).
- **5-6:** Modules exist but boundaries blur (scripts at root, duplicated helpers), or tracked artifacts.
- **3-4:** Flat dump of files; config and secrets mixed into code.
- **1-2:** No discernible structure.

### 6. Portability
- **9-10:** No developer-specific absolute paths in code or setup docs; paths and endpoints configurable; devcontainer, Dockerfile, or scripted setup; `.gitattributes`/`.editorconfig` set line endings; CI runs on the platforms claimed.
- **7-8:** Configurable paths and a documented setup that works off the author's machine; at most one OS assumption, documented.
- **5-6:** A few hardcoded absolute paths in docs or defaults, or OS-only tooling (Homebrew-only, PowerShell-only) without alternatives.
- **3-4:** Default paths point into one developer's home directory (`/Users/<name>/...`); setup assumes sibling repos at fixed locations.
- **1-2:** Cannot run anywhere but the author's machine.
- Absolute paths inside test fixtures, CI runner paths (`/home/runner`), or illustrative docs are not findings.

### 7. Technical Leadership Signals
- **9-10:** Vision or roadmap doc; ADRs with alternatives and trade-offs; issues triaged with labels; tech debt tracked; changelog or release notes show iteration.
- **7-8:** Decisions recorded somewhere (ADRs, design docs, or detailed PR descriptions); a changelog or regular releases.
- **5-6:** Some rationale in commits or docs, but no decision record or roadmap.
- **3-4:** Decisions invisible; TODO/FIXME debt with no tracking.
- **1-2:** No sign of planning, decisions, or iteration.
- Issue trackers and boards live outside the repo. Do not score what you cannot see; say "not visible from the repository" and score only the in-repo evidence.

## N/A

Mark a dimension `N/A — <reason>` when nothing in scope can be judged, for example Dependency Management for a repo with no package manifests, or Code Review for a single-commit scratch repo. N/A dimensions are left out of the overall.

Do not use N/A for something that should exist and is missing; that is a low score. Cite an absence by the place it should be: `.github/workflows/ (none)`, `LICENSE (absent; README.md:389 names MIT)`.

## Evidence locations

A finding's Location is one of:
- `path:line` for file content (line must exist);
- `path (absent)` for a missing file, with the place it should be;
- `commit <sha>` for one commit (from `git log`);
- `git log <range or command>` for a measured rate, quoting the numbers (for example `git log --first-parent main: 60/65 direct`).

## Overall

Overall = mean of the scored (non-N/A) dimensions, one decimal. If any CRITICAL finding exists, cap the overall at 4.0. Status bands: a score at or above `statusThresholds.healthy[0]` is Healthy, at or above `statusThresholds.needsAttention[0]` is Needs Attention, anything lower is Critical (defaults 8 / 5 when the resolver gives none). Only the lower bounds count, so a fractional score such as 7.5 is Needs Attention, never a gap; review-full uses the same rule.
