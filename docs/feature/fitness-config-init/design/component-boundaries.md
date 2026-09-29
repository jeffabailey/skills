# Component Boundaries: fitness-config-init

## 1. Components

| Component | Location | Kind | Owns | Must not |
|---|---|---|---|---|
| **Init skill workflow** | `skills/fitness-config-init/SKILL.md` (new) | Driving adapter (agent-executed) | Target and anchor resolution, mode selection, evidence scan, classification, weight judgment, rationale, user prompts, relaying resolver output | Contain weight numbers; read, parse, or write `fitness-config.json` directly; run project code; write any file |
| **Purpose signals** | `skills/fitness-config-init/references/purpose-signals.md` (new) | Knowledge | Evidence-to-archetype signals, confidence rubric, read budget | Contain weights |
| **Purpose profiles** | `skills/fitness-config-init/references/purpose-profiles.md` (new) | Knowledge (parseable table) | Six archetype weight rows (floor 1, sum 100) | Contain baseline/default weights |
| **Resolver CLI** | `scripts/fitness-config.py` (entry point) and the `scripts/fitness_config/` package (logic; split per ADR-012) | Deterministic core plus filesystem adapter | Baseline, strict validation, completeness, canonical rendering, diff, fingerprint, gated atomic write, verification, chain display | Make judgment calls; prompt the user |
| **Example config** | `fitness-config.example.json` (unchanged) | Documentation mirror | Human-readable defaults; degraded-mode baseline | Diverge from `DEFAULT_*` (parity test) |
| **review-full** | `skills/review-full/` (unchanged) | External skill | Domain scores, skips, findings; writes `docs/fitness-report.md` | Be modified by this feature |

## 2. Resolver Internals (additions, ADR-006 grouping)

| Group | Addition | Pure? |
|---|---|---|
| Defaults | `KNOWN_DOMAINS` derived from `DEFAULT_WEIGHTS` keys (no new literal list) | yes |
| Validator | extended `validate_config` (ADR-008); new completeness rules for complete configs | yes (printing moves to the CLI edge; crafter's call) |
| Reporter | canonical renderer; value diff; fingerprint | yes |
| Seed | anchor guard: never walk above the anchor; target == anchor gives an empty chain (fixes `cmd_init_path` too) | yes |
| I/O boundary | stdin reader; atomic writer with verify and rollback (single impure adapter, substitutable in tests) | no |
| CLI | `init --path` flags `--dry-run`, `--from`, `--expect`, `--force`; `audit` glob adds `fitness-config-init/SKILL.md` | edge |

Dependency rule: CLI → (pure groups, I/O adapter); pure groups never call the I/O adapter. Since ADR-012 each group is a module in `scripts/fitness_config/` (`model`, `resolution`, `validation`, `render`, `write_gate`, `adapters`, `audit`, `cli`).

## 3. Requirement Traceability

| Req | Component(s) | Decision |
|---|---|---|
| FR-1, FR-2, FR-3, NFR-2, NFR-5 | Skill workflow + purpose signals | architecture-design section 3 (DQ-7) |
| FR-4, BR-1, BR-5 | Resolver (validator + completeness) and the profile fitness test | ADR-008 |
| FR-5, BR-2, BR-3 | Skill workflow + profiles; baseline from resolver | ADR-007, ADR-009, ADR-011 |
| FR-6, FR-7, BR-4, NFR-1 | Resolver write gate + skill confirm prompt | ADR-010 |
| FR-8 | Resolver `show --path` output relayed verbatim | ADR-009 (anchor) |
| FR-9 | Skill workflow → review-full (scoped explicitly, probed) | ADR-007 (applicability) |
| FR-10, BR-6 | Skill workflow (judgment) + resolver completeness (contiguity), R3 | ADR-008 |
| NFR-3 | Resolver canonical renderer + parity test | ADR-010 |
| NFR-4 | Skill resource location convention + step-0 probe | architecture-design section 6 |

## 4. Release Slicing (maps to DISCUSS releases)

| Release | Skill | Resolver |
|---|---|---|
| Walking skeleton (US-01..03) | Steps 0-5, 7-8. Existing file means print the proposal and stop. | Validator extension, completeness (no contiguity), canonical render, fingerprint, `--dry-run` (both forms), `--from --expect` create-only, anchor guard, audit glob |
| R1 (US-04) | Step 6 confirm | Diff lines, `unchanged`, `--force` replace, rollback |
| R2 (US-05) | Full mode | none |
| R3 (US-06) | Threshold judgment | Contiguity rule |
