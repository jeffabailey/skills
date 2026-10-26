# Architecture Scoring Rubric

Hand-maintained scoring rubric. sync-wisdom does not regenerate this file.

This file is the scoring source for review-architecture. `checklist.md` lists what to inspect; this file says what score and severity the results earn. Numeric thresholds match `checklist.md`; change both together.

## Severity

| Severity | Definition | Architecture examples |
|----------|------------|-----------------------|
| CRITICAL | The structure blocks safe change today: a change in one place routinely breaks or forces changes elsewhere, or the system cannot start/import cleanly. | An import-time cycle between core modules that fails on a fresh import order; domain logic that cannot run without a live database or web framework, so nothing in it can be tested. |
| HIGH | A boundary is violated in a way that will spread or bite on the next likely change. | A data-access module imports presentation/HTTP types (upward dependency); a public API returns errors in three different shapes so every caller special-cases them. |
| MEDIUM | A local design problem with a contained blast radius; worth fixing in normal work. | A module imports another module's underscore-private helpers; a 600-line class that mixes parsing and persistence. |
| LOW | Hygiene or consistency; no realistic breakage. | `fetch_`/`get_`/`load_` used for the same kind of read; a magic number with an obvious meaning. |

Severity is about consequence, confidence is about certainty. A finding can be HIGH with confidence 7 or LOW with confidence 10.

## Dimension anchors

Pick the band whose description fits best, then move within it by the number and severity of findings. When two bands fit, take the lower one and say why. Scores are integers.

### Coupling

Evidence: `scripts/import_graph.py` output (cycles, fan-in/out, hubs, external imports), plus reads of shared state and private-name imports.

- **9-10:** No cycles. No module imported by more than 70% of the others except stable leaf types (constants, data models with no imports). Cross-module calls go through public names. No shared mutable module-level state.
- **7-8:** No import-time cycles; at most one deferred (function-level or TYPE_CHECKING) cycle, documented or obviously intentional. One or two private-name imports across modules, or one shared mutable default.
- **5-6:** One import-time cycle, or a utility hub over 70% fan-in that mixes unrelated helpers, or private internals of one module used by several others, or concrete infrastructure clients created inside business functions so callers cannot swap them.
- **3-4:** Several cycles or a package-level cycle; modules communicate through mutable globals; changing one module's internals regularly forces edits in 3+ others.
- **1-2:** Effectively one tangle: most modules sit in one strongly connected component, or everything reaches into everything.

### Cohesion

- **9-10:** Each module/class can be described in one sentence without "and". Methods share the same fields. No `utils`/`helpers`/`common` grab-bags.
- **7-8:** One module has a second, related responsibility, or one small grab-bag file with fewer than ~5 unrelated functions.
- **5-6:** A module/class has 2-3 change reasons (for example SQL, formatting and business rules together), or the same concern (one query, one parse) is implemented in 2+ modules.
- **3-4:** God class or module over 500 lines / 20+ methods serving several consumers; a feature's logic is scattered so one change touches 10+ files (shotgun surgery).
- **1-2:** No discernible organizing principle; files are buckets of unrelated code.

### Layering

