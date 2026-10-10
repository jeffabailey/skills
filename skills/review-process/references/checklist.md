# Development Process Checklist

What to check during a process review, grouped by the seven scoring dimensions in SKILL.md. Scores come from `rubric.md`; this file says where to look. Items marked **Pitfall** are mistakes a quick "does it exist?" pass misses, so check them explicitly.

Derived from the Fundamentals series by Jeff Bailey (sources at the end).

---

## 1. Documentation Quality

### README

- [ ] Project name, one-line description, the problem it solves, and who it is for
- [ ] Prerequisites and system requirements
- [ ] Setup instructions that produce a working environment
- [ ] Usage examples with expected output
- [ ] How to run tests
- [ ] How to contribute (or a link to CONTRIBUTING.md)
- [ ] License named
- [ ] **Pitfall:** every relative path, script, and command the README names exists in the repo (`git-evidence.sh` lists `readme_paths_missing`, including `uv run X.py`-style commands whose script exists nowhere; open each before citing, since model IDs and generated or gitignored outputs are legitimate)
- [ ] **Pitfall:** the README names a license, and a LICENSE file with the license text exists (a name alone grants nothing)

### Contributor documentation

- [ ] CONTRIBUTING.md with the fork/branch/PR/review cycle and how to run checks locally
- [ ] CODE_OF_CONDUCT.md for projects that accept outside contributors
- [ ] Issue and PR templates guide contributors

### Architecture and API documentation

- [ ] High-level architecture description or diagram
- [ ] Key design decisions recorded with rationale and trade-offs (ADRs or design docs)
- [ ] Public APIs documented with parameters, return values, errors, and an example

### Currency

- [ ] Docs change alongside code (commits touch both)
- [ ] No references to removed files, tools, or features
- [ ] Volatile details (versions, absolute paths) kept out in favor of stable concepts

