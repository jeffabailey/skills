"""review-agent-memory collectors: cited-path sizes, miner sizes, savings arithmetic."""

import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "skills/review-agent-memory/scripts"
COLLECT = SCRIPTS / "collect_sources.py"
MINE = SCRIPTS / "mine_transcripts.py"


def run(script, *args, home):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        capture_output=True, text=True, env={"HOME": str(home), "PATH": "/usr/bin:/bin:/usr/local/bin"},
    )


def project(tmp_path):
    """A repo with known sizes: CLAUDE.md 400 bytes / 4 lines, docs/ 2 files of 1,000 bytes."""
    home, repo = tmp_path / "home", tmp_path / "home" / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "CLAUDE.md").write_text(("x" * 99 + "\n") * 4)
    (repo / "docs/a.md").write_text("a" * 600)
    (repo / "docs/b.md").write_text("b" * 400)
    mem = home / ".claude/projects" / re.sub(r"[^A-Za-z0-9]", "-", str(repo.resolve())) / "memory"
    mem.mkdir(parents=True)
    (mem / "gotcha.md").write_text("m" * 80)
    return home, repo


def test_size_prints_known_sizes_and_missing(tmp_path):
    home, repo = project(tmp_path)
    r = run(COLLECT, repo, "--size", "gone.md", "docs", "CLAUDE.md", "gotcha.md", "CLAUDE.md", home=home)
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    assert lines[1:] == [
        "- CLAUDE.md: 4 lines, 400 bytes, ~100 tok",
        "- docs: dir, 2 files, 1,000 bytes, ~250 tok",
        "- gone.md: MISSING",
        "- gotcha.md (auto-memory): 0 lines, 80 bytes, ~20 tok",
        "- 4 paths: 3 found, 1 missing",
    ]
    assert "Harness memory sources" not in r.stdout


def test_size_absolute_path_and_all_missing(tmp_path):
    home, repo = project(tmp_path)
    r = run(COLLECT, repo, "--size", repo / "docs/a.md", "/no/such/file", home=home)
    assert r.returncode == 0
    assert f"- {repo / 'docs/a.md'}: 0 lines, 600 bytes, ~150 tok" in r.stdout
    assert "- /no/such/file: MISSING" in r.stdout
    assert r.stdout.rstrip().endswith("2 paths: 1 found, 1 missing")


def test_inventory_lists_tokens_for_empty_project(tmp_path):
    home = tmp_path / "home"
    (home / "empty").mkdir(parents=True)
    r = run(COLLECT, home / "empty", home=home)
    assert r.returncode == 0, r.stderr
    assert "Always-loaded estimate (Claude Code): ~0 tokens" in r.stdout
    assert "- Auto-memory: none" in r.stdout


def test_inventory_token_estimate_matches_size_mode(tmp_path):
    home, repo = project(tmp_path)
    r = run(COLLECT, repo, home=home)
    assert "- CLAUDE.md [claude, always] ~100 tok" in r.stdout
    assert "- gotcha.md [None] ~20 tok" in r.stdout


def test_estimate_arithmetic():
    r = run(MINE, "--window", "30:20", "--estimate", "lint retries:12:3300", "CLAUDE.md: always:900:2000:cached",
            home="/nonexistent")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [
        "# Savings estimates (30 sessions over 20 days = 45.0 sessions/month)",
        # 900 / 30 x 45 x 2000 x 0.1 = 270,000; 12 / 30 x 45 x 3300 = 59,400
        "- CLAUDE.md: always: 900 ÷ 30 sessions × 45.0 sessions/month × 2,000 tok × 0.1 cache weight"
        " ≈ 270,000 tok/month (estimate)",
        "- lint retries: 12 ÷ 30 sessions × 45.0 sessions/month × 3,300 tok ≈ 59,400 tok/month (estimate)",
    ]


def test_estimate_thin_window_is_flagged_and_short_window_counts_as_a_day():
    r = run(MINE, "--window", "2:0.2", "--estimate", "x:2:100", home="/nonexistent")
    assert "- x: 2 ÷ 2 sessions × 60.0 sessions/month × 100 tok ≈ 6,000 tok/month (estimate)" in r.stdout
    assert "thin window" in r.stdout


def test_estimate_malformed_input_fails_in_one_line():
    for args in (["--estimate", "x:1:2"], ["--window", "0:5", "--estimate", "x:1:2"],
                 ["--window", "30:20", "--estimate", "nocount"], ["--window", "30:20", "--estimate", "x:a:b"], []):
        r = run(MINE, *args, home="/nonexistent")
        assert r.returncode != 0
        assert r.stderr.startswith("error: ") and r.stderr.count("\n") == 1, r.stderr
        assert "Traceback" not in r.stderr


def test_miner_prints_file_sizes_and_window(tmp_path):
    home, repo = project(tmp_path)
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(repo))
    tdir = home / "transcripts" / slug
    tdir.mkdir(parents=True)

    def assistant(ts, mid, path):
        return json.dumps({"type": "assistant", "timestamp": ts, "message": {
            "id": mid, "usage": {"input_tokens": 10, "output_tokens": 5},
            "content": [{"type": "tool_use", "id": "t" + mid, "name": "Read", "input": {"file_path": path}}]}})

    (tdir / "s1.jsonl").write_text("\n".join([
        assistant("2026-01-01T00:00:00Z", "1", str(repo / "CLAUDE.md")),
        assistant("2026-01-01T00:01:00Z", "2", str(repo / "CLAUDE.md")),
        "not json",
    ]) + "\n")
    (tdir / "s2.jsonl").write_text(assistant("2026-01-11T00:00:00Z", "3", str(repo / "deleted.md")) + "\n")
    r = run(MINE, repo, "--projects-dir", home / "transcripts", home=home)
    assert r.returncode == 0, r.stderr
    assert "- sessions per month: ~6.0 (--window 2:10.0)" in r.stdout
    assert "~1.5 requests (3 requests in the window)" in r.stdout
    assert "- 1 sessions / 2 reads: CLAUDE.md (~100 tok)" in r.stdout
    assert "- 1 sessions / 1 reads: deleted.md (missing)" in r.stdout
    assert "- +1 extra reads: CLAUDE.md (~100 tok)" in r.stdout


def test_miner_without_transcripts_says_so(tmp_path):
    home, repo = project(tmp_path)
    r = run(MINE, repo, "--projects-dir", home / "transcripts", home=home)
    assert r.returncode == 0
    assert "No transcripts found" in r.stdout
