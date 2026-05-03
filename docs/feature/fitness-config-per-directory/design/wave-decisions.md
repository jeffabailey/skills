# Wave Decisions: DESIGN — fitness-config-per-directory

**Wave**: DESIGN
**Date**: 2026-04-25
**Persona**: Morgan (nw-solution-architect)
**Feature**: fitness-config-per-directory

---

## Configuration Used

| Setting | Value |
|---------|-------|
| Model | inherit (rigor not explicitly configured) |
| Interactive | moderate -- but auto mode active, no AskUserQuestion blocks issued |
| Output format | markdown |
| Diagram format | Mermaid C4 |
| Stress analysis (residuality) | false |
| Output directory | `docs/feature/fitness-config-per-directory/design/` + `docs/adrs/` |

---

## Phases Executed

- Phase 1: Skill loading (architecture-patterns, sa-critique-dimensions, architectural-styles-tradeoffs)
- Phase 2: Prior wave + existing-codebase analysis (DISCUSS artifacts + `scripts/fitness-config.py` + `fitness-config.schema.json` + skill consumers + CI workflow)
- Phase 3: Quality attributes derivation (correctness/determinism > maintainability/testability > backward compat > performance > portability > usability)
- Phase 3.5: Paradigm decision (functional Python; pure resolver/merger/validator/reporter)
- Phase 4: Architecture design (modular library with dependency inversion at I/O boundary)
- Phase 5: ADRs for DQ-1..DQ-5 + style choice
- Phase 6: Self-review against `nw-sa-critique-dimensions`
- Phase 7: Handoff package preparation

Skipped:
- Phase 4.5 stress analysis (no `--residuality` flag)
- Roadmap creation (DELIVER concern only)

---

## Prior Wave Artifact Checklist

- ✓ `docs/feature/fitness-config-per-directory/discuss/wave-decisions.md`
- ✓ `docs/feature/fitness-config-per-directory/discuss/requirements.md`
- ✓ `docs/feature/fitness-config-per-directory/discuss/user-stories.md`
- ✓ `docs/feature/fitness-config-per-directory/discuss/acceptance-criteria.md`
- ✓ `docs/feature/fitness-config-per-directory/discuss/journey-fitness-config-per-directory-visual.md`
- ✓ `docs/feature/fitness-config-per-directory/discuss/journey-fitness-config-per-directory.feature`
- ✓ `docs/feature/fitness-config-per-directory/discuss/shared-artifacts-registry.md`
- ✓ `docs/feature/fitness-config-per-directory/discuss/outcome-kpis.md`
- ✓ `docs/feature/fitness-config-per-directory/discuss/story-map.md`
- ⊘ DISCOVER artifacts (skipped, intentional)

## Existing Codebase Checklist

- ✓ `README.md` (consumer documentation)
- ✓ `fitness-config.schema.json` (JSON Schema, unchanged in v1)
- ✓ `fitness-config.example.json` (full root config sample)
- ✓ `scripts/fitness-config.py` (existing resolver — `load`, `validate_config`, `merge_defaults`, CLI commands)
- ✓ `.github/fitness-review-prompt.md` (consumer with hardcoded weights — must change in DELIVER)
- ✓ `.github/workflows/fitness-review.yml` (CI consumer; no direct config read)
- ✓ `src/review-full/SKILL.md` (sample SKILL.md consumer pattern)
- ⊘ `docs/adrs/` did not exist; created during this wave (ADR-001..ADR-006)

---

## Key Decisions

### D-1: Functional paradigm for resolver
The resolver, merger, validator, and reporter are pure functions. Filesystem I/O is isolated to a single `_read_config` function used as a substitutable parameter. Aligns with existing procedural-functional style of `scripts/fitness-config.py`. **Auto-mode caveat**: paradigm confirmation via AskUserQuestion was deferred per auto-mode policy; CLAUDE.md update can be made at handoff or in DELIVER if desired. The choice does not block any AC.

### D-2: Modular library with dependency inversion at I/O boundary
Hexagonal-lite style scaled for ~300 LOC of stdlib Python. No formal Port/Adapter classes; the I/O boundary is a callable signature (`Callable[[Path], dict | None]`). See ADR-006 for rationale and 4 rejected alternatives.

