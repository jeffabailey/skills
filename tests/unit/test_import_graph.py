"""skills/review-architecture/scripts/import_graph.py: import resolution and file collection."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "skills/review-architecture/scripts/import_graph.py"
spec = importlib.util.spec_from_file_location("import_graph", SCRIPT)
import_graph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(import_graph)


def write(root, files):
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


def edges(root):
    graph = import_graph.build(root, include_tests=False)
    return {(node["module"], dst) for node in graph["nodes"] for dst in node["imports"]}


def test_a_stdlib_submodule_does_not_match_a_local_module_with_the_same_leaf_name(tmp_path):
    root = write(tmp_path / "proj", {"app.py": "import logging.config\n",
                                     "config.py": "import app\n"})
    assert edges(root) == {("config", "app")}


def test_a_third_party_from_import_does_not_match_a_local_leaf(tmp_path):
    root = write(tmp_path / "proj", {"app.py": "from requests.utils import quote\n",
                                     "utils.py": ""})
    assert edges(root) == set()


def test_an_absolute_import_through_the_root_package_still_resolves(tmp_path):
    root = write(tmp_path / "pkg", {"__init__.py": "", "a.py": "from pkg.b import x\n",
                                    "b.py": "x = 1\n"})
    assert edges(root) == {("a", "b")}


def test_an_absolute_import_through_parent_packages_still_resolves(tmp_path):
    write(tmp_path / "top", {"__init__.py": "", "sub/__init__.py": "",
                             "sub/a.py": "import top.sub.b\n", "sub/b.py": ""})
    assert edges(tmp_path / "top" / "sub") >= {("a", "b")}


def test_skipped_directories_are_never_walked(tmp_path, monkeypatch):
    root = write(tmp_path / "proj", {"app.py": "", "node_modules/dep/index.js": "",
                                     ".venv/lib/x.py": ""})
    visited = []
    real_walk = import_graph.os.walk

    def spy(top, *args, **kwargs):
        for dirpath, dirnames, filenames in real_walk(top, *args, **kwargs):
            visited.append(Path(dirpath).name)
            yield dirpath, dirnames, filenames

    monkeypatch.setattr(import_graph.os, "walk", spy)
    files, _ = import_graph.collect(root, include_tests=False)
    assert [p.name for p in files] == ["app.py"]
    assert not {"node_modules", "dep", ".venv", "lib"} & set(visited)


@pytest.mark.parametrize("inits", [
    ["sub/__init__.py"],   # ROOT is a package, its parent is a namespace package
    [],                    # PEP 420: no __init__.py anywhere
    ["__init__.py"],       # parent is a package, ROOT is a namespace package
])
def test_a_fully_qualified_import_resolves_through_namespace_packages(tmp_path, inits):
    write(tmp_path / "top", {**{rel: "" for rel in inits},
                             "sub/a.py": "import top.sub.b\nfrom top.sub.c import y\n",
                             "sub/b.py": "", "sub/c.py": "y = 1\n"})
    assert edges(tmp_path / "top" / "sub") == {("a", "b"), ("a", "c")}
