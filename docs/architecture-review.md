# Software Architecture Fitness Review

**Date:** 2026-02-22  
**Scope:** Project Fitness Review Skills repository (SKILL.md files, markdown docs, tests)

## Summary

Overall fitness score: **7.6 / 10**

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Coupling | 9/10 | One-way dependency graph; no circular refs; review-full orchestrates only |
| Cohesion | 8/10 | Clear domain boundaries; minor duplication between workflow and README |
| Layering | 7/10 | Skills/checklist/doc/tests layers clear; .github workflow duplicates domain logic |
| Modularity | 9/10 | Consistent skill structure; public SKILL.md interfaces; references hidden |
| Naming | 7/10 | Consistent `review-<domain>` pattern; one report-path inconsistency |
| API Design | 7/10 | Report output paths mostly consistent; process-fitness-report.md outlier |
| Maintainability | 7/10 | Files under 400 lines; checklist ref patterns vary; no automated tests for skills |

## Detailed Findings

### Coupling (9/10)

**Evidence:**
- `src/review-full/SKILL.md:23-31` — Orchestrator lists domain skills; one-way dependency
- `docs/adrs/0001-skill-based-review-architecture.md:18-25` — ADR documents independent domain design
- `src/review-architecture/SKILL.md` — No imports of other skills; self-contained

**Findings:**
- Domain skills have no cross-references; each is self-contained
- review-full references domain skills by name only (orchestrator pattern)
- Skills depend only on their internal `references/checklist.md`
- README, SETUP, docs reference all skills for install but do not create code-level coupling

**Recommendations:**
- Document the orchestrator dependency explicitly in review-full (done)
- Consider a shared schema for report output format to avoid drift when skills evolve

### Cohesion (8/10)

**Evidence:**
- `src/review-architecture/SKILL.md` — Single responsibility: architecture review workflow and rubric
- `src/review-security/references/checklist.md` — Security-specific checklist; no mixed concerns
- `src/review-full/SKILL.md` — Orchestration only; no domain scoring logic embedded

**Findings:**
- Each skill has a single, clear purpose
- Checklists are domain-focused with no cross-domain concerns
- `.github/workflows/fitness-review.md:39-126` duplicates domain list and scoring from review-full — change to one domain would require updates in two places

**Recommendations:**
- Extract domain list and weights from a single source (e.g., docs or review-full) and have .github workflow reference it, or document the duplication as intentional (pipeline runs without skills loaded)

### Layering (7/10)

**Evidence:**
- `review-<domain>/SKILL.md` — Presentation/workflow layer
- `review-<domain>/references/checklist.md` — Reference data layer
- `docs/` — Documentation; `tests/` — Test specifications

**Findings:**
- Clear separation: skills define workflows; checklists hold detailed criteria; docs hold ADRs and index
- `.github/workflows/fitness-review.md` embeds full domain/scoring structure — operates as standalone pipeline (gh-aw) without loading skills; duplicates layering
- No skip-layer violations within the skills structure

**Recommendations:**
- Add ADR or comment in fitness-review.md explaining why it embeds domain logic (gh-aw runs without skill files)
- Consider a shared spec file that both review-full and fitness-review.md can reference

### Modularity (9/10)

**Evidence:**
- `README.md:266-308` — Structure documents each skill as `review-<domain>/SKILL.md` + `references/checklist.md`
- All skills expose SKILL.md as public interface; `references/` is internal
- `src/review-full/SKILL.md:19-34` — Orchestrator launches domains; each runs independently

**Findings:**
- Consistent module boundaries; each skill is independently installable
- Public interface: SKILL.md (name, description, workflow, output format)
- Internal: references/checklist.md — not imported by other skills
- Adding a new domain skill requires only adding a directory under `src/` and updating README/review-full list

**Recommendations:**
- Document the "skill contract" (SKILL.md frontmatter + workflow sections) in SETUP or a skill-creator doc for contributors

### Naming (7/10)

