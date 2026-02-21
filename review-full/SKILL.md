---
name: review-full
description: Runs a comprehensive project fitness review combining architecture, security, reliability, testing, performance, accessibility, and process analysis. Use when the user says "full review", "comprehensive review", "project fitness", "review everything", or wants all review skills run on current changes before shipping.
---

# Full Project Fitness Review

Run all review skills in parallel to produce a unified fitness assessment.

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
6. **Accessibility** (`/review:review-accessibility`) - UX and a11y fitness (if frontend code exists)
7. **Process** (`/review:review-process`) - Development workflow and documentation fitness

Skip review-accessibility if the project has no frontend code (no HTML, CSS, JSX, TSX, Vue, Svelte files).

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
| Accessibility | X/10 | [status emoji] |
| Process | X/10 | [status emoji] |

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

...repeat for each domain...

## References

Based on guidance from https://jeffbailey.us/categories/fundamentals/
```

### Scoring

Overall score = weighted average:
- Architecture: 20%
- Security: 20%
- Reliability: 15%
- Testing: 15%
- Performance: 15%
- Accessibility: 10% (0% if skipped)
- Process: 5%

If accessibility is skipped, redistribute its weight proportionally.

## Action Item Prioritization

Rank by severity and exploitability:
1. **CRITICAL** - Security vulnerabilities, data loss risks, production outages
2. **HIGH** - Architecture violations causing maintenance burden, missing tests for critical paths
3. **MEDIUM** - Performance bottlenecks, observability gaps, process improvements
4. **LOW** - Style issues, minor naming inconsistencies, nice-to-have improvements
