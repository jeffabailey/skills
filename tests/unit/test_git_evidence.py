"""git-evidence.sh (review-process): README stale-path classification."""

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "skills/review-process/scripts/git-evidence.sh"
)

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")

README = """# Fixture
Models: `anthropic/claude-opus-5-5`, `openai/gpt-4o`, `sentence-transformers/all-MiniLM-L6-v2`.
More: `meta-llama/Llama-3.1-8B-Instruct`, `mistralai/Mistral-7B-v0.1`.
Not paths: `github.com/acme/widget`, `v1.2/v1.3`, `node/18.x`, `lodash/fp`, `application/json`.
Also: `actions/checkout@v4`, `--input/--output`, `ghcr.io/acme/app:1.0`.
Fine: `scripts/build.sh`, [usage](scripts/build.sh#usage).
Stale: `scripts/deploy.sh`, `tools/old.py`, `src/main.py`, [guide](docs/guide.md#install).
Relative: `references/checklist.md`.
Generated: `out/report.md`.
Run: `python run.py`.
    cd scripts && ls
    cd ../tool-s
    cd /path/to/project
Docs: see SETUP.md, RUN.md, GONE.md and `mkdocs.yml`; edit `Makefile`.
Generic: every skill has a SKILL.md. Ignored: `local.json`.
Not files: `example.com`, `gpt-4o`, `v1.2.json`, `lodash.debounce`, `-o.txt`.

```bash
uv run scripts/build.sh
cd tools2 && python ok.py
python ok.py
cd ../sub
python helper.py
```

```bash
cd <project-name>
uv run test_suite.py
```
"""

NOT_PATHS = [
    "anthropic/claude-opus-5-5",
    "openai/gpt-4o",
    "sentence-transformers/all-MiniLM-L6-v2",
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-v0.1",
    "github.com/acme/widget",
    "v1.2/v1.3",
    "node/18.x",
    "lodash/fp",
    "application/json",
    "actions/checkout@v4",
    "--input/--output",
    "ghcr.io/acme/app:1.0",
    "example.com",
    "gpt-4o",
    "v1.2.json",
    "lodash.debounce",
    "-o.txt",
]


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def section(out, name):
    """Lines under a `name (...):` header up to the next unindented line."""
    lines = out.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(name + " "))
    body = []
    for line in lines[start + 1 :]:
        if not line.startswith("  "):
            break
        body.append(line)
    return "\n".join(body)


@pytest.fixture(scope="module")
def output(tmp_path_factory):
    repo = tmp_path_factory.mktemp("repo")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "t")
    for rel in (
        "scripts/build.sh",
        "tools/old.py",
        "skills/a/references/checklist.md",
        ".github/pull_request_template.md",
        "SETUP.md",
        ".github/RUN.md",
        "mkdocs.yml",
        "tools2/ok.py",
        "tools2/helper.py",
        "sub/keep.txt",
        "a/test_suite.py",
        "b/test_suite.py",
        "a/SKILL.md",
        "b/SKILL.md",
        "c/SKILL.md",
    ):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text("x\n")
    (repo / ".gitignore").write_text("out/\nlocal.json\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "feat: init")
    git(repo, "rm", "-q", "tools/old.py")
    git(repo, "commit", "-qm", "chore: drop old tool")
    (repo / "README.md").write_text(README)
    git(repo, "add", "README.md")
    git(repo, "commit", "-qm", "docs: readme")
    proc = subprocess.run(
        ["bash", str(SCRIPT), str(repo)], capture_output=True, text=True, timeout=60
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


@pytest.mark.parametrize("token", NOT_PATHS)
def test_non_paths_are_not_reported_missing(output, token):
    assert token not in section(output, "readme_paths_missing")


@pytest.mark.parametrize(
    "expected",
    [
        "scripts/deploy.sh (never tracked)",
        "tools/old.py (deleted or renamed in",
        "src/main.py (never tracked)",
        "docs/guide.md (never tracked)",
        "python run.py (no such script anywhere)",
        "cd ../tool-s (no such directory anywhere in the repo)",
    ],
)
def test_real_stale_references_are_reported(output, expected):
    assert expected in section(output, "readme_paths_missing")


def test_existing_and_absolute_references_are_quiet(output):
    missing = section(output, "readme_paths_missing")
    assert "scripts/build.sh" not in missing
    assert "cd scripts" not in missing
    assert "/path/to/project" not in missing


def test_subdirectory_relative_path_is_classified_elsewhere(output):
    assert "references/checklist.md -> skills/a/references/checklist.md" in section(
        output, "readme_paths_elsewhere"
    )


def test_gitignored_output_is_not_a_defect(output):
    assert "out/report.md" in section(output, "readme_paths_ignored")
    assert "out/report.md" not in section(output, "readme_paths_missing")


def test_model_ids_are_listed_as_skipped(output):
    assert "anthropic/claude-opus-5-5" in section(output, "readme_tokens_skipped")


def test_presence_check_is_case_exact(output):
    # macOS filesystems are case-insensitive; only the tracked spelling counts.
    assert "present: .github/pull_request_template.md" in output
    assert "PULL_REQUEST_TEMPLATE.md" not in output


# Gap: command file arguments resolve from the preceding `cd` in the same block.
def test_script_resolved_from_preceding_cd(output):
    elsewhere = section(output, "readme_paths_elsewhere")
    assert "python helper.py -> runs from sub/ (preceding cd)" in elsewhere
    assert "tools2/helper.py" in elsewhere


def test_script_with_placeholder_cd_lists_where_it_exists(output):
    elsewhere = section(output, "readme_paths_elsewhere")
    assert "uv run test_suite.py -> runs from unresolvable cd <project-name>" in elsewhere
    assert "a/test_suite.py, b/test_suite.py" in elsewhere


def test_script_after_block_reset_runs_from_doc_dir(output):
    # A script before any cd runs from the doc's directory; the second
    # `python ok.py` follows `cd tools2 &&` earlier in the block, so it resolves.
    elsewhere = section(output, "readme_paths_elsewhere")
    missing = section(output, "readme_paths_missing")
    assert "ok.py" not in elsewhere + missing
    assert "uv run scripts/build.sh" not in elsewhere + missing


# Gap: bare doc/config filenames with no slash.
def test_bare_doc_name_found_only_in_subdirectory_is_elsewhere(output):
    assert "RUN.md -> .github/RUN.md" in section(output, "readme_paths_elsewhere")


def test_bare_doc_name_that_exists_nowhere_is_missing(output):
    assert "GONE.md (bare name; no tracked file has this name)" in section(
        output, "readme_paths_missing"
    )


@pytest.mark.parametrize("name", ["SETUP.md", "mkdocs.yml", "SKILL.md", "local.json"])
def test_bare_names_that_resolve_are_not_missing(output, name):
    assert name not in section(output, "readme_paths_missing")


def test_bare_backticked_makefile_is_checked(output):
    assert "Makefile (bare name; no tracked file has this name)" in section(
        output, "readme_paths_missing"
    )
