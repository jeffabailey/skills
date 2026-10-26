---
name: review-architecture
description: Analyzes code for software architecture fitness, producing scores (1-10) across coupling, cohesion, layering, modularity, naming, API design, and maintainability. Use when the user says /review:review-architecture, requests an architecture review, asks about coupling and cohesion, wants to analyze design or check code structure, asks to review naming or API design, or needs architecture fitness scores. Triggers on "architecture review", "coupling and cohesion", "analyze design", "check code structure", "review naming", "API design". Only reports findings with confidence >= 7/10.
---

# Software Architecture Fitness Review

Analyze the codebase (or specified files/modules) for software architecture fitness. Identify structural problems, design violations, and maintainability risks using evidence from the code.

Reference: [Fundamentals of Software Architecture](https://jeffbailey.us/blog/2025/10/19/fundamentals-of-software-architecture/), [Fundamentals of Software Design](https://jeffbailey.us/blog/2025/11/05/fundamentals-of-software-design/), [Fundamentals of API Design and Contracts](https://jeffbailey.us/blog/2026/01/16/fundamentals-of-api-design-and-contracts/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

- `references/rubric.md` is the scoring source: severity definitions, score anchors for each dimension, the N/A rule, and how to compute the overall. Read it first; it is short.
- `references/checklist.md` is what to inspect during the analysis steps. Its numeric thresholds (70% fan-in, 500-line classes, 50-line functions, 4 nesting levels) match the rubric.
- `references/wisdom.md` is optional background, auto-generated from the articles below. It has no rubric. Grep it by heading for a specific question (`grep -n '^#' references/wisdom.md`, then read one section); never read it whole.
  - [Fundamentals of Software Architecture](https://jeffbailey.us/blog/2025/10/19/fundamentals-of-software-architecture/)
  - [Fundamentals of Software Design](https://jeffbailey.us/blog/2025/11/05/fundamentals-of-software-design/)
  - [Fundamentals of API Design and Contracts](https://jeffbailey.us/blog/2026/01/16/fundamentals-of-api-design-and-contracts/)
- `scripts/import_graph.py` builds the internal import graph for Python and JS/TS so every run does not hand-roll one.

## Configuration

Invoke the resolver CLI to obtain effective weights and thresholds for the review target. Never load `fitness-config.json` directly.

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py" show --path <target>
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; the resolver ships two levels up in the plugin's `scripts/`. If your agent does not expand the variable, substitute the directory containing this `SKILL.md`.

Where `<target>` is the file or directory under review. The CLI walks up to discover any module override and merges it with the root config. Copy the `Config:` and `Effective weights:` lines from the resolver output into the report header (the template has the slot; they must land within the first 10 lines as the provenance trail, AC-03.1, AC-08.2). The weights are for the review-full aggregate; this report uses only `statusThresholds`. The `effective` object inside the JSON block delimited by `<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->` / `<!-- END_EFFECTIVE_CONFIG_JSON -->` carries weights, status thresholds, security, and scoring for any programmatic needs.

## Workflow

1. **Load the rubric** — Read `references/rubric.md` and `references/checklist.md`.

2. **Scope the review** — Note the target (path or file set) and whether the user asked a specific question (for example "is `claude_client.py` too tangled?"). Map the structure with Glob/Grep: top-level directories, entry points, packages, dependency manifests, and where the tests for the target live (they may sit outside it). Decide what kind of system it is (script, library, CLI, layered app, services).

3. **Decide applicability** — For each of the 7 dimensions, decide whether anything in scope can be evaluated. Mark the rest N/A with a one-line reason (rubric.md, "N/A and evidence of absence"). A focused question narrows the emphasis, not the coverage: still score every applicable dimension, but go deepest on the ones asked about.

4. **Map the dependency graph** — Run the bundled script on the target (or its package root):

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/import_graph.py" <target-dir>
   ```

   It prints per-module line count, fan-in, fan-out and import lines, cycles (with import-time cycles separated from deferred ones), and modules imported by more than 70% of the others. Tests are excluded by default (`--include-tests` to add them); `--json` for machine output. For other languages, trace imports with Grep. Use these numbers as evidence for Coupling and Modularity rather than estimating.

5. **Inspect each dimension** — Walk the matching section of `checklist.md` for Coupling, Cohesion, Layering, Modularity, Naming, API Design and Maintainability. Read the code behind every candidate finding.

6. **Verify each finding** — Before keeping a candidate:
   - Confirm the cited file:line says what the finding claims.
   - Check the Impact by reading the code path end to end or running it (a CLI call, a tiny import, an existing test). If you could not verify it, say "unverified" in the Impact and lower confidence by at least 2. A correct citation with a wrong consequence is still a wrong finding.
   - Drop anything below confidence 7 and count it.

7. **Score** — Score each applicable dimension with the rubric.md anchors, compute the overall per rubric.md (mean of scored dimensions, CRITICAL cap at 4.0), and apply status bands.

8. **Self-check, then write** — Confirm: every file:line exists and says what the finding claims; every reported finding has confidence >= 7; the overall equals the stated computation; every dimension below 6 has an action item; no secret values are reproduced (refer to secrets by file:line only). Then write the report.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?
- Did you verify the stated Impact by reading or running the code path?

If any answer is no, do not report it (or lower its confidence until it drops out). It is better to miss a theoretical issue than to flood the report with noise. Record how many candidates were dropped so the reader knows the filter ran.

Severity definitions (CRITICAL, HIGH, MEDIUM, LOW) with architecture examples are in `references/rubric.md`.

## Scoring Dimensions (1-10 each)

Score anchors for each dimension are in `references/rubric.md`; the checks are in `references/checklist.md`.

1. **Coupling** — Cross-boundary import count, concrete vs abstract dependencies, shared mutable state, circular dependencies, temporal coupling
2. **Cohesion** — Single responsibility, functional cohesion, concern separation, change-reason analysis
3. **Layering** — Layer separation, dependency direction, skip-layer violations, infrastructure leakage
4. **Modularity** — Boundary clarity, public interfaces, information hiding, independent testability
5. **Naming** — Clarity, consistency, context-appropriateness, convention compliance, discoverability, truthfulness
6. **API Design** — Contract explicitness, error consistency, backward compatibility, semantic clarity, idempotency
7. **Maintainability** — Code smells, duplication, magic numbers, test coverage, documentation, dependency health

## Output Format

Write the report to `docs/architecture-review.md` at the root of the repository that contains the target (`git -C <target> rev-parse --show-toplevel`; if the target is not in a git repo, the target directory), unless the user gives a path. When the review is scoped to a subdirectory or file set rather than the whole repo, write `docs/architecture-review-<scope-slug>.md` instead (for example `docs/architecture-review-scripts-fitness-config.md`) so a scoped run does not replace the whole-repo report. If the file already exists, overwrite it only when it is an earlier report from this skill (its first line is `# Software Architecture Fitness Review`); otherwise pick a new name and say so.

```markdown
# Software Architecture Fitness Review

**Target:** <path(s) or scope reviewed>
Config: <copied from resolver output>
Effective weights: <copied from resolver output>

## Direct Answer

(Only when the user asked a specific question. Answer it in 2-5 sentences with file:line evidence, e.g. fan-in/fan-out numbers from import_graph.py.)

## Summary

Overall fitness score: X.X / 10 — <status band> (mean of <list of scored dimensions>; <CRITICAL cap applied / not applied>)

| Dimension | Score | Status | Key Finding |
|-----------|-------|--------|-------------|
| Coupling | X/10 | Healthy / Needs Attention / Critical | ... |
| Cohesion | X/10 | ... | ... |
| Layering | N/A — reason | — | ... |
| Modularity | X/10 | ... | ... |
| Naming | X/10 | ... | ... |
| API Design | X/10 | ... | ... |
| Maintainability | X/10 | ... | ... |

Dependency graph: <N modules, cycles, hubs, max fan-in/fan-out from import_graph.py>.
Candidates dropped below confidence 7: <count> (<one-line gist each, or "none">).

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line
- **Description:** What the issue is and why it matters.
- **Evidence:** The specific code pattern found.
- **Impact:** What could go wrong as the codebase evolves, and how you verified it (read path X -> Y, or ran Z).
- **Remediation:** Concrete fix with code example or specific steps.

(repeat for each finding, ordered by severity)

### Coupling (X/10)
- Evidence: file:line references (or the place something is missing)
- Issues found
- Recommendations

(repeat for each dimension; N/A dimensions get one line with the reason)

## Top Action Items (by impact)

Up to 5, fewer is fine. Every dimension scored below 6 needs at least one item; add items beyond 5 only for that.

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line (Dimension)
2. ...

## Checklist Reference

See references/checklist.md for the full architecture checklist and references/rubric.md for the scoring anchors.

## Reference

Based on [Fundamentals of Software Architecture](https://jeffbailey.us/blog/2025/10/19/fundamentals-of-software-architecture/), [Fundamentals of Software Design](https://jeffbailey.us/blog/2025/11/05/fundamentals-of-software-design/), [Fundamentals of API Design and Contracts](https://jeffbailey.us/blog/2026/01/16/fundamentals-of-api-design-and-contracts/), and guidance from https://jeffbailey.us/categories/fundamentals/
```
