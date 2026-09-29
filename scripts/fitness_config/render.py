"""Rendering: the show report, canonical config bytes, fingerprint and value diff. Pure."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .model import SECTION_DEFAULTS, SUPPORTED_SCHEMA_VERSION, WEIGHTS_SUM_TOLERANCE

# json.dumps(indent=2) spreads a [lo, hi] pair over four lines; canonical bytes keep it inline.
_INLINE_PAIR = re.compile(r"\[\s+([^\[\]\s,]+),\s+([^\[\]\s,]+)\s+\]")


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
    """The `show --path` report: config sources, weights table, inline weights,
    then the effective config as JSON between BEGIN/END sentinels.

    Chain entries print relative to `base` when possible. Weights sort by value
    descending, ties alphabetical (AC-03.6); same inputs, same bytes (AC-NFR-2).
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
    status = "OK" if abs(total - 100) <= WEIGHTS_SUM_TOLERANCE else "ERROR"

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
        "version": effective.get("version", SUPPORTED_SCHEMA_VERSION),
        "source_chain": chain_strs,
        "effective": effective,
    }
    lines.append("<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->")
    lines.append(json.dumps(payload, indent=2, default=str))
    lines.append("<!-- END_EFFECTIVE_CONFIG_JSON -->")

    return "\n".join(lines) + "\n"


def render_canonical(config: dict) -> str:
    """Canonical bytes (data-models section 2): known keys in DEFAULT_* order,
    2-space indent, inline [lo, hi] pairs, LF, trailing newline."""
    ordered = {"version": config["version"], **{
        name: {key: config[name][key] for key in defaults}
        for name, defaults in SECTION_DEFAULTS.items()}}
    return _INLINE_PAIR.sub(r"[\1, \2]", json.dumps(ordered, indent=2, ensure_ascii=False)) + "\n"


def proposal_fingerprint(canonical: str) -> str:
    """First 12 hex characters of SHA-256 over the canonical bytes."""
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


class _Missing:
    def __repr__(self) -> str:
        return "MISSING"


MISSING = _Missing()  # the side of a value diff that has no such leaf


@dataclass(frozen=True)
class ValueDiff:
    """(path, before, after) per differing leaf; `unchanged` counts equal tuning values."""

    changes: tuple[tuple[str, object, object], ...]
    unchanged: int


def _config_leaves(config: dict, prefix: str = "") -> dict:
    """Dot-joined leaf path -> value; a list (a [lo, hi] range) is one leaf."""
    leaves = {}
    for key, value in config.items():
        if isinstance(value, dict) and value:
            leaves.update(_config_leaves(value, f"{prefix}{key}."))
        else:
            leaves[f"{prefix}{key}"] = value
    return leaves


def value_diff(current: dict, proposal: dict) -> ValueDiff:
    """Leaves that differ, in the proposal's (canonical) order, then leaves
    only the current config has. The schema version is not a tuning value."""
    before, after = _config_leaves(current), _config_leaves(proposal)
    paths = [*after, *(path for path in before if path not in after)]
    pairs = [(path, before.get(path, MISSING), after.get(path, MISSING)) for path in paths]
    changes = tuple(pair for pair in pairs if pair[1] != pair[2])
    same = sum(1 for path, old, new in pairs if old == new and path != "version")
    return ValueDiff(changes, same)


def _diff_value(value, when_missing: str) -> str:
    return when_missing if value is MISSING else json.dumps(value, ensure_ascii=False)


def render_value_diff(diff: ValueDiff) -> tuple[str, ...]:
    """data-models 6.1: `path old -> new` lines, then `(N values unchanged)`."""
    lines = [f"{path} {_diff_value(old, '(absent)')} -> {_diff_value(new, '(removed)')}"
             for path, old, new in diff.changes]
    return (*lines, f"({diff.unchanged} values unchanged)")
