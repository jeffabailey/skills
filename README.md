# Project Fitness Review Skills

Reusable Claude Code skills that review software project fitness across architecture, security, reliability, testing, performance, algorithms, data, accessibility, and process. Based on guidance from the [Fundamentals series](https://jeffbailey.us/categories/fundamentals/).

**Repository:** [github.com/jeffabailey/skills](https://github.com/jeffabailey/skills)

This repository and the article [Fundamental Skills](https://jeffbailey.us/blog/2026/02/21/fundamental-skills) on [jeffbailey.us](https://jeffbailey.us) are cross-linked: the article explains the design, trade-offs, and how the skills fit together; this repository contains the installable skill definitions and checklists.

## Skills

| Skill | Scores | Triggers |
|-------|--------|----------|
| `review-architecture` | Coupling, Cohesion, Layering, Modularity, Naming, API Design, Maintainability | "architecture review", "coupling and cohesion", "check code structure" |
| `review-security` | Input Validation, Auth, Data Protection, Dependencies, Error Handling, Crypto | "security review", "check vulnerabilities", "audit security" |
| `review-reliability` | Observability, Availability, Timeouts, CI/CD, Incident Readiness, Capacity, Deploy | "reliability review", "production ready", "check observability" |
| `review-testing` | Pyramid Balance, Test Quality, Coverage, Perf Testing, Debugging, CI Integration | "review test quality", "testing strategy", "test pyramid" |
| `review-performance` | Algorithmic Efficiency, Database Design, Caching, Scalability, Resources, Pipelines | "performance review", "N+1 queries", "scalability analysis" |
| `review-algorithms` | Algorithm Choice, Data Structure Selection, Complexity, Concurrency Safety, Edge Cases, Correctness | "algorithm review", "concurrency safety", "correctness check" |
| `review-data` | Schema Design, Migration Safety, Data Integrity, Query Correctness, Data Modeling, Pipeline Quality | "data review", "schema design", "migration safety" |
| `review-accessibility` | Semantic HTML, Keyboard Nav, Screen Reader, Color/Contrast, Progressive Enhancement, Responsive, Usability | "accessibility review", "a11y check", "WCAG compliance" |
| `review-process` | Documentation, Workflow, Code Review, Dependencies, Organization, Portability, Leadership | "process review", "repo health", "development practices" |
| `review-full` | All of the above (weighted average) | "full review", "comprehensive review", "project fitness" |
| `review-jit-test-gen` | Generates tests (no scores) | "generate tests", "write tests for changes" |

Each domain skill produces scores (1-10) with file:line evidence and prioritized action items.

## Installation

### Claude Code

Skills are installed automatically via [mcp-configure](https://github.com/jeffabailey/ide). To install manually:

```bash
git clone https://github.com/jeffabailey/skills.git ~/Projects/skills

# Symlink all review skills
for skill in review-architecture review-security review-reliability review-testing review-performance review-algorithms review-data review-accessibility review-process review-full review-jit-test-gen; do
  ln -sf ~/Projects/skills/$skill ~/.claude/skills/$skill
done
```

### Cursor

```bash
for skill in review-architecture review-security review-reliability review-testing review-performance review-algorithms review-data review-accessibility review-process review-full review-jit-test-gen; do
  ln -sf ~/Projects/skills/$skill ~/.cursor/skills/$skill
done
```

## Usage

### Slash Commands

```
/review:review-architecture    # Architecture fitness scores
/review:review-security        # Security vulnerability scan
/review:review-reliability     # Production readiness check
/review:review-testing         # Test quality assessment
/review:review-performance     # Performance bottleneck analysis
/review:review-algorithms      # Algorithm and data structure correctness
/review:review-data            # Schema, migration, and data integrity
/review:review-accessibility   # A11y compliance check
/review:review-process         # Development process audit
/review:review-full            # Run all reviews, unified report
/review:review-jit-test-gen    # Generate tests for changed code
```

### Natural Language

Skills trigger on natural language too:

- "Review the architecture of this project"
- "Are there any security vulnerabilities?"
- "Is this production ready?"
- "Check test quality"
- "Find performance bottlenecks"
- "Check algorithm correctness"
- "Review database schema"
- "Full review before shipping"
- "Generate tests for my changes"

### Reports

Domain skills write reports to `docs/<domain>-review.md`. The full review writes a unified report to `docs/fitness-report.md` with weighted scoring:

- Architecture: 15%
- Security: 15%
- Reliability: 10%
- Testing: 10%
- Performance: 10%
- Algorithms: 10%
- Data: 10% (skipped if no database code)
- Accessibility: 10% (skipped for backend-only projects)
- Process: 10%

## Structure

```
review-architecture/
  SKILL.md                # Skill definition (workflow + scoring rubric)
  references/
    checklist.md          # Detailed checklist items with source citations
review-security/
  SKILL.md
  references/
    checklist.md
review-reliability/
  SKILL.md
  references/
    checklist.md
review-testing/
  SKILL.md
  references/
    checklist.md
review-performance/
  SKILL.md
  references/
    checklist.md
review-algorithms/
  SKILL.md
  references/
    checklist.md
review-data/
  SKILL.md
  references/
    checklist.md
review-accessibility/
  SKILL.md
  references/
    checklist.md
review-process/
  SKILL.md
  references/
    checklist.md
review-full/
  SKILL.md                # Orchestrator (no references needed)
review-jit-test-gen/
  SKILL.md                # Test generator (no references needed)
tests/
  trigger-tests.md        # What phrases should/shouldn't trigger each skill
  functional-tests.md     # Expected behavior for each skill
```

## License

Unlicense (public domain)
