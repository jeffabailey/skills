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

import hashlib
import json
from pathlib import Path

import pytest

from ._loader import fitness_config


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


# ---------------------------------------------------------------------------
# Behavior R5: canonical renderer (data-models section 2). The rendered text
# is the byte-exact write payload: canonical key order, 2-space indent,
# inline two-element ranges, LF, trailing newline. Input key order and
# formatting never change the bytes, so the fingerprint is stable.
# ---------------------------------------------------------------------------

from hypothesis import given  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from .test_validator import complete_configs  # noqa: E402

_EXAMPLE_CONFIG = Path(__file__).resolve().parents[3] / "fitness-config.example.json"


def _reordered(value, rng):
    """Same config, keys shuffled at every level."""
    if isinstance(value, dict):
        keys = list(value)
        rng.shuffle(keys)
        return {key: _reordered(value[key], rng) for key in keys}
    return value


@given(complete_configs(), st.randoms(use_true_random=False))
def test_canonical_rendering_roundtrips_and_ignores_input_key_order(config, rng):
    rendered = fitness_config.render_canonical(config)
    assert json.loads(rendered) == config
    assert fitness_config.render_canonical(_reordered(config, rng)) == rendered
    assert list(json.loads(rendered)) == ["version", "weights", "statusThresholds", "security", "scoring"]
    assert rendered.endswith("}\n") and "\r" not in rendered
    assert fitness_config.proposal_fingerprint(rendered) == hashlib.sha256(rendered.encode()).hexdigest()[:12]


def test_canonical_rendering_of_the_defaults_is_the_example_file():
    # bypass: golden-master fitness function (data-models section 2) -- one
    # fixed input by definition; the property above covers the input domain.
    defaults = fitness_config.build_seed_config([])
    rendered = fitness_config.render_canonical(defaults)
    assert rendered == _EXAMPLE_CONFIG.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Behavior R6: fingerprint identity (AC-03.2). The dry run's observables
# (status, canonical bytes, fingerprint) depend only on the config's meaning,
# never on key order or whitespace, and the fingerprint separates exactly the
# configs whose canonical bytes differ.
# ---------------------------------------------------------------------------

from .test_write_gate import state_delta  # noqa: E402

_DRY_RUN_UNIVERSE = {"status", "canonical", "fingerprint"}


def _dry_run_observables(proposal_text: str) -> dict:
    outcome = fitness_config.check_proposal(proposal_text, config_exists=False)
    return {"status": outcome.status, "canonical": outcome.canonical, "fingerprint": outcome.fingerprint}


@given(complete_configs(), st.randoms(use_true_random=False), st.sampled_from([None, 1, 4, "\t"]))
def test_semantically_equal_proposals_show_the_same_bytes_and_fingerprint(config, rng, indent):
    canonical = fitness_config.render_canonical(config)
    reformatted = json.dumps(_reordered(json.loads(canonical), rng), indent=indent)
    before = _dry_run_observables(canonical)
    state_delta.assert_state_delta(before, _dry_run_observables(reformatted), _DRY_RUN_UNIVERSE, {})
    assert before["canonical"] == canonical  # render(parse(render(c))) == render(c)


@given(complete_configs(), complete_configs())
def test_fingerprints_match_exactly_when_the_saved_bytes_match(first, second):
    first_bytes, second_bytes = map(fitness_config.render_canonical, (first, second))
    same_fingerprint = (fitness_config.proposal_fingerprint(first_bytes)
                        == fitness_config.proposal_fingerprint(second_bytes))
    assert same_fingerprint == (first_bytes == second_bytes)


# ---------------------------------------------------------------------------
# Behavior R7: review before replace (AC-04.1, AC-04.4, data-models 6.1).
# The dry run against a current config lists value changes by dot-joined leaf
# path (a two-element range is one leaf), canonical order first, then keys the
# format does not know shown as removed.  An equal current config shows no
# changes; applying the listed changes to the current config yields exactly
# the proposal.
# ---------------------------------------------------------------------------

_REVIEW_UNIVERSE = {"status", "canonical", "fingerprint", "review"}
_TUNING_VALUES = 16  # every leaf of a complete config except its schema version

unknown_notes = st.dictionaries(st.sampled_from(["$comment", "owner", "tunedBy"]),
                                st.text(max_size=12), max_size=2)


def _review_observables(proposal_text: str, current: bytes | None) -> dict:
    outcome = fitness_config.check_proposal(proposal_text, current is not None, current)
    return {"status": outcome.status, "canonical": outcome.canonical,
            "fingerprint": outcome.fingerprint, "review": outcome.review}


@given(complete_configs(), st.randoms(use_true_random=False), st.sampled_from([None, 2, "\t"]))
def test_a_current_config_equal_to_the_proposal_shows_no_changes(config, rng, indent):
    text = fitness_config.render_canonical(config)
    current = json.dumps(_reordered(config, rng), indent=indent).encode("utf-8")
    state_delta.assert_state_delta(
        _review_observables(text, None), _review_observables(text, current), _REVIEW_UNIVERSE, {
            "status": state_delta.Predicate("unchanged", lambda _, now: now == "unchanged"),
            "review": state_delta.Predicate(
                "no changes", lambda _, now: now == (f"({_TUNING_VALUES} values unchanged)",)),
        })


def _apply_changes(config: dict, changes) -> dict:
    result = json.loads(json.dumps(config))
    for path, _, after in changes:
        *parents, leaf = path.split(".")
        section = result
        for key in parents:
            section = section.setdefault(key, {})
        if after is fitness_config.MISSING:
            section.pop(leaf)
        else:
            section[leaf] = after
    return result


@given(complete_configs(), complete_configs(), unknown_notes, unknown_notes)
def test_applying_the_listed_changes_to_the_current_config_yields_the_proposal(
        current, proposal, top_notes, weight_notes):
    current = {**top_notes, **current, "weights": {**current["weights"], **weight_notes}}
    diff = fitness_config.value_diff(current, proposal)
    assert _apply_changes(current, diff.changes) == proposal
    removed = [after is fitness_config.MISSING for _, _, after in diff.changes]
    assert removed == sorted(removed), "keys the format does not know come last"
    changed_tuning_values = [path for path, _, after in diff.changes
                             if after is not fitness_config.MISSING and path != "version"]
    assert diff.unchanged == _TUNING_VALUES - len(changed_tuning_values)
