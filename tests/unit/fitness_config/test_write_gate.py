"""Property tests for the write gate, create path (ADR-010, data-models 6.2).

Driving port:
  save_new_proposal(proposal_text, expected_fingerprint, create_file) -> GateOutcome
  check_proposal(proposal_text, config_exists) -> GateOutcome
Driven port (injected): CreateFile = bytes -> bool  (False = file already there)

The universe is the fake project folder the injected writer controls, plus
the gate's reported status. Every test asserts the state delta over that
whole universe (strict: every slot not expected to change must be unchanged).

Behaviors (budget 2 x 5 = 10; 5 properties here):
  G1 a reviewed proposal is created byte-for-byte as checked
  G2 a fingerprint that is not the proposal's writes nothing
  G3 an existing config is never overwritten on the create path
  G4 an invalid proposal writes nothing
  G5 the chain starts inside the anchor (target == anchor reads nothing above)
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from ._loader import fitness_config
from .test_validator import complete_configs

_STATE_DELTA = (Path(__file__).resolve().parents[2]
                / "acceptance" / "fitness-config-init" / "steps" / "fci_state_delta.py")
if "fci_state_delta" in sys.modules:
    state_delta = sys.modules["fci_state_delta"]
else:
    _spec = importlib.util.spec_from_file_location("fci_state_delta", _STATE_DELTA)
    state_delta = importlib.util.module_from_spec(_spec)
    sys.modules["fci_state_delta"] = state_delta
    _spec.loader.exec_module(state_delta)

CONFIG = "fitness-config.json"
NEIGHBOUR = "README.md"


def project_folder(existing_config: bytes | None) -> dict:
    """Fake project folder: file name -> bytes."""
    folder = {NEIGHBOUR: b"# ledgerd\n"}
    if existing_config is not None:
        folder[CONFIG] = existing_config
    return folder


def exclusive_creator(folder: dict):
    """Pure-function stand-in for the exclusive-create adapter."""
    def create_file(data: bytes) -> bool:
        if CONFIG in folder:
            return False
        folder[CONFIG] = data
        return True
    return create_file


def universe_snapshot(folder: dict, outcome=None) -> dict:
    return {CONFIG: folder.get(CONFIG), NEIGHBOUR: folder.get(NEIGHBOUR),
            "status": None if outcome is None else outcome.status}


def formatted(config: dict, indent) -> str:
    return json.dumps(config, indent=indent)


UNIVERSE = {CONFIG, NEIGHBOUR, "status"}
indents = st.sampled_from([None, 2, 4])


def is_(value):
    return state_delta.Predicate(f"== {value!r}", lambda before, after: after == value)


def run_save(folder: dict, proposal_text: str, fingerprint: str):
    before = universe_snapshot(folder)
    outcome = fitness_config.save_new_proposal(proposal_text, fingerprint, exclusive_creator(folder))
    return before, universe_snapshot(folder, outcome), outcome


@given(complete_configs(), indents)
def test_reviewed_proposal_is_created_byte_for_byte_as_checked(config, indent):
    text = formatted(config, indent)
    checked = fitness_config.check_proposal(text, config_exists=False)
    assert checked.status == "would-create"
    before, after, _ = run_save(project_folder(None), text, checked.fingerprint)
    state_delta.assert_state_delta(before, after, UNIVERSE, {
        CONFIG: is_(checked.canonical.encode("utf-8")),
        "status": is_("created"),
    })


@given(complete_configs(), indents, st.text("0123456789abcdef", min_size=12, max_size=12))
def test_fingerprint_that_is_not_the_proposals_writes_nothing(config, indent, other_fingerprint):
    text = formatted(config, indent)
    if other_fingerprint == fitness_config.check_proposal(text, config_exists=False).fingerprint:
        return
    before, after, _ = run_save(project_folder(None), text, other_fingerprint)
    state_delta.assert_state_delta(before, after, UNIVERSE, {"status": is_("fingerprint-mismatch")})


@given(complete_configs(), st.binary(max_size=64))
def test_existing_config_is_never_overwritten_on_the_create_path(config, existing):
    text = formatted(config, 2)
    fingerprint = fitness_config.check_proposal(text, config_exists=True).fingerprint
    before, after, _ = run_save(project_folder(existing), text, fingerprint)
    state_delta.assert_state_delta(before, after, UNIVERSE, {"status": is_("refused-exists")})


@given(st.one_of(
    st.text(max_size=40).filter(lambda text: not text.strip().startswith("{")),
    complete_configs().map(lambda cfg: json.dumps({**cfg, "weights": {"security": 100}})),
))
def test_invalid_proposal_writes_nothing(proposal_text):
    before, after, outcome = run_save(project_folder(None), proposal_text, "0" * 12)
    state_delta.assert_state_delta(before, after, UNIVERSE, {"status": is_("invalid")})
    assert outcome.errors


folder_names = st.lists(st.sampled_from(["services", "billing", "api", "web"]), max_size=3)


@given(folder_names, folder_names)
def test_chain_origin_never_leaves_the_anchor(anchor_parts, target_parts):
    anchor = Path("/workspace", *anchor_parts, "ledgerd")
    target = anchor.joinpath(*target_parts)
    origin, error = fitness_config.chain_origin(target, anchor)
    assert error is None
    if target == anchor:
        assert origin is None
    else:
        assert origin == target.parent and (origin == anchor or anchor in origin.parents)
    outside, outside_error = fitness_config.chain_origin(anchor.parent / "elsewhere", anchor)
    assert outside is None and outside_error
