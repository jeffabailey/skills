---
name: review-jit-test-gen
description: Analyzes code for JIT (just-in-time) catching test generation opportunities. Identifies uncovered paths and suggests focused tests that catch regressions at the moment of change. Use when the user says /review:jit-test-gen, requests JIT test generation, asks for test coverage analysis, or wants tests generated for changed code.
---

# JIT Catching Test Generation

Reference: https://jeffbailey.us/blog/2026/02/14/what-is-just-in-time-catching-test-generation/

Analyze the changed or specified files for test generation opportunities using the JIT catching approach.

## Process

1. Identify functions/methods that lack test coverage (use `git diff` if on a branch)
2. For each uncovered path, generate focused tests that:
   - Test the boundary conditions and edge cases
   - Catch regressions at the moment of change (not retroactively)
   - Follow existing test patterns in the repo
3. Prioritize tests for:
   - Code paths touching external APIs or I/O
   - State mutations
   - Error handling branches
   - Recently changed logic (git blame/diff)
4. Generate tests following the project's existing test framework and conventions
5. Run the tests to verify they pass

## Output

Provide a summary of what was generated and why each test matters.