Reference: [Fundamentals of Technical Writing](https://jeffbailey.us/blog/2025/10/12/fundamentals-of-technical-writing/)

---

## 2. Development Workflow

### CI/CD

- [ ] CI configuration exists and runs on every pull request and push to the default branch
- [ ] **Pitfall:** GitHub Actions workflows live in `.github/workflows/` at the repository root. A workflow under `<subdir>/.github/workflows/` never runs; treat it as no CI for the whole repo (`git-evidence.sh` lists `nested_workflows`)
- [ ] Tests run automatically before merge, and failures block merge
- [ ] Lint and format checks enforced
- [ ] Build is scripted and reproducible; deployment automated or documented step by step

### Branch strategy

- [ ] One strategy used consistently (trunk-based with short-lived branches, or git-flow)
- [ ] No long-lived branches drifting from main (`git-evidence.sh` lists branches idle 90+ days)

### Commit hygiene

- [ ] Messages say what changed and why
- [ ] Claimed convention followed: conventional-commit rate >= 80% over the last 100 non-merge commits (`conventional_rate_pct`)
- [ ] Zero vague subjects ("fix", "update", "wip", "stuff") (`vague_subjects`)
- [ ] Commits small and focused (one logical change)

Reference: [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/), [Fundamentals of Agile Software Development](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-agile-software-development/)

---

## 3. Code Review Practices

- [ ] Changes reach the default branch through PRs: count merge commits plus `(#N)` squash subjects against direct commits on `git log --first-parent` (`git-evidence.sh` integration path)
- [ ] **Pitfall:** CONTRIBUTING or a PR template says "all changes via PR" while most first-parent commits are direct; cite the policy line and the measured ratio
- [ ] PR template asks for what changed, why, and how it was tested
- [ ] CODEOWNERS maps directories to reviewers (in `.github/`, root, or `docs/`)
- [ ] PRs small and focused (under 400 changed lines preferred)
- [ ] Branch protection or required checks documented
- [ ] Review comments are substantive and turnaround is days, not weeks (only when PR history is visible)

Solo trunk-based repos: direct commits alone are not a defect. Judge what an incoming contributor would meet.

Reference: [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/)

---

## 4. Dependency Management

- [ ] Every manifest has a committed lockfile (package-lock.json, yarn.lock, pnpm-lock.yaml, Cargo.lock, go.sum, poetry.lock, uv.lock, Gemfile.lock, composer.lock)
- [ ] **Pitfall:** in a monorepo, check each module's manifest; per-module lockfiles count
- [ ] Lockfiles not in .gitignore
- [ ] Versions pinned or bounded, no `*` or `latest`
- [ ] Automated updates configured (Dependabot, Renovate) and update PRs or commits appear in history
- [ ] Vulnerability scanning in CI (npm audit, pip-audit, cargo audit, Dependabot alerts, Snyk)
- [ ] License compatibility of dependencies considered

Reference: [Fundamentals of Software Development Operations](https://jeffbailey.us/blog/2026/01/13/fundamentals-of-software-development-operations/)

---

## 5. Project Organization

- [ ] Layout follows the language or framework convention
- [ ] Module boundaries clear; entry points obviously named
- [ ] Tests co-located or in a parallel structure
- [ ] Configuration separated from code; environment-specific values from env vars or config files
- [ ] `.env.example` or documented defaults for required settings
- [ ] No hardcoded secrets (cite by file:line only, never reproduce the value)
- [ ] `.gitignore` covers the stack; no build artifacts, IDE files, or large binaries tracked

Reference: [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/)

---

## 6. Portability

- [ ] No developer-specific absolute paths in code defaults, scripts, or setup docs (`/Users/<name>/`, `/home/<name>/`, `C:\Users\`) (`absolute_paths_in_tracked_text`; ignore test fixtures, CI runner paths, and illustrative examples)
- [ ] Paths, endpoints, and credentials configurable rather than fixed
- [ ] Setup does not assume sibling repos or tools at fixed locations
- [ ] Agent instruction files (CLAUDE.md, AGENTS.md) do not require tools or servers that only exist on the author's machine
- [ ] OS-specific tooling (Homebrew, apt, PowerShell) has an alternative or a stated platform requirement
- [ ] Reproducible environment: devcontainer, Dockerfile, Nix, or a setup script
- [ ] Line endings and encoding pinned (`.gitattributes`, `.editorconfig`)
- [ ] CI runs on every platform the README claims to support

---

## 7. Technical Leadership Signals

### Direction and decisions

- [ ] Vision, roadmap, or scope document (in-scope and out-of-scope)
- [ ] Decisions recorded with alternatives considered, not just conclusions
- [ ] Technology choices justified by project needs, not hype or authority
- [ ] Success criteria defined for major initiatives

### Iteration

- [ ] Changelog, release notes, or tags show regular delivery
- [ ] Retrospective or postmortem notes lead to visible process changes
- [ ] Commit history shows steady work rather than rare large dumps

### Backlog and debt

- [ ] Issues triaged and labeled (only when an issue tracker is visible; otherwise say so)
- [ ] Technical debt tracked (labels, a debt log, or linked TODOs), not scattered untracked TODO/FIXME

### Governance (projects with outside contributors)

- [ ] Maintainer roles and decision process documented
- [ ] CLA or DCO when required

Reference: [Fundamentals of Software Project Management](https://jeffbailey.us/blog/2026/01/12/fundamentals-of-software-project-management/), [Logical Fallacies in Software Development](https://jeffbailey.us/blog/2026/02/01/logical-fallacies-in-software-development/), [Fundamentals of Open Source](https://jeffbailey.us/blog/2025/03/06/fundamentals-of-open-source/)

---

## Out of scope

Monitoring, alerting, incident response, and runbooks belong to review-reliability. Test quality belongs to review-testing. Mention them here only as a pointer.

## Source Articles

1. [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/)
2. [Fundamentals of Agile Software Development](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-agile-software-development/)
3. [Fundamentals of Software Product Development](https://jeffbailey.us/blog/2025/11/28/fundamentals-of-software-product-development/)
4. [Fundamentals of Software Project Management](https://jeffbailey.us/blog/2026/01/12/fundamentals-of-software-project-management/)
5. [Fundamentals of Technical Writing](https://jeffbailey.us/blog/2025/10/12/fundamentals-of-technical-writing/)
6. [Fundamentals of Open Source](https://jeffbailey.us/blog/2025/03/06/fundamentals-of-open-source/)
7. [Fundamentals of Software Development Operations](https://jeffbailey.us/blog/2026/01/13/fundamentals-of-software-development-operations/)
8. [Logical Fallacies in Software Development](https://jeffbailey.us/blog/2026/02/01/logical-fallacies-in-software-development/)
