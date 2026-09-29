"""Pure-function unit tests for the merger: deep_merge_chain.

Per ADR-002, deep-merge merges per top-level key:
  - weights: per-domain merge (override wins for keys it sets)
  - statusThresholds, security, scoring: replace as wholes

Input: list[dict] of raw configs in precedence order (nearest-to-target first).
Output: dict with merged 'weights', 'statusThresholds', 'security', 'scoring'.

deep_merge_chain is pure: no filesystem, no mutation of inputs.

Test count budget (per 2x distinct-behaviors rule):
  Behavior B4: deep_merge_chain merges weights per-domain
  Behavior B5: deep_merge_chain replaces statusThresholds/security/scoring as wholes
"""

from __future__ import annotations

import pytest

from ._loader import resolution


# ---------------------------------------------------------------------------
# B4: weights merged per-domain; nearest entry wins per key.
# Parametrized over input-variation cases that share the SAME assertion
# logic: merged["weights"] equals expected.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "case_id,chain,expected_weights",
    [
        # Module override wins for the keys it specifies; root unaffected keys flow through.
        (
            "module_overrides_root_per_domain",
            [
                {"version": 1, "weights": {
                    "architecture": 14, "security": 14, "reliability": 20, "testing": 10,
                    "performance": 6, "algorithms": 4, "data": 30, "accessibility": 0,
                    "process": 1, "maintainability": 1,
                }},
                {"version": 1, "weights": {
                    "architecture": 14, "security": 14, "reliability": 10, "testing": 10,
                    "performance": 10, "algorithms": 10, "data": 10, "accessibility": 8,
                    "process": 8, "maintainability": 6,
                }},
            ],
            {
                "architecture": 14, "security": 14, "reliability": 20, "testing": 10,
                "performance": 6, "algorithms": 4, "data": 30, "accessibility": 0,
                "process": 1, "maintainability": 1,
            },
        ),
        # Single-entry chain: merged result equals that root's weights.
        (
            "single_entry_returns_root_weights",
            [{"version": 1, "weights": {"data": 10, "architecture": 90}}],
            {"data": 10, "architecture": 90},
        ),
        # Partial override: unspecified domains inherit from root.
        (
            "partial_override_inherits_unspecified_domains",
            [
                {"version": 1, "weights": {"data": 30}},
                {"version": 1, "weights": {"architecture": 50, "security": 30, "data": 20}},
            ],
            {"architecture": 50, "security": 30, "data": 30},
        ),
        # Empty chain: merger returns empty weights (caller substitutes defaults).
        ("empty_chain_returns_empty_weights", [], {}),
        # Three-level chain: nearest beats intermediate beats root, per-key.
        (
            "three_level_chain_nearest_wins_per_key",
            [
                {"version": 1, "weights": {"c": 3}},               # deepest
                {"version": 1, "weights": {"b": 2, "c": 2}},       # intermediate
                {"version": 1, "weights": {"a": 1, "b": 1, "c": 1}},  # root
            ],
            {"a": 1, "b": 2, "c": 3},
        ),
    ],
)
def test_deep_merge_chain_merges_weights_per_domain(
    case_id: str, chain: list[dict], expected_weights: dict
):
    merged = resolution.deep_merge_chain(chain)

    assert merged["weights"] == expected_weights, f"case={case_id}"


