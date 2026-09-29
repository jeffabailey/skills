# Data Models: fitness-config-init

Shapes and contracts only. Internal representation (dicts, dataclasses) is the crafter's choice, within ADR-006 style.

## 1. Config (unchanged schema, stricter "complete" profile)

The schema (`fitness-config.schema.json`, version 1) is unchanged. The skill always writes a **complete config**, a stricter subset of what the schema allows:

| Section | Complete-config rule | Enforced by |
|---|---|---|
| `version` | integer `1` | `validate_config` (ADR-008) |
| `weights` | exactly the 10 known domains; integers; each 0-100; sum 100 | names, range, sum: `validate_config`; exactly-10 and integer: completeness rules |
| `statusThresholds` | `healthy`, `needsAttention`, `critical`, each `[lo, hi]` numbers, lo ≤ hi | shape: `validate_config`; contiguous and non-overlapping over 1-10 (BR-6): completeness rules, added with US-06 |
| `security.confidenceThreshold` | number 1-10 | `validate_config` |
| `scoring` | `goodRange`, `badRange`, each `[lo, hi]` | shape: `validate_config` |
| other top-level keys | not emitted (no `$comment`, ADR-011) | canonical renderer drops them. The diff shows existing unknown keys as removals. |

Known domains, in canonical order (the `DEFAULT_WEIGHTS` order, same as the example file): architecture, security, reliability, testing, performance, algorithms, data, accessibility, process, maintainability.

## 2. Canonical Bytes

- Top-level key order: `version`, `weights`, `statusThresholds`, `security`, `scoring`.
- Nested key order: the `DEFAULT_*` order.
- 2-space indent, two-element numeric arrays inline (`[8, 10]`), UTF-8, LF, trailing newline.
- Fitness function: the canonical rendering of the built-in defaults is **byte-identical** to `fitness-config.example.json`.
- **Fingerprint**: the first 12 hex characters of SHA-256 over the canonical bytes. Shown to the user as `Proposal: <fp>` and passed back as `--expect`.

## 3. Purpose Profiles (`skills/fitness-config-init/references/purpose-profiles.md`)

A single markdown table that people read and tests parse. One row per archetype; columns are the 10 domains in canonical order plus `sum`.

| archetype | architecture | security | reliability | testing | performance | algorithms | data | accessibility | process | maintainability | sum |
|---|---|---|---|---|---|---|---|---|---|---|---|
| database-backend | 10 | 14 | 18 | 10 | 10 | 8 | 18 | 1 | 6 | 5 | 100 |
| ... 5 more rows | | | | | | | | | | | |

(The example row comes from US-02. DELIVER sets the final numbers.)

Archetypes (fixed IDs): `database-backend`, `web-frontend`, `cli-tool`, `library-sdk`, `data-pipeline`, `api-service`. `mixed` and `unknown` are classifications, not profiles: mixed means ask for the primary purpose; unknown means use the baseline.

Invariants (pytest fitness test): exactly 6 rows; IDs match the list; all integers; each value ≥ 1; each row sums to 100; each row, embedded in the baseline defaults, passes `validate_config` and the completeness rules. Numbers appear only here, never in SKILL.md (audit).

Each profile row may carry a short "typical rationale" line below the table for the agent to adapt. It is not machine-read.

## 4. Purpose Signals (`references/purpose-signals.md`)

Prose plus a table: archetype, then strong signals (manifest dependencies, directories, file types, deploy artifacts), then disqualifiers. Confidence rubric: **high** = two or more independent strong signals for one archetype and none for a competitor. **medium** = one strong signal, or competing archetypes. **low** = no strong signal. Also states the read budget (40 files) and the bounded listing method (`git ls-files` extension histogram when git is present; otherwise top-level plus one level of listing).

## 5. In-session Structures (agent-held, shown to the user)

| Structure | Fields | Invariants |
|---|---|---|
| Evidence item | `path`, `signal` (short text), `source` (`fast` \| `review-full`) | `path` exists in the target (returned by a read/list tool) |
| Classification | `archetype` \| `mixed` \| `unknown`, `confidence` (high/medium/low/user-confirmed), `evidence[]` | Unknown implies low |
| Proposal row | `key` (e.g. `weights.reliability`), `baseline`, `proposed`, `reason` \| `(unchanged)` | Reason present iff proposed ≠ baseline. Each reason cites at least one evidence path or review finding. Adjustment ≤ ±4 from the profile. |
| Proposal | complete config (section 1) plus rows plus `baseline_source` (`built-in defaults` \| `parent chain: <paths>` \| `example file (degraded)`) | Number of reasons = number of changed rows |

The rationale table is printed only (ADR-011). It is shown at step 4 (proposal) and repeated verbatim in the step 8 summary. Each reason is one line (at most ~100 characters) naming at least one evidence path or review-full finding.

## 6. Resolver CLI Contract (additions to `init --path`)

**Status: IMPLEMENTED** (DELIVER complete 2026-09-29; code now lives in the `scripts/fitness_config/` package per ADR-012, and the line references below are historical). Original pre-DELIVER specification text follows: none of `--dry-run`, `--from`, `--expect`, `--force` exist in `scripts/fitness-config.py` today. The crafter adds them to `_build_parser()` (currently lines 859-880) and routes them from the `init` branch of `main()`. Internal function names are the crafter's call. The seed-only `init --path T` behavior stays as it is, except for the anchor guard (6.3).

