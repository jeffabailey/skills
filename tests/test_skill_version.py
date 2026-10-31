"""Tests for skills/version-skills/scripts/skill_version.py, run in throwaway repos."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "skills" / "version-skills" / "scripts" / "skill_version.py"
MANIFESTS = ("plugin.json", ".claude-plugin/plugin.json")


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def run(repo, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True, text=True)


def write_skill(repo, name, extra=""):
    path = repo / "skills" / name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nname: {name}\ndescription: d\n{extra}---\n\nbody\n")
    return path


def plugin_versions(repo):
    return {json.loads((repo / name).read_text())["version"] for name in MANIFESTS}


@pytest.fixture
def repo(tmp_path):
    (tmp_path / ".claude-plugin").mkdir()
    for name in MANIFESTS:
        (tmp_path / name).write_text('{\n  "$schema": "https://x/1.0.0/s.json",\n  "version": "1.5.0"\n}\n')
    write_skill(tmp_path, "one")
    write_skill(tmp_path, "two")
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    assert run(tmp_path, "bump", "minor", "--all").returncode == 0
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def test_adoption_writes_initial_versions_and_raises_the_plugin_once(repo):
    assert 'metadata:\n  version: "1.0.0"\n---' in (repo / "skills/one/SKILL.md").read_text()
    assert plugin_versions(repo) == {"1.6.0"}
    assert run(repo, "check").returncode == 0


def test_check_fails_on_a_reference_change_without_a_bump(repo):
    (repo / "skills/one/references").mkdir()
    (repo / "skills/one/references/x.md").write_text("x\n")
    result = run(repo, "check")
    assert result.returncode == 1
    assert "one: changed since HEAD" in result.stderr
    assert "plugin: skills changed" in result.stderr


def test_bump_defaults_to_changed_skills_and_is_safe_to_rerun(repo):
    (repo / "skills/one/SKILL.md").write_text((repo / "skills/one/SKILL.md").read_text() + "more\n")
    for _ in range(2):
        assert "one: 1.0.1" in run(repo, "bump", "patch").stdout
    assert 'version: "1.0.0"' in (repo / "skills/two/SKILL.md").read_text()
    assert plugin_versions(repo) == {"1.6.1"}
    assert run(repo, "check").returncode == 0


def test_a_lower_level_keeps_the_higher_plugin_version(repo):
    run(repo, "bump", "minor", "one")
    run(repo, "bump", "patch", "two")
    assert plugin_versions(repo) == {"1.7.0"}


def test_new_skill_starts_at_initial_version_and_ignores_a_body_example(repo):
    path = write_skill(repo, "fresh")
    path.write_text(path.read_text() + 'metadata:\n  version: "9.9.9"\n')
    assert run(repo, "check").returncode == 1
    run(repo, "bump", "patch")
    text = path.read_text()
    assert 'metadata:\n  version: "1.0.0"\n---' in text
    assert text.endswith('metadata:\n  version: "9.9.9"\n')
    assert run(repo, "check").returncode == 0


def test_version_joins_an_existing_metadata_block(repo):
    write_skill(repo, "one", "metadata:\n  author: x\n")
    run(repo, "bump", "patch", "one")
    assert 'metadata:\n  version: "1.0.1"\n  author: x\n' in (repo / "skills/one/SKILL.md").read_text()


def test_deleted_skill_raises_the_plugin_when_named(repo):
    git(repo, "rm", "-rq", "skills/one")
    assert "plugin: skills changed" in run(repo, "check").stderr
    assert run(repo, "bump", "major", "one").returncode == 0
    assert plugin_versions(repo) == {"2.0.0"}
    assert run(repo, "check").returncode == 0


@pytest.mark.parametrize("name", ["no-such", "\x1b[34mone\x1b[0m"])
def test_unknown_skill_changes_nothing(repo, name):
    result = run(repo, "bump", "patch", name)
    assert result.returncode == 2
    assert "no such skill" in result.stderr
    assert plugin_versions(repo) == {"1.6.0"}


def test_check_reports_disagreeing_manifests(repo):
    (repo / "plugin.json").write_text('{"version": "1.6.1"}\n')
    assert "manifests disagree" in run(repo, "check").stderr


def test_repo_without_manifests_versions_only_skills(tmp_path):
    write_skill(tmp_path, "solo")
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    assert "solo: 1.0.0" in run(tmp_path, "bump", "patch", "--all").stdout
    assert run(tmp_path, "check").returncode == 0
