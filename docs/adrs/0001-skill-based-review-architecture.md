# ADR 0001: Skill-Based Review Architecture

**Date:** 2026-02-22
**Status:** Accepted

## Context

We need a way to perform structured, repeatable fitness reviews of software projects across multiple quality domains (architecture, security, reliability, testing, performance, algorithms, data, accessibility, process). Reviews should produce consistent, evidence-based scores rather than subjective opinions.

The options considered were:

1. **A single monolithic review prompt** that covers all domains in one pass.
2. **Separate skill files per domain** that can run independently or be orchestrated together.
3. **A custom CLI tool or linter** that programmatically analyzes code.

## Decision

We chose **separate skill files per domain** with a `review-full` orchestrator.

Each domain has its own directory containing:

- `SKILL.md` -- the skill definition with workflow steps, scoring rubric, and output format.
- `references/checklist.md` -- detailed checklist items sourced from the Fundamentals series.

The `review-full` skill launches all domain skills in parallel using Claude Code's Task tool and synthesizes the results into a unified weighted report.

## Rationale

**Independent domain skills** allow:

- Running a single domain review when only that area matters (e.g., security review before a release).
- Parallel execution for speed -- each domain reviews the codebase concurrently.
- Independent evolution -- updating the security checklist doesn't risk breaking the architecture review.
- Reuse across tools -- skills can be symlinked into Claude Code, Cursor, or any tool that supports the skill format.

**A monolithic prompt** was rejected because:

- Context window limits make it impractical to include all checklists in a single prompt.
- A single pass cannot give equal depth to nine domains.
- Updating one domain's criteria risks side effects on others.

**A custom CLI tool** was rejected because:

- Static analysis tools already exist (ESLint, SonarQube, etc.) and cover syntax-level checks well.
- The value of these reviews is in higher-order reasoning about design, architecture, and trade-offs -- areas where LLM judgment adds the most over existing tools.
- A CLI tool would require maintenance across languages and frameworks; skill files are language-agnostic.

## Consequences

- Each skill must define its own complete workflow and scoring rubric in `SKILL.md` since skills run in isolated contexts.
- The `review-full` orchestrator depends on all domain skills being installed; missing skills are silently skipped.
- Checklist updates require editing markdown files, not code -- lowering the contribution barrier.
- Reports are written to `docs/` as markdown, making them version-controllable and diffable.
- Natural language triggers overlap between domains (e.g., "check performance" could mean `review-performance` or `review-algorithms`), so trigger phrases must be carefully scoped. **Resolution:** each skill's trigger phrases should be domain-specific and avoid general terms that apply to multiple domains; prefer phrases like "check algorithm correctness" over "check performance" for `review-algorithms`, and document any remaining ambiguities in the skill's SKILL.md.