# ---------------------------------------------------------------------------
# B5: whole-replacement keys (statusThresholds, security, scoring).
# Parametrized over (key, override-replaces vs override-silent) variations
# that share the SAME assertion: merged[key] equals expected (no leak from root
# when overridden, full inherit when silent).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "case_id,key,root_block,override_block,expected",
    [
        # statusThresholds: override replaces as a whole — no leak from root.
        (
            "statusThresholds_replace_as_whole",
            "statusThresholds",
            {"healthy": [8, 10], "needsAttention": [5, 7], "critical": [1, 4]},
            {"healthy": [9, 10]},
            {"healthy": [9, 10]},
        ),
        # statusThresholds: override silent -> root block inherited intact.
        (
            "statusThresholds_inherit_when_override_silent",
            "statusThresholds",
            {"healthy": [8, 10], "needsAttention": [5, 7], "critical": [1, 4]},
            None,  # marker: override does NOT set this key
            {"healthy": [8, 10], "needsAttention": [5, 7], "critical": [1, 4]},
        ),
        # security: override replaces as a whole — 'extra' from root must NOT leak.
        (
            "security_replace_as_whole",
            "security",
            {"confidenceThreshold": 7, "extra": "x"},
            {"confidenceThreshold": 9},
            {"confidenceThreshold": 9},
        ),
        # security: override silent -> root inherited.
        (
            "security_inherit_when_override_silent",
            "security",
            {"confidenceThreshold": 7},
            None,
            {"confidenceThreshold": 7},
        ),
        # scoring: override replaces as a whole — 'badRange' must not leak.
        (
            "scoring_replace_as_whole",
            "scoring",
            {"goodRange": [8, 10], "badRange": [1, 3]},
            {"goodRange": [9, 10]},
            {"goodRange": [9, 10]},
        ),
    ],
)
def test_deep_merge_chain_whole_replacement_keys(
    case_id: str, key: str, root_block: dict, override_block: dict | None, expected: dict
):
    root = {"version": 1, "weights": {"data": 100}, key: root_block}
    if override_block is None:
        override = {"version": 1, "weights": {"data": 100}}
    else:
        override = {"version": 1, key: override_block}

    merged = resolution.deep_merge_chain([override, root])

    assert merged[key] == expected, f"case={case_id}"


def test_deep_merge_chain_independent_top_level_keys_compose_correctly():
    """Independent top-level keys merge independently per their per-key strategy."""
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

    merged = resolution.deep_merge_chain([override, root])

    assert merged["weights"] == {"architecture": 50, "security": 50}
    assert merged["security"] == {"confidenceThreshold": 9}
    assert merged["statusThresholds"] == {"healthy": [8, 10]}


def test_deep_merge_chain_does_not_mutate_inputs():
    """Purity contract: inputs unchanged after merge."""
    root = {"version": 1, "weights": {"a": 1, "b": 2}}
    override = {"version": 1, "weights": {"b": 20}}
    root_snapshot = {"version": 1, "weights": {"a": 1, "b": 2}}
    override_snapshot = {"version": 1, "weights": {"b": 20}}

    resolution.deep_merge_chain([override, root])

    assert root == root_snapshot
    assert override == override_snapshot


# ---------------------------------------------------------------------------
# B5b (mutation-testing gap): the chain may hold entries that are valid JSON
# but not objects (a file containing `[]` or `7`); the merge ignores them
# wherever they sit, and the version is the nearest declared one.
# ---------------------------------------------------------------------------

from hypothesis import given  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ._loader import model  # noqa: E402

_partial_configs = st.fixed_dictionaries({}, optional={
    "version": st.integers(0, 3),
    "weights": st.dictionaries(st.sampled_from(sorted(model.DEFAULT_WEIGHTS)), st.integers(0, 100)),
    "statusThresholds": st.just(dict(model.DEFAULT_STATUS)),
    "security": st.builds(lambda cutoff: {"confidenceThreshold": cutoff}, st.integers(1, 10)),
    "scoring": st.just(dict(model.DEFAULT_SCORING)),
})
_non_objects = st.one_of(st.none(), st.integers(), st.text(max_size=3),
                         st.lists(st.integers(), max_size=2))


@given(st.lists(_partial_configs, max_size=4), st.data())
def test_deep_merge_chain_ignores_non_object_entries_and_takes_the_nearest_version(chain, data):
    with_junk = list(chain)
    for _ in range(data.draw(st.integers(1, 3))):
        with_junk.insert(data.draw(st.integers(0, len(with_junk))), data.draw(_non_objects))

    merged = resolution.deep_merge_chain(with_junk)

    assert merged == resolution.deep_merge_chain(chain)
    declared = [cfg["version"] for cfg in chain if "version" in cfg]
    assert merged.get("version") == (declared[0] if declared else None)


# ---------------------------------------------------------------------------
# B5c (mutation-testing gap): legacy `show [path]` lays one file over the
# defaults -- all four sections, each the file's or the default, no version.
# ---------------------------------------------------------------------------

@given(_partial_configs)
def test_merge_defaults_fills_every_section_and_drops_the_version(config):
    shown = resolution.merge_defaults(config)

    assert list(shown) == list(model.SECTION_DEFAULTS)
    assert shown["weights"] == {**model.DEFAULT_WEIGHTS, **config.get("weights", {})}
    for section in ("statusThresholds", "security", "scoring"):
        assert shown[section] == config.get(section, model.SECTION_DEFAULTS[section])
