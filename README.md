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

## Using the skills in a GitHub Action

You can run the project fitness review (or any domain skill) in CI using [Claude Code GitHub Actions](https://github.com/anthropics/claude-code-action). The runner must have the skills available so Claude Code can load them.

### 1. Prerequisites

- Add **ANTHROPIC_API_KEY** to your repository secrets (Settings → Secrets and variables → Actions). Get a key from [console.anthropic.com](https://console.anthropic.com/).
- Optional: Install the [Claude GitHub App](https://github.com/apps/claude) for your repo if you want `@claude` in comments; not required for workflow-triggered runs.

### 2. Check out the repo and install the skills

Your workflow must check out the repository and install the skills from this repo so Claude Code can find them. Clone this repo (or your fork) and symlink each skill into the directory Claude Code uses:

```yaml
- uses: actions/checkout@v4
  with:
    repository: jeffabailey/skills   # or your fork
    path: skills

- name: Install project fitness review skills
  run: |
    mkdir -p ~/.claude/skills
    for skill in review-architecture review-security review-reliability review-testing review-performance review-algorithms review-data review-accessibility review-process review-full review-jit-test-gen; do
      ln -sf "$GITHUB_WORKSPACE/skills/$skill" ~/.claude/skills/$skill
    done
```

If the workflow runs in the same repo that contains the skills (e.g. this repo), use the workspace as the source and omit the separate checkout for `skills`:

```yaml
- uses: actions/checkout@v4

- name: Install project fitness review skills
  run: |
    mkdir -p ~/.claude/skills
    for skill in review-architecture review-security review-reliability review-testing review-performance review-algorithms review-data review-accessibility review-process review-full review-jit-test-gen; do
      ln -sf "$GITHUB_WORKSPACE/$skill" ~/.claude/skills/$skill
    done
```

### 3. Run the Claude Code action with a review prompt

Use the `prompt` input to request a full review or a specific domain. The action will run in automation mode and use the installed skills.

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    prompt: "Run a full project fitness review on this repository. Use the review-full skill. Write the unified report to docs/fitness-report.md."
    claude_args: "--max-turns 15"
```

To run a single domain (e.g. security) use natural language that triggers that skill:

```yaml
prompt: "Run a security review of this project using the review-security skill. Write the report to docs/security-review.md."
```

### 4. Use the report (optional)

Upload the report as an artifact or commit it in a follow-up step:

```yaml
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: fitness-report
    path: docs/fitness-report.md
  continue-on-error: true
```

See [Claude Code GitHub Actions](https://code.claude.com/docs/en/github-actions) and the [action usage docs](https://github.com/anthropics/claude-code-action/blob/main/docs/usage.md) for authentication (e.g. AWS Bedrock, Google Vertex), security, and `claude_args` (e.g. `--model`, `--max-turns`).

## Testing the Skills

The `tests/` directory contains test plans for validating that the skills themselves work correctly. This is not about reviewing your project -- it is about verifying the skills behave as designed. Run all tests with the `claude` CLI against a target project.

### 1. Trigger Tests

**Goal:** Verify each skill loads when it should and stays silent when it should not.

Test cases are in `tests/trigger-tests.md`. For each skill, run the "should trigger" phrases and confirm the skill activates, then run the "should NOT trigger" phrases and confirm it does not.

```bash
cd /path/to/a/test/project

# Should trigger review-architecture (expect skill to activate)
claude -p "Review the architecture of this project"

# Should NOT trigger review-architecture (expect no skill activation)
claude -p "Fix this bug"

# Should trigger review-data (expect skill to activate)
claude -p "Review database schema"

# Should NOT trigger review-data (expect no skill activation)
claude -p "Check database performance"
```

A skill passes its trigger tests when it activates for all "should trigger" phrases and does not activate for any "should NOT trigger" phrases.

### 2. Functional Tests

**Goal:** Verify each skill produces correct, structured output with real evidence.

Test scenarios are in `tests/functional-tests.md` using Given/When/Then format. Each scenario defines the preconditions, the command to run, and what to check in the output.

```bash
cd /path/to/a/test/project

# Test: review-architecture produces scores for all dimensions
claude -p "/review:review-architecture"
# Then check docs/architecture-review.md for:
#   - Scores (1-10) for all 7 dimensions
#   - Each score backed by file:line evidence
#   - Scores below 6 generate action items

# Test: review-security only reports high-confidence findings
claude -p "/review:review-security"
# Then check docs/security-review.md for:
#   - All findings have confidence >= 7/10
#   - Each finding has severity, file:line, and remediation
#   - No false positives for safe patterns

# Test: review-full produces unified report
claude -p "/review:review-full"
# Then check docs/fitness-report.md for:
#   - Overall weighted score
#   - All domain scores in table format
#   - Top 10 prioritized action items
```

A skill passes its functional tests when the output report matches the expected structure, scores include file:line evidence, and findings are accurate (no false positives).

### 3. Performance Comparison

**Goal:** Confirm the skills improve review quality versus unassisted review.

Compare results with and without the skill on the same codebase:

```bash
# Without skill: generic prompt, no structured checklist
claude -p "Review this project for security issues"

# With skill: structured workflow, scoring rubric, evidence requirements
claude -p "/review:review-security"
```

The skill should produce more findings, fewer false positives, consistent scoring, and file:line evidence that the unassisted review lacks.

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
