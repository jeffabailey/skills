"""Pure-function unit tests for the merger: deep_merge_chain.

Per ADR-002, deep-merge merges per top-level key:
  - weights: per-domain merge (override wins for keys it sets)
  - statusThresholds, security, scoring: replace as wholes

Input: list[dict] of raw configs in precedence order (nearest-to-target first).
Output: dict with merged 'weights', 'statusThresholds', 'security', 'scoring'.

deep_merge_chain is pure: no filesystem, no mutation of inputs.
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


def test_deep_merge_chain_module_overrides_root_per_domain():
    # Module override wins for the keys it specifies; root fills the rest.
    root = {
        "version": 1,
        "weights": {
            "architecture": 14, "security": 14, "reliability": 10, "testing": 10,
            "performance": 10, "algorithms": 10, "data": 10, "accessibility": 8,
            "process": 8, "maintainability": 6,
        },
    }
    override = {
        "version": 1,
        "weights": {
            "architecture": 14, "security": 14, "reliability": 20, "testing": 10,
            "performance": 6, "algorithms": 4, "data": 30, "accessibility": 0,
            "process": 1, "maintainability": 1,
        },
    }

    merged = fitness_config.deep_merge_chain([override, root])

    assert merged["weights"]["data"] == 30
    assert merged["weights"]["reliability"] == 20
    assert merged["weights"]["architecture"] == 14
    assert sum(merged["weights"].values()) == 100


def test_deep_merge_chain_returns_only_root_when_chain_has_one():
    root = {"version": 1, "weights": {"data": 10, "architecture": 90}}

    merged = fitness_config.deep_merge_chain([root])

    assert merged["weights"]["data"] == 10
    assert merged["weights"]["architecture"] == 90


def test_deep_merge_chain_partial_override_inherits_unspecified_domains():
    root = {
        "version": 1,
        "weights": {"architecture": 50, "security": 30, "data": 20},
    }
    override = {
        "version": 1,
        "weights": {"data": 30},  # only redefines data
    }

    merged = fitness_config.deep_merge_chain([override, root])

    assert merged["weights"]["architecture"] == 50  # inherited
    assert merged["weights"]["security"] == 30      # inherited
    assert merged["weights"]["data"] == 30          # overridden


def test_deep_merge_chain_returns_empty_weights_when_chain_empty():
    merged = fitness_config.deep_merge_chain([])

    # No configs found -> caller will substitute defaults; merger returns empty.
    assert "weights" in merged
    assert merged["weights"] == {}


# ---------------------------------------------------------------------------
# Whole-replacement keys: statusThresholds, security, scoring (ADR-002).
# Override that sets one of these keys replaces it entirely; root is dropped.
# ---------------------------------------------------------------------------

def test_deep_merge_chain_status_thresholds_replace_as_whole():
    # Override sets only 'healthy'; per ADR-002 the entire statusThresholds
    # block from the override REPLACES root, not merges per sub-key.
    root = {
        "version": 1,
        "weights": {"data": 100},
        "statusThresholds": {
            "healthy": [8, 10],
            "needsAttention": [5, 7],
            "critical": [1, 4],
        },
    }
    override = {
        "version": 1,
        "statusThresholds": {"healthy": [9, 10]},
    }

    merged = fitness_config.deep_merge_chain([override, root])

    # Whole-replacement: only 'healthy' present from override; needsAttention/critical
    # do NOT leak from root.
    assert merged["statusThresholds"] == {"healthy": [9, 10]}


def test_deep_merge_chain_status_thresholds_inherit_when_override_silent():
    # Override does not set statusThresholds; root's whole block is inherited.
    root = {
        "version": 1,
        "statusThresholds": {
            "healthy": [8, 10],
            "needsAttention": [5, 7],
            "critical": [1, 4],
        },
    }
    override = {"version": 1, "weights": {"data": 100}}

    merged = fitness_config.deep_merge_chain([override, root])

    assert merged["statusThresholds"] == {
        "healthy": [8, 10], "needsAttention": [5, 7], "critical": [1, 4],
    }


def test_deep_merge_chain_security_replace_as_whole():
    root = {"version": 1, "security": {"confidenceThreshold": 7, "extra": "x"}}
    override = {"version": 1, "security": {"confidenceThreshold": 9}}

    merged = fitness_config.deep_merge_chain([override, root])

    # Whole-replace: 'extra' from root must NOT leak through.
    assert merged["security"] == {"confidenceThreshold": 9}


def test_deep_merge_chain_security_inherits_when_override_silent():
    root = {"version": 1, "security": {"confidenceThreshold": 7}}
    override = {"version": 1, "weights": {"data": 100}}

    merged = fitness_config.deep_merge_chain([override, root])

    assert merged["security"] == {"confidenceThreshold": 7}


def test_deep_merge_chain_scoring_replace_as_whole():
    root = {"version": 1, "scoring": {"goodRange": [8, 10], "badRange": [1, 3]}}
    override = {"version": 1, "scoring": {"goodRange": [9, 10]}}

    merged = fitness_config.deep_merge_chain([override, root])

    # Whole-replace: 'badRange' must not leak from root.
    assert merged["scoring"] == {"goodRange": [9, 10]}


def test_deep_merge_chain_independent_top_level_keys():
    # weights from override (per-domain merge) AND security from override
    # (whole replace) are independently merged with root.
    root = {
        "version": 1,
        "weights": {"architecture": 50, "security": 50},
        "security": {"confidenceThreshold": 7},
        "statusThresholds": {"healthy": [8, 10]},
    }
    override = {
        "version": 1,
        "security": {"confidenceThreshold": 9},
    }

    merged = fitness_config.deep_merge_chain([override, root])

    # weights: untouched by override -> inherited
    assert merged["weights"] == {"architecture": 50, "security": 50}
    # security: overridden as whole
    assert merged["security"] == {"confidenceThreshold": 9}
    # statusThresholds: inherited from root
    assert merged["statusThresholds"] == {"healthy": [8, 10]}


def test_deep_merge_chain_three_level_chain_nearest_wins():
    # When a chain has 3 entries (deepest, intermediate, root), the deepest
    # entry's per-key value should win the per-domain merge.
    root = {"version": 1, "weights": {"a": 1, "b": 1, "c": 1}}
    intermediate = {"version": 1, "weights": {"b": 2, "c": 2}}
    deepest = {"version": 1, "weights": {"c": 3}}

    merged = fitness_config.deep_merge_chain([deepest, intermediate, root])

    assert merged["weights"]["a"] == 1  # only root has it
    assert merged["weights"]["b"] == 2  # intermediate beats root
    assert merged["weights"]["c"] == 3  # deepest beats both


def test_deep_merge_chain_does_not_mutate_inputs():
    root = {"version": 1, "weights": {"a": 1, "b": 2}}
    override = {"version": 1, "weights": {"b": 20}}
    root_snapshot = {"version": 1, "weights": {"a": 1, "b": 2}}
    override_snapshot = {"version": 1, "weights": {"b": 20}}

    fitness_config.deep_merge_chain([override, root])

    # Purity: inputs unchanged after merge.
    assert root == root_snapshot
    assert override == override_snapshot
