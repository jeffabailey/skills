import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / ".github/scripts/review-context.py"
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
