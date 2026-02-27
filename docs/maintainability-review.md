# Maintainability & Understandability Fitness Review

## Summary

Overall fitness score: 7.4 / 10 (average of dimensions)

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Structural Complexity | 8/10 | Functions are short and well-structured; fitness-review.yml at 1150 lines is the only oversized module |
| Understandability | 8/10 | Consistent naming, clear domain language, excellent "why" documentation in ADRs and skill rubrics |
| Technical Debt Indicators | 7/10 | Zero TODO/FIXME/HACK in project code; skill list duplicated 9+ times across docs with no automated sync |
| Coupling and Dependency Depth | 8/10 | Clean module boundaries; each skill is fully self-contained; engine-config.py centralizes CI configuration |
| Code Smell Density | 6/10 | fitness-review.yml exceeds 1000 lines with repeated boilerplate; skill list duplication is a shotgun-surgery risk |

## Detailed Findings

### Structural Complexity (8/10)

**Functions and scripts are well within complexity guardrails.** The only executable code in the repository is `engine-config.py` (367 lines, 3 functions) and two shell test scripts (200 and 79 lines). All functions are short and focused.

**Evidence of good practices:**
- `engine-config.py` — `_domains()`: 2 lines (line 135), `write_outputs()`: 36 lines (line 315), `main()`: 11 lines (line 353). All under the 50-line guardrail.
- `tests/workflow-tests.sh` — linear sequence of independent test blocks with `pass()`/`fail()` helpers, no nesting beyond 2 levels.
- `tests/skill-structure-tests.sh` — same pattern, 79 lines total, clean single-purpose loops.

**Issues found:**

1. **fitness-review.yml is 1150 lines** — `.github/workflows/fitness-review.yml:1-1150`. This is a GitHub Actions workflow, so it is not traditional code, but it far exceeds the 500-line module guardrail. The file contains 5 jobs (activation, agent, detection, safe_outputs, conclusion) with deeply nested YAML and inline JSON schemas. While much of this is dictated by the gh-aw framework pattern, the embedded JSON tool definitions (lines 379-586, ~207 lines of inline JSON) inflate the file substantially.

2. **Long lines in workflow file** — `.github/workflows/fitness-review.yml:650` contains a `docker run` command spanning 473 characters in a single line. Line 382 is also 473 characters. These are difficult to read and maintain.

3. **Long line in workflow-tests.sh** — `tests/workflow-tests.sh:111` is a 234-character `grep` chain. While functional, it reduces readability.

**Parameter count** — `write_outputs()` in `engine-config.py:315` takes 2 parameters (`engine_id`, `config`). All functions are at or below 3 parameters. No issues.

**Nesting depth** — Maximum observed nesting in `engine-config.py` is 3 levels (function > for loop > if/else). Shell scripts nest at most 2 levels (for loop > if). No issues.

### Understandability / Comprehensibility (8/10)

**Naming is consistently excellent across the project.** Skills use domain-specific names (`review-architecture`, `review-security`). Functions use descriptive verbs (`write_outputs`, `_domains`). Constants use SCREAMING_SNAKE_CASE (`CLAUDE_AGENT_ALLOWED_TOOLS`, `COMMON_DOMAINS`). File names communicate purpose (`engine-config.py`, `skill-structure-tests.sh`, `workflow-tests.sh`).

**Evidence of good practices:**
- `engine-config.py:19-75` — `CLAUDE_AGENT_ALLOWED_TOOLS` is a named constant, not a magic string list.
- `engine-config.py:234-237` — Version constants extracted: `CLAUDE_VERSION = "2.1.50"`, `COPILOT_VERSION = "0.0.414"`, `CODEX_VERSION = "0.104.0"`.
- Every SKILL.md follows identical structure: frontmatter, workflow, scoring dimensions, output format.
- `docs/adrs/0001-skill-based-review-architecture.md` documents the key architectural decision with context, rationale, and consequences.
- `CONTRIBUTING.md` explains conventions, naming, structure, and the multi-file update checklist.

**Flow clarity is strong:**
- Each skill's SKILL.md reads as a numbered workflow (Step 1, Step 2, ...) that is easy to follow.
- `engine-config.py` is organized with clear section headers (`# ---------------------------------------------------------------------------`).
- Shell scripts use section headers (`echo "--- File structure ---"`).

**Issues found:**

1. **No inline comments on complex CLI command strings** — `engine-config.py:157-167` — `CLAUDE_AGENT_CLI` is a 10-line string interpolation assembling a bash command. While the section header says "Claude Code agent: set up PATH, run claude with MCP...", individual flags like `--permission-mode bypassPermissions` or `--output-format stream-json` are not explained. A new contributor would need to consult Claude Code CLI docs to understand each flag.

