---
name: review-full
description: Runs a comprehensive project fitness review combining architecture, security, reliability, testing, performance, algorithms, data, accessibility, process, and maintainability analysis. Use when the user says "full review", "comprehensive review", "project fitness", "review everything", or wants all review skills run on current changes before shipping.
---

# Full Project Fitness Review

Run all review skills in parallel to produce a unified fitness assessment.

## Configuration

Always invoke the resolver CLI to read effective weights and thresholds. Never load `fitness-config.json` directly. The CLI walks up from the review target to find module overrides and merges them with the root config per ADR-001 / ADR-002 / ADR-005.

```bash
python3 scripts/fitness-config.py show --path <target>
```

Where `<target>` is:
- The repository root for a broad-scope review (per ADR-005, only the root config is honored at root scope; subtree overrides are listed as a footnote but not applied).
- A specific file or directory when the user has scoped the review to a module.

Parse the resolver output to obtain:
- The `Config:` line (names the config sources actually applied).
- The `Effective weights:` line (lists all 10 domains with their effective values).
- The fenced JSON block delimited by `<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->` and `<!-- END_EFFECTIVE_CONFIG_JSON -->` for programmatic access to weights, status thresholds, security, and scoring.

Include the `Config:` and `Effective weights:` lines in the final report header (within the first 10 lines) as the provenance trail. If the report is at root scope and the resolver names subtree overrides discovered but not applied, restate them as a footnote so reviewers know overrides exist for narrower scopes.

## Workflow

### Step 1: Identify Review Scope

Determine what to review:
- If there are pending git changes (`git diff`), review those changes
- If the user specifies files or directories, review those
- Otherwise, review the entire project

### Step 2: Launch All Reviews in Parallel

Use the Task tool to launch these agents concurrently:

1. **Architecture** (`/review:review-architecture`) - Design, coupling, naming, API fitness
2. **Security** (`/review:review-security`) - Vulnerability and compliance fitness
3. **Reliability** (`/review:review-reliability`) - Operations, observability, availability fitness
4. **Testing** (`/review:review-testing`) - Test strategy and quality fitness
5. **Performance** (`/review:review-performance`) - Scalability and efficiency fitness
6. **Algorithms** (`/review:review-algorithms`) - Algorithm choice, data structures, concurrency, correctness fitness
7. **Data** (`/review:review-data`) - Schema design, migration safety, data integrity fitness
8. **Accessibility** (`/review:review-accessibility`) - UX and a11y fitness (if frontend code exists)
9. **Process** (`/review:review-process`) - Development workflow and documentation fitness
10. **Maintainability** (`/review:review-maintainability`) - Complexity, understandability, technical debt, code smells fitness

Skip review-accessibility if the project has no frontend code (no HTML, CSS, JSX, TSX, Vue, Svelte files).
Skip review-data if the project has no database code (no SQL files, migrations, ORM models, or database configuration).

### Step 3: Collect and Synthesize Results

Wait for all agents to complete. Gather each skill's:
- Dimension scores (1-10)
- Key findings with file:line evidence
- Recommended action items

### Step 4: Produce Unified Report

Write the report to `docs/fitness-report.md` with this structure:

```markdown
# Project Fitness Report

**Date:** YYYY-MM-DD
**Scope:** [what was reviewed]

## Overall Score: X.X / 10

| Domain | Score | Status |
|--------|-------|--------|
| Architecture | X/10 | [status emoji] |
| Security | X/10 | [status emoji] |
| Reliability | X/10 | [status emoji] |
| Testing | X/10 | [status emoji] |
| Performance | X/10 | [status emoji] |
| Algorithms | X/10 | [status emoji] |
| Data | X/10 | [status emoji] |
| Accessibility | X/10 | [status emoji] |
| Process | X/10 | [status emoji] |
| Maintainability | X/10 | [status emoji] |

Status: 8-10 = Healthy, 5-7 = Needs Attention, 1-4 = Critical

## Top 10 Action Items (Priority Order)

1. [CRITICAL] description - file:line
2. [HIGH] description - file:line
...

## Domain Details

### Architecture
[scores and findings from review-architecture]

### Security
[scores and findings from review-security]

### Maintainability
[scores and findings from review-maintainability]

### Algorithms
[scores and findings from review-algorithms]

### Data
[scores and findings from review-data]

...repeat for each domain...

## References

Based on guidance from [Fundamentals](https://jeffbailey.us/categories/fundamentals/). Each domain skill sources its scoring rubrics from dedicated blog posts — see `references/wisdom.md` in each skill directory.
```

### Scoring

Overall score = weighted average across the 10 domains. Read the effective weights from the `Effective weights:` line of the resolver output (or the `effective.weights` field of the embedded JSON sentinel block). Do NOT hardcode weights in this skill — every weight comes from the resolver so a per-directory override changes scoring without editing this file (ADR-002 / FR-7).

If a domain is skipped (e.g., accessibility on a backend-only repo), redistribute its weight proportionally across the remaining domains.

## Action Item Prioritization

Rank by severity and exploitability:
1. **CRITICAL** - Security vulnerabilities, data loss risks, production outages
2. **HIGH** - Architecture violations causing maintenance burden, missing tests for critical paths, algorithm correctness issues, data integrity gaps
3. **MEDIUM** - Performance bottlenecks, observability gaps, process improvements, concurrency risks
4. **LOW** - Style issues, minor naming inconsistencies, nice-to-have improvements
