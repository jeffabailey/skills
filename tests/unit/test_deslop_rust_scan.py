"""skills/deslop-rust/scripts/suite_scan.py: static test facts and report totals."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills/deslop-rust/scripts/suite_scan.py"

LIB = '''\
pub fn double(x: u64) -> u64 { x * 2 }

#[allow(dead_code)]
fn legacy_round(cents: u64) -> u64 { cents }

#[allow(dead_code)]
pub struct Used;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact() {
        assert_eq!(double(2), 4);
    }

    #[test]
    fn weak_ok() {
        assert!("7".parse::<u64>().is_ok());
    }

    #[test]
    fn weak_err() {
        assert!("x".parse::<u64>().is_err());
    }

    #[test]
    fn runs_only() {
        let _ = double(9);
    }

    #[test]
    fn bound_only() {
        assert!(double(3) > 0);
    }

    // The words assert!(x) and thread::sleep( in a comment or "string" are not code.
    #[test]
    fn text_is_not_code() {
        let s = "assert!(true); sleep(1); } {";
        let c = '}';
        let _used: Used = Used;
        assert_eq!((s.len(), c), (28, '}'));
    }

    #[test]
    fn dup_a() {
        let v = vec![1, 2];
        assert_eq!(v.len(), 2);
    }

    #[test]
    fn dup_b() {
        let v = vec![1, 2];   // same body, other spacing
        assert_eq!(v.len(),  2);
    }

    #[test]
    #[ignore]
    fn skipped() {
        assert_eq!(double(1), 2);
    }

    #[test]
    #[should_panic]
    fn panics() {
        double(u64::MAX);
    }

    /// Regression for issue #1234.
    #[test]
    fn overflow_guard() {
        assert_eq!(double(0), 0);
    }
}
'''

INTEGRATION = '''\
use std::thread;
use std::time::Duration;

#[test]
fn slow_flow() {
    thread::sleep(Duration::from_millis(1500));
    assert_eq!(demo::double(2), 4);
}

#[test]
fn setup_one() {
    let a = 1;
    let b = 2;
    let c = 3;
    assert_eq!(a + b + c, 6);
}

#[test]
fn setup_two() {
    let a = 1;
    let b = 2;
    let c = 3;
    assert_eq!(a * b * c, 6);
}

#[test]
fn setup_three() {
    let a = 1;
    let b = 2;
    let c = 3;
    assert_eq!(c - b - a, 0);
}
'''

JUNIT = '''\
<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="nextest-run" tests="4" failures="0" errors="0" time="1.600">
  <testsuite name="demo" tests="3">
    <testcase name="tests::exact" classname="demo" time="0.010"/>
    <testcase name="tests::dup_a" classname="demo" time="0.020"/>
    <testcase name="tests::dup_b" classname="demo" time="0.030"/>
  </testsuite>
  <testsuite name="demo::integration" tests="1">
    <testcase name="slow_flow" classname="demo::integration" time="1.500"/>
  </testsuite>
</testsuites>
'''


def crate(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "target").mkdir()
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "demo"\n')
    (tmp_path / "src/lib.rs").write_text(LIB)
    (tmp_path / "tests/integration.rs").write_text(INTEGRATION)
    (tmp_path / "target/generated.rs").write_text("#[test]\nfn not_ours() {}\n")
    return tmp_path


def mutants(tmp_path, summaries=("CaughtMutant",) * 6 + ("MissedMutant",) * 3 + ("Timeout", "Unviable")):
    out = tmp_path / "baseline" / "mutants.out"
    out.mkdir(parents=True)
    outcomes = [{"scenario": "Baseline", "summary": "Success"}]
    outcomes += [{"scenario": {"Mutant": {"file": "src/lib.rs"}}, "summary": s} for s in summaries]
    (out / "outcomes.json").write_text(json.dumps({"outcomes": outcomes}))
    return out.parent


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


def scan_json(root):
    result = run("scan", root, "--json")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    return data, {t["name"]: t for t in data["tests"]}


def test_scan_lists_each_test_with_its_line_assert_count_and_labels(tmp_path):
    data, tests = scan_json(crate(tmp_path))
    assert len(tests) == 15 and data["files"] == 2 and data["integration_binaries"] == 1
    assert (tests["exact"]["file"], tests["exact"]["line"]) == ("src/lib.rs", 14)
    assert (tests["exact"]["asserts"], tests["exact"]["lines"], tests["exact"]["labels"]) == (1, 4, [])
    assert {name: t["labels"] for name, t in tests.items() if t["labels"]} == {
        "weak_ok": ["is_ok"],
        "weak_err": ["is_err"],
        "runs_only": ["let_", "no-assert"],
        "bound_only": ["bound"],
        "skipped": ["ignore"],
        "panics": ["should_panic"],
        "overflow_guard": ["cites-issue"],
        "slow_flow": ["sleep"],
    }


def test_comments_strings_and_chars_do_not_count_as_code(tmp_path):
    _, tests = scan_json(crate(tmp_path))
    assert (tests["text_is_not_code"]["asserts"], tests["text_is_not_code"]["labels"]) == (1, [])
    assert tests["text_is_not_code"]["lines"] == 7


def test_scan_groups_identical_bodies_and_shared_first_lines(tmp_path):
    data, _ = scan_json(crate(tmp_path))
    assert data["identical_bodies"] == [["src/lib.rs:48 dup_a", "src/lib.rs:54 dup_b"]]
    assert data["same_first_lines"] == [[
        "tests/integration.rs:11 setup_one",
        "tests/integration.rs:19 setup_two",
        "tests/integration.rs:27 setup_three",
    ]]


def test_scan_counts_other_mentions_of_each_dead_code_item(tmp_path):
    data, _ = scan_json(crate(tmp_path))
    assert [(d["line"], d["kind"], d["name"], d["pub"], d["refs"]) for d in data["dead_code"]] == [
        (4, "fn", "legacy_round", False, 0),
        (7, "struct", "Used", True, 2),
    ]


def test_scan_text_output_is_short_and_the_same_on_each_run(tmp_path):
    root = crate(tmp_path)
    first, second = run("scan", root), run("scan", root)
    assert first.returncode == 0 and first.stdout == second.stdout
    assert first.stdout.startswith("15 tests in 2 .rs files; 1 integration binaries")
    assert "    29 runs_only: 0, 4, let_ no-assert" in first.stdout
    assert "src/lib.rs:4 fn legacy_round  refs 0" in first.stdout
    assert "exact" not in first.stdout and str(root) not in first.stdout
    assert "14 exact: 1, 4" in run("scan", root, "--all").stdout
    assert len(first.stdout) < 1200


def test_scan_reports_a_file_with_unbalanced_braces(tmp_path):
    root = crate(tmp_path)
    (root / "src/broken.rs").write_text("#[test]\nfn never_closed() {\n    assert!(true);\n")
    result = run("scan", root)
    assert result.returncode == 0
    assert "unbalanced braces, tests not listed: src/broken.rs" in result.stdout
    assert "never_closed" not in result.stdout


def test_scan_of_a_directory_without_rust_fails_in_one_line(tmp_path):
    for target in (tmp_path, tmp_path / "missing"):
        result = run("scan", target)
        assert result.returncode == 2 and result.stdout == ""
        assert len(result.stderr.strip().splitlines()) == 1 and "Traceback" not in result.stderr


def test_totals_gives_the_baseline_line_and_the_savings(tmp_path):
    root = crate(tmp_path)
    junit = tmp_path / "junit.xml"
    junit.write_text(JUNIT)
    result = run("totals", junit, "--mutants-out", mutants(tmp_path), "--root", root,
                 "--remove", "tests::dup_b", "--shorten", "demo::integration slow_flow=1.5", "--merge", "tests::exact")
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == ("baseline: 4 tests, 1.560s summed test time, 1.600s wall time; "
                        "mutants 6/10 caught (3 missed, 1 timeout; 1 unviable not counted)")
    assert [line.split() for line in lines[3:6]] == [
        ["demo::integration", "slow_flow", "shorten", "1.500", "15.0", "5", "tests/integration.rs:5"],
        ["demo", "tests::dup_b", "remove", "0.030", "0.3", "5", "src/lib.rs:54"],
        ["demo", "tests::exact", "merge", "0.000", "0.0", "4", "src/lib.rs:14"],
    ]
    assert lines[-1] == ("totals: 1 removed, 1 shortened, 1 merged; 1.530s saved per run (98% of summed test time); "
                         "15.3s per mutation run (10 mutants tested); 5 lines in removed tests")


def test_totals_without_items_or_mutants_prints_only_the_baseline(tmp_path):
    junit = tmp_path / "junit.xml"
    junit.write_text(JUNIT)
    result = run("totals", junit)
    assert result.returncode == 0
    assert result.stdout == "baseline: 4 tests, 1.560s summed test time, 1.600s wall time\n"


def test_totals_says_when_a_removed_test_is_not_in_the_source(tmp_path):
    junit = tmp_path / "junit.xml"
    junit.write_text(JUNIT)
    result = run("totals", junit, "--root", tmp_path / "nowhere", "--remove", "tests::dup_a")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().endswith("0 lines in removed tests (1 not found in the source, count by hand)")


def test_totals_rejects_bad_input_in_one_line(tmp_path):
    junit, empty, bad = tmp_path / "junit.xml", tmp_path / "empty.xml", tmp_path / "bad"
    junit.write_text(JUNIT)
    empty.write_text("")
    bad.mkdir()
    (bad / "outcomes.json").write_text("{not json")
    cases = [
        (("totals", empty), "not a JUnit XML report"),
        (("totals", tmp_path / "none.xml"), "cannot read"),
        (("totals", junit, "--mutants-out", bad), "not a cargo-mutants outcomes file"),
        (("totals", junit, "--remove", "tests::gone"), "unknown test: tests::gone"),
        (("totals", junit, "--shorten", "slow_flow"), "--shorten takes TEST=SECONDS"),
        (("totals", junit, "--shorten", "slow_flow=9"), "takes only 1.500s"),
        (("totals", junit, "--remove", "slow_flow", "--merge", "slow_flow"), "named more than once"),
    ]
    for args, message in cases:
        result = run(*args)
        assert result.returncode == 2, args
        assert message in result.stderr and "Traceback" not in result.stderr
        assert len(result.stderr.strip().splitlines()) == 1
