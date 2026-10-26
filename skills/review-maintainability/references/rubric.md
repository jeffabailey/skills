# Maintainability Scoring Rubric

Hand-maintained scoring rubric. sync-wisdom does not regenerate this file.

This is the scoring source for review-maintainability. Score from the anchors below so two runs on the same code land on the same number. `checklist.md` lists what to inspect; `wisdom.md` is background only.

## Threshold table

The single source of numeric thresholds. `checklist.md`, the report's Metrics Summary, and `scripts/metrics.py` (its `FINDING` dict) all use these numbers.

Two columns, because the article's targets (30-line functions, 300-line classes) describe what good code aims for, while reporting every 31-line function would bury the real problems. Code between the two columns is not a finding; it only keeps a dimension out of the 9-10 band.

| Metric | Target (healthy) | Finding (report it) | Severe |
|--------|------------------|---------------------|--------|
| Function / method LOC | <= 30 | > 50 | > 100 |
| Cyclomatic complexity per function | <= 10 | > 15 | > 25 |
| Cognitive complexity per function (judged, not measured) | <= 15 | > 25 | - |
| Nesting depth inside a function | <= 3 | > 4 | > 6 |
| Parameters per function (self/cls and one options object count once) | <= 4 | > 5 | > 8 |
| Class LOC | <= 300 | > 500 | > 1000 |
| Module / file LOC (non-blank) | <= 500 | > 1000 | > 2000 |
| Inheritance depth | <= 3 | > 3 | > 5 |
| Untracked TODO/FIXME/HACK/XXX | < 5 | >= 5, or any HACK without a reason | >= 20 |
| Lint/type suppressions | each justified inline | any file-wide blanket disable, or unjustified ones >= 5 | - |
| Duplicated block | none | >= 10 near-identical lines in 2+ places | the same block in 4+ places |
| Fan-in of one module | < 70% of modules import it | >= 70% | - |

**No classes in the language or codebase?** Apply the class row to the largest unit that holds state and behavior together: a closure factory (a JS function that returns an object of inner functions), a Go type with its methods, or a module whose top-level functions share module-level state. Say which unit you used in the Metrics Summary.

**Measured or estimated?** Run `scripts/metrics.py`. Python is AST-exact. Brace languages are approximate (object literals inflate nesting); spot-check any value you base a HIGH finding on by reading the code. Values you measured by reading are marked `(read)` in the Metrics Summary.

**Function LOC is the physical span** (first to last line, comments included), which is what metrics.py reports. When commented-out code is what pushes a function over the bar, report the commented-out code (a Code Smell), not the length.

## Severity

| Level | Definition | Examples |
|-------|-----------|----------|
| CRITICAL | The code cannot be changed safely in its current shape: a routine change to the system's core has a high chance of breaking something unrelated, and no test or structure contains the blast radius. Rare in maintainability reviews; small scripts almost never qualify. | One 800+ LOC function holding most of a production system's logic with no tests; core business rules copied across 4+ services that already compute different results, with no shared tests. |
| HIGH | Measurably over a Severe threshold, or a pattern that multiplies the cost of every future change. | A function at 120 LOC with CC 30; the same 60-line script copied into four files. |
| MEDIUM | Over a Finding threshold but local; costs time when that area is touched. | A 70-line function with nesting 5; 8 untracked TODOs; a file-wide `eslint-disable`. |
| LOW | Between Target and Finding, or a readability nit with a clear fix. | Magic number `86400` in one place; a vague name like `data` in a small helper. |

## Dimension anchors

Pick the band whose description fits the worst *pattern* (not the single worst line), then use the higher or lower number in the band by how widespread it is.

### 1. Structural Complexity
LOC, CC, and nesting set the band. A parameter-count overage on its own lowers the score by at most one band from where the other metrics put it (e.g. 9-10 becomes 7-8), because a long signature is cheap to fix and local.
- **9-10:** Every function within Target (LOC <= 30, CC <= 10, nesting <= 3, params <= 4).
- **7-8:** No function over a Finding threshold; a few between Target and Finding.
- **5-6:** 1-3 functions over a Finding threshold (e.g. 50-100 LOC or CC 16-25); none Severe.
- **3-4:** Several functions over Finding, or one Severe (LOC > 100, CC > 25, nesting > 6).
- **1-2:** Multiple Severe functions, or one function/closure holding most of the codebase (300+ LOC).

