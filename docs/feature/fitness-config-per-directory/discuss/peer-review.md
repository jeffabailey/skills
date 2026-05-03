# Peer Review: fitness-config-per-directory (DISCUSS artifacts)

```yaml
review_id: req_rev_20260425_self
reviewer: "product-owner (review mode, self-review against review-dimensions skill)"
artifact: "docs/feature/fitness-config-per-directory/discuss/*"
iteration: 1

strengths:
  - "Clear domain language throughout: 'effective config', 'source chain', 'walk-up' consistent across all artifacts"
  - "Real persona (Devin Park) with concrete repo structure (postgresql, networking, logging modules)"
  - "Every story has 3+ domain examples with real module names (no user123 / generic data)"
  - "Outcome KPIs trace from epic-level (KPI 1-4) through story-level mapping table to functional tests"
  - "Provenance/header pattern (US-03) directly addresses the riskiest UX failure: silent override fallback"
  - "Single source of truth (resolver) enforced as a business rule (BR-5), not just a technical hint"
  - "Open questions explicitly marked as DESIGN decisions, not requirements gaps — preserves solution-neutrality"

issues_identified:
  confirmation_bias:
    - issue: "Walk-up-only discovery rule was assumed without comparing alternatives (sibling glob, env var, explicit flag)"
      severity: "medium"
      location: "FR-1, BR-3"
      recommendation: "Documented as DQ-1 with Luna's assumption flagged for DESIGN. Acceptable since this is an availability bias the user is being asked to override in DESIGN if needed."

    - issue: "Deep-merge over full-replacement is the assumed merge mode without explicit user validation"
      severity: "medium"
      location: "FR-2"
      recommendation: "Documented as DQ-2. Acceptable for DISCUSS — DESIGN can choose otherwise without invalidating any AC, since the user-observable behavior (effective config sums to 100, header proves source) is what matters."

  completeness_gaps:
    - issue: "No NFR addressing what happens during concurrent invocations (two reviews running on different paths simultaneously)"
      severity: "low"
      location: "NFR section"
      recommendation: "Resolver is read-only and stateless per invocation; concurrency is implicit non-issue. Note added below — not promoting to a formal NFR."

    - issue: "No explicit story for migrating existing repos (single root config) to per-directory pattern"
      severity: "low"
      location: "Story map / out of scope"
      recommendation: "NFR-3 (backward compatibility) covers this — existing repos behave identically. No migration needed since this is purely additive."

    - issue: "Stakeholder analysis names CI/CD users but no Gherkin scenario covers a CI run with override"
      severity: "medium"
      location: "user-stories.md"
      recommendation: "Existing UAT scenarios are CI-runnable (they invoke `fitness-config.py validate --path` and `review-full`). CI is not a separate code path. Acceptable."

  clarity_issues:
    - issue: "AC-01.5 states '< 100ms in 10k-file repo' — what counts as 'levels deep' is ambiguous"
      severity: "low"
      location: "AC-01.5, NFR-1"
      recommendation: "NFR-1 specifies 'paths up to 10 levels deep'. Acceptable; benchmark fixture defines this concretely."

    - issue: "DQ-5 (broad scope crossing multiple overrides) is a known limitation but the user-facing message is not specified"
      severity: "medium"
      location: "Story map (Future / Out of Scope)"
      recommendation: "AC-03.7 covers the user-facing footnote on root-scoped reviews. Acceptable."

  testability_concerns:
    - issue: "KPI 3 'first-attempt success rate 90%' depends on telemetry that may not exist in this repo"
      severity: "medium"
      location: "outcome-kpis.md KPI 3"
      recommendation: "Measurement plan acknowledges 'where available' for CI telemetry. For this open-source skill repo, KPI 3 may rely on manual sampling of PR history rather than automated telemetry. Note explicitly."

    - issue: "AC-08.1 'documents calling the resolver in SKILL.md' is documentation-only, hard to enforce automatically"
      severity: "low"
      location: "AC-08.1"
      recommendation: "AC-08.4 covers the lint/grep gate which is automatable. AC-08.1 is supporting documentation; the executable check is AC-08.4."

  priority_validation:
    q1_largest_bottleneck: "YES"
    q2_simple_alternatives: "ADEQUATE"
    q3_constraint_prioritization: "CORRECT"
    q4_data_justified: "JUSTIFIED"
    verdict: "PASS"

approval_status: "approved"
critical_issues_count: 0
high_issues_count: 0
```

## Remediation Notes

The medium-severity items above are addressed in-place rather than blocking handoff:

1. **KPI 3 telemetry caveat** — added to outcome-kpis.md measurement plan: "where automated CI telemetry isn't available, sample manually from PR history."
2. **DQ-1 / DQ-2 assumptions** — explicitly flagged as DESIGN decisions in journey YAML, story map, and DoR checklist. DESIGN may revise without invalidating any AC.
3. **DQ-5 user-facing message** — covered by AC-03.7 footnote.

No critical or high-severity issues. No iteration 2 needed. Artifacts are ready for DESIGN handoff.
