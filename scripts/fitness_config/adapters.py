"""Filesystem adapters: config reads, and the ConfigFile port over a real file."""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Callable

from .parsing import parse_document
from .write_gate import ConfigFile, GateStatus, PublishResult


def load_legacy_config(path: Path) -> tuple[dict | None, str | None]:
    """The legacy verbs' read (`validate [path]`, `show [path]`): (config, None), or
    (None, "Error: <path> <why>") when unreadable; (None, None) when missing (NFR-3)."""
    config, unreadable = read_config(path)
    if unreadable is not None:
        return None, f"Error: {path} {unreadable}"
    return config, None


def read_config(path: Path) -> tuple[dict | None, str | None]:
    """Read one config file strictly (parsing.parse_document): (config, None);
    (None, None) when missing; (None, why) when it cannot be read or parsed."""
    if not path.exists():
        return None, None
    try:
        data = path.read_bytes()
    except OSError as exc:
        return None, f"could not be read: {exc.strerror or exc}"
    return parse_document(data)


def read_chain_configs(chain: list[Path]) -> tuple[list[dict] | None, str | None]:
    """Parse every chain file in order: (configs, None), or (None, error naming the
    first unreadable file). Files that vanished since the walk are skipped."""
    raw_configs: list[dict] = []
    for entry in chain:
        cfg, unreadable = read_config(entry)
        if unreadable is not None:
            return None, f"Error: {entry} {unreadable}"
        if cfg is not None:
            raw_configs.append(cfg)
    return raw_configs, None


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
    prior bytes back or removes the file; obstruction names a folder (or any
    non-regular file) sitting at the path."""
    def publish(data: bytes, publisher, success: str) -> PublishResult:
        try:
            _publish_via_temp(path, data, publisher)
        except FileExistsError:
            return GateStatus.REFUSED_EXISTS, None
        except OSError as exc:
            return GateStatus.WRITE_FAILED, f"Error: could not write {path}: {exc.strerror or exc}"
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

    def obstruction() -> str | None:
        if os.path.lexists(path) and not path.is_file():
            return (f"Error: {path.absolute()} is not a regular file.\n"
                    f"  Fix: move it aside, then check the proposal again.")
        return None

    return ConfigFile(create=lambda data: publish(data, os.link, GateStatus.CREATED),
                      replace=lambda data: publish(data, os.replace, GateStatus.REPLACED),
                      read=read, restore=restore, obstruction=obstruction)