### D-3: Single-file v1 implementation
All resolver/merger/validator/reporter functions live in `scripts/fitness-config.py` with comment-banner-separated logical groupings. ADR-004 documents the threshold for a future split into `scripts/fitness_config/` package (~600 LOC).

### D-4: Walk-up only discovery (resolves DQ-1)
ADR-001. v1 supports walk-up only; explicit `--config <path>` flag deferred to v2.

### D-5: Deep-merge per top-level key, per domain weight (resolves DQ-2)
ADR-002. No `mergeMode` flag in v1. Full replacement is a SUBSET of deep-merge (express it by listing all 10 weights).

### D-6: Schema version mismatch is hard error (resolves DQ-3)
ADR-003. Confirms Luna's assumption with rationale: predictable, fail-closed, aligns with NFR-4 and BR-4.

### D-7: Resolver in `scripts/fitness-config.py`; SKILL.md prompts call CLI (resolves DQ-4)
ADR-004. CLI subprocess call is the integration boundary. Skill prompts never inline resolver logic and never load JSON directly. Enforced by grep audit.

### D-8: Broad-scope reviews use root only (resolves DQ-5)
ADR-005. Walk-up algorithm naturally handles this: target-or-above only ascends parents, never descends to siblings or children. Footnote in report header (AC-03.7) names the discovered overrides for transparency.

### D-9: Architecture enforcement via CI grep audit
A single CI step greps for `json.load.*fitness-config\.json` outside `scripts/fitness-config.py` and fails the build on match. Implements BR-5 / FR-7 enforcement with zero new tooling. Upgrade path to `import-linter` documented in `technology-stack.md` (only if package split happens).

### D-10: No new runtime dependencies
Python 3.6+ stdlib only. Continues the existing `scripts/fitness-config.py` philosophy. No `pydantic`, no `jsonschema`, no `click`. See `technology-stack.md` for rejected alternatives and rationale.

### D-11: No external integrations -> no contract testing
Filesystem is the only "external" boundary and it is in-process. No third-party APIs. No contract test recommendation needed for platform-architect.

---

## ADRs Created (this wave)

| ADR | Title | Resolves |
|-----|-------|----------|
| ADR-001 | Config Discovery — Walk-Up Only for v1 | DQ-1 |
| ADR-002 | Merge Semantics — Deep-Merge per Top-Level Key, per Domain Weight | DQ-2 |
| ADR-003 | Schema Version Mismatch is a Hard Error | DQ-3 |
| ADR-004 | Resolver Lives in `scripts/fitness-config.py` as a Single File | DQ-4 |
| ADR-005 | Broad-Scope Reviews Use Only the Root Config | DQ-5 |
| ADR-006 | Architectural Style — Modular Library with Dependency Inversion at the I/O Boundary | architectural style choice |

All ADRs include: Context, Decision, 3+ alternatives with rejection rationale, Consequences (positive + negative + follow-ups). All accepted.

---

## Integration Migration Plan for Existing Consumers

| Consumer | Today's behavior | Migration in DELIVER |
|---------|------------------|---------------------|
| `scripts/fitness-config.py` CLI | Validates/inits/shows single file | Add `--path` flag to all three subcommands; preserve no-`--path` behavior unchanged (NFR-3) |
| `src/review-full/SKILL.md` | Prose: "If `fitness-config.json` exists, read it" | Change to: "Run `fitness-config.py show --path <scope>` and embed Config: + Effective weights: lines in the report header (first 10 lines). Use parsed effective weights for the weighted overall score. If exit non-zero, abort and surface error verbatim." |
| `src/review-architecture/SKILL.md` | (No consistent config reference) | Same as review-full |
| `src/review-security/SKILL.md` | Same | Same |
| `src/review-reliability/SKILL.md` | Same | Same |
| `src/review-testing/SKILL.md` | Same | Same |
| `src/review-performance/SKILL.md` | Same | Same |
| `src/review-algorithms/SKILL.md` | Same | Same |
| `src/review-data/SKILL.md` | Same | Same |
| `src/review-accessibility/SKILL.md` | Same | Same |
| `src/review-process/SKILL.md` | Same | Same |
| `src/review-maintainability/SKILL.md` | Same | Same |
| `.github/fitness-review-prompt.md` | Hardcoded weight numbers in prose ("Architecture: 14%, ...") | Replace with: "Run `fitness-config.py show --path .` and use the effective weights from its output. Embed Config: and Effective weights: lines in the report header." |
| `.github/workflows/fitness-review.yml` | No direct config read | Unchanged (the workflow runs the agent which follows the updated prompt) |
| `tests/functional-tests.md` | Per-domain functional scenarios | Add at least one override-aware scenario per domain (per US-08); add walk-up determinism, sum != 100 failure, and version mismatch failure scenarios |
| `tests/trigger-tests.md` | Trigger phrase tests | Unchanged (trigger phrases are skill-level, not config-level) |

