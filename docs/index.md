# Project Fitness Review Skills

Reusable Claude Code skills that review software project fitness across architecture, security, reliability, testing, performance, algorithms, data, accessibility, and process. Based on guidance from the [Fundamentals series](https://jeffbailey.us/categories/fundamentals/).

## Skills Overview

| Skill | What It Reviews |
|-------|-----------------|
| `review-architecture` | Coupling, cohesion, layering, modularity, naming, API design, maintainability |
| `review-security` | Input validation, auth, data protection, dependencies, error handling, crypto |
| `review-reliability` | Observability, availability, timeouts, CI/CD, incident readiness, capacity |
| `review-testing` | Pyramid balance, test quality, coverage, perf testing, debugging, CI integration |
| `review-performance` | Algorithmic efficiency, database design, caching, scalability, resources |
| `review-algorithms` | Algorithm choice, data structure selection, complexity, concurrency safety, correctness |
| `review-data` | Schema design, migration safety, data integrity, query correctness, data modeling |
| `review-accessibility` | Semantic HTML, keyboard nav, screen reader, color/contrast, responsive design |
| `review-process` | Documentation, workflow, code review, dependencies, organization, portability |
| `review-full` | All of the above with weighted scoring |
| `review-jit-test-gen` | Generates tests for changed code (no scores) |

Each domain skill produces scores (1--10) with `file:line` evidence and prioritized action items.

## How It Works

Skills are installed into Claude Code (or Cursor) via symlinks. They trigger on slash commands (`/review:review-architecture`) or natural language ("review the architecture of this project"). Each skill follows a structured workflow:

1. **Scope identification** -- determine what code to review
2. **Analysis** -- walk the checklist for that domain, gathering evidence
3. **Scoring** -- rate each dimension 1--10 with `file:line` citations
4. **Reporting** -- write a structured markdown report to `docs/`

The `review-full` orchestrator runs all domain skills in parallel and produces a unified fitness report with weighted overall scoring.

## Reports

Domain skills write reports to `docs/<domain>-review.md`. The full review writes a unified report to `docs/fitness-report.md` with these weights:

| Domain | Weight |
|--------|--------|
| Architecture | 15% |
| Security | 15% |
| Reliability | 10% |
| Testing | 10% |
| Performance | 10% |
| Algorithms | 10% |
| Data | 10% (skipped if no database code) |
| Accessibility | 10% (skipped for backend-only projects) |
| Process | 10% |

When a domain is skipped, its weight redistributes proportionally across the remaining domains.

## Repository Structure

```
review-<domain>/
  SKILL.md                # Skill definition (workflow + scoring rubric)
  references/
    checklist.md          # Detailed checklist items with source citations
review-full/
  SKILL.md                # Orchestrator skill
review-jit-test-gen/
  SKILL.md                # Test generator skill
tests/
  trigger-tests.md        # Trigger phrase validation
  functional-tests.md     # Expected behavior specs
docs/
  adrs/                   # Architecture Decision Records
```

## Further Reading

- [Fundamental Skills](https://jeffbailey.us/blog/2026/02/21/fundamental-skills) -- design article explaining trade-offs
- [Architecture Decision Records](adrs/0001-skill-based-review-architecture.md) -- key design decisions
