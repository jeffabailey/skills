---
name: review-performance
description: Analyzes code for performance and scalability issues, producing fitness scores (1-10) across algorithmic efficiency, database design, caching strategy, scalability readiness, resource utilization, and data pipeline efficiency. Covers services, CLIs, CI scripts, batch jobs, and ML inference code. Use when the user says /review:performance, requests a performance review, asks for scalability analysis, wants to find N+1 queries or Big-O hot paths, asks why something gets slow as data grows, or needs performance fitness scores before shipping. Only reports findings with confidence >= 7/10.
---

# Performance and Scalability Fitness Review

Analyze the codebase (or specified files/modules) for performance and scalability fitness. Identify hot paths, inefficient patterns, and scaling bottlenecks using evidence from the code.

Reference: [Fundamentals of Software Performance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-performance/), [Fundamentals of Software Scalability](https://jeffbailey.us/blog/2025/12/22/fundamentals-of-software-scalability/), [Fundamentals of Software Caching](https://jeffbailey.us/blog/2025/12/24/fundamentals-of-software-caching/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

Three references, with different jobs:

- `references/rubric.md` is the scoring source: severity definitions, 1-10 anchors per dimension, where a finding belongs, the N/A rule, and the overall-score computation. Read it first; it is short. Using it keeps scores repeatable across runs.
- `references/checklist.md` is what to look for during the analysis steps, section by section.
- `references/wisdom.md` is optional background, auto-generated from the blog posts below. It has no rubric. Grep it by heading for a specific question (for example "percentiles" or "stampede"); never read it whole, it is about 86 KB.

Sources for wisdom.md:

- [Fundamentals of Software Performance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-performance/)
- [Fundamentals of Software Scalability](https://jeffbailey.us/blog/2025/12/22/fundamentals-of-software-scalability/)
- [Fundamentals of Software Caching](https://jeffbailey.us/blog/2025/12/24/fundamentals-of-software-caching/)

## Configuration

Invoke the resolver CLI to obtain effective weights and thresholds for the review target. Never load `fitness-config.json` directly.

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py" show --path <target>
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; the resolver ships two levels up in the plugin's `scripts/`. If your agent does not expand the variable, substitute the directory containing this `SKILL.md`.

Where `<target>` is the file or directory under review. The CLI walks up to discover any module override and merges it with the root config. Copy the `Config:` and `Effective weights:` lines from the resolver output verbatim into the report header (see Output Format) as the provenance trail (AC-03.1, AC-08.2); they record exactly which config produced the scores, so a paraphrase or a pointer to another file breaks the trail. The `effective` object inside the JSON block delimited by `<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->` / `<!-- END_EFFECTIVE_CONFIG_JSON -->` carries weights, status thresholds, security, and scoring for any programmatic needs; use its `statusThresholds` for the status band.

The resolver resolves from the target's location, not your working directory, so pass the target as an absolute path when it lives in another repository. When the request names several targets, run the resolver once per target. If every run prints the same `Config:` and `Effective weights:` lines, copy them once. If they differ, copy each pair, prefixed with its target (`Config (scripts/): ...`), and keep all of them in the header.

## Workflow

1. **Read the rubric and checklist** — Read `references/rubric.md`, then `references/checklist.md`. Do not read `wisdom.md` up front.

2. **Scope and resolve** — Settle the target path(s) and run the resolver for each (see Configuration). Note the repository root that contains the target; the report goes there.

3. **Decide applicability** — For each of the six dimensions, decide whether the target has anything for it to evaluate (any DB access? any cache or repeated expensive work? any batch or streaming job?). Mark the rest `N/A` with a reason and a cited absence, per rubric.md. This keeps placeholder scores out of the average and out of review-full.

4. **Identify hot paths** — Find where work grows with input. The kind of code decides where to look:
   - Services: request handlers, API endpoints, message consumers, background workers.
   - CLIs and scripts: the `main`/entry point and the loop over files, rows, or items it processes.
   - CI: scripts called from `.github/workflows/` or similar; anything that walks the repo or fetches per item.
   - Batch and ETL: the per-record or per-batch loop and its reads and writes.
   - ML inference: model loading, `encode`/`embed`/`predict` calls, similarity loops, and whether results are recomputed each run.

   If the user named a symptom ("slow as post count grows"), start from the code that iterates over that collection.

5. **Trace data flow** — For each hot path, trace what gets queried, fetched, computed, and cached, from entry to output.

6. **Analyze the applicable dimensions** — Work through the matching `checklist.md` sections: algorithmic complexity (1, 5), database interactions (2), caching (3), scalability (4), resource utilization (6), data pipelines (7), and CLI/CI/batch/ML paths (8). Look at the actual line before writing a finding; grep hits are leads, not evidence.

7. **Score** — Assign severities and dimension scores from `rubric.md`, each with file:line evidence. File each finding under the one dimension rubric.md assigns it.

8. **Self-check, then write** — Before writing the report, re-open each cited location and confirm:
   - every file:line exists and the line shows what the finding claims (line numbers drift as you read; fix them now);
   - every finding has confidence >= 7;
   - the overall equals the stated mean of the scored dimensions (with the CRITICAL cap applied);
   - no secret values appear in the report (refer to secrets by file:line only).

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

Severity levels (CRITICAL, HIGH, MEDIUM, LOW) and their performance-specific examples are defined in `references/rubric.md`. Severity depends on whether the input grows and whether the path is hot, so state both in the finding.

## Scoring Dimensions (1-10 each)

Score anchors for each dimension are in `references/rubric.md`; checks for each are in `references/checklist.md`. A dimension with nothing to evaluate is `N/A`, not a number.

1. **Algorithmic Efficiency** — Big-O complexity of hot paths, data structure selection, bounded vs unbounded collections
2. **Database Design** — N+1 queries, indexing, connection pooling, result set bounding, query patterns
3. **Caching Strategy** — Cache coverage (including repeated model inference), TTL/invalidation, stampede protection, bounded growth, observability
4. **Scalability Readiness** — Stateless design, downstream resilience, database scaling, async or concurrent processing, backpressure
5. **Resource Utilization** — Memory bounds, connection pools, timeouts, payload sizing, model/client reuse, inference batching, thread/goroutine management
6. **Data Pipeline Efficiency** — Incremental processing, validation placement, error isolation, idempotency, schema handling

## Output Format

Write the report to `docs/performance-review.md` at the root of the repository that contains the target, unless the user gives a path. For a review scoped to a subdirectory or a file set, write `docs/performance-review-<scope-slug>.md` instead (for example `docs/performance-review-github-scripts.md`), so a scoped run does not replace the whole-repo report. Use this structure:

```markdown
# Performance and Scalability Review

**Target:** <path(s) or scope reviewed>
Config: <copied verbatim from resolver output>
Effective weights: <copied verbatim from resolver output>

## Direct Answer

(Only when the user asked a specific question, such as "why does this get slow?" Two to five sentences answering it, pointing at the findings below.)

## Summary

Overall fitness score: X.X / 10 (mean of <list the scored dimensions>; <N/A dimensions> excluded) — <status band>

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Algorithmic Efficiency | X/10 | ... |
| Database Design | X/10 or N/A — reason | ... |
| Caching Strategy | X/10 or N/A — reason | ... |
| Scalability Readiness | X/10 or N/A — reason | ... |
| Resource Utilization | X/10 or N/A — reason | ... |
| Data Pipeline Efficiency | X/10 or N/A — reason | ... |

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line
- **Description:** What the issue is, whether the path is hot, and how the input grows.
- **Evidence:** The specific code pattern found.
- **Impact:** What gets slower or fails, and at what scale.
- **Remediation:** Concrete fix with code example or specific steps.

(repeat for each finding, ordered by severity)

### Algorithmic Efficiency (X/10)
- Evidence: file:line references
- Issues found
- Recommendations

(repeat for each scored dimension; for N/A dimensions, one line with the reason)

## Top Action Items (by impact)

Up to 5; fewer is fine.

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...

## Checklist Reference

See references/checklist.md for the full performance checklist.

## Reference

Based on [Fundamentals of Software Performance](https://jeffbailey.us/blog/2025/12/16/fundamentals-of-software-performance/), [Fundamentals of Software Scalability](https://jeffbailey.us/blog/2025/12/22/fundamentals-of-software-scalability/), [Fundamentals of Software Caching](https://jeffbailey.us/blog/2025/12/24/fundamentals-of-software-caching/) and guidance from https://jeffbailey.us/categories/fundamentals/
```
