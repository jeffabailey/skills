"""Fixtures for the fitness-config-init acceptance suite.

Strategy C (real services), same as fitness-config-per-directory:
  - driving port: `python3 scripts/fitness-config.py` as a real subprocess
  - driven adapter: real files under pytest's tmp_path
  - no mocks at the acceptance level

Layout note: this steps/ directory deliberately has no __init__.py. The sibling
suite owns the `steps` package name; a second `steps` package makes pytest
raise ImportPathMismatchError. Helper modules therefore use an `fci_` prefix
and are imported by bare name.

Tag handling:
  @skip    pending scenario; DELIVER removes the tag one scenario at a time
  @manual  agent-behaviour scenario checked by hand / agent eval, never by pytest
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fci_support import Workspace  # noqa: E402

SUITE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def workspace(tmp_path: Path):
    ws = Workspace(root=tmp_path / "workspace")
    ws.root.mkdir()
    yield ws
    ws.restore_permissions()


@pytest.fixture
def context() -> dict:
    """Per-scenario state shared between steps (last report, snapshots, proposal)."""
    return {}


@pytest.fixture
def not_root():
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.skip("read-only folders are writable by root")


def pytest_collection_modifyitems(config, items):
    # FCI_RUN_PENDING=1 runs every @skip scenario (not @manual) to audit that
    # each one binds to steps and fails for the right reason (red-classification).
    run_pending = os.environ.get("FCI_RUN_PENDING") == "1"
    for item in items:
        if SUITE_DIR not in Path(str(item.fspath)).resolve().parents:
            continue
        if run_pending and not item.get_closest_marker("manual"):
            item.own_markers[:] = [m for m in item.own_markers if m.name != "skip"]
            continue
        if item.get_closest_marker("manual"):
            item.add_marker(pytest.mark.skip(
                reason="manual agent-eval scenario; see docs/feature/fitness-config-init/distill/test-scenarios.md"),
                append=False)
        elif item.get_closest_marker("skip"):
            item.add_marker(pytest.mark.skip(
                reason="pending: DELIVER enables one scenario at a time"), append=False)
