#!/usr/bin/env python3
"""Manage fitness-review config: validate, init, show.

Place fitness-config.json in your project root to customize thresholds and
weights. Skills read it at runtime. No need to edit SKILL.md files.

Usage:
    python3 fitness-config.py validate [path]   # Validate JSON (default: fitness-config.json)
    python3 fitness-config.py init [path]       # Create default config
    python3 fitness-config.py show [path]       # Print effective config (merged with defaults)
    python3 fitness-config.py show --path TARGET # Resolve walk-up chain from TARGET, deep-merge, render

Works on Windows, macOS, and Linux. Requires Python 3.6+.

Internal architecture (per ADR-004 / ADR-006):
  - All logic lives in this single file.
  - Pure functions: walk_up_chain, deep_merge_chain, build_effective_config,
    render_show_output. No filesystem I/O. No mutation of inputs.
  - Single impure adapter: _read_config (filesystem boundary).
  - CLI verbs (cmd_*) and main() compose pure functions with the adapter.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_WEIGHTS = {
    "architecture": 14,
    "security": 14,
    "reliability": 10,
    "testing": 10,
    "performance": 10,
    "algorithms": 10,
    "data": 10,
    "accessibility": 8,
    "process": 8,
    "maintainability": 6,
}

DEFAULT_STATUS = {
    "healthy": [8, 10],
    "needsAttention": [5, 7],
    "critical": [1, 4],
}

DEFAULT_SECURITY = {"confidenceThreshold": 7}

DEFAULT_SCORING = {"goodRange": [8, 10], "badRange": [1, 3]}

CONFIG_FILENAME = "fitness-config.json"


# ---------------------------------------------------------------------------
# Impure adapters — only these touch the filesystem.
# ---------------------------------------------------------------------------

def load(path: Path) -> dict | None:
    """Load config from path for legacy CLI verbs (cmd_validate, cmd_show).

    Returns None if the file is missing OR malformed; on a JSON parse error it
    prints a one-line "Invalid JSON: ..." message to stderr. This swallow-and-
    log contract is preserved verbatim from the pre-refactor CLI to keep bare
    invocations byte-identical (NFR-3). New path-based verbs use _read_config,
    which RAISES JSONDecodeError so the caller can name the offending file.
    """
    if not path.exists():
        return None
    try:
        return _read_config(path)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return None


def _read_config(path: Path) -> dict | None:
    """Adapter: read+parse a fitness-config.json. Returns None for missing
    files and raises json.JSONDecodeError for malformed JSON so callers can
    surface the offending path in their error message.
    """
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _read_chain_configs(chain: list[Path]) -> tuple[list[dict] | None, str | None]:
    """Adapter: read every fitness-config.json on the chain in order.

    Returns (raw_configs, None) on success, or (None, error_message) on the
    first malformed JSON file. Result-style return so command verbs can
    short-circuit cleanly without nested try/except blocks. Missing files
    are skipped silently (already filtered by walk_up_chain's existence
    check, but we double-check for robustness).
    """
    raw_configs: list[dict] = []
    for entry in chain:
        try:
            cfg = _read_config(entry)
        except json.JSONDecodeError as exc:
            return None, f"Error: invalid JSON in {entry}: {exc}"
        if cfg is not None:
            raw_configs.append(cfg)
    return raw_configs, None


def _print_validation_errors(errors: list[str]) -> None:
    """Adapter: print each error line on its own to stderr.

    Centralises the multi-line ValidationResult.errors -> stderr boundary
    so command verbs read as a flat pipeline of validation gates.
    """
    for line in errors:
        print(line, file=sys.stderr)


# ---------------------------------------------------------------------------
# Pure functions — no I/O, no mutation of inputs.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WalkUpResult:
    """Immutable algebraic result of walking the ancestor chain.

    chain: discovered fitness-config.json files in precedence order
    (nearest-first, root-last). depth_capped: True iff the 64-level safety
    cap terminated the walk before reaching the stop boundary — surfaced
    so the CLI can fail-closed with a pathological-tree error instead of
    silently truncating (ADR-006).
    """

    chain: list[Path] = field(default_factory=list)
    depth_capped: bool = False


# Maximum number of ancestor directories the walk-up will visit before
# halting. Per ADR-006, the cap is a hard error signal, not a silent truncation.
_WALK_UP_DEPTH_CAP = 64


def walk_up_chain_with_status(target: Path, stop: Path) -> WalkUpResult:
    """Walk up from target to stop boundary, returning chain + depth_capped flag.

    Pure: only reads file metadata via Path.exists(); does not mutate state.

    Returns the same chain as walk_up_chain plus a depth_capped boolean. The
    flag is True iff the safety cap fired before either the stop boundary or
    the filesystem root was reached, signalling a pathological tree.
    """
    target = target.resolve(strict=False)
    stop = stop.resolve(strict=False)

    start_dir = target if target.is_dir() else target.parent
    chain: list[Path] = []
    cursor = start_dir
    visited = 0
    depth_capped = False
    while True:
        candidate = cursor / CONFIG_FILENAME
        if candidate.exists() and candidate.is_file():
            chain.append(candidate)
        if cursor == stop:
            break
        parent = cursor.parent
        if parent == cursor:
            break  # reached filesystem root
        cursor = parent
        visited += 1
        if visited > _WALK_UP_DEPTH_CAP:
            depth_capped = True
            break
    return WalkUpResult(chain=chain, depth_capped=depth_capped)


def walk_up_chain(target: Path, stop: Path) -> list[Path]:
    """Walk up from target to stop boundary, returning the chain only.

    Inputs:
      target: directory or file inside the repo to resolve from.
      stop: ancestor at which the walk halts (typically repo root / cwd).
    Output: list of fitness-config.json paths in precedence order
      (nearest-to-target first, root last). Empty if no configs exist.
    Side effects: none. Pure aside from Path.exists() metadata reads.
    Invariants:
      - The returned list never contains paths outside [target..stop].
      - File targets are normalised to their parent directory before walking.
      - On a pathological tree, the depth_capped signal is silently dropped;
        prefer walk_up_chain_with_status when fail-closed semantics matter.
    """
    return walk_up_chain_with_status(target, stop).chain


def deep_merge_chain(raw_configs: list[dict]) -> dict:
    """Deep-merge a chain of configs in precedence order (nearest-first).

    Inputs: list[dict] of raw configs ordered nearest-to-target first.
    Output: a new merged dict with keys: weights, statusThresholds, security,
      scoring, version (any may be omitted if no chain entry set them).
    Side effects: none. Pure — returns a fresh dict; never mutates inputs.
    Invariants (per ADR-002):
      - weights is per-domain merged (each domain key resolved independently;
        nearest-wins precedence).
      - statusThresholds, security, scoring are replace-as-whole (first
        non-empty entry in the chain wins; lower entries are dropped entirely).
      - version: nearest-to-target wins, falling back to root.
    """
    merged: dict = {"weights": {}}
    # Iterate from lowest precedence (root) to highest (override) so that
    # higher-precedence values overwrite lower ones in the per-domain merge.
    for cfg in reversed(raw_configs):
        if not isinstance(cfg, dict):
            continue
        weights = cfg.get("weights")
        if isinstance(weights, dict):
            merged["weights"] = {**merged["weights"], **weights}

    # Replace-as-whole keys: nearest-to-target wins (first entry in chain).
    for whole_key in ("statusThresholds", "security", "scoring"):
        for cfg in raw_configs:
            if isinstance(cfg, dict) and whole_key in cfg:
                merged[whole_key] = cfg[whole_key]
                break

    # Version: nearest-to-target wins, falling back to root.
    for cfg in raw_configs:
        if isinstance(cfg, dict) and "version" in cfg:
            merged["version"] = cfg["version"]
            break

    return merged


def build_effective_config(merged: dict) -> dict:
    """Apply built-in defaults to fill any missing pieces of a merged config.

    Inputs: a dict produced by deep_merge_chain (or any equivalent shape).
    Output: a new dict with all five top-level keys populated (version,
      weights, statusThresholds, security, scoring), filled from
      DEFAULT_* constants where the input was silent.
    Side effects: none. Pure — returns a fresh dict; never mutates input.
    Invariants:
      - Every key in DEFAULT_WEIGHTS is present in output["weights"].
      - Override values from `merged` always win over DEFAULT_* values.
    """
    return {
        "version": merged.get("version", 1),
        "weights": {**DEFAULT_WEIGHTS, **(merged.get("weights") or {})},
        "statusThresholds": {**DEFAULT_STATUS, **(merged.get("statusThresholds") or {})},
        "security": {**DEFAULT_SECURITY, **(merged.get("security") or {})},
        "scoring": {**DEFAULT_SCORING, **(merged.get("scoring") or {})},
    }


def build_seed_config(raw_configs: list[dict]) -> dict:
    """Build a fully-populated seed config dict for `init --path` to write.

    When `raw_configs` is non-empty (i.e., a root or ancestor chain was found),
    the seed reflects the effective merged config so the new override starts
    out byte-equivalent to what was already applied at that scope. When the
    chain is empty, the seed is the documented built-in defaults so the file
    is valid on first author.

    Pure: returns a new dict; does not mutate inputs and does no I/O.
    """
    merged = deep_merge_chain(raw_configs)
    return build_effective_config(merged)


@dataclass(frozen=True)
class ValidationResult:
    """Immutable algebraic result of validating an effective config.

    ok=True means the config passes all invariants.
    errors holds zero or more actionable messages naming files when possible.

    Pure data — no methods with side effects.
    """

    ok: bool
    errors: list[str] = field(default_factory=list)


# Acceptable absolute deviation from 100 when summing weights, to absorb
# rounding from floating-point overrides without permitting real drift.
_WEIGHTS_SUM_TOLERANCE = 0.01


def _sum_weights(weights: dict) -> float:
    """Sum numeric weight values, ignoring non-numeric noise. Pure."""
    return sum(v for v in weights.values() if isinstance(v, (int, float)))


def _nearest_chain_label(source_chain: list[Path]) -> str | None:
    """Return a human-readable label for the deepest (override) entry.

    Pure: takes already-resolved paths and returns a string. The deepest entry
    is the one most likely responsible for an override that pushed the
    effective sum off 100, so naming it gives Devin a single place to look.
    """
    if not source_chain:
        return None
    nearest = source_chain[0]
    return str(nearest)


def _format_chain_for_error(source_chain: list[Path]) -> str:
    """Render every file in the chain as a bulleted list.

    Pure: takes already-resolved paths and returns a string. Naming every
    chain entry — not just the nearest — lets Devin locate the offending
    file even when responsibility lies upstream of the deepest override
    (fail-closed contract, Step 03-01).
    """
    return "\n".join(f"  - {entry}" for entry in source_chain)


# Supported schema version. ADR-003: any chain config declaring a different
# version is a HARD ERROR, surfaced before any merge is attempted so the CLI
# never produces an effective config from incompatible inputs.
_SUPPORTED_SCHEMA_VERSION = 1


def validate_schema_versions(
    raw_configs: list[dict],
    source_chain: list[Path],
) -> ValidationResult:
    """Validate that every chain config declares the supported schema version.

    Pure function: no filesystem, no mutation of inputs.

    Per ADR-003, schema-version mismatch is a HARD ERROR. Configs missing
    a `version` key are treated as version 1 (the documented default). On
    mismatch, the returned ValidationResult.errors names every chain file
    paired with its declared version, states the supported version, and
    offers two concrete fixes (upgrade the older config, or pin the newer
    config to the supported version).
    """
    if not raw_configs:
        return ValidationResult(ok=True, errors=[])

    declared: list[tuple[Path, int]] = []
    mismatched: list[tuple[Path, int]] = []
    for entry, cfg in zip(source_chain, raw_configs):
        if not isinstance(cfg, dict):
            continue
        version = cfg.get("version", _SUPPORTED_SCHEMA_VERSION)
        if not isinstance(version, int):
            mismatched.append((entry, version))
            continue
        declared.append((entry, version))
        if version != _SUPPORTED_SCHEMA_VERSION:
            mismatched.append((entry, version))

    if not mismatched:
        return ValidationResult(ok=True, errors=[])

    # Build chain-naming message: every file with its declared version.
    chain_lines = [
        f"  - {entry} declares version {version}"
        for entry, version in declared
    ]
    errors: list[str] = [
        "Schema version mismatch across the resolution chain "
        f"(supported schema version is {_SUPPORTED_SCHEMA_VERSION}):",
        *chain_lines,
    ]
    # Two concrete fixes per ADR-003 / fail-closed contract.
    has_newer = any(v > _SUPPORTED_SCHEMA_VERSION for _, v in declared)
    has_older = any(v < _SUPPORTED_SCHEMA_VERSION for _, v in declared)
    if has_older and not has_newer:
        errors.append(
            f"Fix: upgrade the older config(s) to version {_SUPPORTED_SCHEMA_VERSION}, "
            f"or pin the newer config(s) back to version {_SUPPORTED_SCHEMA_VERSION}."
        )
    elif has_newer and not has_older:
        errors.append(
            f"Fix: pin the newer config(s) back to version {_SUPPORTED_SCHEMA_VERSION}, "
            f"or upgrade tooling to support the newer schema."
        )
    else:
        errors.append(
            f"Fix: align every config to version {_SUPPORTED_SCHEMA_VERSION} "
            "(upgrade older entries or pin newer entries)."
        )
    return ValidationResult(ok=False, errors=errors)


def validate_effective(effective: dict, source_chain: list[Path]) -> ValidationResult:
    """Validate an EFFECTIVE merged config against domain invariants.

    Pure function: no filesystem, no globals, no mutation of inputs.

    Invariants enforced:
      - Effective weights sum to 100 (±_WEIGHTS_SUM_TOLERANCE).

    On violation, the returned ValidationResult.errors lists actionable
    messages naming EVERY file in the source chain (not just the deepest)
    and offers two fixes (adjust the override weights, or use a full
    replacement of all 10). Naming the whole chain is a fail-closed
    requirement: Devin must be able to locate the offending file even when
    responsibility lies upstream of the deepest override.

    Per ADR-002 / ADR-006, this is the single validator that downstream
    review skills consult before initiating a review.
    """
    weights = effective.get("weights") or {}
    total = _sum_weights(weights)

    if abs(total - 100) <= _WEIGHTS_SUM_TOLERANCE:
        return ValidationResult(ok=True, errors=[])

    # Sum violation — build an actionable error message that names every
    # entry in the chain so Devin can find the offending file.
    errors: list[str] = []
    nearest = _nearest_chain_label(source_chain)
    if nearest:
        errors.append(
            f"Effective weights from {nearest} sum to {total:g}; must sum to 100."
        )
    else:
        errors.append(
            f"Effective weights sum to {total:g}; must sum to 100."
        )
    if source_chain:
        errors.append("Resolution chain (nearest first):")
        errors.append(_format_chain_for_error(source_chain))
    errors.append(
        "Fix: either adjust the override weights so the merged total is 100, "
        "or replace all 10 weights in the override (full replacement)."
    )
    return ValidationResult(ok=False, errors=errors)


def _format_chain_path(path: Path, base: Path | None) -> str:
    """Render a chain entry relative to base when possible, else absolute."""
    if base is None:
        return str(path)
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except (ValueError, OSError):
        return str(path)


def render_show_output(
    target: Path,
    source_chain: list[Path],
    effective: dict,
    base: Path | None = None,
) -> str:
    """Render the human-readable + JSON-sentinel output for `show --path`.

    Inputs:
      target: the path the user passed via `show --path`.
      source_chain: ordered list of contributing fitness-config.json paths
        (nearest-first); empty when no configs were found.
      effective: dict from build_effective_config — fully-populated config.
      base: optional directory used to render chain entries as relative paths;
        falls back to absolute when relativisation fails.
    Output: a single string ending in '\\n', suitable for direct stdout write.
    Side effects: none. Pure — does not print, does not touch the filesystem.
    Invariants:
      - Domains are sorted descending by value, alphabetical for ties (AC-03.6).
      - The BEGIN/END_EFFECTIVE_CONFIG_JSON sentinel block is always emitted
        as valid JSON parseable by downstream consumers.
      - Same inputs produce byte-identical output (AC-NFR-2).
    """
    weights = effective.get("weights", {})
    chain_strs = [_format_chain_path(p, base) for p in source_chain]

    lines: list[str] = []
    lines.append(f"Resolved config for: {target}")
    lines.append("")

    # Source-chain section + Config: header line for the report.
    if not source_chain:
        lines.append("Config: built-in defaults (no fitness-config.json found)")
        lines.append("")
        lines.append("  config sources (in precedence order):")
        lines.append("    (no fitness-config.json found — using built-in defaults)")
    elif len(source_chain) == 1:
        lines.append(f"Config: {chain_strs[0]}")
        lines.append("")
        lines.append("  config sources (in precedence order):")
        lines.append(f"    1. {chain_strs[0]}  (root)")
    else:
        lines.append(f"Config: {chain_strs[0]} (merged with root, found by walking up from input path)")
        lines.append("")
        lines.append("  config sources (in precedence order, found by walking up the ancestor chain):")
        lines.append(f"    1. {chain_strs[0]}  (override)")
        for idx, entry in enumerate(chain_strs[1:-1], start=2):
            lines.append(f"    {idx}. {entry}  (intermediate)")
        lines.append(f"    {len(chain_strs)}. {chain_strs[-1]}  (root)")
    lines.append("")

    # Effective weights — table with one row per domain, descending by value
    # then alphabetical, plus an inline single-line listing all 10 domains.
    ordered = sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))
    total = sum(weights.values())
    status = "OK" if abs(total - 100) <= 0.01 else "ERROR"

    lines.append("  effective weights (merged):")
    for domain, value in ordered:
        lines.append(f"    {domain:<16} {value}")
    lines.append("    -------------------")
    lines.append(f"    total            {total}   {status}")
    lines.append("")

    # Inline "Effective weights:" line per data-models.md §3.3 — all 10 domains
    # on a single line, descending by value, ties alphabetical.
    inline_pairs = " ".join(f"{domain}={value}" for domain, value in ordered)
    lines.append(f"Effective weights: {inline_pairs}")
    lines.append("")

    # Embedded JSON sentinel block.
    payload = {
        "version": effective.get("version", 1),
        "source_chain": chain_strs,
        "effective": effective,
    }
    lines.append("<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->")
    lines.append(json.dumps(payload, indent=2, default=str))
    lines.append("<!-- END_EFFECTIVE_CONFIG_JSON -->")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Validation (existing behavior preserved).
# ---------------------------------------------------------------------------

def validate_config(data: dict) -> bool:
    """Basic validation without jsonschema. Returns True if valid."""
    if not isinstance(data.get("version"), int):
        print("Error: 'version' must be an integer", file=sys.stderr)
        return False
    if "weights" in data:
        w = data["weights"]
        if not isinstance(w, dict):
            print("Error: 'weights' must be an object", file=sys.stderr)
            return False
        total = sum(v for v in w.values() if isinstance(v, (int, float)))
        if abs(total - 100) > 0.01:
            print(f"Error: weights sum to {total}, should be 100", file=sys.stderr)
            return False
    if "security" in data and "confidenceThreshold" in data["security"]:
        t = data["security"]["confidenceThreshold"]
        if not (1 <= t <= 10):
            print(f"Error: confidenceThreshold must be 1–10, got {t}", file=sys.stderr)
            return False
    return True


def merge_defaults(data: dict) -> dict:
    """Merge loaded config with defaults (legacy single-file mode)."""
    out = {
        "weights": {**DEFAULT_WEIGHTS, **(data.get("weights") or {})},
        "statusThresholds": {**DEFAULT_STATUS, **(data.get("statusThresholds") or {})},
        "security": {**DEFAULT_SECURITY, **(data.get("security") or {})},
        "scoring": {**DEFAULT_SCORING, **(data.get("scoring") or {})},
    }
    return out


# ---------------------------------------------------------------------------
# CLI verbs — compose pure functions with adapters.
# ---------------------------------------------------------------------------

def cmd_validate(path: Path) -> int:
    """Validate config file.

    On failure, names the offending file in the error message so downstream
    consumers (CI, milestone-5 backward-compat) can identify the source. The
    successful "Valid: <path>" line is preserved verbatim from the legacy
    behavior to keep bare invocations byte-identical (NFR-3).
    """
    data = load(path)
    if data is None:
        print(f"Error: {path} not found or invalid JSON", file=sys.stderr)
        return 1
    if not validate_config(data):
        print(f"Error: invalid config: {path}", file=sys.stderr)
        return 1
    print("Valid:", path)
    return 0


def cmd_init(path: Path) -> int:
    """Create default config."""
    if path.exists():
        print(f"Error: {path} already exists", file=sys.stderr)
        return 1
    cfg = {
        "version": 1,
        "weights": DEFAULT_WEIGHTS,
        "statusThresholds": DEFAULT_STATUS,
        "security": DEFAULT_SECURITY,
        "scoring": DEFAULT_SCORING,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print("Created:", path)
    return 0


def cmd_init_path(target: Path, base: Path) -> int:
    """Seed a per-directory override at <target>/fitness-config.json.

    Resolution rule: walk up from <target>'s PARENT (so we don't read the
    file we're about to create) to <base>, collect any fitness-config.json
    files into a chain (nearest-first), and seed the new override from the
    deep-merged effective config. When no ancestor config is found, fall
    back to documented DEFAULT_WEIGHTS and note that on stdout so Devin
    knows the seed source.

    Refuses to overwrite an existing file (exit 1, names the file). The
    file-write boundary stays here; the seed builder above is pure.
    """
    out_path = target / CONFIG_FILENAME

    if out_path.exists():
        print(f"Error: {out_path} already exists", file=sys.stderr)
        return 1

    # Walk up from the parent of target so we never include the file we're
    # about to create. Use base (cwd) as the stop boundary like show/validate.
    target_resolved = target.resolve(strict=False)
    parent = target_resolved.parent
    chain = walk_up_chain(parent, stop=base)
    raw_configs, error = _read_chain_configs(chain)
    if error is not None:
        print(error, file=sys.stderr)
        return 1

    seed = build_seed_config(raw_configs)

    target.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(seed, f, indent=2)

    if not raw_configs:
        print(
            "No root fitness-config.json found; seeded with documented default weights."
        )
    print("Created:", out_path)
    return 0


def cmd_show(path: Path) -> int:
    """Print effective config (legacy single-file mode)."""
    data = load(path) or {}
    effective = merge_defaults(data)
    print(json.dumps(effective, indent=2))
    return 0


def _check_target_exists(target: Path, base: Path) -> str | None:
    """Return an actionable error message iff the target path is missing.

    Adapter-level guard: walk-up resolution requires a real anchor for the
    chain. Missing-path is a hard error per ADR-006 (fail-closed): silent
    fallback to defaults would let downstream consumers receive an effective
    config from the wrong scope.

    A path is considered "missing" iff neither the path itself NOR its
    immediate parent directory exists under base. This preserves the prior
    contract for `show --path` invocations that name a file inside a real
    directory (the file may not exist yet, but the anchor directory does).
    """
    candidate = (base / target) if not target.is_absolute() else target
    if candidate.exists():
        return None
    if candidate.parent.exists():
        return None
    return (
        f"Error: target path does not exist: {target}\n"
        f"  Fix: create the directory at {target}, "
        f"or invoke validate from a path that exists."
    )


def _depth_cap_error_message(target: Path) -> str:
    """Build the pathological-tree depth-cap error message.

    The 64-level safety cap fires only when an ancestor walk traverses more
    than _WALK_UP_DEPTH_CAP directories without reaching the stop boundary.
    That signals a pathological tree (no .git, no repo root, no fitness-config
    anywhere on the way up). Surfacing this as a hard error lets the CLI
    fail-closed instead of silently truncating.
    """
    return (
        f"Error: pathological-tree depth limit (>{_WALK_UP_DEPTH_CAP} levels) "
        f"reached while resolving config from {target}.\n"
        f"  Fix: invoke from a path within a normal repo tree, "
        f"or place a fitness-config.json above the target so resolution can anchor."
    )


def cmd_show_path(target: Path, base: Path) -> int:
    """Resolve walk-up chain from target, deep-merge, render to stdout.

    Fail-closed: every IO/parse/depth-cap/version-mismatch error short-
    circuits BEFORE rendering so downstream consumers cannot read the JSON
    sentinel block from a partial chain.

    Note: `show` deliberately does NOT reject non-existent target paths —
    legacy preview behavior (milestone-5 backward-compat) renders the root
    chain when the target is a hypothetical/future path. `validate` is the
    fail-closed gate; `show` is a preview tool.
    """
    walk = walk_up_chain_with_status(target, stop=base)
    if walk.depth_capped:
        print(_depth_cap_error_message(target), file=sys.stderr)
        return 1

    chain = walk.chain
    raw_configs, error = _read_chain_configs(chain)
    if error is not None:
        print(error, file=sys.stderr)
        return 1

    version_check = validate_schema_versions(raw_configs, source_chain=chain)
    if not version_check.ok:
        _print_validation_errors(version_check.errors)
        return 1

    merged = deep_merge_chain(raw_configs)
    effective = build_effective_config(merged)
    output = render_show_output(target, chain, effective, base=base)
    sys.stdout.write(output)
    return 0


def cmd_validate_path(target: Path, base: Path) -> int:
    """Resolve walk-up chain from target, deep-merge, validate effective config.

    On success: prints a confirmation that the merged config is valid.
    On failure: prints actionable error(s) to stderr and exits non-zero.
    Critical: on failure, the JSON sentinel block MUST NOT appear on stdout
    so downstream review skills cannot consume an invalid config.

    Fail-closed order (each step short-circuits before the next):
      1. Target path must exist
      2. Walk-up must complete within the depth cap
      3. Every chain file must parse as JSON
      4. Every chain file must declare the supported schema version
      5. The effective merged config must satisfy domain invariants
    """
    missing = _check_target_exists(target, base)
    if missing is not None:
        print(missing, file=sys.stderr)
        return 1

    walk = walk_up_chain_with_status(target, stop=base)
    if walk.depth_capped:
        print(_depth_cap_error_message(target), file=sys.stderr)
        return 1

    chain = walk.chain
    raw_configs, error = _read_chain_configs(chain)
    if error is not None:
        print(error, file=sys.stderr)
        return 1

    version_check = validate_schema_versions(raw_configs, source_chain=chain)
    if not version_check.ok:
        _print_validation_errors(version_check.errors)
        return 1

    merged = deep_merge_chain(raw_configs)
    effective = build_effective_config(merged)
    result = validate_effective(effective, source_chain=chain)

    if result.ok:
        if chain:
            print(f"Valid: merged config from {chain[0]}")
        else:
            print("Valid: built-in defaults (no fitness-config.json found)")
        return 0

    _print_validation_errors(result.errors)
    return 1


# ---------------------------------------------------------------------------
# Argparse wiring.
# ---------------------------------------------------------------------------

_AUDIT_INLINE_WEIGHTS_PATTERN = r'"weights"\s*:\s*\{'
_AUDIT_DIRECT_LOAD_PATTERN = r"(json\.load.*fitness-config\.json|open.*fitness-config\.json)"


def cmd_audit(repo_root: Path) -> int:
    """Grep audit step (BR-5 / FR-7 / US-08): refuse inline weight tables and direct config loads in SKILL.md.

    Walks every SKILL.md under <repo_root>/src/ plus the canonical prompt at
    <repo_root>/.github/fitness-review-prompt.md and fails closed if any of
    them either:
      - declares an inline `"weights": { ... }` JSON literal (ADR-002 / FR-7
        forbids hardcoded weights in skill prose), or
      - reads `fitness-config.json` directly via `json.load(...)` or `open(...)`
        instead of calling the resolver CLI (US-08 / AC-08.4).

    Designed to be invoked from CI:

        python3 scripts/fitness-config.py audit

    Exit 0 means clean. Exit 1 means at least one violation; the script names
    every offender so reviewers can locate the regression.
    """
    inline = re.compile(_AUDIT_INLINE_WEIGHTS_PATTERN)
    direct_load = re.compile(_AUDIT_DIRECT_LOAD_PATTERN)

    candidates: list[Path] = []
    src_dir = repo_root / "src"
    if src_dir.is_dir():
        for skill in sorted(src_dir.glob("review-*/SKILL.md")):
            candidates.append(skill)
    prompt = repo_root / ".github" / "fitness-review-prompt.md"
    if prompt.is_file():
        candidates.append(prompt)

    inline_hits: list[tuple[Path, int, str]] = []
    direct_hits: list[tuple[Path, int, str]] = []
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if inline.search(line):
                inline_hits.append((path, lineno, line.strip()))
            if direct_load.search(line):
                direct_hits.append((path, lineno, line.strip()))

    if not inline_hits and not direct_hits:
        print(f"Audit clean: scanned {len(candidates)} SKILL.md / prompt files; no inline weight tables, no direct config loads.")
        return 0

    if inline_hits:
        print("Inline weight tables found (forbidden by ADR-002 / FR-7):", file=sys.stderr)
        for path, lineno, line in inline_hits:
            print(f"  {path}:{lineno}: {line}", file=sys.stderr)
        print("  Fix: replace the inline table with a CLI invocation: python3 scripts/fitness-config.py show --path <target>", file=sys.stderr)

    if direct_hits:
        print("Direct fitness-config.json loads found (forbidden by US-08 / AC-08.4):", file=sys.stderr)
        for path, lineno, line in direct_hits:
            print(f"  {path}:{lineno}: {line}", file=sys.stderr)
        print("  Fix: invoke the resolver CLI instead of reading the file directly.", file=sys.stderr)

    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage fitness-config.json for project fitness review skills."
    )
    parser.add_argument(
        "command",
        choices=["validate", "init", "show", "audit"],
        help="Command to run",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Config file path (default: fitness-config.json) — legacy mode for show/validate/init",
    )
    parser.add_argument(
        "--path",
        dest="resolve_path",
        default=None,
        help="(show/validate/init) Resolve walk-up chain or seed override starting from this target path",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    # `audit` is a special-case CI gate: it scans the repo for inline weight
    # tables and direct fitness-config.json loads in SKILL.md prose. It does
    # not accept --path or a positional config path; the scan root is cwd.
    if args.command == "audit":
        if args.resolve_path is not None or args.path is not None:
            print(
                "Error: audit takes no path arguments — it scans cwd",
                file=sys.stderr,
            )
            return 2
        return cmd_audit(Path.cwd())

    if args.resolve_path is not None:
        if args.path is not None:
            print(
                "Error: positional path and --path are mutually exclusive",
                file=sys.stderr,
            )
            return 2
        target = Path(args.resolve_path)
        if args.command == "show":
            return cmd_show_path(target, base=Path.cwd())
        if args.command == "validate":
            return cmd_validate_path(target, base=Path.cwd())
        if args.command == "init":
            return cmd_init_path(target, base=Path.cwd())
        return 1

    legacy_path = Path(args.path) if args.path else Path(CONFIG_FILENAME)

    if args.command == "validate":
        return cmd_validate(legacy_path)
    if args.command == "init":
        return cmd_init(legacy_path)
    if args.command == "show":
        return cmd_show(legacy_path)
    return 1


if __name__ == "__main__":
    sys.exit(main())
