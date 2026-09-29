"""Write gate (ADR-010): check a proposal, then save only the reviewed bytes.

Pure apart from calls through the ConfigFile port, which the CLI wires to a real file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Callable, Sequence

from .resolution import build_effective_config, deep_merge_chain
from .render import proposal_fingerprint, render_canonical, render_value_diff, value_diff
from .validation import validate_effective, validate_proposal


class GateStatus:
    """Every outcome code of the write gate, printed as `STATUS: <code>` (data-models 6.2)."""

    READY = "ready"  # internal: valid and fingerprinted, not yet compared or saved
    INVALID = "invalid"
    # dry run (check_proposal)
    WOULD_CREATE = "would-create"
    WOULD_REPLACE = "would-replace"
    UNCHANGED = "unchanged"
    EXISTING_MALFORMED = "existing-malformed"
    # save (save_reviewed_proposal), including what the ConfigFile port reports
    FINGERPRINT_MISMATCH = "fingerprint-mismatch"
    REFUSED_EXISTS = "refused-exists"
    CREATED = "created"
    REPLACED = "replaced"
    WRITE_FAILED = "write-failed"
    VERIFY_FAILED_ROLLED_BACK = "verify-failed-rolled-back"

    SUCCESSFUL = frozenset({WOULD_CREATE, WOULD_REPLACE, UNCHANGED, EXISTING_MALFORMED,
                            CREATED, REPLACED})


# (status, reason): reason explains a WRITE_FAILED, else None.
PublishResult = tuple[str, str | None]


@dataclass(frozen=True)
class ConfigFile:
    """Driven port (ADR-010): the one config file the write gate may touch.

    create(data): CREATED, REFUSED_EXISTS (a file is already there) or
    WRITE_FAILED. replace(data): REPLACED or WRITE_FAILED, swapping atomically.
    read(): the bytes now on disk, or None. restore(prior): put the prior
    bytes back (None removes the file).
    """

    create: Callable[[bytes], PublishResult]
    replace: Callable[[bytes], PublishResult]
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

    @property
    def succeeded(self) -> bool:
        return self.status in GateStatus.SUCCESSFUL


def _config_object(data: bytes) -> dict | None:
    """The bytes as a JSON object, or None when they are not one."""
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
        return GateOutcome(GateStatus.INVALID, errors=(f"Proposal is not valid JSON: {exc}",))
    errors = validate_proposal(proposal)
    if errors:
        return GateOutcome(GateStatus.INVALID, errors=tuple(errors))
    canonical = render_canonical(proposal)
    return GateOutcome(GateStatus.READY, proposal_fingerprint(canonical), canonical)


def check_proposal(proposal_text: str, current: bytes | None) -> GateOutcome:
    """Dry run: validate, render and fingerprint the proposal, then diff it by
    value against the current config's bytes (None: no config yet). Never writes."""
    prepared = _prepare_proposal(proposal_text)
    if prepared.status == GateStatus.INVALID:
        return prepared
    if current is None:
        return replace(prepared, status=GateStatus.WOULD_CREATE)
    existing = _config_object(current)
    if existing is None:
        return replace(prepared, status=GateStatus.EXISTING_MALFORMED, review=(_MALFORMED_NOTE,))
    diff = value_diff(existing, json.loads(prepared.canonical))
    return replace(prepared, status=GateStatus.WOULD_REPLACE if diff.changes else GateStatus.UNCHANGED,
                   review=render_value_diff(diff))


def save_reviewed_proposal(proposal_text: str, expected_fingerprint: str,
                           config_file: ConfigFile, configs_above: Sequence[dict] = (),
                           force: bool = False) -> GateOutcome:
    """The write gate (data-models 6.2): save the canonical bytes only for the
    reviewed proposal -- creating the file, or replacing a different one only
    when forced -- then verify them, merged with the configs above
    (nearest-first), or roll back to the prior bytes."""
    prepared = _prepare_proposal(proposal_text)
    if prepared.status == GateStatus.INVALID:
        return prepared
    if prepared.fingerprint != expected_fingerprint:
        return replace(prepared, status=GateStatus.FINGERPRINT_MISMATCH)
    prior = config_file.read()
    if prior is not None and _config_object(prior) == json.loads(prepared.canonical):
        return replace(prepared, status=GateStatus.UNCHANGED)
    if prior is not None and not force:
        return replace(prepared, status=GateStatus.REFUSED_EXISTS)
    publish, success = ((config_file.create, GateStatus.CREATED) if prior is None
                        else (config_file.replace, GateStatus.REPLACED))
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
    return replace(prepared, status=GateStatus.VERIFY_FAILED_ROLLED_BACK, errors=tuple(problems))
