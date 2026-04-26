"""Pure-function unit tests for the reporter: render_show_output.

The reporter takes a ResolutionResult-like input and produces the stdout text
that `show --path <target>` prints. It must:
  - Name the override as the highest-precedence source
  - Name the root as the next source
  - Use the phrasing "merged with root" when the chain has 2+ entries
  - Omit "merged with" phrasing when the chain has only the root (AC-03.4)
  - Emit an embedded JSON sentinel block with source_chain + effective config
  - Show "total <sum> OK" with all 10 domain weights inline
  - Sort the inline weights line descending by value, alpha-ties (AC-03.6)
  - Be deterministic across calls (AC-NFR-2)

render_show_output is pure: no filesystem, no print, returns a str.

Test count budget (per 2x distinct-behaviors rule):
  Behavior B8: render_show_output produces correct format incl. JSON sentinel
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from unit.fitness_config._loader import fitness_config


_FULL_WEIGHTS = {
    "architecture": 14, "security": 14, "reliability": 20, "testing": 10,
    "performance": 6, "algorithms": 4, "data": 30, "accessibility": 0,
    "process": 1, "maintainability": 1,
}


def _effective_with(weights: dict) -> dict:
    return {
        "version": 1,
        "weights": weights,
        "statusThresholds": dict(fitness_config.DEFAULT_STATUS),
        "security": dict(fitness_config.DEFAULT_SECURITY),
        "scoring": dict(fitness_config.DEFAULT_SCORING),
    }


# ---------------------------------------------------------------------------
# B8a: chain-shape-driven format variations (input-variation parametrization).
# Each case shares the SAME assertion logic: render_show_output produces the
# expected substrings (or excludes them) based on chain shape.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "case_id,chain_subpaths,expect_merged_phrase,expect_defaults_message",
    [
        # 2-entry chain: override + root -> "merged with" phrasing required.
        (
            "two_entry_chain_uses_merged_with_root_phrasing",
            ["infrastructure/modules/postgresql/fitness-config.json", "fitness-config.json"],
            True,
            False,
        ),
        # 1-entry chain: root only -> NO "merged with" phrasing (AC-03.4).
        (
            "single_entry_chain_omits_merged_phrasing",
            ["fitness-config.json"],
            False,
            False,
        ),
        # 0-entry chain: defaults message required, names that no config was found.
        (
            "empty_chain_emits_defaults_message",
            [],
            False,
            True,
        ),
    ],
)
def test_render_show_output_renders_chain_shape_variants(
    case_id: str,
    chain_subpaths: list[str],
    expect_merged_phrase: bool,
    expect_defaults_message: bool,
):
    chain = [Path(p) for p in chain_subpaths]
    weights = _FULL_WEIGHTS if chain else dict(fitness_config.DEFAULT_WEIGHTS)
    effective = _effective_with(weights)
    target = Path("infrastructure/modules/postgresql/main.tf") if chain else Path("anywhere/file.txt")

    text = fitness_config.render_show_output(
        target=target, source_chain=chain, effective=effective
    )

    if expect_merged_phrase:
        assert "merged with root" in text, f"case={case_id}"
        # And the highest-precedence source (override) appears before root.
        pg_idx = text.index("postgresql/fitness-config.json")
        root_idx = text.rindex("fitness-config.json")
        assert pg_idx < root_idx, f"case={case_id}: override must precede root"
    else:
        assert "merged with" not in text, f"case={case_id}"

    if expect_defaults_message:
        assert "built-in defaults" in text, f"case={case_id}"
        assert "no fitness-config.json found" in text, f"case={case_id}"
    else:
        # When configs ARE found, the rendered text must reference them.
        for sub in chain_subpaths:
            assert Path(sub).name in text, f"case={case_id}: {sub} not in output"


# ---------------------------------------------------------------------------
# B8b: JSON sentinel block — assertion is structural (parse + field-check),
# distinct from chain-shape variants because it parses the embedded JSON
# rather than searching substrings.
# ---------------------------------------------------------------------------

def test_render_show_output_emits_sentinel_json_block_with_chain_and_effective():
    chain = [
        Path("infrastructure/modules/postgresql/fitness-config.json"),
        Path("fitness-config.json"),
    ]
    effective = _effective_with(_FULL_WEIGHTS)

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


# ---------------------------------------------------------------------------
# B8c: inline weights line — total OK, all 10 domains present, deterministic
# sort order. One test asserts the contract because total/all-domains/sort
# are interlocking parts of the SAME inline-line behavior (AC-03.6).
# ---------------------------------------------------------------------------

def test_render_show_output_inline_weights_line_total_all_domains_and_sort_order():
    chain = [Path("fitness-config.json")]
    effective = _effective_with(dict(fitness_config.DEFAULT_WEIGHTS))

    text = fitness_config.render_show_output(
        target=Path("repo/file.py"),
        source_chain=chain,
        effective=effective,
    )

    # Total 100 with OK status appears in the rendered text.
    assert "100" in text
    assert "OK" in text

    # Exactly one inline "Effective weights:" line.
    inline_lines = [ln for ln in text.splitlines() if ln.startswith("Effective weights:")]
    assert len(inline_lines) == 1
    inline = inline_lines[0]

    # All 10 default domains present in the inline line.
    for domain in fitness_config.DEFAULT_WEIGHTS.keys():
        assert domain in inline, f"{domain} missing from inline weights line"

    # Deterministic sort: descending by value, alphabetical tie-break.
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
    """Determinism property: same inputs -> byte-identical output (AC-NFR-2)."""
    chain = [
        Path("infrastructure/modules/postgresql/fitness-config.json"),
        Path("fitness-config.json"),
    ]
    effective = _effective_with(_FULL_WEIGHTS)
    target = Path("infrastructure/modules/postgresql/main.tf")

    first = fitness_config.render_show_output(target=target, source_chain=chain, effective=effective)
    second = fitness_config.render_show_output(target=target, source_chain=chain, effective=effective)

    assert first == second, "render_show_output produced non-deterministic output"
