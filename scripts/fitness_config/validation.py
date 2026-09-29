"""Validation rules: schema versions, effective sum, per-file strict rules, completeness. Pure."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .model import (DEFAULT_WEIGHTS, SECTION_DEFAULTS, SUPPORTED_SCHEMA_VERSION,
                    WEIGHTS_SUM_TOLERANCE)

@dataclass(frozen=True)
class ValidationResult:
    """Immutable algebraic result of validating an effective config.

    ok=True means the config passes all invariants.
    errors holds zero or more actionable messages naming files when possible.

    Pure data — no methods with side effects.
    """

    ok: bool
    errors: list[str] = field(default_factory=list)


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
        version = cfg.get("version", SUPPORTED_SCHEMA_VERSION)
        if not isinstance(version, int):
            mismatched.append((entry, version))
            continue
        declared.append((entry, version))
        if version != SUPPORTED_SCHEMA_VERSION:
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
        f"(supported schema version is {SUPPORTED_SCHEMA_VERSION}):",
        *chain_lines,
    ]
    # Two concrete fixes per ADR-003 / fail-closed contract.
    has_newer = any(v > SUPPORTED_SCHEMA_VERSION for _, v in declared)
    has_older = any(v < SUPPORTED_SCHEMA_VERSION for _, v in declared)
    if has_older and not has_newer:
        errors.append(
            f"Fix: upgrade the older config(s) to version {SUPPORTED_SCHEMA_VERSION}, "
            f"or pin the newer config(s) back to version {SUPPORTED_SCHEMA_VERSION}."
        )
    elif has_newer and not has_older:
        errors.append(
            f"Fix: pin the newer config(s) back to version {SUPPORTED_SCHEMA_VERSION}, "
            f"or upgrade tooling to support the newer schema."
        )
    else:
        errors.append(
            f"Fix: align every config to version {SUPPORTED_SCHEMA_VERSION} "
            "(upgrade older entries or pin newer entries)."
        )
    return ValidationResult(ok=False, errors=errors)


def validate_effective(effective: dict, source_chain: list[Path]) -> ValidationResult:
    """Validate an EFFECTIVE merged config against domain invariants.

    Pure function: no filesystem, no globals, no mutation of inputs.

    Invariants enforced:
      - Effective weights sum to 100 (±WEIGHTS_SUM_TOLERANCE).

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

    if abs(total - 100) <= WEIGHTS_SUM_TOLERANCE:
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

_RANGE_SECTIONS = ("statusThresholds", "scoring")

def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


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


def _weights_violations(weights: dict) -> list[str]:
    unknown = [f"weights.{name} is not a known domain ({', '.join(DEFAULT_WEIGHTS)})"
               for name in weights if name not in DEFAULT_WEIGHTS]
    out_of_range = [f"weights.{name} must be a number 0-100, got {value!r}"
                    for name, value in weights.items()
                    if name in DEFAULT_WEIGHTS and not (_is_number(value) and 0 <= value <= 100)]
    return unknown + out_of_range + _weight_sum_violations(weights)


def _pair_violations(name: str, section: dict) -> list[str]:
    return [f"{name}.{key} must be a [low, high] pair of numbers, got {section[key]!r}"
            for key in SECTION_DEFAULTS[name] if key in section and not _is_pair(section[key])]


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

    Pure. Returns every violation as a message line (empty = valid); never
    raises. Partial override files stay valid: only the sections and weight
    domains present are checked, and the sum only when all domains are listed.
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
    """Strict validation plus completeness for a proposal headed for a write.

    Complete = version 1, all four sections with exactly their known keys,
    all 10 domains as whole numbers adding up to 100. Returns error lines
    (empty when the proposal may be written).
    """
    violations = validate_config(proposal)
    if not isinstance(proposal, dict):
        return violations
    return violations + _completeness_violations(proposal)
