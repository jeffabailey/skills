# Component Boundaries — fitness-config-per-directory

**Wave**: DESIGN
**Date**: 2026-04-25

Defines responsibilities, public contracts, dependencies, and forbidden interactions for each logical component. Software-crafter implements the internal structure of each; this document is the boundary contract.

---

## 1. Logical Components

| Component | Location (v1) | Type | I/O? |
|-----------|--------------|------|------|
| Resolver | `scripts/fitness-config.py` (function group) | Pure orchestration | Reads files (only impure component) |
| Merger | `scripts/fitness-config.py` (function group) | Pure | None |
| Validator | `scripts/fitness-config.py` (function group) | Pure | None |
| Reporter | `scripts/fitness-config.py` (function group) | Pure | None |
| CLI | `scripts/fitness-config.py` (`main`, `cmd_*`) | Thin shell | stdin/stdout/stderr; exit codes |
| Skill prompts | `src/review-*/SKILL.md`, `.github/fitness-review-prompt.md` | Markdown instructions to LLM agent | (Tells agent to invoke CLI) |

In v1 these live in a single `.py` file as logical groupings (function clusters). ADR-004 documents the choice to keep them as a single file; ADR-004 also defines the threshold at which a future split into a `scripts/fitness_config/` package is warranted.

---

## 2. Resolver

### 2.1 Responsibility
Given a target path, produce a `ResolutionResult` containing: source chain (ordered list of paths), raw configs from each chain entry, and a status (ok | error with reason).

### 2.2 Public contract

```text
resolve_effective_config(target_path: Path, *, reader: Callable[[Path], dict | None] = _read_config) -> ResolutionResult
```

`ResolutionResult` shape (see `data-models.md`):
- `source_chain: list[Path]` — empty if no config found anywhere; ordered highest-precedence first
- `raw_configs: list[dict]` — raw parsed dict for each chain entry, same order
- `effective: dict` — merged configuration dict (post-merge, post-default-fill)
- `valid: bool`
- `errors: list[str]` — empty if valid

### 2.3 Dependencies
- May call: Merger, Validator, Reporter, filesystem reader (`_read_config`)
- May NOT call: CLI command functions (CLI calls down, not up)

### 2.4 Walk-up algorithm (pseudocode, not implementation)

1. Canonicalize `target_path` via `Path.resolve(strict=False)`.
2. If target is a file, start at its parent directory; if a directory, start there.
3. From the starting directory, ascend one parent at a time.
4. At each directory, check for `fitness-config.json`. If found, append to chain.
5. Stop when:
   - A directory containing `.git/` is encountered (after that directory is checked).
   - Filesystem root is reached.
   - 64 levels are walked (pathological-tree guard).
6. Return chain in walk order (deepest match first; root last).

Software-crafter owns the actual loop structure (recursion vs iteration vs `Path.parents`).

### 2.5 Forbidden
- Mutating any input dict.
- Caching across invocations (every call re-reads).
- Any network I/O.
- Any path globbing or sibling-directory enumeration.

---

## 3. Merger

### 3.1 Responsibility
Deep-merge an ordered list of config dicts into a single effective config dict. Highest-precedence (deepest in the tree) entries win at every key level; missing keys inherit from lower-precedence entries; unrepresented keys at the bottom of the chain inherit from `DEFAULT_*` constants.

### 3.2 Public contract

```text
deep_merge_chain(chain: list[dict], defaults: dict) -> dict
```

Merge rules (see ADR-002 for trade-offs):
- Top-level keys (`weights`, `statusThresholds`, `security`, `scoring`): merged per inner key.
- Within `weights`: per-domain key. If override sets `data=30`, only `data` changes; other domains inherit from below.
- Within `statusThresholds`: per range key (`healthy`, `needsAttention`, `critical`). Whole array replaces if present in override.
- Within `security`: per inner key. `confidenceThreshold` replaced if set.
- Within `scoring`: per inner key (`goodRange`, `badRange`). Whole array replaces if present.
- `version`: copied from the highest-precedence entry that has it (validated for chain consistency by Validator, not Merger).

### 3.3 Dependencies
- None (pure data transform on dicts).

### 3.4 Forbidden
- Mutating any input.
- Reading from filesystem.
- Calling Validator (the orchestrator does that AFTER merge).

---

## 4. Validator

### 4.1 Responsibility
Verify the effective merged config and the chain's schema-version consistency.

### 4.2 Public contract

```text
validate_effective(effective: dict, raw_configs: list[dict], source_chain: list[Path]) -> list[str]
```

Returns an empty list if valid; otherwise a list of human-readable error strings, each naming the file(s) involved.

### 4.3 Validation rules
- Effective `weights` values sum to 100 within 0.01 tolerance (BR-1).
- All `version` values across `raw_configs` are equal (BR-2). Mismatch -> error naming both files and the supported version.
- Each weight value is a number in [0, 100].
- `confidenceThreshold` (if present in effective) in [1, 10].
- Status threshold and scoring range arrays are length-2 numeric arrays.

### 4.4 Dependencies
- None (pure).

### 4.5 Forbidden
- Filesystem access.
- Mutating inputs.
- Throwing exceptions for validation failures (return error list instead — exceptions reserved for programmer errors).

---

## 5. Reporter

### 5.1 Responsibility
Render a `ResolutionResult` (or its components) as the human-readable strings that go into CLI stdout, into report headers, and into error messages.

### 5.2 Public contract

