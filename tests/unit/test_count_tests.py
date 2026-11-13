"""skills/review-testing/scripts/count-tests.py: test counts per runner, level, and directory."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills/review-testing/scripts/count-tests.py"
spec = importlib.util.spec_from_file_location("count_tests", SCRIPT)
count_tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(count_tests)

PY_UNIT = """\
import pytest


@pytest.mark.parametrize("n", [1, 2, 3])
def test_double(n):
    assert n * 2 == n + n


def test_plain():
    assert True


def helper_test():
    return 1
"""
PY_INTEGRATION = "class TestApi:\n    def test_get(self):\n        assert True\n"
GO = """\
package calc

import "testing"

func TestAdd(t *testing.T) {}
func TestSub(t *testing.T) {}
func FuzzParse(f *testing.F) {}
func BenchmarkAdd(b *testing.B) {}
func helper() {}
"""
JS = """\
describe('cart', () => {
  it('adds an item', () => {});
  test('removes an item', () => {});
  test.each([1, 2])('prices %i', (n) => {});
  it.skip('later', () => {});
  submit('not a test');
});
"""


def write(root, files):
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


def pytest_project(tmp_path):
    return write(tmp_path / "proj", {"tests/unit/test_calc.py": PY_UNIT,
                                     "tests/integration/test_api.py": PY_INTEGRATION,
                                     "src/calc.py": "def test_not_in_a_test_file():\n    pass\n"})


def runner(res, name):
    return next(r for r in res["runners"] if r["runner"] == name)


def test_pytest_collector_counts_parametrized_cases(tmp_path):
    res = count_tests.count(str(pytest_project(tmp_path)))
    assert runner(res, "pytest") == {"runner": "pytest", "tests": 5, "source": "collector",
                                     "note": "pytest --collect-only -q", "files": 2}
    assert res["tests"] == 5 and res["levels"] == {"unit": 4, "integration": 1}
    assert [(d["dir"], d["tests"]) for d in res["directories"]] == [("tests/unit", 4), ("tests/integration", 1)]


def test_pytest_collector_leaves_no_cache_behind(tmp_path):
    root = pytest_project(tmp_path)
    count_tests.count(str(root))
    assert not list(root.rglob(".pytest_cache")) and not list(root.rglob("__pycache__"))


def test_pytest_paths_are_relative_to_the_target_when_rootdir_is_above_it(tmp_path):
    root = pytest_project(tmp_path)
    (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\naddopts = ''\n")
    res = count_tests.count(str(root / "tests"))
    assert [(d["dir"], d["tests"]) for d in res["directories"]] == [("unit", 4), ("integration", 1)]


def test_missing_toolchain_falls_back_to_a_labelled_pattern_count(tmp_path, monkeypatch, capsys):
    root = write(pytest_project(tmp_path), {"calc/calc_test.go": GO})
    monkeypatch.setattr(count_tests, "_pytest_command", lambda cwd: None)
    monkeypatch.setattr(count_tests.shutil, "which", lambda name: None)
    res = count_tests.count(str(root))
    assert runner(res, "pytest") == {"runner": "pytest", "tests": 3, "source": "pattern",
                                     "note": "pytest not installed", "files": 2}
    assert runner(res, "go test") == {"runner": "go test", "tests": 3, "source": "pattern",
                                      "note": "go not installed", "files": 1}
    assert count_tests.main([str(root)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("tests=6 test_files=3 runners=2\n")
    assert "pattern (pytest not installed)" in out and "parametrized cases count once" in out


def test_no_collect_never_starts_a_process(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("a collector was started")
    monkeypatch.setattr(count_tests.subprocess, "run", fail)
    res = count_tests.count(str(pytest_project(tmp_path)), use_collectors=False)
    assert runner(res, "pytest")["note"] == "--no-collect" and res["tests"] == 3


def test_a_failing_collector_falls_back_and_says_why(tmp_path):
    root = write(tmp_path / "proj", {"test_broken.py": "import does_not_exist_anywhere\n\ndef test_a():\n    pass\n"})
    row = runner(count_tests.count(str(root)), "pytest")
    assert (row["tests"], row["source"], row["note"]) == (1, "pattern", "collector exit 2")


def test_go_collector_total_is_used_when_go_is_installed(tmp_path, monkeypatch):
    root = write(tmp_path / "proj", {"calc/calc_test.go": GO})

    class Done:
        returncode = 0
        stdout = "TestAdd\nTestSub\nFuzzParse\nTestGenerated\nok  \texample/calc\t0.01s\n"

    seen = {}

    def fake_run(cmd, cwd, env):
        seen.update(cmd=cmd, env=env)
        return Done(), None
    monkeypatch.setattr(count_tests.shutil, "which", lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(count_tests, "_run", fake_run)
    row = runner(count_tests.count(str(root)), "go test")
    assert (row["tests"], row["source"]) == (4, "collector") and "pattern count, 3" in row["note"]
    assert seen["cmd"][:3] == ["go", "test", "-list"] and seen["env"]["GOPROXY"] == "off"


def test_js_declarations_are_counted_by_pattern_with_a_level_guess(tmp_path):
    root = write(tmp_path / "proj", {"src/cart.test.ts": JS, "e2e/checkout.spec.ts": JS,
                                     "src/cart.ts": JS, "node_modules/x/x.test.js": JS})
    res = count_tests.count(str(root))
    assert runner(res, "js") == {"runner": "js", "tests": 6, "source": "pattern",
                                 "note": "no read-only collector", "files": 2}
    assert res["levels"] == {"unlabelled": 3, "e2e": 3}


def test_empty_and_malformed_inputs(tmp_path, capsys):
    assert count_tests.main([str(tmp_path)]) == 0
    assert capsys.readouterr().out.startswith("tests=0 test_files=0 runners=0\nno test declarations found")
    (tmp_path / "test_bad.py").write_bytes(b"\x00\xff\xfe\ndef broken(:\n")
    assert count_tests.count(str(tmp_path))["tests"] == 0
    assert count_tests.main([str(tmp_path / "missing")]) == 2
    assert capsys.readouterr().err == f"error: path not found: {tmp_path / 'missing'}\n"


def test_directory_rows_are_capped(tmp_path, capsys):
    root = write(tmp_path / "proj", {f"pkg{n}/x_test.go": GO for n in range(4)})
    assert count_tests.main([str(root), "--no-collect", "--top", "2"]) == 0
    assert "... and 2 more directories with 6 tests (--all lists them)" in capsys.readouterr().out
