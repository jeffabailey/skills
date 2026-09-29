# Requirements: fitness-config-init

## Context

Today a maintainer adopts fitness reviews in one of two ways. They copy `fitness-config.example.json`, or they run `fitness-config.py init`, which writes the built-in defaults. Either way they end up with generic weights: for example, accessibility gets 8 on a UI-less Postgres service and data gets 10 on a static blog. `review-full` then computes an overall score that over-weights domains that don't matter and under-weights the ones that do. Tuning ten numbers so they sum to 100, and remembering why, is tedious. In practice nobody does it.

**Job statement (inferred; JTBD phase skipped)**: *When I start using fitness reviews on a project, I want weights that reflect what this project is for, so the overall score tells me something true about its health.* Proposed `job_id: J-FCI-01`.

## Scope

In scope:

- A new skill `skills/fitness-config-init/SKILL.md` with the Agent Skills frontmatter `name` and `description` plus trigger phrases, and a `## Workflow` section. No scoring dimensions are needed because this is a utility skill.
- Two evidence modes: fast scan and full review.
- A config proposal with rationale.
- A validated write to `<folder>/fitness-config.json`.
- A diff and confirmation when a config already exists.

Out of scope:

- Changes to `scripts/fitness-config.py`. DESIGN may propose small additions under DQ-6.
- Changes to the schema.
- Generating per-directory overrides for subfolders.
- Editing any other project file.

## Functional Requirements

| ID | Requirement | Story |
|---|---|---|
| FR-1 | The first output line names the folder being configured. The user chooses the evidence mode, and the default is the fast scan. The mode can also be passed as an argument (`fast`, `full`). | US-01, US-05 |
| FR-2 | The fast scan reads only purpose signals: README, package/build manifests, the top-level directory layout, and deploy/CI config. It reports each piece of evidence with its path. | US-01 |
| FR-3 | The skill classifies the purpose (for example database-backed service, public web frontend, CLI tool, data pipeline, library, mixed, or unknown) with a confidence of high, medium, or low. | US-01 |
| FR-4 | The proposal contains all 10 weights, and they sum to exactly 100. It must pass both `fitness-config.schema.json` and `fitness-config.py validate`. | US-02, US-03 |
| FR-5 | Every value that differs from the baseline gets one short reason that cites evidence. Unchanged values are labeled unchanged. | US-02 |
| FR-6 | If no config exists, the skill writes the file only after validation passes. If validation fails, it writes nothing and shows the errors. | US-03 |
| FR-7 | If a config exists, the skill shows a per-value diff (current vs proposed) and overwrites only on an explicit `y`/`yes`. If the proposal is identical to the current file, it writes nothing. | US-03, US-04 |
| FR-8 | After writing, the skill shows the resolver chain for the folder (`fitness-config.py show --path`). If the folder is under an ancestor config, it says the new file is an override. | US-03 |
| FR-9 | Full mode runs `review-full` on the folder. Before running, it discloses that `docs/fitness-report.md` will be written. Findings feed the classification and the rationale. | US-05 |
| FR-10 | Optionally, the skill tunes `statusThresholds`, `security.confidenceThreshold`, and `scoring` to the purpose, and gives a reason for each change. | US-06 |

## Non-Functional Requirements

| ID | Requirement | Measure |
|---|---|---|
| NFR-1 Safety | In fast mode, no file other than `<folder>/fitness-config.json` is created or modified. | File-tree snapshot before and after shows exactly one changed path, or none. |
| NFR-2 Non-invasive scan | The fast scan executes no project code, installs nothing, and makes no network calls. It reads at most 40 files. | Transcript review in functional tests |
| NFR-3 Clean diffs | Written JSON uses 2-space indentation and the top-level and weight key order of `fitness-config.example.json`. It ends with a trailing newline. | Byte comparison of the key order |
| NFR-4 Portability | The skill locates the resolver with `${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py`, following the review-full convention. It adds no runtime dependencies beyond the Python 3 stdlib. | Works when installed as an Agent Skill and as a Claude Code plugin |
| NFR-5 Speed | The fast scan produces a proposal in under 2 minutes wall time on a repo with 10k files. | Timed functional test on `ledgerd`-sized fixture |

