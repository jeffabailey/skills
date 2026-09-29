"""Property tests for the write gate, create and replace paths (ADR-010, data-models 6.2).

Driving port:
  save_reviewed_proposal(proposal_text, expected_fingerprint, config_file, force=) -> GateOutcome
  check_proposal(proposal_text, current) -> GateOutcome
Driven port (injected): ConfigFile(create, replace, read, restore) -- the one file the
gate may touch. Faults are injected by substituting its functions: a silent
no-op, a partial or tampered write, a concurrent create, an OS failure.

The universe is the fake project folder the injected writer controls, plus
the gate's reported status. Every test asserts the state delta over that
whole universe (strict: every slot not expected to change must be unchanged).

Behaviors (budget 2 x 11 = 22; 11 properties here):
  G1 a reviewed proposal is created byte-for-byte as checked
  G2 a fingerprint that is not the proposal's writes nothing
  G3 an existing config is never overwritten on the create path
  G4 an invalid proposal writes nothing
  G5 the chain starts inside the anchor (target == anchor reads nothing above)
  G6 a write that does not verify is rolled back to the prior state
  G7 a config created concurrently after the check is kept and the save refused
  G8 an OS write failure leaves the folder as it was and reports write-failed
  G9 with --force a reviewed proposal replaces a different config byte-for-byte
  G10 a proposal equal to the current config writes nothing, forced or not
  G11 a replace that does not verify restores the prior bytes
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from ._loader import render, resolution, write_gate
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


def config_file(folder: dict, write=lambda data: data, racer: bytes | None = None,
                os_error: str | None = None):
    """Pure-function stand-in for the ConfigFile port over the fake folder.

    `write` decides what actually lands on disk (None = silent no-op),
    `racer` plants a concurrent config just before the create, `os_error`
    makes the create fail the way a read-only folder does.
    """
    def create(data: bytes):
        if racer is not None:
            folder[CONFIG] = racer
        if os_error is not None:
            return "write-failed", os_error
        if CONFIG in folder:
            return "refused-exists", None
        return land(data, "created")

    def land(data: bytes, status: str):
        landed = write(data)
        if landed is not None:
            folder[CONFIG] = landed
        return status, None

    def replace(data: bytes):
        return ("write-failed", os_error) if os_error is not None else land(data, "replaced")

    def restore(prior: bytes | None) -> None:
        if prior is None:
            folder.pop(CONFIG, None)
        else:
            folder[CONFIG] = prior

    return write_gate.ConfigFile(create=create, replace=replace, read=lambda: folder.get(CONFIG),
                                     restore=restore)


def universe_snapshot(folder: dict, outcome=None) -> dict:
    return {CONFIG: folder.get(CONFIG), NEIGHBOUR: folder.get(NEIGHBOUR),
            "status": None if outcome is None else outcome.status}


def formatted(config: dict, indent) -> str:
    return json.dumps(config, indent=indent)


UNIVERSE = {CONFIG, NEIGHBOUR, "status"}
indents = st.sampled_from([None, 2, 4])


def is_(value):
    return state_delta.Predicate(f"== {value!r}", lambda before, after: after == value)


def run_save(folder: dict, proposal_text: str, fingerprint: str, force: bool = False, **faults):
    before = universe_snapshot(folder)
    outcome = write_gate.save_reviewed_proposal(proposal_text, fingerprint,
                                                    config_file(folder, **faults), force=force)
    return before, universe_snapshot(folder, outcome), outcome


@given(complete_configs(), indents)
def test_reviewed_proposal_is_created_byte_for_byte_as_checked(config, indent):
    text = formatted(config, indent)
    checked = write_gate.check_proposal(text, current=None)
    assert checked.status == "would-create"
    before, after, _ = run_save(project_folder(None), text, checked.fingerprint)
    state_delta.assert_state_delta(before, after, UNIVERSE, {
        CONFIG: is_(checked.canonical.encode("utf-8")),
        "status": is_("created"),
    })


@given(complete_configs(), indents, st.text("0123456789abcdef", min_size=12, max_size=12))
def test_fingerprint_that_is_not_the_proposals_writes_nothing(config, indent, other_fingerprint):
    text = formatted(config, indent)
    if other_fingerprint == write_gate.check_proposal(text, current=None).fingerprint:
        return
    before, after, _ = run_save(project_folder(None), text, other_fingerprint)
    state_delta.assert_state_delta(before, after, UNIVERSE, {"status": is_("fingerprint-mismatch")})


@given(complete_configs(), st.binary(max_size=64))
def test_existing_config_is_never_overwritten_on_the_create_path(config, existing):
    text = formatted(config, 2)
    fingerprint = write_gate.check_proposal(text, current=existing).fingerprint
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


def reviewed(config: dict, indent) -> tuple[str, str]:
    text = formatted(config, indent)
    return text, write_gate.check_proposal(text, current=None).fingerprint


faulty_writes = st.one_of(
    st.just(lambda data: None),                                            # silent no-op
    st.floats(0, 0.99).map(lambda cut: lambda data: data[:int(len(data) * cut)]),  # partial
    st.binary(min_size=1, max_size=8).map(lambda junk: lambda data: data + junk),  # tampered
)


@given(complete_configs(), indents, faulty_writes)
def test_write_that_does_not_verify_is_rolled_back(config, indent, faulty_write):
    text, fingerprint = reviewed(config, indent)
    before, after, _ = run_save(project_folder(None), text, fingerprint, write=faulty_write)
    state_delta.assert_state_delta(before, after, UNIVERSE, {"status": is_("verify-failed-rolled-back")})


@given(complete_configs(), indents, st.binary(max_size=64))
def test_config_created_concurrently_is_kept_and_the_save_refused(config, indent, racer):
    text, fingerprint = reviewed(config, indent)
    before, after, _ = run_save(project_folder(None), text, fingerprint, racer=racer)
    state_delta.assert_state_delta(before, after, UNIVERSE, {
        CONFIG: is_(racer), "status": is_("refused-exists")})


@given(complete_configs(), indents, st.text(min_size=1, max_size=40))
def test_os_write_failure_leaves_the_folder_as_it_was(config, indent, reason):
    text, fingerprint = reviewed(config, indent)
    before, after, outcome = run_save(project_folder(None), text, fingerprint, os_error=reason)
    state_delta.assert_state_delta(before, after, UNIVERSE, {"status": is_("write-failed")})
    assert reason in outcome.errors


folder_names = st.lists(st.sampled_from(["services", "billing", "api", "web"]), max_size=3)


@given(folder_names, folder_names)
def test_chain_origin_never_leaves_the_anchor(anchor_parts, target_parts):
    anchor = Path("/workspace", *anchor_parts, "ledgerd")
    target = anchor.joinpath(*target_parts)
    origin, error = resolution.chain_origin(target, anchor)
    assert error is None
    if target == anchor:
        assert origin is None
    else:
        assert origin == target.parent and (origin == anchor or anchor in origin.parents)
    outside, outside_error = resolution.chain_origin(anchor.parent / "elsewhere", anchor)
    assert outside is None and outside_error


# ---------------------------------------------------------------------------
# Replace path (--expect FP --force): the reviewed bytes replace a different
# config atomically; an identical config is left alone; a replace that does
# not verify puts the prior bytes back.
# ---------------------------------------------------------------------------

def different_config(config: dict, other: dict, indent) -> bytes:
    other = other if other != config else {**config, "security": {"confidenceThreshold": 0}}
    return formatted(other, indent).encode("utf-8")


@given(complete_configs(), complete_configs(), indents, indents)
def test_forced_save_replaces_a_different_config_with_the_reviewed_bytes(config, other, indent, old_indent):
    text, fingerprint = reviewed(config, indent)
    folder = project_folder(different_config(config, other, old_indent))
    before, after, _ = run_save(folder, text, fingerprint, force=True)
    state_delta.assert_state_delta(before, after, UNIVERSE, {
        CONFIG: is_(render.render_canonical(config).encode("utf-8")),
        "status": is_("replaced"),
    })


@given(complete_configs(), indents, indents, st.booleans())
def test_proposal_equal_to_the_current_config_writes_nothing(config, indent, current_indent, force):
    text, fingerprint = reviewed(config, indent)
    folder = project_folder(formatted(config, current_indent).encode("utf-8"))
    before, after, _ = run_save(folder, text, fingerprint, force=force)
    state_delta.assert_state_delta(before, after, UNIVERSE, {"status": is_("unchanged")})


@given(complete_configs(), st.one_of(st.binary(max_size=64),
                                     complete_configs().map(lambda other: formatted(other, 2).encode())),
       indents, faulty_writes)
def test_replace_that_does_not_verify_restores_the_prior_bytes(config, prior, indent, faulty_write):
    text, fingerprint = reviewed(config, indent)
    if prior == formatted(config, 2).encode():
        prior = b"{}"
    before, after, _ = run_save(project_folder(prior), text, fingerprint, force=True, write=faulty_write)
    state_delta.assert_state_delta(before, after, UNIVERSE, {"status": is_("verify-failed-rolled-back")})
