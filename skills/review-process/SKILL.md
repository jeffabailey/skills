---
name: review-process
description: Evaluates a repository's development process maturity across documentation, workflow, code review, dependency management, project organization, portability, and leadership signals, using repo files and git history. Use when the user says /review:process or /review:review-process, requests a process review, asks for development process fitness scores, wants to assess repo health or contributor readiness, or asks how well a project follows software development best practices. Only reports findings with confidence >= 7/10.
---

# Development Process Fitness Review

Judge how a repository is developed, not what its code does: whether a newcomer can set it up, whether checks actually run, how changes reach the default branch, and whether decisions are visible. Much of that evidence lives in git history rather than in any file, so this review reads both.

Reference: [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/), [Fundamentals of Agile Software Development](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-agile-software-development/), [Fundamentals of Software Project Management](https://jeffbailey.us/blog/2026/01/12/fundamentals-of-software-project-management/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

- `references/rubric.md` is the scoring source: severity definitions, 1-10 anchors per dimension, N/A rules, accepted evidence locations, and the overall formula. It is short; read it first.
- `references/checklist.md` is what to check, grouped by the seven dimensions, including pitfalls a quick existence check misses.
- `scripts/git-evidence.sh` gathers the history and layout numbers the rubric uses.
- `references/wisdom.md` is optional background generated from the source articles (about 45k tokens). Never read it whole; grep it by heading when you need the reasoning behind a practice, such as `grep -n "Trunk-Based" references/wisdom.md`.

## Configuration

Invoke the resolver CLI to obtain effective weights and thresholds for the review target. Never load `fitness-config.json` directly.

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py" show --path <target>
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; the resolver ships two levels up in the plugin's `scripts/`. If your agent does not expand the variable, substitute the directory containing this `SKILL.md`.

Where `<target>` is the file or directory under review. The CLI walks up to discover any module override and merges it with the root config. Copy the `Config:` and `Effective weights:` lines from the resolver output into the report header (the template has the slots) as the provenance trail (AC-03.1, AC-08.2). The `effective` object inside the JSON block delimited by `<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->` / `<!-- END_EFFECTIVE_CONFIG_JSON -->` carries `statusThresholds`, which override the default status bands in rubric.md. If the resolver is not at that path (for example a standalone install), use `scripts/fitness-config.py` from a checkout of the plugin; if none is available, write `Config: resolver unavailable (defaults)` and use the rubric.md bands.

## Workflow

1. **Load the rubric** — Read `references/rubric.md` and `references/checklist.md`. Run the resolver above.

2. **Scope** — Identify the repository root containing the target and whether the user asked a specific question (for example "is this ready for contributors?"). That question shapes the Direct Answer and which findings lead.

3. **Decide applicability** — For each of the seven dimensions, decide whether anything in scope can be judged. Mark the rest `N/A — <reason>` per rubric.md; a missing artifact that should exist is a low score, not N/A.

4. **Gather git evidence** — Run `bash "${CLAUDE_SKILL_DIR}/scripts/git-evidence.sh" <repo-root>`. It is read-only and prints: commit counts and authors; conventional-commit rate and vague subjects over the last 100 non-merge commits; how changes reach the default branch (PR merge commits, `(#N)` squash subjects, direct commits on `--first-parent`); stale branches; root vs nested workflows; LICENSE/CONTRIBUTING/CODEOWNERS presence; lockfiles; README paths that do not exist; and developer-specific absolute paths. If the script cannot run, use the equivalent commands directly:
   - `git log --no-merges -n 100 --format=%s main | grep -cE '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?: '` for the convention rate
   - `git log --first-parent --merges --oneline main | wc -l` and `git log --first-parent --no-merges --format=%s main | grep -cE '\(#[0-9]+\)$'` for PR-merged changes; the remaining first-parent commits are direct pushes
   - `git ls-files | grep '/\.github/workflows/'` for nested workflows that never run

   A shallow clone or a non-git directory makes history items N/A; say so instead of guessing.

5. **Scan the repository** — Walk `references/checklist.md` section by section with Glob, Grep, and Read: README and contributor docs, CI files, manifests and lockfiles per module, layout and config, setup scripts, ADRs and changelogs. Verify each pitfall the script flagged by opening the file before citing it.

6. **Score and find** — Score each applicable dimension against its rubric.md anchors. Record findings with severity from rubric.md and a location in one of the accepted forms.

7. **Self-check, then write** — Before writing the report, confirm: every `path:line` exists and says what the finding claims; every `commit <sha>` resolves; every finding has confidence >= 7; measured rates match the script output; the overall equals the stated computation; no secret values are reproduced (refer to them by file:line only). Then write the report.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, ask:
- Did you observe it directly (a file you opened, a command you ran), rather than infer it from a name or convention?
- Does it point to a location a maintainer can check: `path:line`, `path (absent)`, `commit <sha>`, or a `git log` measurement with its numbers?
- Does it matter for how the project is developed today? A practice the project never claimed (Conventional Commits in a repo with no convention, PR review in a solo trunk-based repo) is not a defect unless the user's question or a written policy makes it one.
- Is it a process gap rather than something another review owns (runtime reliability, test quality, code security)?

If any answer is no, leave it out. Missing a marginal finding costs less than a report full of noise.

Severity definitions (CRITICAL, HIGH, MEDIUM, LOW) with process examples are in `references/rubric.md`.

## Scoring Dimensions (1-10 each)

Score with the anchors in `references/rubric.md`; `references/checklist.md` lists what to inspect for each.

1. **Documentation Quality** — README completeness and accuracy, contributor guides, LICENSE text, architecture and decision docs, API docs
2. **Development Workflow** — CI that actually runs, automated tests and lint, branch strategy, commit conventions and message quality
3. **Code Review Practices** — How changes reach the default branch, PR templates, CODEOWNERS, PR size, policy vs practice
4. **Dependency Management** — Lockfiles per manifest, version bounds, update automation, vulnerability scanning, license compliance
5. **Project Organization** — Directory structure, module boundaries, configuration separation, entry points, .gitignore and tracked artifacts
6. **Portability** — Hardcoded absolute paths, configurable endpoints, OS-specific tooling, reproducible environments, line endings
7. **Technical Leadership Signals** — Vision and roadmap, decision records, iteration evidence, backlog and debt tracking, governance

## Output Format

Produce a markdown report with this structure:

```markdown
# Development Process Fitness Report

**Target:** <repository root, or the scoped path(s)>
Config: <copied from resolver output>
Effective weights: <copied from resolver output>

## Direct Answer

(Only when the user asked a specific question: answer it in 2-4 sentences, citing the findings that decide it.)

## Summary

| Dimension                      | Score | Key Finding |
|-------------------------------|-------|-------------|
| Documentation Quality          | X/10  | ...         |
| Development Workflow           | X/10  | ...         |
| Code Review Practices          | X/10  | ...         |
| Dependency Management          | X/10  | ...         |
| Project Organization           | X/10  | ...         |
| Portability                    | X/10  | ...         |
| Technical Leadership Signals   | X/10  | ...         |
| **Overall**                    | X/10  | Status      |

(A dimension that does not apply shows `N/A — reason` in the Score column.)

Overall = mean of <list the scored dimensions> = X.X<, capped at 4.0 because of a CRITICAL finding>.

## Git Evidence

- Commits: N total, N authors; last commit <date>
- Conventional commits: N/100 (N%); vague subjects: N
- Default branch integration: N PR merges, N squash-merged PRs, N direct commits (first-parent)
- CI workflows at root: <list or none>; nested (never run): <list or none>

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** path:line | path (absent) | commit <sha> | git log <command>: <numbers>
- **Description:** What the issue is and why it matters.
- **Evidence:** What you observed (quoted line, command output).
- **Impact:** What goes wrong for contributors or quality.
- **Remediation:** Concrete fix or specific steps.

(repeat for each finding, ordered by severity)

### Documentation Quality (X/10)
**Evidence:** [specific files and observations]
**Strengths:** ...
**Gaps:** ...

[Repeat for each dimension]

## Action Items (up to 5, by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- location
2. ...

## Checklist Reference

See references/checklist.md in the review-process skill for the full process checklist.

## Reference

Based on [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/), [Fundamentals of Agile Software Development](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-agile-software-development/), [Fundamentals of Software Project Management](https://jeffbailey.us/blog/2026/01/12/fundamentals-of-software-project-management/), and guidance from https://jeffbailey.us/categories/fundamentals/
```

Write the report to `docs/process-review.md` at the root of the repository that contains the target, unless the user gives a path. Create `docs/` if needed. For a review scoped to a subdirectory or file set, write `docs/process-review-<scope-slug>.md` instead (for example `docs/process-review-match-ranker.md`) so a scoped run does not replace the whole-repo report.
