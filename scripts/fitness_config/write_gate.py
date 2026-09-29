"""Write gate (ADR-010): check a proposal, then save only the reviewed bytes. Pure over the ConfigFile port."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Callable, Sequence

from .resolution import build_effective_config, deep_merge_chain
from .render import proposal_fingerprint, render_canonical, render_value_diff, value_diff
from .validation import validate_effective, validate_proposal

@dataclass(frozen=True)
class ConfigFile:
    """Driven port (ADR-010): the one config file the write gate may touch.

    create(data) -> (status, reason): "created", "refused-exists" (a file is
    already there) or "write-failed" (the OS refused; reason says why).
    replace(data) -> "replaced" or "write-failed": atomically swaps the file.
    read() -> the bytes now on disk, or None.  restore(prior) puts the prior
    bytes back (None removes the file).
    """

    create: Callable[[bytes], tuple[str, str | None]]
    replace: Callable[[bytes], tuple[str, str | None]]
    read: Callable[[], bytes | None]
    restore: Callable[[bytes | None], None]

@dataclass(frozen=True)
class GateOutcome:
    """What the write gate decided; `canonical` is the byte-exact payload."""

    status: str
    fingerprint: str | None = None
    canonical: str | None = None
    errors: tuple[str, ...] = ()
    review: tuple[str, ...] = ()

def _config_object(data: bytes) -> dict | None:
    try:
        parsed = json.loads(data)
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


_MALFORMED_NOTE = "Current file is not valid JSON; cannot diff by value."


def _prepare_proposal(proposal_text: str) -> GateOutcome:
    try:
        proposal = json.loads(proposal_text)
    except ValueError as exc:
        return GateOutcome("invalid", errors=(f"Proposal is not valid JSON: {exc}",))
    errors = validate_proposal(proposal)
    if errors:
        return GateOutcome("invalid", errors=tuple(errors))
    canonical = render_canonical(proposal)
    return GateOutcome("ready", proposal_fingerprint(canonical), canonical)


def check_proposal(proposal_text: str, config_exists: bool,
                   current: bytes | None = None) -> GateOutcome:
    """Dry run: validate, render, fingerprint and diff by value against the
    current config's bytes. Never writes."""
    prepared = _prepare_proposal(proposal_text)
    if prepared.status == "invalid" or not config_exists:
        return prepared if prepared.status == "invalid" else replace(prepared, status="would-create")
    if current is None:
        return replace(prepared, status="would-replace")
    existing = _config_object(current)
    if existing is None:
        return replace(prepared, status="existing-malformed", review=(_MALFORMED_NOTE,))
    diff = value_diff(existing, json.loads(prepared.canonical))
    return replace(prepared, status="would-replace" if diff.changes else "unchanged",
                   review=render_value_diff(diff))


def save_new_proposal(proposal_text: str, expected_fingerprint: str,
                      config_file: ConfigFile, configs_above: Sequence[dict] = (),
                      force: bool = False) -> GateOutcome:
    """The write gate (data-models 6.2): write the canonical bytes only for the
    reviewed proposal -- creating the file, or replacing a different one only
    when forced -- then verify them, merged with the configs above
    (nearest-first), or roll back to the prior bytes."""
    prepared = _prepare_proposal(proposal_text)
    if prepared.status == "invalid":
        return prepared
    if prepared.fingerprint != expected_fingerprint:
        return replace(prepared, status="fingerprint-mismatch")
    prior = config_file.read()
    if prior is not None and _config_object(prior) == json.loads(prepared.canonical):
        return replace(prepared, status="unchanged")
    if prior is not None and not force:
        return replace(prepared, status="refused-exists")
    publish, success = ((config_file.create, "created") if prior is None
                        else (config_file.replace, "replaced"))
    status, reason = publish(prepared.canonical.encode("utf-8"))
    if status != success:
        return replace(prepared, status=status, errors=(reason,) if reason else ())
    return _verify_or_roll_back(prepared, config_file, prior, configs_above, success)


def _saved_problems(saved: bytes | None, fingerprint: str,
                    configs_above: Sequence[dict]) -> list[str]:
    """Why the bytes read back are not the reviewed config, or why the folder's
    effective config (saved merged with the configs above) is invalid."""
    text = None if saved is None else saved.decode("utf-8", errors="replace")
    if text is None or proposal_fingerprint(text) != fingerprint:
        return ["the saved file is not the reviewed proposal"]
    merged = deep_merge_chain([json.loads(text), *configs_above])
    return validate_effective(build_effective_config(merged), []).errors


def _verify_or_roll_back(prepared: GateOutcome, config_file: ConfigFile,
                         prior: bytes | None, configs_above: Sequence[dict],
                         success: str) -> GateOutcome:
    problems = _saved_problems(config_file.read(), prepared.fingerprint, configs_above)
    if not problems:
        return replace(prepared, status=success)
    config_file.restore(prior)
    return replace(prepared, status="verify-failed-rolled-back", errors=tuple(problems))
