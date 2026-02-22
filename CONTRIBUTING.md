# Contributing to Skills

Thank you for your interest in contributing! This guide explains how to propose changes to skills, add reference checklists, and submit improvements.

## Types of contributions

- **Bug fixes** — correcting typos, broken links, or inaccurate scoring rubrics in any `SKILL.md`
- **Checklist improvements** — adding or updating items in `references/checklist.md` files
- **New skills** — proposing an entirely new review domain
- **Documentation updates** — improving README.md, SETUP.md, RUN.md, or ADRs

## Workflow

1. **Fork** the repository and create a branch from `main`.
2. Make your changes following the conventions below.
3. Open a **pull request** with a clear description of what changed and why.
4. Address any review feedback.

## Conventions

### Skill file structure

Each skill lives in its own directory:

```
review-<domain>/
  SKILL.md               # skill definition: triggers, workflow, scoring rubric
  references/
    checklist.md         # detailed checklist items
```

- `SKILL.md` must include: a `## Triggers` section, a `## Workflow` section, and a `## Scoring` section.
- Scoring weights in `review-full/SKILL.md` must stay consistent with the weights listed in `README.md`.
- Trigger phrases must be domain-specific. Avoid general phrases that overlap with other skills (see [ADR 0001](docs/adrs/0001-skill-based-review-architecture.md)).

### Naming

- Skill directories: `review-<domain>` (all lowercase, hyphenated)
- Report output files: `docs/<domain>-review.md`

### Scoring weights

The current domain weights (used by `review-full`) are:

| Domain | Weight |
|--------|--------|
| Architecture | 14% |
| Security | 14% |
| Reliability | 10% |
| Testing | 10% |
| Performance | 10% |
| Algorithms | 10% |
| Data | 10% |
| Accessibility | 8% |
| Process | 8% |
| Maintainability | 6% |

If you propose adding or removing a domain, update both `review-full/SKILL.md` and `README.md` to keep them consistent.

## Questions

Open a GitHub issue for any questions or suggestions before starting significant work.
