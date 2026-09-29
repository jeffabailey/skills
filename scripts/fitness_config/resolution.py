"""Chain resolution: walk-up discovery, anchored chain, deep merge, effective config. Pure."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .model import (CONFIG_FILENAME, DEFAULT_SCORING, DEFAULT_SECURITY, DEFAULT_STATUS,
                    DEFAULT_WEIGHTS)

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
WALK_UP_DEPTH_CAP = 64


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
        if visited > WALK_UP_DEPTH_CAP:
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


def chain_origin(target: Path, anchor: Path) -> tuple[Path | None, str | None]:
    """Where `init --path` starts its walk-up (ADR-009 anchor guard).

    Pure over resolved paths. Target == anchor: no chain (None). A target
    outside the anchor is an error. Otherwise the walk starts at the parent,
    so the file about to be written is never part of its own chain.
    """
    if target == anchor:
        return None, None
    if anchor not in target.parents:
        return None, f"Error: {target} is outside the project folder {anchor}"
    return target.parent, None


def anchored_chain(target: Path, anchor: Path,
                   has_config: Callable[[Path], bool]) -> tuple[list[Path], str | None]:
    """The `init --path` chain, nearest-first, bounded by the anchor (ADR-009).

    Pure over paths: only configs from target's parent up to the anchor are
    probed through `has_config`; nothing above the anchor is ever consulted.
    """
    origin, error = chain_origin(target, anchor)
    if origin is None:
        return [], error
    folders = [origin, *origin.parents][: len(origin.relative_to(anchor).parts) + 1]
    return [folder / CONFIG_FILENAME for folder in folders
            if has_config(folder / CONFIG_FILENAME)], None

def merge_defaults(data: dict) -> dict:
    """Merge loaded config with defaults (legacy single-file mode)."""
    out = {
        "weights": {**DEFAULT_WEIGHTS, **(data.get("weights") or {})},
        "statusThresholds": {**DEFAULT_STATUS, **(data.get("statusThresholds") or {})},
        "security": {**DEFAULT_SECURITY, **(data.get("security") or {})},
        "scoring": {**DEFAULT_SCORING, **(data.get("scoring") or {})},
    }
    return out