2. **`_TOOLCACHE_PATH` is cryptic** — `engine-config.py:149-153` — This shell one-liner uses nested quoting (`'\"'\"'\\n'\"'\"'`) that is extremely hard to parse visually. A comment explaining the quoting strategy or a code comment about what PATH entries this produces would help.

3. **`heredoc_threshold = 200`** — `engine-config.py:331` — This magic number controls when values are written as heredoc vs. simple assignment. The threshold is meaningful but not documented with a "why" comment explaining the 200-character choice.

### Technical Debt Indicators (7/10)

**Zero TODO/FIXME/HACK comments in project source code.** A grep across the entire repository found these markers only in skill checklist definitions and review output documents (where they describe what to look for in other projects), not in any actual project code.

**Zero lint suppressions.** No `eslint-disable`, `noqa`, `@SuppressWarnings`, or equivalent suppression markers in any file.

**Issues found:**

1. **Skill list duplicated 9+ times with no automated sync** — The complete list of 13 skills appears in:
   - `README.md` — 4 occurrences in `for` loops (lines 45, 54, 147, 160)
   - `SETUP.md` — 5 occurrences in `for` loops (lines 100, 140, 150, 166, 185)
   - `tests/skill-structure-tests.sh:12-15` — `SKILLS` array
   - `.github/workflows/pr-checks.yml:88` — `for dir in ...` loop
   - `review-full/SKILL.md:21-32` — domain launch list
   - `CONTRIBUTING.md:60-71` — update checklist enumerating locations

   This is the most significant duplication in the project. The `CONTRIBUTING.md:60-71` checklist acknowledges the problem and instructs contributors to update all locations, but `skill-structure-tests.sh` only validates directory existence, not that the prose references are correct. The previous fitness report (`docs/fitness-report.md:29`) documented a case where `review-apply` was added to some files but missed in others, proving this is an active maintenance risk.

2. **Repeated boilerplate in fitness-review.yml** — `.github/workflows/fitness-review.yml` contains multiple occurrences of the `setupGlobals` + `require` pattern for GitHub Script steps:
   ```
   const { setupGlobals } = require('/opt/gh-aw/actions/setup_globals.cjs');
   setupGlobals(core, github, context, exec, io);
   ```
   This 2-line preamble appears at lines 49-50, 67-68, 183-184, 200-201, 296-297, 820-821, 847-848, 914-915, 922-923, 935-936, 953-954, 971-972, 1025-1026, 1082-1083, 1141-1142 — a total of 15 times. While this is dictated by the gh-aw framework pattern (not custom code), it contributes to the 1150-line file length.

3. **Magic number in engine-config.py** — `engine-config.py:331` — `heredoc_threshold = 200`. Named as a variable (good) but lacks a comment explaining why 200 (the GitHub Actions output format limit that makes this necessary).

4. **Inline JSON schemas in workflow YAML** — `.github/workflows/fitness-review.yml:379-586` — 207 lines of inline JSON define tool schemas (create_issue, missing_tool, noop, missing_data) and validation rules. These are embedded directly in a shell `cat` heredoc inside a YAML step. While functional, this mixing of formats makes the file harder to maintain. A separate JSON file referenced by the step would reduce complexity.

### Coupling and Dependency Depth (8/10)

**Skills are fully self-contained.** Each `review-<domain>/` directory contains everything needed: `SKILL.md` for the workflow and scoring rubric, `references/checklist.md` for detailed checks. No skill imports from another skill. The `review-full` orchestrator references other skills by name only (for the Task tool to dispatch), not by importing their content.

**Evidence of good practices:**
- `engine-config.py` centralizes all engine-specific configuration in one place. The workflow references it via `steps.engine-config.outputs.*` — a clean interface.
- `.github/workflows/pr-checks.yml` is completely independent of `fitness-review.yml`.
- Shell test scripts depend only on the file system (checking that files/directories exist and running `python3`/`grep`).
- No circular dependencies. The dependency graph is: `review-full` -> all domain skills (fan-out only). `fitness-review.yml` -> `engine-config.py` -> nothing.

**Issues found:**

1. **fitness-review.yml depends heavily on gh-aw external actions** — The workflow references `github/gh-aw/actions/setup@<sha>` at 5 separate points (lines 42, 263, 898, 988, 1117) and uses ~15 different `.cjs` scripts from `/opt/gh-aw/actions/`. This is an intentional framework dependency, but the tight coupling means that any breaking change in gh-aw requires updates across all 5 `uses:` references plus potentially updating inline integration patterns.

2. **Copilot-specific branching in MCP config** — `engine-config.py:170-178` and `fitness-review.yml:652-710` both contain Copilot-specific logic. The `if copilot ... else ...` branch in the workflow (lines 652-710) duplicates the MCP server config JSON with minor differences (escaped env refs for Copilot). This is coupling between the workflow YAML and the engine-config.py that could be reduced by having engine-config.py output the full MCP config template.