```text
render_show_output(result: ResolutionResult) -> str
render_header_lines(result: ResolutionResult, scope: Path) -> str   # Two-line "Config: ..." + "Effective weights: ..." block
render_validation_error(result: ResolutionResult) -> str
render_inline_weights(effective_weights: dict) -> str               # "data=30 reliability=20 ... maintainability=1"
```

### 5.3 Rendering rules
- Inline weights line: sorted by descending weight value, ties broken alphabetically (NFR-2 determinism).
- Source chain rendering:
  - 0 entries -> `Config: built-in defaults (no fitness-config.json found)`
  - 1 entry -> `Config: <path>` (no "merged with..." suffix)
  - 2+ entries -> `Config: <highest-precedence path> (merged with root)`
- Error messages name every file in the chain plus the rejected condition plus two concrete remediation suggestions (per AC-02.4 / AC-02.5).

### 5.4 Dependencies
- None (pure string formatting).

### 5.5 Forbidden
- Filesystem access.
- Side effects (no `print` — return strings).

---

## 6. CLI

### 6.1 Responsibility
Parse arguments, dispatch to the appropriate command function, format result, set exit code. No business logic.

### 6.2 Public contract (CLI subcommands)

| Subcommand | Existing v1 args | New v1 args | Backward compat |
|-----------|-----------------|-------------|-----------------|
| `validate` | `[path]` (positional, default `fitness-config.json`) | `--path <target>` flag | YES — bare `validate` uses positional default |
| `init` | `[path]` (positional, default `fitness-config.json`) | `--path <dir>` flag | YES |
| `show` | `[path]` (positional, default `fitness-config.json`) | `--path <target>` flag | YES |

Mutual exclusion: positional `path` and `--path` are mutually exclusive. Specifying both is an argparse error.

When `--path <target>` is supplied:
- `validate --path X`: resolve effective config for X; validate the merged result; exit 0/1.
- `show --path X`: resolve effective config for X; render via Reporter; exit 0 unless resolution fails.
- `init --path X`: write a new `<X>/fitness-config.json` seeded from the current root effective config (or DEFAULT_WEIGHTS if no root); refuse if file exists; exit 0 on creation, 1 on conflict.

### 6.3 Exit codes
- 0: success
- 1: validation failure, file conflict (init), or any resolution error
- 2: argparse error (unchanged from argparse default)

### 6.4 Dependencies
- Calls Resolver, Validator, Reporter directly.
- May NOT inline merge / validate / render logic.

---

## 7. Skill prompts (markdown integration boundary)

### 7.1 Responsibility
Instruct the LLM agent to:
1. Identify the review target path.
2. Invoke `python3 <skills>/scripts/fitness-config.py show --path <target>` and capture stdout.
3. Embed the rendered Config: and Effective weights: lines verbatim into the first 10 lines of the generated report (US-03).
4. Use the parsed effective weights to compute the weighted overall score.
5. If the CLI exits non-zero, abort the review and surface the error verbatim (NFR-4 fail-closed).

### 7.2 Files affected (per US-08)

- `src/review-architecture/SKILL.md`
- `src/review-security/SKILL.md`
- `src/review-reliability/SKILL.md`
- `src/review-testing/SKILL.md`
- `src/review-performance/SKILL.md`
- `src/review-algorithms/SKILL.md`
- `src/review-data/SKILL.md`
- `src/review-accessibility/SKILL.md`
- `src/review-process/SKILL.md`
- `src/review-maintainability/SKILL.md`
- `src/review-full/SKILL.md`
- `.github/fitness-review-prompt.md`

(`src/review-jit-test-gen/SKILL.md` and `src/review-apply/SKILL.md` do NOT score and do NOT need updating.)

### 7.3 Forbidden
- Inlining numerical weights in skill prompts (today's `.github/fitness-review-prompt.md` does this — must change).
- Reading `fitness-config.json` directly (BR-5 / FR-7).
- Computing or printing effective weights without going through the CLI.

### 7.4 CI enforcement (per Architecture Enforcement section of `architecture-design.md`)

```bash
# Forbidden direct read
! grep -rn "json\.load.*fitness-config\.json\|open.*fitness-config\.json" \
    --include="*.py" --include="*.md" \
    --exclude-dir=docs \
    --exclude="scripts/fitness-config.py" .
```

---

## 8. Dependency graph

```text
              CLI
               |
               v
           Resolver  --(reads)--> Filesystem
           |   |
       Merger  Validator
                  |
                  v
              Reporter
```

- CLI -> Resolver -> {Merger, Validator, Reporter, Filesystem}
- All edges are calls down the diagram. No upward edges.
- Filesystem is the only impure node.

Skill prompts depend only on the CLI's stdout/stderr/exit-code contract — they do not import or reference internal functions.

---

## 9. What software-crafter decides (out of scope for design)

- Whether each component is a function group, a class, or a module file (v1 keeps as function groups in one file per ADR-004).
- Internal data structure for the source chain (list of (path, dict) tuples? two parallel lists? dataclass? — software-crafter's call).
- Test file organization.
- Specific deep-merge implementation (recursive vs iterative).
- Whether to use `@dataclass` or plain dicts for `ResolutionResult` (Python 3.6 has dataclasses backport via `pip install dataclasses` but stdlib-only would suggest `typing.NamedTuple` or a plain dict; given Python 3.7+ is the realistic floor, `@dataclass` is fine).

This document is the contract; everything else is implementation.
