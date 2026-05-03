# Acceptance Test Self-Review — fitness-config-per-directory

**Wave**: DISTILL
**Date**: 2026-04-25
**Reviewer**: Quinn (acceptance-designer self-review)
**Iteration**: 1
**Critique skill**: nw-ad-critique-dimensions (9 dimensions)

The total scenario count is 44 (> 3), so the full peer-review pass applies
(not the fast-path).

---

## Dimension-by-dimension findings

```yaml
review_id: "accept_rev_2026-04-25_self"
reviewer: "quinn-self-review"
artifact: "tests/acceptance/fitness-config-per-directory/*.feature + steps/*.py"
iteration: 1
total_scenarios: 44
active_scenarios: 1
skipped_scenarios: 43

strengths:
  - "44 scenarios trace cleanly to 39 ACs and 8 user stories — every story has at least one scenario; every AC except AC-08.1 (docs review) and AC-NFR-5 (CI matrix) traces to a scenario"
  - "Error path ratio 43% (19/44) exceeds the 40% mandate (Dim 1)"
  - "All Gherkin steps speak Devin's domain language (override, source chain, effective weights, schema version) — zero database/HTTP/REST/JSON-payload terminology in the .feature files"
  - "Walking skeleton is user-goal-framed (Dim 5): Devin previews weights for his Postgres module, sees override applied, sees total 100 OK"
  - "Strategy C (real-services) declared in walking-skeleton.md; every adapter (filesystem + CLI subprocess) has @real-io coverage (Dim 9)"
  - "All step methods invoke the CLI subprocess via repo.run(...) — zero imports of resolver internals (Mandate 1)"
  - "tmp_path-isolated repo trees give every scenario a clean real filesystem; no fixture parametrization needed (Mandate 4)"
```

### Dimension 1 — Happy path bias

```yaml
happy_path_bias:
  finding: "Pass — 19/44 scenarios are error/boundary/failure paths (43%)"
  severity: "low"
```

Error scenarios cover: invalid merged sums (sum < 100), schema version mismatches (newer + older), malformed JSON in override, malformed JSON in root, missing target path, depth-guard violation, init overwrite refusal, init permission denied, validate failure prevents review, fail-closed enforcement.

### Dimension 2 — GWT format compliance

```yaml
gwt_format:
  finding: "Pass"
  severity: "low"
```

Every scenario has Given (state), When (single CLI invocation), Then (observable outcome). No "Given... and... when... and..." conjunctions inside a single step. The ONE scenario with two When-style invocations ("Devin previews ... twice") is intentional — the determinism property requires two observations of the same action.

### Dimension 3 — Business language purity

```yaml
business_language:
  finding: "Pass with two domain-language exceptions"
  severity: "low"
  notes:
    - "Term 'JSON' appears in 1 scenario name — 'Show output embeds a parseable JSON block'. Justified: the skill-prompt CONSUMER contract IS the JSON block (data-models.md §3.1). Removing 'JSON' would obscure what the consumer is parsing."
    - "Phrase 'exits with success' / 'exits with a non-zero status' is CLI domain vocabulary the user observes directly when running the command — not a leak from internals."
```

The grep audit:

```
grep -rn -E "(database|REST|HTTP/[0-9]|controller|service\.|endpoint|api\.|status code)" tests/acceptance/fitness-config-per-directory/*.feature
```

returns zero matches.

### Dimension 4 — Coverage completeness

```yaml
coverage_gaps:
  finding: "All 8 stories covered; 37/39 AC traceable to scenarios"
  severity: "low"
  out_of_scope:
    - "AC-08.1 (every review-* SKILL.md documents resolver call) — documentation review, not behavioral. DELIVER inner-loop concern."
    - "AC-NFR-5 (cross-platform Win/Mac/Linux) — CI matrix concern. Same scenario on three OSes; no new scenario needed."
```

### Dimension 5 — Walking skeleton user-centricity

```yaml
walking_skeleton_centricity:
  finding: "Pass"
  severity: "low"
```

Title: "Devin previews module-specific weights for a Postgres review target." Title describes user goal. Then steps assert on Devin's observations: override applied, weights at specific values, total 100, files named in precedence order. No internal-state assertions ("Then DB row inserted", "Then `_read_config` called"). A non-technical stakeholder reads the scenario and confirms "yes, that is what users need."

### Dimension 6 — Priority validation