### Code Smell Density (6/10)

**No god classes, no long methods, no dead code, no commented-out blocks.** The code smells that exist are structural rather than at the function/class level.

**Issues found:**

1. **fitness-review.yml is a god file (1150 lines)** — `.github/workflows/fitness-review.yml:1-1150`. While GitHub Actions workflows are inherently monolithic (reusable workflows or composite actions can only partially decompose them), this file handles activation, prompt construction, agent execution, threat detection, safe output processing, and conclusion — 5 distinct jobs with at least 6 concerns. The embedded JSON tool/validation schemas (lines 379-586) alone account for 207 lines.

2. **Shotgun surgery risk for skill list changes** — As documented under Technical Debt, adding or removing a skill requires edits in 10+ locations across 6+ files. `CONTRIBUTING.md:60-71` acknowledges this with an explicit checklist, but the only automated check is `skill-structure-tests.sh` which validates directory existence, not documentation consistency. The previous fitness report proved this fails in practice (`review-apply` was missed in several locations).

3. **Repeated `for` loop pattern in documentation** — The `for skill in review-architecture review-security ...` loop appears 9 times across `README.md` and `SETUP.md`. Each is a code block example for a different platform (Cursor, Claude Code, VS Code, CI). If the list changes, all 9 must be updated manually. This is a DRY violation applied to documentation code samples.

4. **Copilot/non-Copilot MCP config duplication** — `fitness-review.yml:652-710` contains two nearly identical JSON blocks (Copilot style with `\${VAR}` escapes and non-Copilot style with `$VAR`). The only differences are the `"type": "stdio"` field for Copilot's github server and the escaping style.

5. **No dead code found.** No unused functions, no unreachable branches, no commented-out blocks. This is clean.

## Top 5 Action Items (by impact)

1. [HIGH] Extract skill list to a single source of truth (e.g., a `skills.txt` or a variable in a shared script) and generate or validate all references from it. The current 9+ duplications have already caused at least one documented omission (`review-apply` missed in multiple files per `docs/fitness-report.md:29`). -- `CONTRIBUTING.md:60-71`, `README.md:45`, `SETUP.md:100`, `tests/skill-structure-tests.sh:12`

2. [MEDIUM] Extract inline JSON tool schemas and validation rules from fitness-review.yml into separate JSON files (e.g., `.github/config/safe-outputs-tools.json`, `.github/config/safe-outputs-validation.json`) and reference them with `cat` in the workflow step. This would reduce the workflow from 1150 lines to ~940 lines and make the JSON schemas independently editable and validatable. -- `.github/workflows/fitness-review.yml:379-586`

3. [MEDIUM] Add a "why" comment to the `_TOOLCACHE_PATH` shell one-liner in engine-config.py explaining the quoting strategy and what PATH entries it produces. This string is the most cognitively complex piece of code in the repository and has no explanatory comment. -- `.github/scripts/engine-config.py:149-153`

4. [LOW] Add a "why" comment to `heredoc_threshold = 200` explaining that this is the GitHub Actions output format threshold beyond which values need heredoc encoding to avoid shell quoting issues. -- `.github/scripts/engine-config.py:331`

5. [LOW] Consider extracting the Copilot vs. non-Copilot MCP config branching into engine-config.py as an output (e.g., `mcp_config_template`), eliminating the duplicated JSON blocks in the workflow YAML. -- `.github/workflows/fitness-review.yml:652-710`, `.github/scripts/engine-config.py`

## Metrics Summary (where measurable)

| Metric | Observed | Target | Status |
|--------|----------|--------|--------|
| Max LOC per function | 36 (`write_outputs`) | < 50 | PASS |
| Max nesting depth | 3 (`engine-config.py`) | < 4 | PASS |
| TODO/FIXME count | 0 | < 5 tracked | PASS |
| God class count (500+ LOC) | 0 | 0 | PASS |
| Max module LOC (code files) | 367 (`engine-config.py`) | < 500 | PASS |
| Max module LOC (all files) | 1150 (`fitness-review.yml`) | < 500 | FAIL |
| Skill list duplication count | 9+ identical lists | 1 (single source) | FAIL |
| Lint suppressions | 0 | 0 | PASS |
| Dead code blocks | 0 | 0 | PASS |
| Commented-out code | 0 | 0 | PASS |
| Magic numbers (unshared) | 1 (`heredoc_threshold = 200`) | 0 | BORDERLINE |

## References

See review-maintainability/references/checklist.md for the full checklist. Based on [Fundamentals of Maintainability](https://jeffbailey.us/blog/2026/02/22/fundamentals-of-maintainability/).
