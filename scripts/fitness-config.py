#!/usr/bin/env python3
"""Manage fitness-review config: validate, init, show.

Place fitness-config.json in your project root to customize thresholds and
weights. Skills read it at runtime. No need to edit SKILL.md files.

Usage:
    python3 fitness-config.py validate [path]   # Validate JSON (default: fitness-config.json)
    python3 fitness-config.py init [path]       # Create default config
    python3 fitness-config.py show [path]       # Print effective config (merged with defaults)

Works on Windows, macOS, and Linux. Requires Python 3.6+.
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
    """Merge loaded config with defaults."""
    out = {
        "weights": {**DEFAULT_WEIGHTS, **(data.get("weights") or {})},
        "statusThresholds": {**DEFAULT_STATUS, **(data.get("statusThresholds") or {})},
        "security": {**DEFAULT_SECURITY, **(data.get("security") or {})},
        "scoring": {**DEFAULT_SCORING, **(data.get("scoring") or {})},
    }
    return out


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
    """Print effective config."""
    data = load(path) or {}
    effective = merge_defaults(data)
    print(json.dumps(effective, indent=2))
    return 0


def main() -> int:
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
        default="fitness-config.json",
        help="Config file path (default: fitness-config.json)",
    )
    args = parser.parse_args()
    path = Path(args.path)

    if args.command == "validate":
        return cmd_validate(path)
    if args.command == "init":
        return cmd_init(path)
    if args.command == "show":
        return cmd_show(path)
    return 1


if __name__ == "__main__":
    sys.exit(main())
