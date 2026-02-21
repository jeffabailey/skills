---
name: review-full
description: Runs a comprehensive code review pipeline combining architecture fitness, JIT test generation, and security analysis. Use when the user says /review:full-review, requests a full review, asks for comprehensive code review before shipping, or wants all review agents on current changes.
---

# Full Code Review Pipeline

Run a comprehensive review of the current changes. Launch these analyses (in parallel when possible):

1. **Architecture Fitness** — Evaluate architectural fitness scores for changed modules (see review-arch-fitness skill)
2. **JIT Test Generation** — Identify and generate missing tests for changed code (see review-jit-test-gen skill)
3. **Security Review** — Run security analysis on the diff (or use built-in `/security-review` if available)

## Output

Produce a unified review summary at `docs/review-summary.md` with:

- Overall quality score
- Architecture fitness scores
- Generated tests summary
- Security findings
- Top 5 action items ranked by priority
