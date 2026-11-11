"""skills/deslop-python/scripts/mutants_compare.py: the lost-kill gate."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills/deslop-python/scripts/mutants_compare.py"
KILLED, SURVIVED = 1, 0


def snapshot(root, modules):
    """modules: {"pkg/cli": (hash, [exit codes])}; every module defines x_main."""
    for rel, (digest, codes) in modules.items():
        meta = root / f"{rel}.py.meta"
        meta.parent.mkdir(parents=True, exist_ok=True)
        dotted = rel.replace("/", ".")
        meta.write_text(json.dumps({
            "exit_code_by_key": {f"{dotted}.x_main__mutmut_{i + 1}": code
                                 for i, code in enumerate(codes)},
            "hash_by_function_name": {"x_main": digest},
        }))
    return root


def diff(base, after):
    return subprocess.run([sys.executable, str(SCRIPT), "diff", str(base), str(after)],
                          capture_output=True, text=True)


def test_a_change_in_one_module_does_not_hide_a_lost_kill_in_a_same_named_function(tmp_path):
    base = snapshot(tmp_path / "base", {"pkg/cli": ("h1", [KILLED, KILLED]),
                                        "pkg/core": ("h2", [KILLED, KILLED])})
    after = snapshot(tmp_path / "after", {"pkg/cli": ("CHANGED", [KILLED, KILLED]),
                                          "pkg/core": ("h2", [KILLED, SURVIVED])})
    result = diff(base, after)
    assert result.returncode == 1, result.stdout
    assert "pkg.core.x_main__mutmut_2" in result.stdout


def test_an_unchanged_run_passes(tmp_path):
    modules = {"pkg/cli": ("h1", [KILLED, KILLED]), "pkg/core": ("h2", [KILLED, SURVIVED])}
    result = diff(snapshot(tmp_path / "base", modules), snapshot(tmp_path / "after", modules))
    assert result.returncode == 0, result.stdout


def test_a_changed_function_is_reported_changed_not_lost(tmp_path):
    base = snapshot(tmp_path / "base", {"pkg/cli": ("h1", [KILLED, KILLED])})
    after = snapshot(tmp_path / "after", {"pkg/cli": ("CHANGED", [KILLED, SURVIVED])})
    result = diff(base, after)
    assert result.returncode == 0, result.stdout
    assert "x_main" in result.stdout
