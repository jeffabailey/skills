---
name: review-process
description: Evaluates a repository's development process maturity across documentation, workflow, code review, dependency management, project organization, portability, and leadership signals. Use when the user says /review:process, requests a process review, asks for development process fitness scores, wants to assess repo health or contributor readiness, or asks how well a project follows software development best practices. Only reports findings with confidence >= 7/10.
---

# Development Process Fitness Review

Analyze the repository for development process maturity. Score each dimension 1-10 with evidence from actual repo contents. Reference the detailed checklist at `review-process/references/checklist.md` for specific items to verify.

## Workflow

1. **Scan the repository** - Use Glob and Read to locate documentation files, configuration, CI/CD pipelines, dependency manifests, and contribution guides.
2. **Score each dimension** - Evaluate the seven dimensions below. Cite specific files and lines as evidence.
3. **Identify gaps** - Note missing artifacts, stale docs, or process antipatterns.
4. **Produce the report** - Write scores, evidence, and action items in the output format below.

## Confidence and Severity

### Confidence Threshold

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

### Severity Levels

- **CRITICAL** -- Process gap that directly causes quality or collaboration failures. No CI pipeline, no version control discipline, secrets committed to repository, no dependency management.
- **HIGH** -- Significant process gap affecting team productivity under realistic conditions. No code review process, stale documentation misleading contributors, no automated testing in pipeline, no CODEOWNERS.
- **MEDIUM** -- Process weakness that reduces effectiveness under specific conditions. Inconsistent commit message conventions, partial CI coverage, dependency updates not automated, missing PR templates.
- **LOW** -- Process improvement opportunities. Better issue labeling, additional ADRs, changelog improvements, portability enhancements.

## Scoring Dimensions (1-10 each)

### 1. Documentation Quality

What to check:
- README.md exists and includes: project purpose, setup instructions, usage examples, and contribution pointers.
- CONTRIBUTING.md or equivalent guide exists with clear steps for new contributors.
- Architecture decision records (ADRs) or design docs exist and are current.
- API documentation exists (generated or handwritten) and matches current code.
- Inline code comments explain "why" not "what" for complex logic.

What good looks like (8-10):
- README answers "what is this, how do I run it, how do I contribute" within the first screen.
- Setup instructions are testable and produce a working environment.
- Architecture docs explain key decisions with rationale and trade-offs.
- Docs are updated alongside code changes (evidence: recent commits touching both).

What bad looks like (1-3):
- README is a template placeholder or empty.
- No setup instructions, or instructions that reference removed files/tools.
- No architecture docs; design lives only in people's heads.
- Stale docs that contradict current code behavior.

### 2. Development Workflow

What to check:
- Branch strategy is evident (trunk-based, git-flow, or consistent pattern in branch names and merge history).
- CI/CD pipeline configuration exists and runs on pull requests.
- Automated tests run before merge (check CI config for test steps).
- Linting and formatting are enforced (config files like .eslintrc, .prettierrc, rustfmt.toml, etc.).
- Build and deploy processes are scripted, not manual.
- Commit messages follow a convention (Conventional Commits, imperative mood, ticket references).

What good looks like (8-10):
- Consistent branching pattern visible in git log.
- CI pipeline runs tests, lints, and builds on every PR.
- Commit messages are descriptive and follow a convention.
- Deployment is automated via CI/CD or documented scripts.

What bad looks like (1-3):
- No CI/CD configuration.
- Long-lived branches with large, infrequent merges.
- Commit messages like "fix", "update", "wip" with no context.
- Manual deployment with no scripts or documentation.

### 3. Code Review Practices

