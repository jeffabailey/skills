"""skills/review-maintainability/scripts/metrics.py: brace-language function detection."""

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