**Evidence:**
- `README.md:14-25` — Consistent `review-<domain>` pattern for all 11 skills
- `src/review-process/SKILL.md:214` — Report path: `docs/process-fitness-report.md` vs others `docs/<domain>-review.md`
- `README.md:5` — `jeffabailey` vs `catalog-info.yaml:12` — `jeffabailey` (possible typo; one 'b')

**Findings:**
- Skill names: `review-architecture`, `review-security`, etc. — consistent, discoverable
- Report paths: 9 of 10 use `<domain>-review.md`; process uses `process-fitness-report.md`
- Checklist references: mix of `references/checklist.md` (relative) and `src/review-<domain>/references/checklist.md` (absolute)

**Recommendations:**
- Rename `docs/process-fitness-report.md` to `docs/process-review.md` for consistency
- Verify `jeffabailey` vs `jeffbailey` in README and catalog-info.yaml; correct if typo

### API Design (7/10)

**Evidence:**
- Report output paths:
  - `src/review-architecture/SKILL.md:207` — `docs/architecture-review.md` ✓
  - `src/review-security/SKILL.md:223` — `docs/security-review.md` ✓
  - `src/review-process/SKILL.md:214` — `docs/process-fitness-report.md` ✗ (inconsistent)

**Findings:**
- Domain skills follow `docs/<domain>-review.md` contract (8 of 9)
- review-process breaks pattern: `process-fitness-report.md`
- No formal API spec; contract implied by README and each SKILL.md
- review-full expects reports in `docs/` with domain-specific filenames; process name would require orchestrator update

**Recommendations:**
- Standardize all domain report paths to `docs/<domain>-review.md`
- Add a "Skill Output Contract" section to docs/index.md or SETUP listing report paths and format

### Maintainability (7/10)

**Evidence:**
- Line counts: Largest file `src/review-accessibility/references/checklist.md` 371 lines; no file exceeds 400
- `src/review-architecture/references/checklist.md:197` — Checklist item references TODO/FIXME tracking (instructional, not repo debt)
- `tests/functional-tests.md`, `tests/trigger-tests.md` — Test plans exist; no automated execution

**Findings:**
- No god files; all under 500 lines
- Checklists cite Fundamentals series with stable URLs
- Duplication: domain list in README, SETUP, review-full, .github workflow — 4 places to update for new skill
- No automated tests for the skills themselves (tests are manual runbooks)
- Trigger phrase overlap documented in ADR `docs/adrs/0001-skill-based-review-architecture.md:54`

**Recommendations:**
- Create `docs/skill-list.yaml` or similar single source of truth for skill names and report paths
- Consider automation to validate: each `src/review-*/SKILL.md` exists, report paths are consistent, checklist exists
- Add CONTRIBUTING.md with "Adding a new domain skill" checklist

## Top 5 Action Items (by impact)

1. **[MEDIUM]** Standardize report path: change `review-process` output from `docs/process-fitness-report.md` to `docs/process-review.md` — `src/review-process/SKILL.md:214`
2. **[MEDIUM]** Extract domain list to single source — README:14-25, src/review-full/SKILL.md:23-31, .github/workflows/fitness-review.md:39-126, SETUP:238-248 — reduce duplication
3. **[LOW]** Document skill output contract (report paths, format) in docs — `docs/index.md`
4. **[LOW]** Verify/correct `jeffabailey` vs `jeffbailey` in README:5 and catalog-info.yaml:12
5. **[LOW]** Add CONTRIBUTING.md with "Adding a new domain skill" section — reduce onboarding friction

## Key Findings with Evidence

| Finding | Evidence |
|---------|----------|
| No circular dependencies | review-full → domains one-way; domains have no cross-refs |
| Consistent skill structure | All 9 domain skills: SKILL.md + references/checklist.md |
| Report path inconsistency | src/review-process/SKILL.md:214 uses `process-fitness-report.md` |
| Workflow duplication | .github/workflows/fitness-review.md embeds full domain list |
| Strong modularity | Each skill independently installable; clear boundaries |
| Files under 500 lines | Largest: 371 (review-accessibility checklist) |
| ADR documents design | docs/adrs/0001-skill-based-review-architecture.md |

## Checklist Reference

See `src/review-architecture/references/checklist.md` for the full architecture checklist.
