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

import json
from pathlib import Path

from unit.fitness_config._loader import fitness_config


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


# ---------------------------------------------------------------------------
# Milestone-3 provenance reporting — explicit pure-function unit tests
# ---------------------------------------------------------------------------

def test_render_show_output_single_entry_chain_omits_merged_phrasing():
    """1-entry chain: root only — no "merged with" phrasing per AC-03.4."""
    chain = [Path("fitness-config.json")]
    effective = {
        "version": 1,
        "weights": dict(fitness_config.DEFAULT_WEIGHTS),
        "statusThresholds": dict(fitness_config.DEFAULT_STATUS),
        "security": dict(fitness_config.DEFAULT_SECURITY),
        "scoring": dict(fitness_config.DEFAULT_SCORING),
    }

    text = fitness_config.render_show_output(
        target=Path("src/somefile.py"),
        source_chain=chain,
        effective=effective,
    )

    # Contract: when only the root config applies, the human-readable header
    # MUST NOT use the "merged with..." phrasing reserved for 2+-entry chains.
    assert "merged with" not in text
    # And the root file must still be named.
    assert "fitness-config.json" in text


def test_render_show_output_inline_weights_line_lists_all_ten_domains():
    """Inline effective-weights line lists all 10 domains per AC-03.6."""
    chain = [Path("fitness-config.json")]
    effective = {
        "version": 1,
        "weights": dict(fitness_config.DEFAULT_WEIGHTS),
        "statusThresholds": dict(fitness_config.DEFAULT_STATUS),
        "security": dict(fitness_config.DEFAULT_SECURITY),
        "scoring": dict(fitness_config.DEFAULT_SCORING),
    }

    text = fitness_config.render_show_output(
        target=Path("repo/file.py"),
        source_chain=chain,
        effective=effective,
    )

    inline_lines = [ln for ln in text.splitlines() if ln.startswith("Effective weights:")]
    assert len(inline_lines) == 1, "expected exactly one inline Effective weights line"
    inline = inline_lines[0]
    for domain in fitness_config.DEFAULT_WEIGHTS.keys():
        assert domain in inline, f"{domain} missing from inline weights line"


def test_render_show_output_sorts_descending_with_alphabetical_tiebreak():
    """Deterministic sort: descending by value, alphabetical for ties (AC-03.6)."""
    # Crafted weights to produce ties at multiple buckets:
    #   architecture, security  -> 14 (tie -> alpha: architecture < security)
    #   reliability, testing, performance, algorithms, data -> 10 (tie -> alpha)
    #   accessibility, process -> 8 (tie -> alpha)
    #   maintainability -> 6
    chain = [Path("fitness-config.json")]
    effective = {
        "version": 1,
        "weights": dict(fitness_config.DEFAULT_WEIGHTS),
        "statusThresholds": dict(fitness_config.DEFAULT_STATUS),
        "security": dict(fitness_config.DEFAULT_SECURITY),
        "scoring": dict(fitness_config.DEFAULT_SCORING),
    }

    text = fitness_config.render_show_output(
        target=Path("repo/file.py"),
        source_chain=chain,
        effective=effective,
    )

    inline = next(ln for ln in text.splitlines() if ln.startswith("Effective weights:"))
    expected_order = [
        "architecture", "security",                                  # 14, alpha tie
        "algorithms", "data", "performance", "reliability", "testing",  # 10, alpha tie
        "accessibility", "process",                                  # 8, alpha tie
        "maintainability",                                           # 6
    ]
    positions = [inline.index(d) for d in expected_order]
    assert positions == sorted(positions), (
        f"domains not in (desc value, alpha) order. "
        f"expected {expected_order} positions={positions}"
    )


def test_render_show_output_is_byte_identical_across_two_calls():
    """Determinism: same inputs -> byte-identical output (AC-NFR-2 / property)."""
    chain = [
        Path("infrastructure/modules/postgresql/fitness-config.json"),
        Path("fitness-config.json"),
    ]
    effective = {
        "version": 1,
        "weights": _FULL_WEIGHTS,
        "statusThresholds": dict(fitness_config.DEFAULT_STATUS),
        "security": dict(fitness_config.DEFAULT_SECURITY),
        "scoring": dict(fitness_config.DEFAULT_SCORING),
    }
    target = Path("infrastructure/modules/postgresql/main.tf")

    first = fitness_config.render_show_output(target=target, source_chain=chain, effective=effective)
    second = fitness_config.render_show_output(target=target, source_chain=chain, effective=effective)

    assert first == second, "render_show_output produced non-deterministic output"