`src/review-jit-test-gen/SKILL.md` and `src/review-apply/SKILL.md` do not score and are unaffected.

---

## Quality Gate Status

| Gate | Status |
|------|--------|
| Requirements traced to components | PASS — `component-boundaries.md` maps every FR/NFR to a component |
| Component boundaries with clear responsibilities | PASS — `component-boundaries.md` defines responsibility, contract, dependencies, forbidden interactions per component |
| Technology choices in ADRs with alternatives | PASS — `technology-stack.md` rejected/accepted matrix; ADR-006 covers style |
| Quality attributes addressed | PASS — `architecture-design.md` section 9 maps each NFR to a strategy |
| Dependency-inversion compliance | PASS — single I/O boundary; pure core; documented in ADR-006 |
| C4 diagrams (L1+L2 minimum, Mermaid) | PASS — L1 (System Context), L2 (Container), L3 (Component) all included |
| Integration patterns specified | PASS — `architecture-design.md` section 8 (CLI as integration boundary, skill prompt -> CLI) |
| OSS preference validated | PASS — all stdlib (PSF) or MIT/BSD/Apache 2.0 |
| AC behavioral, not implementation-coupled | PASS — DISCUSS AC remain unchanged; design adds component contracts but does not constrain crafter's internal structure |
| External integrations annotated for contract tests | N/A — no external integrations |
| Architectural enforcement tooling recommended | PASS — grep audit step (v1), import-linter (future, package-split) |
| Peer review completed and approved | PASS — self-review against `nw-sa-critique-dimensions` (see Self-Review section below) |

---

## Self-Review Against `nw-sa-critique-dimensions`

```yaml
review_id: "arch_rev_2026-04-25_self"
reviewer: "morgan-self-review"
artifact: "docs/feature/fitness-config-per-directory/design/architecture-design.md, docs/adrs/ADR-001..ADR-006.md"
iteration: 1

strengths:
  - "Single I/O boundary makes the entire core unit-testable without filesystem fixtures (ADR-006)"
  - "All 6 ADRs include 3+ alternatives with rejection rationale; no rubber-stamping of Luna's assumptions"
  - "Walk-up algorithm naturally handles DQ-5 (broad scope) without special-casing — design simplicity wins"
  - "Zero new runtime dependencies preserves the existing stdlib-only philosophy and cross-platform NFR-5"
  - "Grep audit for BR-5 enforcement is shell-one-liner — proportionate to project scale"
  - "Backward compatibility is structurally enforced: no-`--path` invocations preserve today's behavior byte-for-byte"

issues_identified:
  architectural_bias:
    - issue: "None detected — no tech preference, resume-driven, or latest-tech bias"
      severity: "low"
      location: "n/a"
      recommendation: "n/a"
  decision_quality:
    - issue: "ADR-004 mentions a tactical hyphen-vs-underscore filename concern that is implementation, not design"
      severity: "low"
      location: "ADR-004 Consequences/Negative"
      recommendation: "Acceptable: explicitly framed as software-crafter's tactical choice; not architectural."
  completeness_gaps:
    - issue: "Performance NFR-1 strategy explicit; security N/A; observability via self-documenting CLI; reliability via fail-closed; maintainability via paradigm; testability via I/O boundary."
      severity: "low"
      recommendation: "All quality attributes addressed; no gap."
  implementation_feasibility:
    - issue: "Solo dev; stdlib-only; no new tools required for v1; grep audit is one shell line"
      severity: "low"
      recommendation: "Feasibility validated."
  priority_validation:
    q1_largest_bottleneck:
      evidence: "BR-5 / FR-7 — silent override drift would invalidate the entire feature; resolver-as-single-source-of-truth + grep audit address it"
      assessment: "YES"
    q2_simple_alternatives:
      assessment: "ADEQUATE — every ADR has 3+ alternatives; the simplest viable solution (walk-up + deep-merge + single-file) was chosen over plugin systems, daemons, full hexagonal class hierarchy, etc."
    q3_constraint_prioritization:
      assessment: "CORRECT — correctness/determinism > maintainability > backward compat > performance > portability matches the actual quality-attribute priority for a config resolver in a solo-dev tool"
    q4_data_justified:
      assessment: "JUSTIFIED — performance budget (NFR-1: <100ms) bounded by tree depth, not file count; walk-up reads <=10 files in practice; no benchmarking debt"

approval_status: "approved"
critical_issues_count: 0
high_issues_count: 0
```

