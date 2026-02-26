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

- `SKILL.md` must include: YAML frontmatter with `name` and `description` (including trigger phrases), a `## Workflow` section, and a `## Scoring Dimensions` section.
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

### Adding or removing a skill

The skill list appears in multiple files in different formats. When adding, removing, or renaming a skill, update **all** of these locations:

1. **`README.md`** — Skills table and installation `for` loops
2. **`CONTRIBUTING.md`** — Scoring weights table (this file)
3. **`review-full/SKILL.md`** — Domain launch list and scoring weights
4. **`SETUP.md`** — All platform-specific install `for` loops and the skill reference list
5. **`.github/fitness-review-prompt.md`** — Review domains section
6. **`tests/trigger-tests.md`** — Trigger test cases for the skill
7. **`tests/functional-tests.md`** — Functional test scenarios for the skill
8. **`tests/skill-structure-tests.sh`** — `SKILLS` array

The PR template checklist will remind you to verify these locations. CI will catch missing directories or SKILL.md files but cannot verify that every prose reference is updated.

## Questions

Open a GitHub issue for any questions or suggestions before starting significant work.
