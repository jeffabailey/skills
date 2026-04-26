"""Pure-function unit tests for the validator: validate_effective.

Per ADR-002 / ADR-006:
  - Validator takes the EFFECTIVE merged config (post deep-merge + defaults).
  - Sum of effective weights must equal 100 (±0.01 tolerance).
  - On violation, the result reports an actionable error message that names
    the offending file when possible.
  - validate_effective is a pure function: no filesystem, no globals, no
    mutation of inputs.

Driving port: validate_effective(effective: dict, source_chain: list[Path]) -> ValidationResult
where ValidationResult exposes: ok (bool), errors (list[str]).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "fitness-config.py"
_spec = importlib.util.spec_from_file_location("fitness_config", SCRIPT)
fitness_config = importlib.util.module_from_spec(_spec)
sys.modules["fitness_config"] = fitness_config
_spec.loader.exec_module(fitness_config)


# ---------------------------------------------------------------------------
# Effective fixtures (post deep-merge + defaults). These mirror the shape
# build_effective_config produces.
# ---------------------------------------------------------------------------

def _effective_with_weights(weights: dict) -> dict:
    return {
        "version": 1,
        "weights": weights,
        "statusThresholds": {"healthy": [8, 10], "needsAttention": [5, 7], "critical": [1, 4]},
        "security": {"confidenceThreshold": 7},
        "scoring": {"goodRange": [8, 10], "badRange": [1, 3]},
    }


def _default_effective() -> dict:
    return _effective_with_weights({
        "architecture": 14, "security": 14, "reliability": 10, "testing": 10,
        "performance": 10, "algorithms": 10, "data": 10, "accessibility": 8,
        "process": 8, "maintainability": 6,
    })


# ---------------------------------------------------------------------------
# Sum-100 invariant
# ---------------------------------------------------------------------------

def test_validate_effective_ok_when_weights_sum_to_100():
    result = fitness_config.validate_effective(_default_effective(), source_chain=[])

    assert result.ok is True
    assert result.errors == []


def test_validate_effective_ok_within_floating_tolerance():
    # 99.995 rounds within ±0.01 of 100.
    weights = {
        "architecture": 14.001, "security": 13.999, "reliability": 10, "testing": 10,
        "performance": 10, "algorithms": 10, "data": 10, "accessibility": 8,
        "process": 8, "maintainability": 6,
    }
    result = fitness_config.validate_effective(
        _effective_with_weights(weights), source_chain=[]
    )

    assert result.ok is True


def test_validate_effective_fails_when_sum_is_99():
    # 95: data drops 5
    weights = {
        "architecture": 14, "security": 14, "reliability": 10, "testing": 10,
        "performance": 10, "algorithms": 10, "data": 5, "accessibility": 8,
        "process": 8, "maintainability": 6,
    }

    result = fitness_config.validate_effective(
        _effective_with_weights(weights), source_chain=[]
    )

    assert result.ok is False
    assert any("95" in e for e in result.errors), (
        f"expected actual sum '95' in errors, got {result.errors}"
    )
    assert any("100" in e for e in result.errors), (
        f"expected target sum '100' in errors, got {result.errors}"
    )


def test_validate_effective_fails_when_sum_is_101():
    # Bumped above 100.
    weights = dict(_default_effective()["weights"])
    weights["data"] = 11  # default 10 -> 11 makes sum 101

    result = fitness_config.validate_effective(
        _effective_with_weights(weights), source_chain=[]
    )

    assert result.ok is False
    assert any("101" in e for e in result.errors)


def test_validate_effective_names_offending_file_when_provided():
    # The validator should name the deepest source-chain file (the one most
    # likely responsible for the override) so Devin knows where to fix.
    weights = dict(_default_effective()["weights"])
    weights["data"] = 5  # sum = 95

    chain = [
        Path("infrastructure/modules/postgresql/fitness-config.json"),  # nearest
        Path("fitness-config.json"),  # root
    ]

    result = fitness_config.validate_effective(
        _effective_with_weights(weights), source_chain=chain
    )

    assert result.ok is False
    combined = "\n".join(result.errors)
    assert "postgresql/fitness-config.json" in combined or "modules/" in combined, (
        f"expected nearest override file in error, got: {combined}"
    )


def test_validate_effective_handles_empty_weights_block_as_failure():
    # An empty weights block sums to 0 -> not 100 -> must fail.
    result = fitness_config.validate_effective(
        _effective_with_weights({}), source_chain=[]
    )

    assert result.ok is False
    assert any("0" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Purity contract
# ---------------------------------------------------------------------------

def test_validate_effective_is_pure_does_not_mutate_input():
    cfg = _default_effective()
    snapshot = {
        "version": cfg["version"],
        "weights": dict(cfg["weights"]),
        "statusThresholds": dict(cfg["statusThresholds"]),
        "security": dict(cfg["security"]),
        "scoring": dict(cfg["scoring"]),
    }

    fitness_config.validate_effective(cfg, source_chain=[])

    assert cfg["weights"] == snapshot["weights"]
    assert cfg["statusThresholds"] == snapshot["statusThresholds"]
    assert cfg["security"] == snapshot["security"]
    assert cfg["scoring"] == snapshot["scoring"]


# ---------------------------------------------------------------------------
# ValidationResult shape — algebraic data type with ok + errors.
# ---------------------------------------------------------------------------

def test_validate_effective_returns_result_with_ok_and_errors_fields():
    result = fitness_config.validate_effective(_default_effective(), source_chain=[])

    assert hasattr(result, "ok")
    assert hasattr(result, "errors")
    assert isinstance(result.errors, list)


# ---------------------------------------------------------------------------
# Sum-violation message MUST name every file in the chain (Step 03-01,
# fail-closed contract: Devin needs every chain entry called out so the
# offending file is locatable even when the deepest entry isn't responsible).
# ---------------------------------------------------------------------------

def test_validate_effective_names_every_file_in_chain_on_sum_violation():
    # Chain has THREE distinct entries — message must reference all three so
    # Devin can locate the offending file even when the deepest isn't to blame.
    weights = dict(_default_effective()["weights"])
    weights["data"] = 5  # sum = 95

    chain = [
        Path("infrastructure/modules/postgresql/database/fitness-config.json"),
        Path("infrastructure/modules/postgresql/fitness-config.json"),
        Path("fitness-config.json"),
    ]

    result = fitness_config.validate_effective(
        _effective_with_weights(weights), source_chain=chain
    )

    combined = "\n".join(result.errors)
    # Each distinct chain entry must appear in the error somewhere.
    assert "postgresql/database/fitness-config.json" in combined, (
        f"deepest chain entry missing: {combined}"
    )
    assert "postgresql/fitness-config.json" in combined, (
        f"intermediate chain entry missing: {combined}"
    )
    # Root entry — its rendered string is just 'fitness-config.json' on its own.
    # We assert the bare root form appears at least once outside the longer paths.
    chain_naming = combined
    # Strip the deeper paths so only standalone root mentions remain.
    standalone = chain_naming.replace(
        "postgresql/database/fitness-config.json", ""
    ).replace("postgresql/fitness-config.json", "")
    assert "fitness-config.json" in standalone, (
        f"root entry missing as standalone reference: {combined}"
    )


# ---------------------------------------------------------------------------
# Schema version mismatch detection (ADR-003) — pure function, runs
# BEFORE merge so the CLI can short-circuit without computing an effective
# config from incompatible inputs.
# ---------------------------------------------------------------------------

def test_validate_schema_versions_ok_when_all_configs_match():
    raw_configs = [
        {"version": 1, "weights": {}},  # nearest
        {"version": 1, "weights": {}},  # root
    ]
    chain = [
        Path("infrastructure/modules/postgresql/fitness-config.json"),
        Path("fitness-config.json"),
    ]

    result = fitness_config.validate_schema_versions(raw_configs, source_chain=chain)

    assert result.ok is True
    assert result.errors == []


def test_validate_schema_versions_fails_when_child_newer_than_root():
    raw_configs = [
        {"version": 2, "weights": {}},  # nearest (override) declares newer
        {"version": 1, "weights": {}},  # root declares supported
    ]
    chain = [
        Path("infrastructure/modules/postgresql/fitness-config.json"),
        Path("fitness-config.json"),
    ]

    result = fitness_config.validate_schema_versions(raw_configs, source_chain=chain)

    assert result.ok is False
    combined = "\n".join(result.errors).lower()
    assert "postgresql/fitness-config.json" in "\n".join(result.errors)
    assert "fitness-config.json" in "\n".join(result.errors)
    # Names declared versions and the supported version (1).
    assert "version" in combined
    assert "supported" in combined or "supported schema version is 1" in combined or "1" in combined


def test_validate_schema_versions_fails_when_child_older_than_root_with_upgrade_hint():
    raw_configs = [
        {"version": 1, "weights": {}},  # nearest (override) older
        {"version": 2, "weights": {}},  # root newer
    ]
    chain = [
        Path("infrastructure/modules/postgresql/fitness-config.json"),
        Path("fitness-config.json"),
    ]

    result = fitness_config.validate_schema_versions(raw_configs, source_chain=chain)

    assert result.ok is False
    combined = "\n".join(result.errors).lower()
    assert "upgrade" in combined or "older" in combined or "newer" in combined