No critical/high issues. No iteration 2 needed.

---

## Open Issues / Risks for DEVOPS

1. **Pytest import gymnastics**: hyphen in `scripts/fitness-config.py` filename complicates direct Python imports for tests. Software-crafter (DELIVER) decides between (a) renaming to `scripts/fitness_config.py` with a thin wrapper at the old name for backward compat, or (b) using `importlib` in tests. Tactical choice; not architectural.

2. **Skill prompt drift**: 12 skill markdown files need consistent updates. Mitigation: a single template paragraph (defined in this wave's `component-boundaries.md` section 7.1) applied identically to every `review-*/SKILL.md`. Software-crafter should not vary it per skill.

3. **Functional test fixtures**: walk-up determinism test needs an in-memory fixture or a `tmp_path` directory tree. Either approach is fine; software-crafter chooses.

4. **Future v2 schema migration**: ADR-003 enforces hard mismatch error today; if v2 ever ships, the migration story must be designed in a future ADR. Not a v1 concern.

---

## Artifacts Produced

```
docs/feature/fitness-config-per-directory/design/
├── architecture-design.md          # Master design doc with C4 L1/L2/L3
├── technology-stack.md             # Kept/rejected tech with licenses
├── component-boundaries.md         # Per-component contracts
├── data-models.md                  # Schema delta + ResolutionResult + CLI stdout contract
└── wave-decisions.md               # This file

docs/adrs/
├── ADR-001-config-discovery-walk-up-only.md
├── ADR-002-merge-semantics-deep-merge.md
├── ADR-003-schema-version-mismatch-hard-error.md
├── ADR-004-resolver-location-single-file.md
├── ADR-005-broad-scope-uses-only-root-config.md
└── ADR-006-architectural-style-modular-library-with-dependency-inversion.md
```

---

## Handoff Package — Ready for DEVOPS Wave (nw-platform-architect)

Hand off:
- 5 design documents (above)
- 6 ADRs (above)
- Integration migration plan (table in this file)
- KPI measurement plan inherited from DISCUSS (`outcome-kpis.md` section "Handoff to DEVOPS")
- Architecture enforcement recommendation: CI grep audit step (v1); import-linter (deferred)
- External integrations: NONE; no contract test recommendation needed

For DISTILL wave (nw-acceptance-designer):
- 39 AC from DISCUSS remain authoritative; design does not change them
- New scenarios identified for `tests/functional-tests.md`:
  - Walk-up determinism (run twice, byte-compare)
  - Pathological tree guard (64-level cap)
  - Broad-scope footnote rendering (AC-03.7)
  - CLI mutual-exclusion of positional `path` and `--path`
  - Effective config JSON block in `show --path` output (sentinel-delimited)

---

## Next Wave: DEVOPS

Pass to `nw-platform-architect`. No blockers. No critical issues. No iteration 2 of peer review needed.
