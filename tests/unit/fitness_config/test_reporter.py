"""Pure-function unit tests for the reporter: render_show_output.

The reporter takes a ResolutionResult-like input and produces the stdout text
that `show --path <target>` prints. It must:
  - Name the override as the highest-precedence source
  - Name the root as the next source
  - Use the phrasing "merged with root" when the chain has 2+ entries
  - Emit an embedded JSON sentinel block with source_chain + effective config
  - Show "total <sum> OK" with all 10 domain weights inline

render_show_output is pure: no filesystem, no print, returns a str.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "fitness-config.py"
_spec = importlib.util.spec_from_file_location("fitness_config", SCRIPT)
fitness_config = importlib.util.module_from_spec(_spec)
sys.modules["fitness_config"] = fitness_config
_spec.loader.exec_module(fitness_config)


_FULL_WEIGHTS = {
    "architecture": 14, "security": 14, "reliability": 20, "testing": 10,
    "performance": 6, "algorithms": 4, "data": 30, "accessibility": 0,
    "process": 1, "maintainability": 1,
}


def test_render_show_output_names_override_and_root_in_precedence_order():
    chain = [
        Path("infrastructure/modules/postgresql/fitness-config.json"),
        Path("fitness-config.json"),
    ]
    effective = {
        "version": 1,
        "weights": _FULL_WEIGHTS,
        "statusThresholds": {"healthy": [8, 10]},
        "security": {"confidenceThreshold": 7},
        "scoring": {"goodRange": [8, 10], "badRange": [1, 3]},
    }

    text = fitness_config.render_show_output(
        target=Path("infrastructure/modules/postgresql/main.tf"),
        source_chain=chain,
        effective=effective,
    )

    assert "postgresql/fitness-config.json" in text
    assert "merged with root" in text
    # Override should appear before root in the rendered text.
    pg_idx = text.index("postgresql/fitness-config.json")
    root_idx = text.rindex("fitness-config.json")
    assert pg_idx < root_idx


def test_render_show_output_emits_sentinel_json_block_with_chain_and_effective():
    chain = [
        Path("infrastructure/modules/postgresql/fitness-config.json"),
        Path("fitness-config.json"),
    ]
    effective = {
        "version": 1,
        "weights": _FULL_WEIGHTS,
        "statusThresholds": {"healthy": [8, 10]},
        "security": {"confidenceThreshold": 7},
        "scoring": {"goodRange": [8, 10], "badRange": [1, 3]},
    }

    text = fitness_config.render_show_output(
        target=Path("infrastructure/modules/postgresql/main.tf"),
        source_chain=chain,
        effective=effective,
    )

    begin = "<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->"
    end = "<!-- END_EFFECTIVE_CONFIG_JSON -->"
    assert begin in text
    assert end in text

    block = text.split(begin, 1)[1].split(end, 1)[0].strip()
    parsed = json.loads(block)
    assert parsed["effective"]["weights"]["data"] == 30
    assert parsed["effective"]["weights"]["reliability"] == 20
    assert parsed["source_chain"][0].endswith("postgresql/fitness-config.json")


def test_render_show_output_shows_total_100_with_OK_status():
    chain = [Path("fitness-config.json")]
    effective = {
        "version": 1,
        "weights": _FULL_WEIGHTS,
        "statusThresholds": {"healthy": [8, 10]},
        "security": {"confidenceThreshold": 7},
        "scoring": {"goodRange": [8, 10], "badRange": [1, 3]},
    }

    text = fitness_config.render_show_output(
        target=Path("repo/file.py"),
        source_chain=chain,
        effective=effective,
    )

    assert "100" in text
    assert "OK" in text
    # All 10 domains should appear somewhere in the rendered text.
    for domain in _FULL_WEIGHTS.keys():
        assert domain in text


def test_render_show_output_handles_empty_chain_with_defaults_message():
    effective = {
        "version": 1,
        "weights": dict(fitness_config.DEFAULT_WEIGHTS),
        "statusThresholds": dict(fitness_config.DEFAULT_STATUS),
        "security": dict(fitness_config.DEFAULT_SECURITY),
        "scoring": dict(fitness_config.DEFAULT_SCORING),
    }

    text = fitness_config.render_show_output(
        target=Path("anywhere/file.txt"),
        source_chain=[],
        effective=effective,
    )

    assert "built-in defaults" in text
    assert "no fitness-config.json found" in text
