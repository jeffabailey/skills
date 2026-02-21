# Project Fitness Review Skills

Reusable Claude Code skills that review software project fitness across architecture, security, reliability, testing, performance, accessibility, and process. Based on guidance from the [Fundamentals series](https://jeffbailey.us/categories/fundamentals/).

## Skills

| Skill | Scores | Triggers |
|-------|--------|----------|
| `review-architecture` | Coupling, Cohesion, Layering, Modularity, Naming, API Design, Maintainability | "architecture review", "coupling and cohesion", "check code structure" |
| `review-security` | Input Validation, Auth, Data Protection, Dependencies, Error Handling, Crypto | "security review", "check vulnerabilities", "audit security" |
| `review-reliability` | Observability, Availability, Timeouts, CI/CD, Incident Readiness, Capacity, Deploy | "reliability review", "production ready", "check observability" |
| `review-testing` | Pyramid Balance, Test Quality, Coverage, Perf Testing, Debugging, CI Integration | "review test quality", "testing strategy", "test pyramid" |
| `review-performance` | Algorithmic Efficiency, Database Design, Caching, Scalability, Resources, Pipelines | "performance review", "N+1 queries", "scalability analysis" |
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
for skill in review-architecture review-security review-reliability review-testing review-performance review-accessibility review-process review-full review-jit-test-gen; do
  ln -sf ~/Projects/skills/$skill ~/.claude/skills/$skill
done
```

### Cursor

```bash
for skill in review-architecture review-security review-reliability review-testing review-performance review-accessibility review-process review-full review-jit-test-gen; do
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
- "Full review before shipping"
- "Generate tests for my changes"

### Reports

Domain skills write reports to `docs/<domain>-review.md`. The full review writes a unified report to `docs/fitness-report.md` with weighted scoring:

- Architecture: 20%
- Security: 20%
- Reliability: 15%
- Testing: 15%
- Performance: 15%
- Accessibility: 10% (skipped for backend-only projects)
- Process: 5%

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
