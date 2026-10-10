"""The legacy single-file verbs behave like their --path counterparts.

show fails closed on a file it cannot parse (a missing file still shows the
defaults), and init creates its file through the same exclusive, atomic write
as the write gate, so it never truncates a file that appears meanwhile.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "fitness-config.py"


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(_SCRIPT), *args],
                          cwd=cwd, capture_output=True, text=True, timeout=30)


def test_legacy_show_of_malformed_json_fails_naming_the_file(tmp_path):
    (tmp_path / "fitness-config.json").write_text("{not json")
    result = _run("show", "fitness-config.json", cwd=tmp_path)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "fitness-config.json" in result.stderr


def test_legacy_show_of_a_missing_file_prints_the_defaults(tmp_path):
    result = _run("show", "fitness-config.json", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert sum(json.loads(result.stdout)["weights"].values()) == 100


def test_legacy_init_creates_a_valid_file_and_leaves_no_temp_behind(tmp_path):
    created = tmp_path / "fitness-config.json"
    result = _run("init", created.name, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(created.read_text())["version"] == 1
    assert [p.name for p in tmp_path.iterdir()] == ["fitness-config.json"]


def test_legacy_init_never_overwrites(tmp_path):
    existing = tmp_path / "fitness-config.json"
    existing.write_text("keep me")
    result = _run("init", existing.name, cwd=tmp_path)
    assert result.returncode == 1
    assert existing.read_text() == "keep me"
