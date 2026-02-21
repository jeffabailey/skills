---
name: review-jit-test-gen
description: Generates just-in-time catching tests for changed code. Analyzes pending changes to find uncovered paths and writes focused tests that catch regressions at the moment of change. Use when the user says "generate tests", "jit tests", "test generation", "write tests for changes", or wants tests for recently modified code.
---

# JIT Test Generation

Generate focused tests that catch regressions for code being changed right now.

The JIT approach: write tests at the moment of change, when context is freshest and the risk of regression is highest. Every change is a potential regression - catch it before it ships.

Reference: https://jeffbailey.us/blog/2026/02/14/what-is-just-in-time-catching-test-generation/

## Workflow

### Step 1: Identify Changed Code

```bash
git diff --name-only HEAD
git diff --cached --name-only
```

If no changes exist, ask the user which files to target.

### Step 2: Analyze Each Changed File

For each modified file:

1. **Read the full file** to understand its purpose and structure
2. **Read the diff** to understand what specifically changed
3. **Find existing tests** by searching for test files that import or reference the changed code
4. **Identify uncovered paths** - focus on:
   - New functions/methods without tests
   - Modified branches (if/else, switch) without branch coverage
   - Error handling paths that aren't tested
   - Edge cases in changed logic (null, empty, boundary values)
   - State mutations that could regress

### Step 3: Prioritize What to Test

Generate tests in this priority order:

1. **External API boundaries** - Functions called by other modules or services
2. **State mutations** - Code that modifies databases, files, or shared state
3. **Error handling** - Catch blocks, error returns, fallback logic
4. **Complex conditionals** - Branches with multiple conditions
5. **Recently changed hot paths** - Code modified frequently (check git log)

### Step 4: Generate Tests

For each test:

1. **Follow existing conventions** - Match the project's test framework, naming, and file organization
2. **Test behavior, not implementation** - Assert on outputs and side effects, not internal details
3. **Use descriptive names** - Test name should describe the scenario and expected outcome
4. **One assertion per test** - Each test verifies one specific behavior
5. **Include edge cases** - Null/undefined inputs, empty collections, boundary values
6. **Use realistic test data** - Not "foo"/"bar" but domain-appropriate values

### Step 5: Validate Tests

Run the generated tests to confirm they pass:

```bash
# Detect and use the project's test runner
# npm test, pytest, go test, cargo test, etc.
```

If tests fail, fix them. Tests that don't pass are worse than no tests.

## Output Format

For each changed file, output:

```markdown
## Tests for `path/to/changed-file.ext`

**Changes detected:** [brief description of what changed]
**Existing coverage:** [what tests already exist]
**New tests generated:** [count]

### Test: [descriptive test name]
**Covers:** [what regression this catches]
**File:** `path/to/test-file.ext`
```

Then write the actual test files.

## What NOT to Generate

- Tests for trivial getters/setters
- Tests that duplicate existing coverage
- Tests that depend on implementation details (brittle)
- Tests for generated/vendored code
- Tests for configuration files

## Test Quality Checks

Before finalizing, verify each test:
- Has a clear, descriptive name
- Tests one behavior
- Would fail if the covered code regressed
- Uses the project's existing test patterns
- Doesn't require external services (mock them)
- Runs in isolation (no test interdependence)
