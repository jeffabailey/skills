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
import sys
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
    """Load config from path. Returns None if file missing."""
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return None


def _read_config(path: Path) -> dict | None:
    """Adapter: read+parse a fitness-config.json. Pure caller-friendly variant
    that returns None for missing files and raises for malformed JSON.
    """
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Pure functions — no I/O, no mutation of inputs.
# ---------------------------------------------------------------------------

def walk_up_chain(target: Path, stop: Path) -> list[Path]:
    """Walk up from target to stop boundary, collecting fitness-config.json
    paths in precedence order (nearest-to-target first, root last).

    Pure: only reads file metadata via Path.exists(); does not mutate state.
    """
    target = target.resolve(strict=False)
    stop = stop.resolve(strict=False)

    start_dir = target if target.is_dir() else target.parent
    chain: list[Path] = []
    cursor = start_dir
    visited = 0
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
        if visited > 64:  # ADR safety: bound walk-up depth
            break
    return chain


def deep_merge_chain(raw_configs: list[dict]) -> dict:
    """Deep-merge a chain of configs in precedence order (nearest-first).

    Per ADR-002:
      - weights: per-domain merge (override wins for keys it sets)
      - statusThresholds, security, scoring: replace as wholes (first non-empty wins)

    Pure: returns new dict; does not mutate inputs.
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

    Pure: returns new dict; does not mutate inputs.
    """
    return {
        "version": merged.get("version", 1),
        "weights": {**DEFAULT_WEIGHTS, **(merged.get("weights") or {})},
        "statusThresholds": {**DEFAULT_STATUS, **(merged.get("statusThresholds") or {})},
        "security": {**DEFAULT_SECURITY, **(merged.get("security") or {})},
        "scoring": {**DEFAULT_SCORING, **(merged.get("scoring") or {})},
    }


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

    Pure: returns a string; does not print, does not touch the filesystem.
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
        lines.append(f"Config: {chain_strs[0]} (merged with root)")
        lines.append("")
        lines.append("  config sources (in precedence order):")
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
    """Validate config file."""
    data = load(path)
    if data is None:
        print(f"Error: {path} not found or invalid JSON", file=sys.stderr)
        return 1
    if not validate_config(data):
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


def cmd_show(path: Path) -> int:
    """Print effective config (legacy single-file mode)."""
    data = load(path) or {}
    effective = merge_defaults(data)
    print(json.dumps(effective, indent=2))
    return 0


def cmd_show_path(target: Path, base: Path) -> int:
    """Resolve walk-up chain from target, deep-merge, render to stdout."""
    chain = walk_up_chain(target, stop=base)
    raw_configs: list[dict] = []
    for entry in chain:
        try:
            cfg = _read_config(entry)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON in {entry}: {exc}", file=sys.stderr)
            return 1
        if cfg is not None:
            raw_configs.append(cfg)

    merged = deep_merge_chain(raw_configs)
    effective = build_effective_config(merged)
    output = render_show_output(target, chain, effective, base=base)
    sys.stdout.write(output)
    return 0


# ---------------------------------------------------------------------------
# Argparse wiring.
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage fitness-config.json for project fitness review skills."
    )
    parser.add_argument(
        "command",
        choices=["validate", "init", "show"],
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
        help="(show only) Resolve walk-up chain starting from this target path",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "show" and args.resolve_path is not None:
        if args.path is not None:
            print(
                "Error: positional path and --path are mutually exclusive",
                file=sys.stderr,
            )
            return 2
        target = Path(args.resolve_path)
        return cmd_show_path(target, base=Path.cwd())

    legacy_path = Path(args.path) if args.path else Path("fitness-config.json")

    if args.command == "validate":
        return cmd_validate(legacy_path)
    if args.command == "init":
        return cmd_init(legacy_path)
    if args.command == "show":
        return cmd_show(legacy_path)
    return 1


if __name__ == "__main__":
    sys.exit(main())
