import importlib.util
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/review-context.py"
spec = importlib.util.spec_from_file_location("review_context", SCRIPT)
review_context = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review_context)


def test_context_marks_database_free_repo_and_frontend_files(tmp_path):
    (tmp_path / ".git").mkdir()
    files = ["README.md", "src/app.py"]
    for name in files:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("print('ok')\n")

    context = review_context.build_context_from_files(tmp_path, files)

    assert context["applicability"] == {"data": False, "accessibility": False}
    assert context["signals"] == {"data": [], "accessibility": []}


def test_context_detects_data_and_frontend_signals(tmp_path):
    files = ["schema.sql", "templates/index.html", "src/app.py"]
    for name in files:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("CREATE TABLE users (id INT);" if name.endswith(".sql") else "")

    context = review_context.build_context_from_files(tmp_path, files)

    assert context["applicability"] == {"data": True, "accessibility": True}
    assert context["signals"]["data"] == ["schema.sql"]
    assert context["signals"]["accessibility"] == ["templates/index.html"]


def test_prose_and_test_mentions_do_not_activate_data(tmp_path):
    files = ["README.md", "docs/design.md", "tests/test_db.py", "skills/review-data/SKILL.md"]
    for name in files:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("SQLAlchemy migrations and CREATE TABLE are discussed here.")

    context = review_context.build_context_from_files(tmp_path, files)

    assert context["applicability"]["data"] is False
    assert context["signals"]["data"] == []


def test_detector_does_not_activate_itself(tmp_path):
    path = tmp_path / "scripts/review-context.py"
    path.parent.mkdir(parents=True)
    path.write_text("DATA_TERMS = ('sqlalchemy', 'create table')")

    context = review_context.build_context_from_files(tmp_path, [str(path.relative_to(tmp_path))])

    assert context["applicability"]["data"] is False


def test_source_database_import_activates_data(tmp_path):
    path = tmp_path / "src/database.py"
    path.parent.mkdir(parents=True)
    path.write_text("import sqlalchemy\n")

    context = review_context.build_context_from_files(tmp_path, ["src/database.py"])

    assert context["applicability"]["data"] is True
    assert context["signals"]["data"] == ["src/database.py"]


INVENTORY_TREE = {
    "src/app.py": "import os\nprint(os.name)\n",
    "src/db.py": "import sqlalchemy\n",
    "src/util.go": "package util\n",
    "src/util_test.go": "package util\n",
    "tests/test_app.py": "def test_ok():\n    assert True\n",
    "tests/test_db.py": "def test_db():\n    assert True\n",
    "web/app.test.ts": "test('x', () => {})\n",
    "web/index.html": "<html></html>\n",
    ".github/workflows/ci.yml": "name: CI\n",
    ".gitlab-ci.yml": "stages: []\n",
    "Dockerfile": "FROM scratch\n",
    "docker-compose.yml": "services: {}\n",
    "infra/main.tf": "\n",
    "db/migrations/001_init.sql": "CREATE TABLE users (id INT);\n",
    "pyproject.toml": "[tool.pytest.ini_options]\n",
    "uv.lock": "\n",
    "web/package.json": "{}\n",
    "node_modules/left-pad/index.js": "x\n",
    "node_modules/left-pad/index.test.js": "x\n",
}


def write_tree(root, tree):
    for name, text in tree.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def test_inventory_counts_each_category(tmp_path):
    write_tree(tmp_path, INVENTORY_TREE)

    inventory = review_context.build_inventory(tmp_path)

    assert inventory["files"] == 17
    assert inventory["skipped"] == {"node_modules": 2}
    assert inventory["languages"]["Python"] == {"files": 4, "lines": 7}
    assert inventory["languages"]["Go"] == {"files": 2, "lines": 2}
    assert {key: len(value) for key, value in inventory["tests"].items()} == {"pytest": 2, "go test": 1, "js/ts": 1}
    assert inventory["categories"] == {
        "ci": [".github/workflows/ci.yml", ".gitlab-ci.yml"],
        "containers": ["Dockerfile", "docker-compose.yml"],
        "iac": ["infra/main.tf"],
        "migrations/schemas": ["db/migrations/001_init.sql"],
        "test config": ["pyproject.toml"],
    }
    assert inventory["manifests"] == [["pyproject.toml", "uv.lock"], ["web/package.json", "NO LOCKFILE"]]
    assert inventory["frontend"] == ["web/index.html"]
    assert inventory["data"] == ["db/migrations/001_init.sql", "src/db.py"]


def test_inventory_render_is_capped_and_stable(tmp_path):
    write_tree(tmp_path, {f"migrations/{n:03}.sql": "\n" for n in range(8)})

    first = review_context.render_inventory(review_context.build_inventory(tmp_path))
    full = review_context.render_inventory(review_context.build_inventory(tmp_path), show_all=True)

    assert first == review_context.render_inventory(review_context.build_inventory(tmp_path))
    assert "- migrations/schemas: 8: migrations/000.sql, " in first
    assert "migrations/004.sql, +3 more" in first
    assert "migrations/007.sql" in full and "more" not in full
    assert str(tmp_path) not in first


def test_inventory_of_empty_directory_and_single_file(tmp_path):
    empty = review_context.build_inventory(tmp_path)
    assert empty["files"] == 0
    text = review_context.render_inventory(empty)
    assert "- languages (files/lines): none" in text and "- tests: none" in text

    (tmp_path / "one.py").write_text("x = 1\n")
    single = review_context.build_inventory(tmp_path / "one.py")
    assert single["files"] == 1
    assert single["languages"] == {"Python": {"files": 1, "lines": 1}}


def test_missing_target_fails_in_one_line(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path / "nope"), "--inventory"], capture_output=True, text=True
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.strip() == f"error: target not found: {tmp_path / 'nope'}"


def test_default_output_keeps_the_ci_contract(tmp_path):
    (tmp_path / "README.md").write_text("hi\n")
    result = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.startswith("## Deterministic Review Context\n")
    assert "## Scope Inventory" not in result.stdout
