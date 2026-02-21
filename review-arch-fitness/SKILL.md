---
name: review-arch-fitness
description: Analyzes code architecture and produces fitness scores (1-10) across coupling, cohesion, testability, layering, API surface, error handling, and configuration hygiene. Use when the user says /review:arch-fitness, requests architectural analysis, asks for architecture fitness scores, or wants to evaluate codebase structure before shipping.
---

# Architectural Fitness Analysis

Analyze the codebase (or specified files/modules) for architectural fitness.

## Scoring Dimensions (1-10 each)

Evaluate and score each dimension with evidence:

1. **Coupling** — How tightly are modules connected? Check import graphs, shared state
2. **Cohesion** — Do modules have single responsibilities?
3. **Testability** — Can components be tested in isolation? Check dependency injection patterns
4. **Layering violations** — Are there calls that skip architectural layers?
5. **API surface area** — Are public interfaces minimal and well-defined?
6. **Error handling consistency** — Uniform patterns across the codebase?
7. **Configuration hygiene** — Secrets, env vars, feature flags handled properly?

## Process

1. Use Grep/Glob to map the dependency graph
2. Identify the top 5 most-coupled modules
3. Check for circular dependencies
4. Score each dimension with specific file:line evidence
5. Produce a markdown report with an overall fitness score (average)
6. List top 3 actionable improvements

## Output

Write the report to `docs/arch-fitness-report.md`