What to check:
- Pull request templates exist (.github/PULL_REQUEST_TEMPLATE.md or equivalent).
- PR history shows review comments and approvals (not just self-merges).
- Review turnaround is reasonable (PRs don't sit for weeks).
- PRs are focused and small (not thousand-line mega-PRs as a pattern).
- CODEOWNERS file exists assigning review responsibility.

What good looks like (8-10):
- PR template guides authors to describe changes, testing done, and impact.
- CODEOWNERS maps directories to responsible reviewers.
- PR history shows multi-reviewer engagement with substantive comments.
- Average PR size is under 400 lines changed.

What bad looks like (1-3):
- No PR template; PRs have empty descriptions.
- Single-person merges with no review evidence.
- PRs routinely exceed 1000 lines.
- No CODEOWNERS; review responsibility is unclear.

### 4. Dependency Management

What to check:
- Lockfiles exist and are committed (package-lock.json, Cargo.lock, go.sum, poetry.lock, etc.).
- Dependency versions are pinned or bounded, not floating.
- Dependency update tooling is configured (Dependabot, Renovate, or equivalent).
- Dependencies are reasonably current (check age of lockfile updates).
- Vulnerability scanning is configured (Snyk, npm audit, cargo audit, etc.).
- License compliance is tracked or documented.

What good looks like (8-10):
- Lockfiles committed and recently updated.
- Dependabot or Renovate PRs appear regularly in history.
- No known critical vulnerabilities in dependencies.
- Dependency policy documented (when to add, when to remove).

What bad looks like (1-3):
- No lockfiles, or lockfiles in .gitignore.
- Dependencies many major versions behind.
- No automated update tooling.
- Known vulnerabilities in dependency tree with no remediation plan.

### 5. Project Organization

What to check:
- Directory structure follows a recognizable pattern for the language/framework.
- Module boundaries are clear (not everything in one flat directory).
- Configuration is separated from code (env vars, config files, not hardcoded values).
- Entry points are obvious (main files, handler files clearly named).
- Test files are co-located or in a clear parallel structure.
- .gitignore is comprehensive (no build artifacts, IDE files, or secrets in repo).

What good looks like (8-10):
- Directory structure communicates architecture at a glance.
- Clear separation: src/lib for code, tests for tests, config for configuration.
- .gitignore covers all common artifacts for the tech stack.
- No secrets, credentials, or environment-specific values in committed code.

What bad looks like (1-3):
- Flat directory with hundreds of files.
- Mixed concerns: tests, config, source, and build artifacts interleaved.
- Hardcoded secrets or API keys in source files.
- Build artifacts committed to the repository.

### 6. Portability

What to check:
- Platform-specific code is isolated behind abstractions or feature flags.
- Build instructions work across common platforms (or document platform requirements).
- Docker or containerization config exists for reproducible environments.
- External service dependencies are documented and configurable (not hardcoded URLs).
- File paths use platform-appropriate handling (no hardcoded separators).
- Character encoding is explicit where relevant (UTF-8 default).

What good looks like (8-10):
- Dockerfile or docker-compose.yml provides reproducible dev environment.
- Platform-specific code is behind clear abstraction layers.
- All external URLs and service endpoints are configurable via environment variables.
- Build works on Linux, macOS, and Windows (or documents requirements).

What bad looks like (1-3):
- Hardcoded paths assuming a specific OS.
- No containerization or reproducible environment setup.
- External service URLs hardcoded in source files.
- Build only works on one developer's machine.

### 7. Technical Leadership Signals

What to check:
- Technical vision is documented (roadmap, architecture vision, or tech strategy doc).
- Decision-making is visible (ADRs, RFCs, or design docs with rationale).
- Iteration evidence exists (retrospective notes, changelog, or improvement tracking).
- Backlog health: issues are triaged, labeled, and prioritized (not a graveyard of stale issues).
- On-call or incident response process is documented.
- Technical debt is tracked explicitly (labeled issues, tech debt backlog).

What good looks like (8-10):
- ADRs or design docs capture key decisions with context and trade-offs.
- Issue tracker shows active triage with labels, milestones, and assignments.
- Changelog or release notes document what shipped and why.
- Technical debt has dedicated tracking and periodic attention.

What bad looks like (1-3):
- No documented decisions; architecture is tribal knowledge.
- Issue tracker is a graveyard of unresolved, unlabeled issues.
- No changelog or release notes.
- Technical debt is untracked and growing silently.

## Output Format

Produce a markdown report with this structure:

```markdown
# Development Process Fitness Report

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
| **Overall**                    | X/10  | ...         |

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line
- **Description:** What the issue is and why it matters.
- **Evidence:** The specific code pattern found.
- **Impact:** What could go wrong for contributors or quality.
- **Remediation:** Concrete fix with code example or specific steps.

(repeat for each finding, ordered by severity)

### Documentation Quality (X/10)
**Evidence:** [specific files and observations]
**Strengths:** ...
**Gaps:** ...

[Repeat for each dimension]

## Top 5 Action Items (by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...
3. ...
4. ...
5. ...

## Checklist Reference

See review-process/references/checklist.md for the full process checklist
derived from software development fundamentals.

## Reference

Based on guidance from https://jeffbailey.us/categories/fundamentals/
```

Write the report to `docs/process-review.md`.
