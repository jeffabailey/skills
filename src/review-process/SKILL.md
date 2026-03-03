---
name: review-process
description: Evaluates a repository's development process maturity across documentation, workflow, code review, dependency management, project organization, portability, and leadership signals. Use when the user says /review:process, requests a process review, asks for development process fitness scores, wants to assess repo health or contributor readiness, or asks how well a project follows software development best practices. Only reports findings with confidence >= 7/10.
---

# Development Process Fitness Review

Analyze the repository for development process maturity. Score each dimension 1-10 with evidence from actual repo contents. Reference the detailed checklist at `review-process/references/checklist.md` for specific items to verify.

Reference: [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/), [Fundamentals of Agile Software Development](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-agile-software-development/), [Fundamentals of Software Project Management](https://jeffbailey.us/blog/2026/01/12/fundamentals-of-software-project-management/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

For detailed scoring rubrics, severity definitions, what-good-looks-like / what-bad-looks-like criteria, and domain expertise, read `references/wisdom.md` before scoring. That file is auto-generated from:

- [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/)
- [Fundamentals of Agile Software Development](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-agile-software-development/)
- [Fundamentals of Software Project Management](https://jeffbailey.us/blog/2026/01/12/fundamentals-of-software-project-management/)

Use the wisdom reference when evaluating the repository and assigning dimension scores.

## Workflow

1. **Read domain knowledge** — Read `references/wisdom.md` to load scoring rubrics, thresholds, and severity definitions.

2. **Scan the repository** — Use Glob and Read to locate documentation files, configuration, CI/CD pipelines, dependency manifests, and contribution guides.

3. **Score each dimension** — Evaluate the seven dimensions below. Apply the rubrics/thresholds from the wisdom reference. Cite specific files and lines as evidence.

4. **Identify gaps** — Note missing artifacts, stale docs, or process antipatterns. Apply the severity definitions from the wisdom reference.

5. **Produce the report** — Write scores, evidence, and action items in the output format below.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

For severity level definitions (CRITICAL, HIGH, MEDIUM, LOW) with domain-specific examples, consult `references/wisdom.md`.

## Scoring Dimensions (1-10 each)

Dimensions to score (detailed rubrics including what-to-check, what-good-looks-like, and what-bad-looks-like are in `references/wisdom.md`):

1. **Documentation Quality** — README completeness, contribution guides, architecture decision records, API docs, inline comments
2. **Development Workflow** — Branch strategy, CI/CD pipelines, automated tests, linting/formatting, commit conventions
3. **Code Review Practices** — PR templates, review engagement, turnaround time, PR size, CODEOWNERS
4. **Dependency Management** — Lockfiles, version pinning, update tooling, vulnerability scanning, license compliance
5. **Project Organization** — Directory structure, module boundaries, configuration separation, entry point clarity, .gitignore coverage
6. **Portability** — Platform abstraction, containerization, configurable endpoints, cross-platform builds, encoding handling
7. **Technical Leadership Signals** — Technical vision docs, decision-making visibility, iteration evidence, backlog health, tech debt tracking

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

Based on [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/), [Fundamentals of Agile Software Development](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-agile-software-development/), [Fundamentals of Software Project Management](https://jeffbailey.us/blog/2026/01/12/fundamentals-of-software-project-management/), and guidance from https://jeffbailey.us/categories/fundamentals/
```

Write the report to `docs/process-review.md`.
