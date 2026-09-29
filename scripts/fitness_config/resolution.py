"""Chain resolution: walk-up discovery, anchored chain, deep merge, effective config.

Pure apart from path metadata probes (Path.exists / is_file) during the walk-up.
A chain is always nearest-first: the config closest to the target leads, the
root config comes last.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .model import (CONFIG_FILENAME, DEFAULT_SCORING, DEFAULT_SECURITY, DEFAULT_STATUS,
                    DEFAULT_WEIGHTS, SUPPORTED_SCHEMA_VERSION)

# ADR-006: past this many ancestors the walk stops and reports a pathological
# tree instead of silently truncating the chain.
WALK_UP_DEPTH_CAP = 64


@dataclass(frozen=True)
class WalkUpResult:
    """The configs found walking up (nearest-first) and whether the depth cap cut the walk short."""

    chain: list[Path] = field(default_factory=list)
    depth_capped: bool = False


def walk_up_chain_with_status(target: Path, stop: Path) -> WalkUpResult:
    """Walk from target (or a file target's folder) up to stop, collecting configs.

    The walk also ends at the filesystem root; depth_capped is True only when
    WALK_UP_DEPTH_CAP ended it first.
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
        if visited > WALK_UP_DEPTH_CAP:
            depth_capped = True
            break
    return WalkUpResult(chain=chain, depth_capped=depth_capped)


def walk_up_chain(target: Path, stop: Path) -> list[Path]:
    """The walk-up chain alone; use walk_up_chain_with_status to fail closed on the depth cap."""
    return walk_up_chain_with_status(target, stop).chain


def deep_merge_chain(raw_configs: list[dict]) -> dict:
    """Merge a nearest-first chain (ADR-002). Returns a new dict; inputs untouched.

    weights merge per domain (nearest wins); statusThresholds, security and
    scoring are replaced whole by the nearest config that sets them; version
    comes from the nearest config that declares one.
    """
    merged: dict = {"weights": {}}
    # Root first, so nearer configs overwrite per domain.
    for cfg in reversed(raw_configs):
        if not isinstance(cfg, dict):
            continue
        weights = cfg.get("weights")
        if isinstance(weights, dict):
            merged["weights"] = {**merged["weights"], **weights}

    for whole_key in ("statusThresholds", "security", "scoring"):
        for cfg in raw_configs:
            if isinstance(cfg, dict) and whole_key in cfg:
                merged[whole_key] = cfg[whole_key]
                break

    for cfg in raw_configs:
        if isinstance(cfg, dict) and "version" in cfg:
            merged["version"] = cfg["version"]
            break

    return merged


def build_effective_config(merged: dict) -> dict:
    """Fill whatever the merged config leaves unset from the built-in defaults.

    The result always has version, weights (all ten domains), statusThresholds,
    security and scoring; merged values win over defaults.
    """
    return {
        "version": merged.get("version", SUPPORTED_SCHEMA_VERSION),
        "weights": {**DEFAULT_WEIGHTS, **(merged.get("weights") or {})},
        "statusThresholds": {**DEFAULT_STATUS, **(merged.get("statusThresholds") or {})},
        "security": {**DEFAULT_SECURITY, **(merged.get("security") or {})},
        "scoring": {**DEFAULT_SCORING, **(merged.get("scoring") or {})},
    }


def build_seed_config(raw_configs: list[dict]) -> dict:
    """The config `init --path` starts from: the chain's effective config, or the defaults."""
    return build_effective_config(deep_merge_chain(raw_configs))


def chain_origin(target: Path, anchor: Path) -> tuple[Path | None, str | None]:
    """Where `init --path` starts its walk-up (ADR-009 anchor guard).

    Target == anchor: no chain. A target outside the anchor is an error.
    Otherwise the walk starts at the parent, so the file about to be written
    is never part of its own chain.
    """
    if target == anchor:
        return None, None
    if anchor not in target.parents:
        return None, f"Error: {target} is outside the project folder {anchor}"
    return target.parent, None


def anchored_chain(target: Path, anchor: Path,
                   has_config: Callable[[Path], bool]) -> tuple[list[Path], str | None]:
    """The `init --path` chain, nearest-first, bounded by the anchor (ADR-009).

    Only folders from target's parent up to the anchor are probed through
    `has_config`; nothing above the anchor is ever consulted.
    """
    origin, error = chain_origin(target, anchor)
    if origin is None:
        return [], error
    folders = [origin, *origin.parents][: len(origin.relative_to(anchor).parts) + 1]
    return [folder / CONFIG_FILENAME for folder in folders
            if has_config(folder / CONFIG_FILENAME)], None


def merge_defaults(data: dict) -> dict:
    """Legacy `show [path]`: one file over the defaults, without a version key."""
    return {key: value for key, value in build_effective_config(data).items() if key != "version"}
