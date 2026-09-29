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

from ._loader import audit, model, validation


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
    result = validation.validate_effective(
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

    result = validation.validate_effective(
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

    result = validation.validate_effective(cfg, source_chain=[])

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

    result = validation.validate_schema_versions(raw_configs, source_chain=chain)

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

DOMAINS = list(model.DEFAULT_WEIGHTS)


@st.composite
def weights_summing_to_100(draw) -> dict:
    cuts = sorted(draw(st.lists(st.integers(0, 100), min_size=9, max_size=9)))
    bounds = [0, *cuts, 100]
    return {domain: bounds[i + 1] - bounds[i] for i, domain in enumerate(DOMAINS)}


def score_ranges() -> st.SearchStrategy:
    return st.tuples(st.integers(1, 10), st.integers(1, 10)).map(lambda pair: sorted(pair))


@st.composite
def contiguous_status_bands(draw) -> dict:
    """Any split of 1-10 into critical < needsAttention < healthy, each non-empty (BR-6)."""
    low_cut, high_cut = sorted(draw(st.lists(st.integers(1, 9), min_size=2, max_size=2, unique=True)))
    return {"healthy": [high_cut + 1, 10], "needsAttention": [low_cut + 1, high_cut],
            "critical": [1, low_cut]}


@st.composite
def complete_configs(draw) -> dict:
    """Every proposal the write gate must accept."""
    return {
        "version": 1,
        "weights": draw(weights_summing_to_100()),
        "statusThresholds": draw(contiguous_status_bands()),
        "security": {"confidenceThreshold": draw(st.integers(1, 10))},
        "scoring": {key: draw(score_ranges()) for key in model.DEFAULT_SCORING},
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
    assert validation.validate_proposal(config) == []


@given(
    complete_configs(),
    st.sampled_from(sorted(INCOMPLETENESS)),
    st.sampled_from(DOMAINS),
    st.sampled_from(["weights", "statusThresholds", "security", "scoring"]),
)
def test_any_incomplete_proposal_is_rejected_with_a_reason(config, flaw, domain, section):
    broken = INCOMPLETENESS[flaw](config, domain, section)
    errors = validation.validate_proposal(broken)
    assert errors, f"{flaw} accepted: {broken}"
    assert all(isinstance(line, str) and line for line in errors)


# ---------------------------------------------------------------------------
# Behavior B9: per-file strict validation (ADR-008 Decision 1).
# Driving port: validate_config(data) -> list[str]  (every violation, as data).
# Universe: the config handed in (never mutated) and the violations reported.
# Partial overrides stay valid on their own; the weights sum is checked only
# when the file lists every domain (the merged sum is validate_effective's job).
# ---------------------------------------------------------------------------

import copy  # noqa: E402
import importlib.util  # noqa: E402
import sys  # noqa: E402

if "fci_state_delta" not in sys.modules:
    _spec = importlib.util.spec_from_file_location(
        "fci_state_delta", Path(__file__).resolve().parents[2]
        / "acceptance" / "fitness-config-init" / "steps" / "fci_state_delta.py")
    sys.modules["fci_state_delta"] = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(sys.modules["fci_state_delta"])
state_delta = sys.modules["fci_state_delta"]


def is_(value) -> "state_delta.Predicate":
    return state_delta.Predicate(f"== {value!r}", lambda before, after: after == value)


VALIDATION_UNIVERSE = {"config", "violations"}
SECTIONS = ["weights", "statusThresholds", "security", "scoring"]


def run_validate_config(config) -> tuple[dict, dict]:
    before = {"config": copy.deepcopy(config), "violations": None}
    violations = validation.validate_config(config)
    return before, {"config": config, "violations": violations}


def naming_each(words) -> state_delta.Predicate:
    return state_delta.Predicate(
        f"a violation naming each of {sorted(words)}",
        lambda before, after: all(any(word in line for line in after) for word in words))


@st.composite
def partial_overrides(draw) -> dict:
    """A complete config with any sections and any weight domains left out."""
    config = draw(complete_configs())
    kept_domains = draw(st.sets(st.sampled_from(DOMAINS)))
    kept_sections = draw(st.sets(st.sampled_from(SECTIONS)))
    trimmed = {**config, "weights": {domain: value for domain, value in config["weights"].items()
                                     if domain in kept_domains}}
    return {"version": 1, **{name: trimmed[name] for name in kept_sections}}


@given(st.one_of(complete_configs(), partial_overrides()))
def test_every_complete_config_and_partial_override_validates_alone(config):
    before, after = run_validate_config(config)
    state_delta.assert_state_delta(before, after, VALIDATION_UNIVERSE, {"violations": is_([])})


def _set(config: dict, section: str, key: str, value) -> dict:
    return {**config, section: {**config[section], key: value}}


FLAWS = {
    "unknown domain": lambda cfg, domain: (_set(cfg, "weights", f"{domain}-typo", 0), f"{domain}-typo"),
    "yes-or-no weight": lambda cfg, domain: (_set(cfg, "weights", domain, True), domain),
    "weight below 0": lambda cfg, domain: (_set(cfg, "weights", domain, -1), domain),
    "weight above 100": lambda cfg, domain: (_set(cfg, "weights", domain, 101), domain),
    "wordy cutoff": lambda cfg, domain: (_set(cfg, "security", "confidenceThreshold", "high"),
                                         "confidenceThreshold"),
    "cutoff out of range": lambda cfg, domain: (_set(cfg, "security", "confidenceThreshold", 11),
                                                "confidenceThreshold"),
    "three-number band": lambda cfg, domain: (_set(cfg, "statusThresholds", "healthy", [8, 9, 10]),
                                              "healthy"),
    "range as text": lambda cfg, domain: (_set(cfg, "scoring", "goodRange", "8-10"), "goodRange"),
    "one-number range": lambda cfg, domain: (_set(cfg, "scoring", "badRange", [3]), "badRange"),
    "version 2": lambda cfg, domain: ({**cfg, "version": 2}, "version"),
    "version 0": lambda cfg, domain: ({**cfg, "version": 0}, "version"),
}


@given(complete_configs(), st.sets(st.sampled_from(sorted(FLAWS)), min_size=1, max_size=4),
       st.sampled_from(DOMAINS))
def test_every_flaw_in_a_config_is_named_in_its_violations(config, flaws, domain):
    named = set()
    for flaw in sorted(flaws):
        config, word = FLAWS[flaw](config, domain)
        named.add(word)
    before, after = run_validate_config(config)
    state_delta.assert_state_delta(before, after, VALIDATION_UNIVERSE, {"violations": naming_each(named)})


@given(complete_configs(), st.sampled_from(DOMAINS), st.integers(1, 50))
def test_a_complete_weights_table_off_100_names_its_total_and_100(config, domain, extra):
    unbalanced = _set(config, "weights", domain, config["weights"][domain] + extra)
    total = sum(unbalanced["weights"].values())
    before, after = run_validate_config(unbalanced)
    state_delta.assert_state_delta(before, after, VALIDATION_UNIVERSE,
                                   {"violations": naming_each({str(total), "100"})})


json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text(max_size=8),
    lambda inner: st.lists(inner, max_size=3) | st.dictionaries(st.text(max_size=8), inner, max_size=3),
    max_leaves=10)


@given(complete_configs(), st.sampled_from([*SECTIONS, None]),
       json_values)
def test_any_json_in_any_slot_is_answered_with_violations_not_a_crash(config, section, junk):
    candidate = junk if section is None else {**config, section: junk}
    before, after = run_validate_config(candidate)
    state_delta.assert_state_delta(before, after, VALIDATION_UNIVERSE, {
        "violations": state_delta.Predicate(
            "a list of message lines",
            lambda was, now: isinstance(now, list) and all(isinstance(line, str) for line in now)),
    })


# ---------------------------------------------------------------------------
# Behavior B10: the config audit covers the fitness-config-init guide (BR-2).
# Driving port: cmd_audit(repo_root) -> exit code, offenders named on stderr.
# Universe: the guide on disk (never touched), the exit code, the guide lines
# the audit names, and how many files it says it scanned.
# ---------------------------------------------------------------------------

import contextlib  # noqa: E402
import io  # noqa: E402
import re  # noqa: E402
import tempfile  # noqa: E402

AUDIT_UNIVERSE = {"guide", "exit_code", "named_lines", "scanned"}
INIT_GUIDE = Path("skills") / "fitness-config-init" / "SKILL.md"

prose_lines = st.text(alphabet="abcdefghijklmnopqrstuvwxyz ,", max_size=60)


@st.composite
def inline_weight_objects(draw) -> str:
    gap = draw(st.sampled_from(["", " ", "  ", "\t"]))
    return f'{{ "weights"{gap}:{gap}{{ "{draw(st.sampled_from(DOMAINS))}": {draw(st.integers(1, 100))} }} }}'


@st.composite
def direct_config_reads(draw) -> str:
    name = "fitness-config" + ".json"
    return draw(st.sampled_from([
        f'cfg = json.load(open("{name}"))',
        f"with open('{name}') as handle:",
        f"data = json.loads(Path('{name}').read_text())",
    ]))


def run_audit_on_guide(guide_text: str) -> tuple[dict, dict]:
    with tempfile.TemporaryDirectory() as root:
        guide = Path(root) / INIT_GUIDE
        guide.parent.mkdir(parents=True)
        guide.write_text(guide_text, encoding="utf-8")
        before = {"guide": guide_text, "exit_code": None, "named_lines": set(), "scanned": None}
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = audit.cmd_audit(Path(root))
        named = {int(n) for n in re.findall(r"fitness-config-init/SKILL\.md:(\d+):", err.getvalue())}
        scanned = re.search(r"scanned (\d+)", out.getvalue())
        after = {"guide": guide.read_text(encoding="utf-8"), "exit_code": code,
                 "named_lines": named, "scanned": int(scanned.group(1)) if scanned else None}
    return before, after


@given(st.lists(prose_lines, max_size=12), st.one_of(inline_weight_objects(), direct_config_reads()),
       st.data())
def test_any_init_guide_with_a_weight_table_or_direct_config_read_fails_the_audit(prose, offence, data):
    position = data.draw(st.integers(0, len(prose)))
    lines = [*prose[:position], offence, *prose[position:]]
    before, after = run_audit_on_guide("\n".join(lines) + "\n")
    state_delta.assert_state_delta(before, after, AUDIT_UNIVERSE, {
        "exit_code": is_(1),
        "named_lines": is_({position + 1}),
    })


@given(st.lists(prose_lines, max_size=12))
def test_a_clean_init_guide_is_scanned_and_passes_the_audit(prose):
    before, after = run_audit_on_guide("\n".join(prose) + "\n")
    state_delta.assert_state_delta(before, after, AUDIT_UNIVERSE, {
        "exit_code": is_(0),
        "scanned": is_(1),
    })


# ---------------------------------------------------------------------------
# Behavior B10: status bands cover 1-10 contiguously, without overlap (BR-6).
# A write-bound completeness rule (ADR-008 Decision 2): validate_proposal
# rejects a gap or an overlap naming the status bands; validate_config keeps
# accepting the same bands in a partial override.
# ---------------------------------------------------------------------------

PROPOSAL_UNIVERSE = {"proposal", "violations"}
BAND_ORDER = ["critical", "needsAttention", "healthy"]


def run_validate_proposal(proposal) -> tuple[dict, dict]:
    before = {"proposal": copy.deepcopy(proposal), "violations": None}
    violations = validation.validate_proposal(proposal)
    return before, {"proposal": proposal, "violations": violations}


@given(complete_configs())
def test_any_contiguous_split_of_1_to_10_into_status_bands_is_accepted(config):
    before, after = run_validate_proposal(config)
    state_delta.assert_state_delta(before, after, PROPOSAL_UNIVERSE, {"violations": is_([])})


def _move_band_edge(bands: dict, band: str, edge: int, shift: int) -> dict:
    moved = list(bands[band])
    moved[edge] += shift
    return {**bands, band: moved}


@given(complete_configs(), st.sampled_from(BAND_ORDER), st.sampled_from([0, 1]),
       st.sampled_from([-1, 1]))
def test_any_gap_or_overlap_in_the_status_bands_is_rejected_naming_status(config, band, edge, shift):
    bands = _move_band_edge(config["statusThresholds"], band, edge, shift)
    broken = {**config, "statusThresholds": bands}
    before, after = run_validate_proposal(broken)
    state_delta.assert_state_delta(before, after, PROPOSAL_UNIVERSE,
                                   {"violations": naming_each({"statusThresholds"})})


# ---------------------------------------------------------------------------
# Mutation-testing gaps (DELIVER phase 5).
#   B8b: a complete proposal with exactly one completeness flaw gets exactly
#        one violation, naming that flaw (a missing key is not also "unknown";
#        an unknown weight domain is reported once; a reversed scoring range
#        is caught even though the bands still tile).
#   B7b: the version-mismatch fix advice fits the chain: older configs only,
#        newer configs only, or both.
#   B6b: an effective sum off 100 is blamed first on the nearest chain file.
#   B7c: the chain version check sees every entry: non-object entries hide
#        nothing, a version that is not an integer is a mismatch, and every
#        integer version is listed.
#   B9b: a complete weights table off 100 is named even beside an unknown
#        domain, and a total of 200 is not mistaken for 100.
#   B10c: a gap or overlap in the status bands shows each band as given.
#   B10b: an audited file the audit cannot read (not UTF-8, or a folder in
#        place of SKILL.md) is skipped, never a crash.
# ---------------------------------------------------------------------------

FIXED_KEY_SECTIONS = ["statusThresholds", "security", "scoring"]


def exactly_one_violation_naming(*words) -> state_delta.Predicate:
    return state_delta.Predicate(
        f"exactly one violation, naming {list(words)}",
        lambda before, after: len(after) == 1 and all(word in after[0] for word in words))


@st.composite
def proposals_with_one_completeness_flaw(draw) -> tuple[dict, tuple[str, ...]]:
    config = draw(complete_configs())
    flaw = draw(st.sampled_from(["missing key", "unknown key", "unknown domain", "reversed range"]))
    if flaw == "unknown domain":
        domain = draw(st.sampled_from(DOMAINS))
        return _set(config, "weights", f"{domain}-typo", 0), (f"weights.{domain}-typo", "not a known domain")
    if flaw == "missing key":
        section = draw(st.sampled_from(FIXED_KEY_SECTIONS))
        key = draw(st.sampled_from(sorted(config[section])))
        trimmed = {name: value for name, value in config[section].items() if name != key}
        return {**config, section: trimmed}, (f"'{section}' is missing", key)
    if flaw == "unknown key":
        section = draw(st.sampled_from(FIXED_KEY_SECTIONS))
        return _set(config, section, "notes", "tuned in June"), (f"'{section}' has unknown keys", "notes")
    key = draw(st.sampled_from(sorted(model.DEFAULT_SCORING)))
    low, high = draw(st.lists(st.integers(1, 10), min_size=2, max_size=2, unique=True).map(sorted))
    return _set(config, "scoring", key, [high, low]), (f"scoring.{key}", "low end first")


@given(proposals_with_one_completeness_flaw())
def test_a_proposal_with_one_completeness_flaw_gets_exactly_the_violation_naming_it(flawed):
    proposal, named = flawed
    before, after = run_validate_proposal(proposal)
    state_delta.assert_state_delta(before, after, PROPOSAL_UNIVERSE,
                                   {"violations": exactly_one_violation_naming(*named)})


FIX_ADVICE = {
    "older only": "upgrade the older config(s)",
    "newer only": "upgrade tooling to support the newer schema",
    "older and newer": "align every config",
}


@given(st.lists(st.integers(-2, 4), min_size=1, max_size=4).filter(
    lambda versions: any(version != model.SUPPORTED_SCHEMA_VERSION for version in versions)))
def test_the_version_mismatch_fix_advice_fits_the_versions_in_the_chain(versions):
    chain = [Path(f"level{depth}") / "fitness-config.json" for depth in range(len(versions))]
    has_older = any(version < model.SUPPORTED_SCHEMA_VERSION for version in versions)
    has_newer = any(version > model.SUPPORTED_SCHEMA_VERSION for version in versions)
    kind = ("older and newer" if has_older and has_newer
            else "older only" if has_older else "newer only")

    result = validation.validate_schema_versions([{"version": v} for v in versions], chain)

    assert result.ok is False
    advice = result.errors[-1]
    assert FIX_ADVICE[kind] in advice, f"{versions}: {advice}"
    assert not any(other in advice for name, other in FIX_ADVICE.items() if name != kind), advice


def test_an_audited_file_that_cannot_be_read_is_skipped_without_crashing():
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        not_utf8 = root / "skills" / "review-latin1" / "SKILL.md"
        not_utf8.parent.mkdir(parents=True)
        not_utf8.write_bytes('caf\xe9 { "weights": { "data": 10 } }\n'.encode("latin-1"))
        (root / "skills" / "review-folder" / "SKILL.md").mkdir(parents=True)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = audit.cmd_audit(root)

    assert (code, err.getvalue()) == (0, "")
    assert "scanned 2" in out.getvalue()


@given(st.lists(st.text(alphabet="abcdef", min_size=1, max_size=5), min_size=1, max_size=4, unique=True),
       st.integers(1, 30))
def test_an_effective_sum_off_100_names_the_nearest_chain_file_first(folders, shortfall):
    chain = [Path(folder) / "fitness-config.json" for folder in folders]
    weights = {**model.DEFAULT_WEIGHTS, "architecture": model.DEFAULT_WEIGHTS["architecture"] - shortfall}

    result = validation.validate_effective(_effective_with_weights(weights), chain)

    assert result.ok is False
    assert result.errors[0].startswith(f"Effective weights from {chain[0]} sum to")


@st.composite
def version_chains(draw) -> list:
    """Chain entries, nearest first: configs declaring an integer version,
    configs declaring something else, and entries that are not objects."""
    entries = draw(st.lists(st.one_of(
        st.integers(-1, 3).map(lambda version: {"version": version}),
        st.one_of(st.text(max_size=3), st.floats(allow_nan=False), st.none())
        .map(lambda version: {"version": version}),
        st.one_of(st.integers(), st.lists(st.integers(), max_size=2), st.text(max_size=3)),
    ), min_size=1, max_size=6))
    return entries


@given(version_chains())
def test_the_chain_version_check_sees_every_entry(entries):
    chain = [Path(f"level{depth}") / "fitness-config.json" for depth in range(len(entries))]
    configs = [entry for entry in entries if isinstance(entry, dict)]
    integer_declared = [(path, entry["version"]) for path, entry in zip(chain, entries)
                        if isinstance(entry, dict) and type(entry["version"]) is int]
    supported = all(type(cfg["version"]) is int and cfg["version"] == model.SUPPORTED_SCHEMA_VERSION
                    for cfg in configs)

    result = validation.validate_schema_versions(entries, chain)

    assert result.ok is supported
    if not supported:
        for path, version in integer_declared:
            assert f"  - {path} declares version {version}" in result.errors, result.errors


@given(complete_configs(), st.sampled_from(DOMAINS), st.one_of(st.integers(1, 50), st.just(100)))
def test_a_complete_weights_table_off_100_is_named_beside_an_unknown_domain(config, domain, extra):
    unbalanced = _set(config, "weights", domain, config["weights"][domain] + extra)
    with_typo = _set(unbalanced, "weights", f"{domain}-typo", 0)
    total = sum(unbalanced["weights"].values())
    before, after = run_validate_config(with_typo)
    state_delta.assert_state_delta(before, after, VALIDATION_UNIVERSE,
                                   {"violations": naming_each({f"add up to {total}", f"{domain}-typo"})})


@given(complete_configs(), st.sampled_from(BAND_ORDER), st.sampled_from([0, 1]),
       st.sampled_from([-1, 1]))
def test_a_gap_or_overlap_in_the_status_bands_shows_each_band_as_given(config, band, edge, shift):
    bands = _move_band_edge(config["statusThresholds"], band, edge, shift)
    before, after = run_validate_proposal({**config, "statusThresholds": bands})
    shown = [f"{name} {low}-{high}" for name, (low, high) in ((name, bands[name]) for name in BAND_ORDER)]
    state_delta.assert_state_delta(before, after, PROPOSAL_UNIVERSE, {"violations": naming_each(shown)})
