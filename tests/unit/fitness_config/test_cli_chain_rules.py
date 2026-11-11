"""The walk-up verbs apply the per-file rules to every chain file.

A chain file that parses as JSON and declares version 1 can still hold a value
the renderer cannot use (a weight written as text). show and validate must
fail closed with a message naming that file, never with a traceback, because
every review skill calls show before it scores anything.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "fitness-config.py"


def _run(verb: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(_SCRIPT), verb, "--path", "."],
                          cwd=cwd, capture_output=True, text=True, timeout=30)


@pytest.mark.parametrize("verb", ["show", "validate"])
@pytest.mark.parametrize("bad_weights", [{"security": "14"}, {"security": None}, {"security": True}])
def test_a_chain_file_with_an_unusable_weight_fails_closed_naming_the_file(tmp_path, verb, bad_weights):
    (tmp_path / "fitness-config.json").write_text(json.dumps({"version": 1, "weights": bad_weights}))
    result = _run(verb, tmp_path)
    assert result.returncode == 1, result.stdout
    assert "Traceback" not in result.stderr
    assert "fitness-config.json" in result.stderr
    assert "weights.security" in result.stderr


def test_a_partial_override_without_a_version_still_shows(tmp_path):
    (tmp_path / "fitness-config.json").write_text(json.dumps({"weights": {"security": 14}}))
    result = _run("show", tmp_path)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("verb", ["show", "validate"])
def test_a_misspelled_weight_domain_in_an_override_fails_closed(tmp_path, verb):
    """A typo'd domain must not pass: the real domain would silently lose its weight."""
    (tmp_path / "fitness-config.json").write_text(
        json.dumps({"weights": {"algorithms": 0, "algoritms": 10}}))
    result = _run(verb, tmp_path)
    assert result.returncode == 1, result.stdout
    assert "fitness-config.json" in result.stderr
    assert "weights.algoritms is not a known domain" in result.stderr


@pytest.mark.parametrize("verb", ["show", "validate"])
@pytest.mark.parametrize("section,key", [("statusThresholds", "healthy"), ("scoring", "goodRange")])
def test_a_reversed_range_in_an_override_fails_closed(tmp_path, verb, section, key):
    """Consumers read [0] as the lower bound, so [10, 8] would misreport every status."""
    (tmp_path / "fitness-config.json").write_text(json.dumps({section: {key: [10, 8]}}))
    result = _run(verb, tmp_path)
    assert result.returncode == 1, result.stdout
    assert f"{section}.{key} must list the low end first" in result.stderr