cwd for every call = **anchor** (git top-level, or the target when there is no repo). `<target>` must resolve inside the anchor; otherwise exit 2.

| Invocation | Reads | Writes | stdout (first line = status token) | Exit |
|---|---|---|---|---|
| `init --path T` (existing) | chain above T | T/fitness-config.json seed | unchanged | unchanged |
| `init --path T --dry-run` | chain above T (never above the anchor) | nothing | `STATUS: baseline`, `Baseline-Source: defaults \| chain`, chain paths, canonical JSON | 0; 1 on chain error |
| `init --path T --from - --dry-run` | stdin proposal, existing T/fitness-config.json, chain | nothing | `STATUS: would-create \| would-replace \| unchanged \| invalid \| existing-malformed \| existing-not-a-file`, `Proposal: <fp>`, diff lines, canonical JSON | 0 valid; 1 invalid or existing-not-a-file (errors on stderr, one per line) |
| `init --path T --from - --expect FP` | same | T/fitness-config.json only if absent (exclusive create) | `STATUS: created \| unchanged \| refused-exists \| fingerprint-mismatch \| existing-not-a-file \| write-failed \| verify-failed-rolled-back` | 0 created/unchanged; 1 otherwise |
| `init --path T --from - --expect FP --force` | same | replaces T/fitness-config.json atomically | `STATUS: replaced \| unchanged \| fingerprint-mismatch \| existing-not-a-file \| write-failed \| verify-failed-rolled-back` | 0 replaced/unchanged; 1 otherwise |
| `show --path T` (existing) | chain | nothing | unchanged (`Config:` line used verbatim) | unchanged |

`--from` without `--dry-run` requires `--expect`. `--force` requires `--from`. Proposal on stdin must be a JSON object; a parse failure gives `STATUS: invalid`.

Strict reading (every document the resolver reads: the stdin proposal, `validate <file>`, each chain file, the current T/fitness-config.json). The bytes must be UTF-8 text and valid JSON, and no object may set the same key twice at any depth. A proposal that fails gives `STATUS: invalid` with one reason line (`Proposal is not valid UTF-8 text`, `Proposal is not valid JSON: ...`, `Proposal sets the key "<key>" more than once`). A chain file or `validate <file>` that fails is an error naming the file (exit 1). A current file that fails gives `existing-malformed` with `Current file <reason>; cannot diff by value.` Never a traceback.

Target checks (all `init --path T` forms, before stdin is read or any status is printed): T that exists but is not a folder is exit 2, `Error: target is not a folder: T`. The gate forms (`--dry-run`, `--from -`) also need T to exist: otherwise exit 2, `Error: target folder does not exist: T`. The plain seed `init --path T` still creates a missing T.

`existing-not-a-file` (dry run and save): something other than a regular file (a folder, a dangling link) sits at T/fitness-config.json. The error names the path; no `Proposal:` line is printed, because no save can succeed there; exit 1; nothing is written. It is a failure status of its own, not `existing-malformed` (which is a successful dry run that `--force` can replace) and not `write-failed` (which is a save that was attempted).

### 6.1 Diff lines (dry-run with an existing file)

```
weights.reliability 12 -> 18
weights.accessibility 4 -> 1
statusThresholds.healthy [8, 10] -> [9, 10]
$comment "..." -> (removed)
(N values unchanged)
```

Leaf paths are dot-joined; a two-element range is one leaf. Order: canonical order, then unknown keys. When the existing file is malformed: `STATUS: existing-malformed` with `Current file is not valid JSON; cannot diff by value.`, followed by the canonical proposal. Replacing it still requires `--force` (US-04 example 3).

### 6.2 Write-gate sequence (inside `--from` without `--dry-run`)

1. Parse stdin and run strict validation plus completeness rules; if they fail, `invalid`. Then, if something other than a regular file is at T/fitness-config.json, `existing-not-a-file`.
2. Canonicalize and fingerprint; if ≠ `--expect`, `fingerprint-mismatch`.
3. Chain pre-check above T: parse and version (existing functions); if it fails, the existing error message.
4. Existing file: equal object means `unchanged` (no write, mtime kept). Present without `--force` means `refused-exists`.
5. Write a temp file in T, fsync, then `os.replace` (or exclusive create when no file exists).
6. Verify: re-read the bytes and compare the fingerprint; `validate_effective` on the new chain. If this fails, restore the prior bytes (or unlink) and report `verify-failed-rolled-back`.

### 6.3 Anchor guard (fixes the latent defect in `cmd_init_path`)

Location: the seed/baseline path shared by `init --path` (all forms), today `cmd_init_path` lines 629-633. `walk_up_chain_with_status` itself is unchanged, because `show`/`validate --path` never start above the stop boundary.

Rule: resolve target and base. If target == base, the chain is empty and the seed is the built-in defaults. If the target is not inside base, exit 2. Otherwise walk from `target.parent` with `stop=base`, as today.

Required tests (tmp_path):
- (a) A `fitness-config.json` placed in a directory *above* the anchor, with target == anchor: the baseline is the built-in defaults and the upper file is never read.
- (b) The same case for plain `init --path .`: the seeded file equals the defaults.
- (c) A target outside the anchor: exit 2 and nothing written.
