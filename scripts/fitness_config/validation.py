"""Validation rules. Pure: every function returns error lines as data and never raises.

Two families:
  - chain rules (ADR-003, ADR-006): schema versions across a chain, and the
    effective (merged) weights summing to 100;
  - file rules (ADR-008): strict per-file checks, plus completeness for a
    proposal headed for a write. Partial override files stay valid on their own.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .model import (DEFAULT_WEIGHTS, SECTION_DEFAULTS, SUPPORTED_SCHEMA_VERSION,
                    WEIGHTS_SUM_TOLERANCE)

_RANGE_SECTIONS = ("statusThresholds", "scoring")


@dataclass(frozen=True)
class ValidationResult:
    """ok, plus actionable error lines that name the chain files when there are any."""

    ok: bool
    errors: list[str] = field(default_factory=list)


def _sum_weights(weights: dict) -> float:
    """Sum the numeric weight values, ignoring anything else (bools, NaN, text)."""
    return sum(v for v in weights.values() if _is_number(v))


def _format_chain_for_error(source_chain: list[Path]) -> str:
    """Every chain file as a bulleted list, so the offending one can be found upstream too."""
    return "\n".join(f"  - {entry}" for entry in source_chain)


# ---------------------------------------------------------------------------
# Chain rules
# ---------------------------------------------------------------------------

def _version_fix(declared: list[tuple[Path, int]]) -> str:
    """The two concrete fixes for a version mismatch, worded for older, newer or mixed configs."""
    has_newer = any(v > SUPPORTED_SCHEMA_VERSION for _, v in declared)
    has_older = any(v < SUPPORTED_SCHEMA_VERSION for _, v in declared)
    if has_older and not has_newer:
        return (f"Fix: upgrade the older config(s) to version {SUPPORTED_SCHEMA_VERSION}, "
                f"or pin the newer config(s) back to version {SUPPORTED_SCHEMA_VERSION}.")
    if has_newer and not has_older:
        return (f"Fix: pin the newer config(s) back to version {SUPPORTED_SCHEMA_VERSION}, "
                "or upgrade tooling to support the newer schema.")
    return (f"Fix: align every config to version {SUPPORTED_SCHEMA_VERSION} "
            "(upgrade older entries or pin newer entries).")


def validate_schema_versions(
    raw_configs: list[dict],
    source_chain: list[Path],
) -> ValidationResult:
    """ADR-003: every chain config must declare the supported version (missing = 1).

    On a mismatch the errors list each chain file with its declared version
    and offer two concrete fixes.
    """
    declared: list[tuple[Path, int]] = []
    mismatched = False
    for entry, cfg in zip(source_chain, raw_configs):
        if not isinstance(cfg, dict):
            continue
        version = cfg.get("version", SUPPORTED_SCHEMA_VERSION)
        if type(version) is not int:
            mismatched = True  # e.g. "1", 1.0 or true: never the supported version
            continue
        declared.append((entry, version))
        mismatched = mismatched or version != SUPPORTED_SCHEMA_VERSION

    if not mismatched:
        return ValidationResult(ok=True, errors=[])
    return ValidationResult(ok=False, errors=[
        "Schema version mismatch across the resolution chain "
        f"(supported schema version is {SUPPORTED_SCHEMA_VERSION}):",
        *(f"  - {entry} declares version {version}" for entry, version in declared),
        _version_fix(declared),
    ])


_SUM_FIX = ("Fix: either adjust the override weights so the merged total is 100, "
            "or replace all 10 weights in the override (full replacement).")


def validate_effective(effective: dict, source_chain: list[Path]) -> ValidationResult:
    """ADR-002 / ADR-006: the effective weights must sum to 100.

    On a violation the errors name the nearest file, then every chain file
    (responsibility may lie upstream), then two fixes. This is the validator
    review skills consult before a review.
    """
    total = _sum_weights(effective.get("weights") or {})
    if abs(total - 100) <= WEIGHTS_SUM_TOLERANCE:
        return ValidationResult(ok=True, errors=[])
    if not source_chain:
        return ValidationResult(ok=False, errors=[
            f"Effective weights sum to {total:g}; must sum to 100.", _SUM_FIX])
    return ValidationResult(ok=False, errors=[
        f"Effective weights from {source_chain[0]} sum to {total:g}; must sum to 100.",
        "Resolution chain (nearest first):",
        _format_chain_for_error(source_chain),
        _SUM_FIX,
    ])


# ---------------------------------------------------------------------------
# File rules (ADR-008)
# ---------------------------------------------------------------------------

def _is_number(value) -> bool:
    """A finite int or float; bools, NaN and Infinity are not numbers here."""
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _is_pair(value) -> bool:
    return isinstance(value, list) and len(value) == 2 and all(_is_number(v) for v in value)


def _version_violations(config: dict) -> list[str]:
    version = config.get("version")
    if type(version) is int and version == SUPPORTED_SCHEMA_VERSION:
        return []
    return [f"'version' must be the integer {SUPPORTED_SCHEMA_VERSION}, got {version!r}"]


def _weight_sum_violations(weights: dict) -> list[str]:
    """Sum-to-100 binds a file only when it lists every domain; a partial
    override is summed after merging, by validate_effective."""
    if not set(DEFAULT_WEIGHTS) <= set(weights):
        return []
    total = _sum_weights(weights)
    if abs(total - 100) <= WEIGHTS_SUM_TOLERANCE:
        return []
    return [f"weights add up to {total:g}; they must add up to 100"]


def _weight_value_violations(weights: dict) -> list[str]:
    return [f"weights.{name} must be a number 0-100, got {value!r}"
            for name, value in weights.items()
            if name in DEFAULT_WEIGHTS and not (_is_number(value) and 0 <= value <= 100)]


def _weights_violations(weights: dict) -> list[str]:
    unknown = [f"weights.{name} is not a known domain ({', '.join(DEFAULT_WEIGHTS)})"
               for name in weights if name not in DEFAULT_WEIGHTS]
    return unknown + _weight_value_violations(weights) + _weight_sum_violations(weights)


def _pair_violations(name: str, section: dict) -> list[str]:
    """Every range is a [low, high] pair of scores, so each end lies within 1-10."""
    present = [key for key in SECTION_DEFAULTS[name] if key in section]
    malformed = [f"{name}.{key} must be a [low, high] pair of numbers, got {section[key]!r}"
                 for key in present if not _is_pair(section[key])]
    out_of_scale = [f"{name}.{key} must stay within scores 1-10, got {section[key]!r}"
                    for key in present
                    if _is_pair(section[key]) and not all(1 <= v <= 10 for v in section[key])]
    return malformed + out_of_scale


def _cutoff_violations(security: dict) -> list[str]:
    if "confidenceThreshold" not in security:
        return []
    cutoff = security["confidenceThreshold"]
    if _is_number(cutoff) and 1 <= cutoff <= 10:
        return []
    return [f"security.confidenceThreshold must be a number 1-10, got {cutoff!r}"]


_SECTION_RULES: dict[str, Callable[[dict], list[str]]] = {
    "weights": _weights_violations,
    "statusThresholds": lambda section: _pair_violations("statusThresholds", section),
    "security": _cutoff_violations,
    "scoring": lambda section: _pair_violations("scoring", section),
}


def validate_config(config) -> list[str]:
    """Strict per-file rules (ADR-008 Decision 1), mirroring the schema.

    Only the sections and weight domains present are checked, and the sum only
    when every domain is listed. Empty list = valid.
    """
    if not isinstance(config, dict):
        return ["A fitness config must be a JSON object"]
    section_lines = [
        line for name, rule in _SECTION_RULES.items() if name in config
        for line in (rule(config[name]) if isinstance(config[name], dict)
                     else [f"'{name}' must be an object"])]
    return _version_violations(config) + section_lines


def _section_completeness(name: str, section) -> list[str]:
    if section is None:
        return [f"'{name}' section is missing"]
    if not isinstance(section, dict):
        return []
    missing = [key for key in SECTION_DEFAULTS[name] if key not in section]
    unknown = [] if name == "weights" else sorted(set(section) - set(SECTION_DEFAULTS[name]))
    return ([f"'{name}' is missing: {', '.join(missing)}"] if missing else []) + (
        [f"'{name}' has unknown keys: {', '.join(unknown)}"] if unknown else [])


def _band_coverage_violations(bands) -> list[str]:
    """BR-6: critical, needsAttention, healthy tile 1-10 in order, no gap, no overlap."""
    order = ("critical", "needsAttention", "healthy")
    if not isinstance(bands, dict) or not all(_is_pair(bands.get(key)) for key in order):
        return []
    starts = [bands[key][0] for key in order] + [11]
    next_starts = [1] + [bands[key][1] + 1 for key in order]
    if starts == next_starts:
        return []
    shown = ", ".join(f"{key} {bands[key][0]:g}-{bands[key][1]:g}" for key in order)
    return [f"statusThresholds must cover every score 1-10 once, with no gap or overlap; got {shown}"]


def _completeness_violations(proposal: dict) -> list[str]:
    """Write-bound rules (ADR-008 Decision 2): every section and key present,
    weights whole numbers, ranges low-first, status bands tiling 1-10."""
    sections = [line for name in SECTION_DEFAULTS
                for line in _section_completeness(name, proposal.get(name))]
    weights = proposal.get("weights") if isinstance(proposal.get("weights"), dict) else {}
    fractional = [f"weights.{name} must be a whole number, got {value!r}"
                  for name, value in weights.items()
                  if name in DEFAULT_WEIGHTS and _is_number(value) and type(value) is not int]
    reversed_ranges = [f"{name}.{key} must list the low end first, got {value!r}"
                       for name in _RANGE_SECTIONS if isinstance(proposal.get(name), dict)
                       for key, value in proposal[name].items()
                       if key in SECTION_DEFAULTS[name] and _is_pair(value) and value[0] > value[1]]
    return sections + fractional + reversed_ranges + _band_coverage_violations(
        proposal.get("statusThresholds"))


def validate_proposal(proposal) -> list[str]:
    """Strict rules plus completeness, for a proposal headed for a write.

    Complete = version 1, all four sections with exactly their known keys,
    all ten domains as whole numbers adding up to 100.
    """
    violations = validate_config(proposal)
    if not isinstance(proposal, dict):
        return violations
    return violations + _completeness_violations(proposal)


_CHAIN_VALUE_RULES: dict[str, Callable[[dict], list[str]]] = {
    "weights": _weight_value_violations,
    "statusThresholds": lambda section: _pair_violations("statusThresholds", section),
    "security": _cutoff_violations,
    "scoring": lambda section: _pair_violations("scoring", section),
}


def validate_chain_values(raw_configs: list[dict], source_chain: list[Path]) -> ValidationResult:
    """Every value in every chain file must be usable before merging and rendering.

    Only the value rules apply: a partial override, a missing version (checked
    by validate_schema_versions) and the merged sum (validate_effective) stay
    the other validators' business. Errors name the file that holds the value.
    """
    errors = [
        f"Error: {entry}: {line}"
        for entry, cfg in zip(source_chain, raw_configs) if isinstance(cfg, dict)
        for name, rule in _CHAIN_VALUE_RULES.items() if name in cfg
        for line in (rule(cfg[name]) if isinstance(cfg[name], dict)
                     else [f"'{name}' must be an object"])]
    if not errors:
        return ValidationResult(ok=True, errors=[])
    return ValidationResult(ok=False, errors=[
        *errors, "Fix: correct the value(s) above, then run validate --path again."])
