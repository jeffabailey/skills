"""check-report.py: fixture reports with known failures."""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/check-report.py"

CLEAN = """# Software Testing Fitness Report

**Target:** whole repository
Config: built-in defaults
Effective weights: testing=16

## Summary

Overall fitness score: 7.3 / 10 — Needs Attention (mean of A, B, C)

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| A | 8/10 | fine |
| B | 7/10 | fine |
| C | 7/10 | fine |
| D | N/A — no load tests needed | — |

## Detailed Findings

### Finding 1: Parser has no tests
- **Severity:** HIGH
- **Confidence:** 8/10
- **Dimension:** A
- **Location:** src/app.py:2; `src/util.py:1-3`, :5
- **Evidence:** A fenced block must not be parsed:

```python
# Finding 9: not a heading
x = "src/app.py:999"
```

### Finding 2: No CI
- **Severity:** MEDIUM
- **Confidence:** 7/10
- **Location:** .github/workflows/ (none); no Jenkinsfile at the root

### A (8/10)
- Evidence: src/app.py:1

## Action Items

1. [HIGH] Add tests -- src/app.py:2
"""


def make_repo(tmp_path, report=CLEAN):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/app.py").write_text("import os\ndef parse(argv):\n    return argv\n")
    (tmp_path / "src/util.py").write_text("".join(f"line {n}\n" for n in range(1, 6)))
    (tmp_path / "docs").mkdir()
    path = tmp_path / "docs/testing-review.md"
    path.write_text(report)
    return path


def run(report, repo, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(report), "--repo", str(repo), *args], capture_output=True, text=True
    )


def test_clean_report_passes_and_lists_each_citation(tmp_path):
    result = run(make_repo(tmp_path), tmp_path)

    assert result.returncode == 0, result.stdout
    assert result.stdout.splitlines() == [
        "check-report: 0 failure(s)",
        "findings: 2",
        "overall: mean 7.33 of 3 scored dimensions",
        "F1 src/app.py:2 | def parse(argv):",
        "F1 src/util.py:1-3 | line 1",
        "F1 src/util.py:5 | line 5",
        "F2 .github/workflows/ | (absent; cited as an absence)",
    ]


def test_wrong_line_number_fails(tmp_path):
    report = make_repo(tmp_path, CLEAN.replace("src/app.py:2;", "src/app.py:412;"))

    result = run(report, tmp_path)

    assert result.returncode == 1
    assert "FAIL finding 1: src/app.py:412: line 412 > 3 lines" in result.stdout.splitlines()


def test_wrong_mean_fails(tmp_path):
    report = make_repo(tmp_path, CLEAN.replace("score: 7.3 / 10", "score: 7.6 / 10"))

    result = run(report, tmp_path)

    assert result.returncode == 1
    assert "FAIL overall 7.6 != 7.3 (mean 7.33 of 3 scored dimensions)" in result.stdout.splitlines()


def test_critical_finding_caps_the_overall(tmp_path):
    report = make_repo(tmp_path, CLEAN.replace("**Severity:** HIGH", "**Severity:** CRITICAL"))

    result = run(report, tmp_path)

    assert "FAIL overall 7.3 != 4.0 (mean 7.33 of 3 scored dimensions, CRITICAL cap 4.0)" in result.stdout.splitlines()
    capped = make_repo_again(tmp_path, report.read_text().replace("score: 7.3 / 10", "score: 4.0 / 10"))
    assert run(capped, tmp_path).returncode == 0


def make_repo_again(tmp_path, text):
    path = tmp_path / "docs/second.md"
    path.write_text(text)
    return path


def test_overall_row_in_the_table_is_checked(tmp_path):
    text = CLEAN.replace("Overall fitness score: 7.3 / 10 — Needs Attention (mean of A, B, C)\n", "")
    text = text.replace("| D | N/A", "| **Overall** | **6.0/10** (Needs Attention) | mean |\n| D | N/A")

    result = run(make_repo(tmp_path, text), tmp_path)

    assert "FAIL overall 6 != 7.3 (mean 7.33 of 3 scored dimensions)" in result.stdout.splitlines()


def test_confidence_missing_or_below_threshold_fails(tmp_path):
    text = CLEAN.replace("- **Confidence:** 8/10\n", "").replace("**Confidence:** 7/10", "**Confidence:** 6/10")

    result = run(make_repo(tmp_path, text), tmp_path)

    lines = result.stdout.splitlines()
    assert "FAIL finding 1: no confidence" in lines
    assert "FAIL finding 2: confidence 6 < 7" in lines
    assert result.returncode == 1


def test_min_confidence_flag_raises_the_bar(tmp_path):
    result = run(make_repo(tmp_path), tmp_path, "--min-confidence", "8")

    assert "FAIL finding 2: confidence 7 < 8" in result.stdout.splitlines()


def test_bare_filename_and_absolute_path_fail_with_a_hint(tmp_path):
    text = CLEAN.replace("src/app.py:2;", "app.py:2; /etc/passwd:1;")

    result = run(make_repo(tmp_path, text), tmp_path)

    lines = result.stdout.splitlines()
    assert "FAIL finding 1: app.py:2: missing path (did you mean src/app.py?)" in lines
    assert "FAIL finding 1: /etc/passwd:1: not repo-relative" in lines


def test_body_citation_out_of_range_fails(tmp_path):
    text = CLEAN.replace("Add tests -- src/app.py:2", "Add tests -- src/app.py:77")

    result = run(make_repo(tmp_path, text), tmp_path)

    assert any(line.endswith("src/app.py:77: line 77 > 3 lines") for line in result.stdout.splitlines())
    assert result.returncode == 1


def test_secret_values_in_cited_lines_are_redacted(tmp_path):
    report = make_repo(tmp_path)
    (tmp_path / "src/app.py").write_text('import os\nAPI_KEY = "sk-live-abcdef123456"\ntoken = os.environ["T"]\n')
    report.write_text(CLEAN.replace("src/app.py:2;", "src/app.py:2; src/app.py:3;"))

    result = run(report, tmp_path)

    assert "sk-live" not in result.stdout
    assert "F1 src/app.py:2 | API_KEY = <redacted>" in result.stdout.splitlines()
    assert 'F1 src/app.py:3 | token = os.environ["T"]' in result.stdout.splitlines()


def test_empty_report_fails_without_a_traceback(tmp_path):
    result = run(make_repo(tmp_path, ""), tmp_path)

    assert result.returncode == 1
    assert result.stderr == ""
    assert result.stdout.splitlines()[:3] == [
        "FAIL no Config: line in the first 10 lines",
        "FAIL no scores table (header: | Dimension | Score |)",
        "check-report: 2 failure(s)",
    ]


def test_missing_report_is_one_line(tmp_path):
    result = run(tmp_path / "nope.md", tmp_path)

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.strip() == f"error: report not found: {tmp_path / 'nope.md'}"