```yaml
priority_validation:
  q1_largest_bottleneck:
    evidence: "BR-5/FR-7 (resolver as single source of truth) is the largest correctness risk; integration-checkpoints scenario 'No skill bypasses the resolver' targets exactly that gate"
    assessment: "YES"
  q2_simple_alternatives:
    assessment: "ADEQUATE — could use scenario outlines for boundary tables, but explicit scenarios per case provide clearer failure messages and align with one-at-a-time DELIVER unskip"
  q3_constraint_prioritization:
    assessment: "CORRECT — happy paths first (milestone-1..3), backward-compat second (milestone-5), errors last (milestone-4); matches risk profile"
  q4_data_justified:
    assessment: "JUSTIFIED — error path ratio 43% exceeds the 40% threshold in critique-dimensions Dim 1"
```

### Dimension 7 — Observable behavior assertions

```yaml
observable_behavior:
  finding: "Pass"
  severity: "low"
```

Every Then step asserts one of:

- A return value from the driving port (`result.exit_code`, `result.stdout`, `result.stderr` — these are CLI subprocess return values).
- An observable outcome on disk written by the CLI (`repo.exists(<created file>)`, `repo.read_json(<created file>)` — the filesystem state IS the user-observable side effect for `init`).
- The PARSED CONTENT of a CLI stdout block (effective weights, source chain) — these are observable outcomes, not internal state.

No step asserts on private fields, method-call counts, or mock interactions. Mocks are not used.

The two filesystem-existence assertions in Dim 7's "concrete violations to flag" list (`assert os.path.exists("output.json")`) DO appear in the init-helper scenarios (`a new fitness-config.json appears at <path>`). For init, the file's creation IS the user-observable outcome — the user RAN init expressly to get that file on disk. This is the same pattern as asserting "an email is in Devin's inbox" after a "send email" command. The dimension's violation list applies to assertions made INSTEAD OF asserting on the user-visible outcome; here the file IS the user-visible outcome.

### Dimension 8 — Traceability coverage

```yaml
traceability_coverage:
  check_a:
    finding: "Pass — every story (US-01..US-08) has at least one scenario tagged @US-XX"
    severity: "low"
  check_b:
    finding: "Pass with caveat"
    severity: "low"
    note: "DEVOPS wave was skipped; environments.yaml does not exist. Per Dim 8 Check B fallback, defaults are clean / with-pre-commit / with-stale-config. The walking skeleton uses Strategy C (tmp_path = clean environment). The other two defaults (with-pre-commit, with-stale-config) are NOT MEANINGFUL for a config-resolver feature: pre-commit hooks and stale skill installs do not interact with fitness-config.json resolution. We declare those environments N/A for this feature with explicit justification."
```

The orchestrator config explicitly skipped DEVOPS for this feature (pure tooling, no infrastructure surface). Dim 8 Check B is satisfied by the single relevant environment (clean / tmp_path).

### Dimension 9 — Walking skeleton boundary proof

```yaml
walking_skeleton_boundary:
  9a_strategy_declared:
    status: "Pass — Strategy C declared in walking-skeleton.md and distill/wave-decisions.md"
  9b_strategy_match:
    status: "Pass — walking skeleton uses real subprocess + real filesystem; no @in-memory tags appear anywhere"
  9c_adapter_coverage:
    status: "Pass — the only adapter (_read_config) has @real-io coverage in walking-skeleton + every milestone-1 walk-up scenario + every error scenario; the CLI subprocess driving port has @real-io coverage in every test"
  9d_fixture_tier:
    status: "Pass — litmus test 'if I deleted _read_config would the WS still pass?' is NO; the WS reads real files via the real reader, so deleting it makes the test fail"
  9e_strategy_drift:
    status: "Pass — grep for @in-memory in walking-skeleton.feature returns zero matches"
```

---

## Issues identified

None at blocker or high severity.

Two low-severity notes for DELIVER:

1. **AC-03.1** (Header section appears within first 10 lines of every report) is a CONSUMER-side guarantee — it depends on each `review-*/SKILL.md` correctly embedding the resolver output. Acceptance tests cover the resolver's CLI output contract (which the consumer must obey) but cannot assert on the consumer's actual report files without also implementing the consumer changes. DELIVER's integration test pass against real review-* commands closes this loop.

2. **AC-NFR-1 perf budget** (avg < 100 ms) uses real subprocess invocation, which adds ~50-150 ms of Python startup overhead alone on slower hardware. The integration scenario asserts wall-clock under 100 ms; this may be tight on CI runners. If the scenario flakes in DELIVER, the budget can be relaxed to "resolver-internal time" by exporting an env var that tells fitness-config.py to print a self-timing line, and the test asserts on that line instead of wall-clock.

---

## Approval

```yaml
approval_status: "approved"
critical_issues_count: 0
high_issues_count: 0
low_issues_count: 2
ready_for_handoff_to: "DELIVER (nw-software-crafter)"
```

Iteration 2 not needed.
