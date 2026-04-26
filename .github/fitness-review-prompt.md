# Project Fitness Review

> Canonical prompt for Claude Code (local or CI). Same review spec as `.github/workflows/fitness-review.yml`.

Analyze this repository and produce a comprehensive fitness report.

**Output (depends on runner):**
- **GitHub Actions**: Create a GitHub issue with your findings using the create_issue tool.
- **Local (Claude Code CLI)**: Write the report to `docs/fitness-report.md`.

## Scope

Review the entire codebase unless the user specifies otherwise. If there are pending git changes, focus on those. Identify the architecture type (monolith, microservices, layered) and adapt the review depth accordingly.

## Review Domains

Evaluate each domain below. Score each dimension from 1–10 with file:line evidence. Skip domains that do not apply (e.g., skip accessibility if no frontend; skip data if no database).

### 1. Architecture

- Coupling (cross-boundary imports, abstractions at boundaries)
- Cohesion (single responsibility, related content per module)
- Layering (presentation, business logic, data access)
- Modularity (clear boundaries, minimal skip-layer violations)
- Naming (clarity, consistency, discoverability)
- API design (consistency, error handling, versioning)
- Maintainability (code smells, god classes, duplication)

### 2. Security

- Input validation and sanitization
- Authentication and authorization
- Data protection and sensitive-data handling
- Dependency vulnerabilities
- Error handling and logging (no sensitive data in logs)
- Cryptography usage

### 3. Reliability

- Observability (logging, metrics, tracing)
- Availability design
- Timeout and retry hygiene
- CI/CD maturity
- Incident readiness
- Capacity planning
- Deploy hygiene

### 4. Testing

- Test pyramid balance
- Test quality and coverage
- Performance testing
- Debugging support
- CI integration

### 5. Performance

- Algorithmic efficiency
- Database design
- Caching strategy
- Scalability readiness
- Resource utilization
- Data pipeline efficiency

### 6. Algorithms

- Algorithm choice for problem domain
- Data structure selection
- Complexity (time and space)
- Concurrency safety
- Edge cases and correctness

### 7. Data

- Schema design
- Migration safety
- Data integrity
- Query correctness
- Data modeling
- Pipeline quality

### 8. Accessibility (skip if no frontend)

- Semantic HTML
- Keyboard navigation
- Screen reader support
- Color and contrast
- Progressive enhancement
- Responsive design
- Usability heuristics

### 9. Process

- Documentation
- Workflow and branching
- Code review
- Dependency management
- Project organization
- Portability
- Leadership signals

### 10. Maintainability

- Structural complexity (cyclomatic, cognitive, LOC, nesting)
- Understandability (naming, flow clarity, non-obvious logic documentation)
- Technical debt (TODO/FIXME, duplication, magic numbers, suppressions)
- Coupling and dependency depth
- Code smell density (god classes, long methods, feature envy)

## Report Structure

```markdown
# Project Fitness Report

**Date:** YYYY-MM-DD
**Scope:** [what was reviewed]

## Overall Score: X.X / 10

| Domain | Score | Status |
|--------|-------|--------|
| Architecture | X/10 | ✅/⚠️/❌ |
| Security | X/10 | ✅/⚠️/❌ |
| ... |

Status: 8–10 = ✅ Healthy, 5–7 = ⚠️ Needs Attention, 1–4 = ❌ Critical

## Top 10 Action Items (Priority Order)

1. [CRITICAL] description — file:line
2. [HIGH] description — file:line
...

## Domain Details

[Per-domain scores, evidence, and findings]

## References

Based on guidance from https://jeffbailey.us/categories/fundamentals/
```

## Configuration

Always invoke the resolver CLI to read effective weights and thresholds. Never load `fitness-config.json` directly. The CLI walks up from the review target to find module overrides and merges them with the root config per ADR-001 / ADR-002 / ADR-005.

```bash
python3 scripts/fitness-config.py show --path <target>
```

For a broad-scope review, pass the repository root as `<target>`. Per ADR-005, only the root config is applied at root scope; the resolver names any discovered subtree overrides as a footnote but does not apply them.

Parse the resolver output to obtain the `Config:` line, the `Effective weights:` line, and the embedded JSON block delimited by `<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->` / `<!-- END_EFFECTIVE_CONFIG_JSON -->`. Include the `Config:` and `Effective weights:` lines within the first 10 lines of the report as the provenance trail.

## Scoring

Overall score = weighted average across the 10 domains. Read the effective weights from the resolver output (the `Effective weights:` line or the `effective.weights` field of the embedded JSON block). Do NOT hardcode weights here — every weight comes from the resolver so a per-directory override changes scoring without editing this prompt (ADR-002 / FR-7).

If a domain is skipped (e.g., accessibility on a backend-only repo), redistribute its weight proportionally.

## Action Item Prioritization

1. **CRITICAL** — Security vulnerabilities, data loss risks, production outages
2. **HIGH** — Architecture violations, missing tests for critical paths, algorithm correctness, data integrity gaps
3. **MEDIUM** — Performance bottlenecks, observability gaps, process improvements, concurrency risks
4. **LOW** — Style, naming, nice-to-haves

## Process

1. Map the codebase structure (directories, entry points, dependencies)
2. Analyze each domain systematically
3. Assign scores with evidence
4. Rank action items by severity
5. Compose the unified report (issue if GitHub Actions, file if local CLI)
