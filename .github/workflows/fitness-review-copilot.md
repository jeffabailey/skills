---
description: |
  Run a full project fitness review using GitHub Copilot (use when Claude returns 529 Overloaded).
  Same scope as fitness-review.md; alternative engine.

on:
  workflow_dispatch:
    inputs:
      agent_type:
        description: "Agent runner: copilot (fallback when Claude is overloaded)"
        required: true
        default: github
        type: choice
        options:
          - github

engine: copilot

run-name: "Project Fitness Review (Copilot) — agent: ${{ github.event.inputs.agent_type || 'scheduled' }}"
timeout-minutes: 30

permissions:
  contents: read
  issues: read
  pull-requests: read

network: defaults

tools:
  github:
    lockdown: false

safe-outputs:
  create-issue:
    title-prefix: "[fitness-report] "
    labels: [report, fitness-review, automation]
    close-older-issues: true
---

# Project Fitness Review (Copilot)

Use this workflow when the main fitness-review workflow fails with **529 Overloaded** from Anthropic. Requires `COPILOT_GITHUB_TOKEN` (PAT with `copilot-requests` scope).

**Same scope and prompt as fitness-review.md** — analyze the codebase and produce a comprehensive fitness report. Create a GitHub issue with your findings.

## Scope

Review the entire codebase unless the user specifies otherwise. If there are pending git changes, focus on those. Identify the architecture type (monolith, microservices, layered) and adapt the review depth accordingly.

## Review Domains

Evaluate each domain below. Score each dimension from 1–10 with file:line evidence. Skip domains that do not apply (e.g., skip accessibility if no frontend; skip data if no database).

### 1. Architecture
- Coupling, cohesion, layering, modularity, naming, API design, maintainability

### 2. Security
- Input validation, auth, data protection, dependencies, error handling, crypto

### 3. Reliability
- Observability, availability, timeout/retry, CI/CD, incident readiness, deploy hygiene

### 4. Testing
- Pyramid balance, quality, coverage, performance testing, CI integration

### 5. Performance
- Algorithms, database, caching, scalability, resource utilization

### 6. Algorithms
- Choice, data structures, complexity, concurrency, correctness

### 7. Data
- Schema, migrations, integrity, queries, modeling

### 8. Accessibility (skip if no frontend)
- Semantic HTML, keyboard, screen reader, contrast, responsive design

### 9. Process
- Documentation, workflow, code review, dependencies, organization

### 10. Maintainability
- Structural complexity, understandability, technical debt, coupling, code smells

## Report Structure

Create a GitHub issue with: Overall Score (X.X/10), per-domain scores with status (✅/⚠️/❌), Top 10 Action Items (CRITICAL/HIGH/MEDIUM/LOW), domain details, and references.

Based on guidance from https://jeffbailey.us/categories/fundamentals/
