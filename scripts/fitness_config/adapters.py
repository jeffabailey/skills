"""Filesystem adapters: config reads and the ConfigFile port over a real file."""

from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path
from typing import Callable

from .resolution import anchored_chain
from .write_gate import ConfigFile

def load(path: Path) -> dict | None:
    """Load config from path for legacy CLI verbs (cmd_validate, cmd_show).

    Returns None if the file is missing OR malformed; on a JSON parse error it
    prints a one-line "Invalid JSON: ..." message to stderr. This swallow-and-
    log contract is preserved verbatim from the pre-refactor CLI to keep bare
    invocations byte-identical (NFR-3). New path-based verbs use read_config,
    which RAISES JSONDecodeError so the caller can name the offending file.
    """
    if not path.exists():
        return None
    try:
        return read_config(path)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return None


def read_config(path: Path) -> dict | None:
    """Adapter: read+parse a fitness-config.json. Returns None for missing
    files and raises json.JSONDecodeError for malformed JSON so callers can
    surface the offending path in their error message.
    """
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def read_chain_configs(chain: list[Path]) -> tuple[list[dict] | None, str | None]:
    """Adapter: read every fitness-config.json on the chain in order.

    Returns (raw_configs, None) on success, or (None, error_message) on the
    first malformed JSON file. Result-style return so command verbs can
    short-circuit cleanly without nested try/except blocks. Missing files
    are skipped silently (already filtered by walk_up_chain's existence
    check, but we double-check for robustness).
    """
    raw_configs: list[dict] = []
    for entry in chain:
        try:
            cfg = read_config(entry)
        except json.JSONDecodeError as exc:
            return None, f"Error: invalid JSON in {entry}: {exc}"
        if cfg is not None:
            raw_configs.append(cfg)
    return raw_configs, None

def read_anchored_chain(target: Path, base: Path):
    """Adapter: read the configs above target, never above the anchor (base).

    Returns (chain, raw_configs, error, exit_code): exit 2 for a target
    outside the anchor, 1 for an unreadable chain file.
    """
    chain, error = anchored_chain(target.resolve(strict=False), base.resolve(), Path.is_file)
    if error is not None:
        return [], None, error, 2
    raw_configs, read_error = read_chain_configs(chain)
    return chain, raw_configs, read_error, 1


def _publish_via_temp(path: Path, data: bytes,
                      publish: Callable[[str, Path], None]) -> None:
    """Write data to a temp file beside path, fsync, then publish it; the
    temp file never outlives the call, so a failure leaves no partial file."""
    temp = path.parent / f".{path.name}.{secrets.token_hex(4)}.tmp"
    handle = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        publish(str(temp), path)
    finally:
        temp.unlink(missing_ok=True)


def config_file_at(path: Path) -> ConfigFile:
    """Adapter for the ConfigFile port: create is exclusive (os.link refuses
    an existing file), replace swaps atomically (os.replace); restore puts
    prior bytes back or removes the file."""
    def publish(data: bytes, publisher, success: str) -> tuple[str, str | None]:
        try:
            _publish_via_temp(path, data, publisher)
        except FileExistsError:
            return "refused-exists", None
        except OSError as exc:
            return "write-failed", f"Error: could not write {path}: {exc.strerror or exc}"
        return success, None

    def read() -> bytes | None:
        try:
            return path.read_bytes()
        except OSError:
            return None

    def restore(prior: bytes | None) -> None:
        if prior is None:
            path.unlink(missing_ok=True)
        else:
            _publish_via_temp(path, prior, os.replace)

    return ConfigFile(create=lambda data: publish(data, os.link, "created"),
                      replace=lambda data: publish(data, os.replace, "replaced"),
                      read=read, restore=restore)