N/A when the target is a single-purpose library or script with no I/O boundary to separate (say so; don't invent layers).

- **9-10:** Presentation (CLI/HTTP/UI), domain logic, and infrastructure (DB, files, network, subprocess) are separable. Dependencies point inward. Domain code runs without the framework.
- **7-8:** Layers exist; one or two skip-layer calls (a CLI handler reading a file directly) with no upward dependencies.
- **5-6:** Infrastructure leaks into domain code in several places (domain functions open DB connections, call subprocess, read env vars), or runtime `sys.path`/global-patching hacks to reach another component.
- **3-4:** Upward dependencies (data access imports presentation types) or business rules living in handlers/controllers throughout.
- **1-2:** No layer separation at all in a system that needs it (a web app where every handler runs SQL and renders HTML).

### Modularity

- **9-10:** Each module/package has a deliberate public surface (`__init__`/`__all__`, `index.ts`, facade). Consumers import from it. Modules are testable with dependencies stubbed. Nesting is 4 levels or fewer.
- **7-8:** Public surface exists but is incomplete or loosely respected (a few deep imports into internals).
- **5-6:** No clear public surface; consumers routinely import internals; a module cannot be tested without starting most of the application.
- **3-4:** Removing or replacing a module would cascade through most of the codebase; boundaries are directory names only.
- **1-2:** No boundaries; any file imports any file.

### Naming

- **9-10:** Names say what things do and are true. One verb per concept (`get` vs `fetch` vs `load` used consistently), one casing style per element type, booleans read as questions, no lookup-needed abbreviations.
- **7-8:** One or two inconsistencies (two verbs for the same kind of read, one vague public name like `process_data`).
- **5-6:** Several public names are generic (`Manager`, `handle`, `data`) or two distinct types share one name in the same package, so readers must open the code to tell them apart.
- **3-4:** Names that lie (a `get_` that writes, a `validate_` that mutates) on public paths.
- **1-2:** Names are mostly unhelpful or misleading across the codebase.

### API Design

Covers public functions, classes, CLI interfaces and HTTP/RPC endpoints the target exposes. N/A only when the target exposes nothing to callers outside itself.

- **9-10:** Inputs, outputs and side effects are explicit (types, docstrings, schemas). One error contract per surface (one exception family, one error shape, one exit-code scheme). Units and enums are explicit. Writes state their idempotency where retries are plausible.
- **7-8:** Contracts are explicit; one surface deviates (one function returns `None` where siblings raise), and the deviation is documented.
- **5-6:** Error contracts differ between sibling entry points without documentation, or callers must read implementations to know what is returned or raised.
- **3-4:** Breaking changes made without versioning or deprecation; public signatures expose internal types (ORM rows, raw dicts with undocumented keys).
- **1-2:** No discernible contract; behavior can only be learned by running it.

### Maintainability

Read tests even when they sit outside the target (for example `tests/` at the repo root): the question is whether the target's critical paths are covered, not where the tests live.

- **9-10:** No files over 500 lines or functions over 50 lines without reason; nesting 4 levels or fewer; no unexplained magic numbers/strings; critical paths have behavior tests; non-obvious decisions have a "why" comment or ADR.
- **7-8:** One or two long functions or magic values; tests exist for main paths but miss an important branch.
- **5-6:** Several functions over 50 lines or nesting over 4 levels; duplicated logic in 2+ places; critical paths untested; stale docs or docstrings that contradict the code.
- **3-4:** God classes over 500 lines on hot paths, widespread duplication, no tests for core behavior.
- **1-2:** Changes cannot be made safely: no tests, pervasive duplication, dead and live code mixed.

## N/A and evidence of absence

Mark a dimension `N/A` when nothing in scope can be evaluated for it, and give the reason in the summary table (for example `N/A: single 80-line script, no layers to separate`). Never give a placeholder score: it skews the overall and the review-full aggregate. Do not mark N/A just because evidence is thin; score from what exists and lower confidence on findings instead.

To cite something missing, cite where it should be: `src/pkg/__init__.py (no __all__)`, `tests/ (no tests import scoring.py)`, `docs/adr/ (none)`.

## Overall score

- Overall = mean of the scored (non-N/A) dimensions, rounded to one decimal. State which dimensions were averaged.
- If any CRITICAL finding exists, cap the overall at 4.0 and say the cap applied.
- Status bands: a score at or above `statusThresholds.healthy[0]` is Healthy, at or above `statusThresholds.needsAttention[0]` is Needs Attention, anything lower is Critical (defaults 8 / 5 when the resolver gives none). Only the lower bounds count, so a fractional score such as 7.5 is Needs Attention, never a gap; review-full uses the same rule.
- Every dimension scored below 6 gets at least one action item.
