# Functional Tests

Verify each skill produces correct, useful output.

## Test Protocol

For each test scenario:
1. Clone a test repository (or use the skills repo itself)
2. Run the skill
3. Verify the output matches expected structure
4. Verify findings are real (no false positives)
5. Verify file:line references are accurate

## review-architecture

### Test: Scores are produced for all dimensions

**Given:** A codebase with at least 5 source files
**When:** Run `/review:review-architecture`
**Then:**
- Report contains scores (1-10) for: Coupling, Cohesion, Layering, Modularity, Naming, API Design, Maintainability
- Each score has at least one file:line evidence citation
- Scores below 6 generate action items

### Test: Detects circular dependencies

**Given:** Module A imports B, B imports A
**When:** Run `/review:review-architecture`
**Then:** Coupling score reflects the circular dependency with specific file references

### Test: Detects poor naming

**Given:** Code with single-letter variables, generic names like `data`, `temp`, `process()`
**When:** Run `/review:review-architecture`
**Then:** Naming score reflects issues with specific examples

## review-security

### Test: High-confidence findings only

**Given:** Code with an obvious SQL injection (string concatenation in query)
**When:** Run `/review:review-security`
**Then:**
- Finding is reported with HIGH severity
- Confidence is 8/10 or higher
- File:line reference points to the vulnerable code
- Remediation suggests parameterized queries

### Test: No false positives for safe patterns

**Given:** Code using parameterized queries, proper auth middleware, bcrypt hashing
**When:** Run `/review:review-security`
**Then:** No findings for these safe patterns

### Test: Privacy checks work

**Given:** Code that logs user email addresses
**When:** Run `/review:review-security`
**Then:** Data Protection finding about PII in logs

## review-reliability

### Test: Detects missing observability

**Given:** A service with no logging, no metrics, no health checks
**When:** Run `/review:review-reliability`
**Then:**
- Observability score is low (1-3)
- Specific recommendations for what to instrument
- References golden signals framework

### Test: Detects missing timeouts

**Given:** HTTP client calls without timeout configuration
**When:** Run `/review:review-reliability`
**Then:** Timeout/Retry Hygiene score reflects the gap

## review-testing

### Test: Detects inverted test pyramid

**Given:** Project with 50 E2E tests, 5 unit tests
**When:** Run `/review:review-testing`
**Then:**
- Test Pyramid Balance score is low
- Recommends adding unit tests
- Identifies which functions lack unit coverage

### Test: Detects test quality issues

**Given:** Tests with no assertions, tests named "test1", "test2"
**When:** Run `/review:review-testing`
**Then:** Test Quality score reflects naming and assertion issues

## review-performance

### Test: Detects N+1 queries

**Given:** ORM code that queries in a loop
**When:** Run `/review:review-performance`
**Then:**
- Database Design score reflects the N+1 pattern
- Specific file:line reference to the loop

### Test: Detects quadratic algorithms

**Given:** Nested loops over the same collection
**When:** Run `/review:review-performance`
**Then:** Algorithmic Efficiency score flags O(n^2) with evidence

## review-accessibility

### Test: Detects missing alt text

**Given:** HTML with images lacking alt attributes
**When:** Run `/review:review-accessibility`
**Then:** Screen Reader Support score reflects the gap

### Test: Detects non-semantic HTML

**Given:** Clickable divs instead of buttons, missing form labels
**When:** Run `/review:review-accessibility`
**Then:** Semantic HTML score is low with specific elements cited

## review-process

### Test: Detects missing documentation

**Given:** Repo with no README or a minimal README
**When:** Run `/review:review-process`
**Then:** Documentation Quality score is low with specific suggestions

### Test: Detects stale dependencies

**Given:** package.json with dependencies 2+ major versions behind
**When:** Run `/review:review-process`
**Then:** Dependency Management score reflects staleness

## review-full

### Test: Produces unified report

**Given:** Any codebase
**When:** Run `/review:review-full`
**Then:**
- Report written to docs/fitness-report.md
- Contains overall score (weighted average)
- Contains all domain scores in table format
- Contains top 10 prioritized action items
- Each domain has detailed findings section

### Test: Skips accessibility for backend-only projects

**Given:** A Python/Go/Java project with no frontend files
**When:** Run `/review:review-full`
**Then:** Accessibility section notes "Skipped - no frontend code detected"

## review-jit-test-gen

### Test: Generates tests for changed code

**Given:** Modified Python/JS/TS file with a new function
**When:** Run `/review:review-jit-test-gen`
**Then:**
- Test file is created following project conventions
- Test covers the new function
- Test uses descriptive name
- Test passes when run

### Test: Doesn't duplicate existing tests

**Given:** File with changes that are already well-tested
**When:** Run `/review:review-jit-test-gen`
**Then:** Reports that existing coverage is sufficient, generates only gap-filling tests
