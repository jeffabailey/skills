"""Write gate (ADR-010): check a proposal, then save only the reviewed bytes.

Pure apart from calls through the ConfigFile port, which the CLI wires to a real file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import Callable, Sequence

from .parsing import parse_document
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
    # dry run and save: a folder (or anything but a regular file) holds the
    # config's path, so nothing can be diffed or saved there
    EXISTING_NOT_A_FILE = "existing-not-a-file"
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
    bytes back (None removes the file). obstruction(): why something other
    than a regular file (a folder, a dangling link) holds the path, or None.
    """

    create: Callable[[bytes], PublishResult]
    replace: Callable[[bytes], PublishResult]
    read: Callable[[], bytes | None]
    restore: Callable[[bytes | None], None]
    obstruction: Callable[[], str | None] = lambda: None


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


def _read_current(data: bytes) -> tuple[dict | None, str]:
    """The current config's bytes as a JSON object, or (None, why they are not one)."""
    parsed, unreadable = parse_document(data)
    if unreadable is not None:
        return None, unreadable
    if not isinstance(parsed, dict):
        return None, "is not a JSON object"
    return parsed, ""


def _malformed_note(unreadable: str) -> str:
    return f"Current file {unreadable}; cannot diff by value."


def _prepare_proposal(proposal_text: bytes | str) -> GateOutcome:
    proposal, unreadable = parse_document(proposal_text)
    if unreadable is not None:
        return GateOutcome(GateStatus.INVALID, errors=(f"Proposal {unreadable}",))
    errors = validate_proposal(proposal)
    if errors:
        return GateOutcome(GateStatus.INVALID, errors=tuple(errors))
    canonical = render_canonical(proposal)
    return GateOutcome(GateStatus.READY, proposal_fingerprint(canonical), canonical)


def _not_a_file(obstruction: str) -> GateOutcome:
    """No fingerprint: it would invite a save that cannot succeed."""
    return GateOutcome(GateStatus.EXISTING_NOT_A_FILE, errors=(obstruction,))


def check_proposal(proposal_text: bytes | str, current: bytes | None,
                   obstruction: str | None = None) -> GateOutcome:
    """Dry run: validate, render and fingerprint the proposal, then diff it by
    value against the current config's bytes (None: no config yet). Never writes.
    An obstruction (something other than a regular file at the config's path)
    is reported instead of a diff."""
    prepared = _prepare_proposal(proposal_text)
    if prepared.status == GateStatus.INVALID:
        return prepared
    if obstruction is not None:
        return _not_a_file(obstruction)
    if current is None:
        return replace(prepared, status=GateStatus.WOULD_CREATE)
    existing, unreadable = _read_current(current)
    if existing is None:
        return replace(prepared, status=GateStatus.EXISTING_MALFORMED,
                       review=(_malformed_note(unreadable),))
    diff = value_diff(existing, json.loads(prepared.canonical))
    return replace(prepared, status=GateStatus.WOULD_REPLACE if diff.changes else GateStatus.UNCHANGED,
                   review=render_value_diff(diff))


def save_reviewed_proposal(proposal_text: bytes | str, expected_fingerprint: str,
                           config_file: ConfigFile, configs_above: Sequence[dict] = (),
                           force: bool = False) -> GateOutcome:
    """The write gate (data-models 6.2): save the canonical bytes only for the
    reviewed proposal -- creating the file, or replacing a different one only
    when forced -- then verify them, merged with the configs above
    (nearest-first), or roll back to the prior bytes."""
    prepared = _prepare_proposal(proposal_text)
    if prepared.status == GateStatus.INVALID:
        return prepared
    obstruction = config_file.obstruction()
    if obstruction is not None:
        return _not_a_file(obstruction)
    if prepared.fingerprint != expected_fingerprint:
        return replace(prepared, status=GateStatus.FINGERPRINT_MISMATCH)
    prior = config_file.read()
    if prior is not None and _read_current(prior)[0] == json.loads(prepared.canonical):
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