## Business Rules

- **BR-1**: Weights cover exactly the 10 schema domains, each between 0 and 100 inclusive, and sum to 100. Integers are preferred.
- **BR-2**: A changed value with no evidence-backed reason is a defect. The skill must not invent evidence.
- **BR-3**: When purpose is `unknown` or confidence is `low`, the skill proposes baseline values and says why. It does not guess.
- **BR-4**: Overwrite requires an explicit yes. Anything else, including silence, means no.
- **BR-5**: Nothing is written unless both the schema gate and the resolver gate pass.
- **BR-6**: `statusThresholds` ranges stay contiguous and non-overlapping over 1-10 (US-06).

## Glossary

- **Baseline**: the default config that "non-default" is measured against. See DQ-3.
- **Purpose**: what the project is for, as inferred from evidence.
- **Evidence mode**: `fast` (purpose scan) or `full` (fast scan plus review-full).
- **Override**: a `fitness-config.json` below an ancestor config (ADR-001/002).
- **Rationale**: a one-line reason for a non-default value that cites evidence.

## Open Questions for DESIGN

| ID | Question | Luna's lean |
|---|---|---|
| DQ-1 | Where does rationale live? JSON has no comments. Options: (a) printed summary only; (b) sidecar `fitness-config.rationale.md`; (c) a `$comment` key. The root schema permits extra keys and the resolver ignores them, but the deep-merge drops them and they diverge from the example. | (a) always, plus optional (b). Avoid (c). |
| DQ-2 | How do review-full scores influence weights? Should scores signal applicability (a domain is absent or skipped, so its weight goes down) or weakness (a low score raises the weight)? Weights mean importance, not current health. | Applicability only. Show scores, but don't boost weights based on weakness. |
| DQ-3 | Which baseline counts as "default": `fitness-config.example.json`, `DEFAULT_*` in `scripts/fitness-config.py`, or, in a subfolder, the ancestor's effective config (as `init --path` does)? | Root folder uses the resolver defaults (single source). Subfolder uses the ancestor's effective config. |
| DQ-4 | Should purpose-to-weights mapping use fixed profiles in `references/purpose-profiles.md`, or agent judgment within guardrails? Should a domain with no surface (accessibility with no UI) get 0 or a small floor? review-full already skips it and redistributes its weight. | Reference profiles as starting points plus judgment, with a floor of 1 for any domain the resolver still scores. |
| DQ-5 | How are mixed purposes handled, such as a monorepo with a web app, an API, and a database? Blend the profiles, or ask the user for the primary purpose? | Ask for the primary purpose when confidence is not high. Mention per-directory overrides without creating them. |
| DQ-6 | How is the proposal validated before writing? The schema needs `jsonschema`, which is not in the stdlib (D-10). The resolver `validate` does not check weight key names, the 0-100 bounds, or unknown weight keys. Options: extend `validate_config`, or validate a temp file in scratch. What is the fallback when `python3` is unavailable? | Extend `validate_config` to cover the schema constraints so one stdlib gate suffices. With no python3, refuse to write and print the proposal. |
| DQ-7 | Should the skill auto-detect the mode from the invocation text ("full review first")? | Yes, if unambiguous. Otherwise prompt. |
| DQ-8 | `docs/product/jobs.yaml` does not exist, so `job_id` J-FCI-01 cannot be resolved. Create the registry or accept the inferred ID? | Accept the inferred ID for now. Create the registry when a second feature needs it. |

## Risks

| Risk | P | I | Mitigation |
|---|---|---|---|
| Misclassification yields confident but wrong weights | M | M | Evidence is listed, the user can correct the purpose, and BR-3 applies |
| Full mode is slow and writes an extra file | H | L | Opt-in, with disclosure (FR-9) |
| Baseline drift between the example and `DEFAULT_*` | L | M | DQ-3: single source |
| Skill-list housekeeping missed (8 locations per CONTRIBUTING.md) | M | L | DoD item for DELIVER |
