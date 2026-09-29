"""Integration tests for the ConfigFile adapter over a real folder (ADR-010).

Example-based on purpose: this is the IO boundary, and the contract is that
the adapter wires to the filesystem correctly. The write gate reaches
`restore` only when a saved file fails verification (a race with another
writer), which the CLI cannot stage, so the adapter is exercised directly.

Behaviors (budget 2 x 2 = 4; 2 tests here):
  A1 restore puts the prior state back: no prior bytes removes the created
     file (and is a no-op when it is already gone); prior bytes are put back
     byte-for-byte after a replace
  A2 a created config is a plain data file: read-write as the umask allows,
     never executable
"""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path

import pytest

from ._loader import adapters, write_gate

PRIOR = b'{\n  "version": 1\n}\n'
SAVED = b'{\n  "version": 1,\n  "weights": {}\n}\n'


def _folder_listing(folder: Path) -> dict[str, bytes]:
    return {entry.name: entry.read_bytes() for entry in folder.iterdir()}


def test_restore_puts_back_the_state_before_the_save():
    with tempfile.TemporaryDirectory() as scratch:
        folder = Path(scratch)
        config_file = adapters.config_file_at(folder / "fitness-config.json")

        assert config_file.create(PRIOR) == (write_gate.GateStatus.CREATED, None)
        assert config_file.replace(SAVED) == (write_gate.GateStatus.REPLACED, None)
        config_file.restore(PRIOR)
        after_replace = _folder_listing(folder)

        config_file.restore(None)
        after_create = _folder_listing(folder)
        config_file.restore(None)
        after_second_restore = _folder_listing(folder)

    assert after_replace == {"fitness-config.json": PRIOR}
    assert after_create == after_second_restore == {}


@pytest.mark.parametrize("umask", [0o000, 0o022, 0o077])
def test_a_created_config_is_a_plain_data_file(umask):
    previous_umask = os.umask(umask)
    try:
        with tempfile.TemporaryDirectory() as scratch:
            path = Path(scratch) / "fitness-config.json"
            adapters.config_file_at(path).create(SAVED)
            mode = stat.S_IMODE(path.stat().st_mode)
    finally:
        os.umask(previous_umask)

    assert mode == 0o666 & ~umask, oct(mode)