### 2. Understandability / Comprehensibility
- **9-10:** Names state intent in domain terms; control flow reads top to bottom; every non-obvious rule has a "why" comment or ADR link.
- **7-8:** Mostly clear; a few generic names (`data`, `handle`, `process`) or an undocumented invariant.
- **5-6:** A reader must trace several call sites to understand a core flow; inconsistent conventions between modules (e.g. two error-handling styles).
- **3-4:** Misleading names or stale comments that contradict the code; large commented-out blocks mixed with live code.
- **1-2:** Core logic is unreadable without running it: single-letter names in long functions, hidden global side effects, no structure.

### 3. Technical Debt Indicators
- **9-10:** No untracked markers, no duplicated blocks, constants named, suppressions justified.
- **7-8:** Under 5 untracked markers; one small duplication or a few magic values.
- **5-6:** 5-19 untracked markers, or one duplicated block (>= 10 lines in 2-3 places), or a blanket suppression.
- **3-4:** Duplication across 4+ files, or hardcoded configuration copied per environment/account, or 20+ untracked markers.
- **1-2:** Duplication is the main structure of the code (most files are copies), and the copies have drifted.

### 4. Coupling and Dependency Depth
- **9-10:** Clear module boundaries; dependencies point inward; no module imported by >= 70%; inheritance <= 3.
- **7-8:** One utility hub or a skip-layer import with a clear reason.
- **5-6:** A god module (fan-in >= 70%), circular imports between two modules, or inheritance depth 4-5.
- **3-4:** Several cycles, presentation code importing data-layer internals, or a change to one module routinely forcing edits in 5+ others.
- **1-2:** No discernible boundaries; everything imports everything.

### 5. Code Smell Density
Count smell instances: each affected unit (function, class, file, or group of copies) counts once per smell type, so four copied files are one shotgun-surgery instance, and commented-out blocks in four files are four instances. Smell types: god class/closure, long method, feature envy, inappropriate intimacy, shotgun surgery, dead or commented-out code, primitive obsession.

Use density per 1,000 non-blank LOC when the target has 1,000+ LOC. Below that, density swings wildly, so use the raw count instead: 0-1 = 9-10, 2-3 = 7-8, 4-5 = 5-6, 6-8 = 3-4, 9+ = 1-2.
- **9-10:** 0-1 smells in total.
- **7-8:** < 2 per 1,000 LOC, none of them god class/closure.
- **5-6:** 2-4 per 1,000 LOC, or one god class/closure over the Finding threshold.
- **3-4:** 5-8 per 1,000 LOC, or a god class/closure over Severe.
- **1-2:** > 8 per 1,000 LOC; smells are the norm.

## N/A

Mark a dimension `N/A — <reason>` only when there is nothing in scope to evaluate, for example Coupling for a single-file script with no imports of local modules, or every dimension for a target with no source code (configuration or data only). N/A is excluded from the average. A dimension with code that simply has no problems is not N/A; it scores 9-10.

## Citing absences

A missing thing is evidence too: cite where it should be. Examples: `CONTRIBUTING.md (none)` for an absent convention guide, `index.js:24-842 (no tests in repo: tests/ (none))`.

## Overall score

- Mean of the scored (non-N/A) dimensions, one decimal. State which dimensions were averaged.
- If any CRITICAL finding exists, cap the overall at 4.0 and say so.
- Status bands: a score at or above `statusThresholds.healthy[0]` is Healthy, at or above `statusThresholds.needsAttention[0]` is Needs Attention, anything lower is Critical (defaults 8 / 5 when the resolver gives none). Only the lower bounds count, so a fractional score such as 7.5 is Needs Attention, never a gap; review-full uses the same rule.
