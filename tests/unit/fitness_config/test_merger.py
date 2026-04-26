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
