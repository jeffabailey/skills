"""skills/review-maintainability/scripts/metrics.py: brace-language function detection and debt counts."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills/review-maintainability/scripts/metrics.py"
spec = importlib.util.spec_from_file_location("metrics", SCRIPT)
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)

RUST = """\
impl Thing {
    fn name(&self) -> &'static str {
        "thing"
    }
}

fn big(a: i32) -> i32 {
    if a > 0 { a } else { -a }
}

fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

fn quote() -> char {
    let brace = '{';
    let tick = '\\'';
    brace
}
"""


def names(rel, text):
    funcs, _classes = metrics.brace_metrics(rel, text)[:2]
    return sorted(f["name"] for f in funcs)


def test_rust_functions_with_lifetimes_are_measured():
    assert names("lib.rs", RUST) == ["big", "longest", "name", "quote"]


def test_rust_char_literals_are_still_blanked():
    code = metrics.strip_code("let b = '{'; let t = '\\''; fn f<'a>() {}", rust=True)
    assert code.count("{") == 1 and "<'a>" in code


def test_single_quoted_strings_stay_strings_outside_rust():
    code = metrics.strip_code("const s = 'a { b'; function f() {}")
    assert code.count("{") == 1


def analyzed(tmp_path, files):
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    res = metrics.analyze([str(tmp_path)])
    return res, metrics.summarize(res)


def test_a_todo_is_untracked_unless_its_line_has_an_issue_reference(tmp_path):
    res, summary = analyzed(tmp_path, {"a.py": (
        "x = 1  # TODO tidy this\n"
        "y = 2  # TODO(#42) tidy that\n"
        "z = 3  # FIXME PROJ-7 rounding\n"
        "w = 4  # HACK see https://example.test/issues/9\n")})
    assert [m["tracked"] for m in res["markers"]] == [False, True, True, True]
    assert summary["markers"] == 4 and summary["untracked_markers"] == 1


def test_commented_out_python_is_counted_in_blocks_and_prose_is_not(tmp_path):
    res, summary = analyzed(tmp_path, {"a.py": (
        "#!/usr/bin/env python3\n"
        "# This module keeps the totals in one place.\n"
        "# note: the order matters\n"
        "import os  # noqa: F401\n"
        "# old = compute(1)\n"
        "# if old:\n"
        "#     print(old)\n"
        "value = 1\n"
        "# return value\n")})
    assert res["commented_out"] == [{"where": "a.py:5", "lines": 3}, {"where": "a.py:9", "lines": 1}]
    assert summary["commented_out_lines"] == 4 and summary["commented_out_blocks"] == 2


def test_commented_out_brace_code_needs_a_statement_ending(tmp_path):
    res, _ = analyzed(tmp_path, {"a.ts": (
        "// Returns the total for one order.\n"
        "/// doc comment with a brace {\n"
        "// const old = total(order);\n"
        "// if (old) {\n"
        "const x = 1; // trailing note;\n"
        "// eslint-disable-next-line no-console;\n")})
    assert res["commented_out"] == [{"where": "a.ts:3", "lines": 2}]


def test_rates_per_1000_lines_use_the_known_counts(tmp_path, capsys):
    long_fn = "def big():\n" + "    x = 1\n" * 60
    filler = "y = 0\n" * 1937  # 61 + 2 + 1937 = 2000 non-blank lines
    _, summary = analyzed(tmp_path, {"a.py": long_fn + "# TODO one\n# z = compute()\n" + filler})
    assert summary["total_loc"] == 2000
    assert summary["measured_smells"] == {"long_functions": 1, "large_classes": 0,
                                          "commented_out_blocks": 1, "total": 2}
    assert summary["per_1000_loc"] == {"measured_smells": 1.0, "untracked_markers": 0.5, "suppressions": 0.0}
    assert metrics.main([str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "untracked: 1;" in out and "a.py:62  TODO  untracked" in out
    assert "measured smells 1.0, untracked markers 0.5" in out


def test_small_targets_get_raw_counts_and_lists_are_capped(tmp_path, capsys):
    _, summary = analyzed(tmp_path, {"a.py": "".join(f"# TODO item {n}\n" for n in range(5))})
    assert summary["per_1000_loc"]["measured_smells"] is None
    assert metrics.main([str(tmp_path), "--top", "2"]) == 0
    out = capsys.readouterr().out
    assert "use raw counts, not density" in out and "... and 3 more" in out
    assert metrics.main([str(tmp_path), "--top", "2", "--all"]) == 0
    assert "a.py:5  TODO  untracked" in capsys.readouterr().out


def test_an_empty_tree_and_an_unparsable_file_do_not_fail(tmp_path, capsys):
    assert metrics.main([str(tmp_path)]) == 0
    assert "Markers TODO/FIXME/HACK/XXX: 0 (untracked: 0" in capsys.readouterr().out
    (tmp_path / "bad.py").write_bytes(b"def broken(:\n\x00\xff # TODO later\n# x = (\n")
    res = metrics.analyze([str(tmp_path)])
    assert len(res["markers"]) == 1 and res["commented_out"] == []
    assert metrics.main([str(tmp_path / "missing")]) == 2
