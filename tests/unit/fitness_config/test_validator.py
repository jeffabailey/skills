"""Pure-function unit tests for the validator.

Per ADR-002 / ADR-006:
  - validate_effective takes the EFFECTIVE merged config (post deep-merge + defaults).
  - Sum of effective weights must equal 100 (±0.01 tolerance).
  - On violation, the result reports an actionable error message that names
    every file in the source chain.
  - validate_schema_versions enforces ADR-003 schema-version compatibility,
    runs BEFORE merge so the CLI can short-circuit on incompatible inputs.
  - Both validators are pure functions: no filesystem, no globals, no
    mutation of inputs.

Driving ports:
  validate_effective(effective: dict, source_chain: list[Path]) -> ValidationResult
  validate_schema_versions(raw_configs: list[dict], source_chain: list[Path]) -> ValidationResult
where ValidationResult exposes: ok (bool), errors (list[str]).

Test count budget (per 2x distinct-behaviors rule):
  Behavior B6: validate_effective enforces sum == 100 (with chain-naming)
  Behavior B7: validate_schema_versions enforces version match
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ._loader import fitness_config


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


_DEFAULT_WEIGHTS_SUM_100 = {
    "architecture": 14, "security": 14, "reliability": 10, "testing": 10,
    "performance": 10, "algorithms": 10, "data": 10, "accessibility": 8,
    "process": 8, "maintainability": 6,
}


def _default_effective() -> dict:
    return _effective_with_weights(dict(_DEFAULT_WEIGHTS_SUM_100))


# ---------------------------------------------------------------------------
# B6: validate_effective enforces sum == 100 (±0.01).
# Parametrized over input variations that share the SAME assertion logic:
# `result.ok == expected_ok` AND, on failure, the rendered sum value
# appears in errors. Distinct edge cases live as their own tests because
# they assert DIFFERENT things (chain-naming, purity, ADT shape).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "case_id,weights,expected_ok,expected_actual_sum_in_errors",
    [
        # Exact 100 — happy path.
        ("sum_exactly_100", _DEFAULT_WEIGHTS_SUM_100, True, None),
        # Within ±0.01 tolerance — still ok.
        (
            "sum_within_floating_tolerance",
            {
                "architecture": 14.001, "security": 13.999, "reliability": 10, "testing": 10,
                "performance": 10, "algorithms": 10, "data": 10, "accessibility": 8,
                "process": 8, "maintainability": 6,
            },
            True,
            None,
        ),
        # Sum below 100 (95) — fails, message names actual sum.
        (
            "sum_below_target_95",
            {
                "architecture": 14, "security": 14, "reliability": 10, "testing": 10,
                "performance": 10, "algorithms": 10, "data": 5, "accessibility": 8,
                "process": 8, "maintainability": 6,
            },
            False,
            "95",
        ),
        # Sum above 100 (101) — fails, message names actual sum.
        (
            "sum_above_target_101",
            {**_DEFAULT_WEIGHTS_SUM_100, "data": 11},
            False,
            "101",
        ),
        # Empty weights -> sum 0 -> fails with '0' in message.
        ("empty_weights_sum_zero", {}, False, "0"),
    ],
)
def test_validate_effective_enforces_sum_target(
    case_id: str, weights: dict, expected_ok: bool, expected_actual_sum_in_errors: str | None
):
    result = fitness_config.validate_effective(
        _effective_with_weights(weights), source_chain=[]
    )

    assert result.ok is expected_ok, f"case={case_id}: errors={result.errors}"
    if expected_ok:
        assert result.errors == []
    else:
        assert any(expected_actual_sum_in_errors in e for e in result.errors), (
            f"case={case_id}: expected '{expected_actual_sum_in_errors}' in errors, "
            f"got {result.errors}"
        )
        # Target sum must always be referenced on failure.
        assert any("100" in e for e in result.errors), (
            f"case={case_id}: target '100' missing from errors {result.errors}"
        )


def test_validate_effective_names_every_file_in_chain_on_sum_violation():
    """On sum violation, error message must reference every chain entry so
    Devin can locate the offending file even when the deepest isn't to blame.
    """
    weights = {**_DEFAULT_WEIGHTS_SUM_100, "data": 5}  # sum = 95
    chain = [
        Path("infrastructure/modules/postgresql/database/fitness-config.json"),
        Path("infrastructure/modules/postgresql/fitness-config.json"),
        Path("fitness-config.json"),
    ]

    result = fitness_config.validate_effective(
        _effective_with_weights(weights), source_chain=chain
    )

    assert result.ok is False
    combined = "\n".join(result.errors)
    assert "postgresql/database/fitness-config.json" in combined
    assert "postgresql/fitness-config.json" in combined
    standalone = combined.replace(
        "postgresql/database/fitness-config.json", ""
    ).replace("postgresql/fitness-config.json", "")
    assert "fitness-config.json" in standalone


def test_validate_effective_returns_pure_result_with_ok_and_errors_fields():
    """Purity contract + ValidationResult ADT shape.

    Single test covers BOTH purity (inputs unchanged) and ADT shape
    (result has ok bool + errors list) — they share the same setup and
    each is a non-input-variation behavioral assertion.
    """
    cfg = _default_effective()
    snapshot = {
        "version": cfg["version"],
        "weights": dict(cfg["weights"]),
        "statusThresholds": dict(cfg["statusThresholds"]),
        "security": dict(cfg["security"]),
        "scoring": dict(cfg["scoring"]),
    }

    result = fitness_config.validate_effective(cfg, source_chain=[])

    # ADT shape
    assert hasattr(result, "ok")
    assert hasattr(result, "errors")
    assert isinstance(result.errors, list)
    # Purity
    assert cfg["weights"] == snapshot["weights"]
    assert cfg["statusThresholds"] == snapshot["statusThresholds"]
    assert cfg["security"] == snapshot["security"]
    assert cfg["scoring"] == snapshot["scoring"]


# ---------------------------------------------------------------------------
# B7: validate_schema_versions enforces version match (ADR-003).
# Parametrized over the version-mismatch cases (newer-than-root,
# older-than-root) that share the SAME assertion logic: result.ok is False
# AND each chain file is named in the error.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "case_id,nearest_version,root_version,expected_ok,expected_keyword",
    [
        # Both match supported version -> ok.
        ("both_match_supported_v1", 1, 1, True, None),
        # Child declares version newer than root's supported version.
        ("child_newer_than_root", 2, 1, False, "version"),
        # Child older than root (newer than supported) — upgrade-style hint.
        ("child_older_than_root_with_upgrade_hint", 1, 2, False, None),
    ],
)
def test_validate_schema_versions_enforces_version_match(
    case_id: str,
    nearest_version: int,
    root_version: int,
    expected_ok: bool,
    expected_keyword: str | None,
):
    raw_configs = [
        {"version": nearest_version, "weights": {}},  # nearest (override)
        {"version": root_version, "weights": {}},     # root
    ]
    chain = [
        Path("infrastructure/modules/postgresql/fitness-config.json"),
        Path("fitness-config.json"),
    ]

    result = fitness_config.validate_schema_versions(raw_configs, source_chain=chain)

    assert result.ok is expected_ok, f"case={case_id}: errors={result.errors}"
    if expected_ok:
        assert result.errors == []
    else:
        combined = "\n".join(result.errors)
        combined_lower = combined.lower()
        # Both chain entries must be referenced so Devin can locate the offender.
        assert "postgresql/fitness-config.json" in combined, (
            f"case={case_id}: nearest entry missing"
        )
        # Root entry standalone (after stripping the deeper path).
        standalone = combined.replace("postgresql/fitness-config.json", "")
        assert "fitness-config.json" in standalone, (
            f"case={case_id}: root entry missing as standalone reference"
        )
        # Each case carries a recognizable diagnostic vocabulary.
        if case_id == "child_newer_than_root":
            assert "version" in combined_lower
            assert "supported" in combined_lower or "1" in combined_lower
        elif case_id == "child_older_than_root_with_upgrade_hint":
            assert (
                "upgrade" in combined_lower
                or "older" in combined_lower
                or "newer" in combined_lower
            )


# ---------------------------------------------------------------------------
# Behavior B8: completeness rules for proposals headed for a write (ADR-008).
# A complete proposal has all 10 domains as integers summing to 100 and all
# four sections. Partial override files stay valid on their own; only the
# write gate applies these rules.
# ---------------------------------------------------------------------------

from hypothesis import given  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

DOMAINS = list(fitness_config.DEFAULT_WEIGHTS)


@st.composite
def weights_summing_to_100(draw) -> dict:
    cuts = sorted(draw(st.lists(st.integers(0, 100), min_size=9, max_size=9)))
    bounds = [0, *cuts, 100]
    return {domain: bounds[i + 1] - bounds[i] for i, domain in enumerate(DOMAINS)}


def score_ranges() -> st.SearchStrategy:
    return st.tuples(st.integers(1, 10), st.integers(1, 10)).map(lambda pair: sorted(pair))


@st.composite
def complete_configs(draw) -> dict:
    """Every proposal the write gate must accept."""
    return {
        "version": 1,
        "weights": draw(weights_summing_to_100()),
        "statusThresholds": {key: draw(score_ranges()) for key in fitness_config.DEFAULT_STATUS},
        "security": {"confidenceThreshold": draw(st.integers(1, 10))},
        "scoring": {key: draw(score_ranges()) for key in fitness_config.DEFAULT_SCORING},
    }


def _drop_section(config: dict, section: str) -> dict:
    return {key: value for key, value in config.items() if key != section}


def _drop_domain(config: dict, domain: str) -> dict:
    weights = {key: value for key, value in config["weights"].items() if key != domain}
    return {**config, "weights": weights}


def _shift_sum(config: dict, domain: str) -> dict:
    return {**config, "weights": {**config["weights"], domain: config["weights"][domain] + 1}}


def _fractional_weight(config: dict, domain: str) -> dict:
    return {**config, "weights": {**config["weights"], domain: config["weights"][domain] + 0.0}}


def _unknown_domain(config: dict, domain: str) -> dict:
    return {**config, "weights": {**config["weights"], f"{domain}-extra": 0}}


INCOMPLETENESS = {
    "missing section": lambda cfg, domain, section: _drop_section(cfg, section),
    "missing domain": lambda cfg, domain, section: _drop_domain(cfg, domain),
    "sum not 100": lambda cfg, domain, section: _shift_sum(cfg, domain),
    "non-integer weight": lambda cfg, domain, section: _fractional_weight(cfg, domain),
    "unknown domain": lambda cfg, domain, section: _unknown_domain(cfg, domain),
}


@given(complete_configs())
def test_every_complete_proposal_passes_the_write_gate_validation(config):
    assert fitness_config.validate_proposal(config) == []


@given(
    complete_configs(),
    st.sampled_from(sorted(INCOMPLETENESS)),
    st.sampled_from(DOMAINS),
    st.sampled_from(["weights", "statusThresholds", "security", "scoring"]),
)
def test_any_incomplete_proposal_is_rejected_with_a_reason(config, flaw, domain, section):
    broken = INCOMPLETENESS[flaw](config, domain, section)
    errors = fitness_config.validate_proposal(broken)
    assert errors, f"{flaw} accepted: {broken}"
    assert all(isinstance(line, str) and line for line in errors)
