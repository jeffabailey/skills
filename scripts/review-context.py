#!/usr/bin/env python3
"""Build deterministic scope and provenance facts for the fitness review skills.

review-context.py <repo> [--prompt FILE] [--json]   provenance block for the CI review
review-context.py <target> --inventory [--all]      scope inventory for the review skills

--inventory prints, for a directory or file: files and lines per language, test files
per runner, CI files, Dockerfiles and compose files, IaC, migrations and schemas,
manifests with lockfiles, and the data and frontend signal counts. Paths are relative
to the repository root. Lists show 5 paths unless --all. Build and vendor directories
are skipped and counted. Exit 2 with one line when the target does not exist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

DATA_NAME = "data"
ACCESSIBILITY_NAME = "accessibility"
FRONTEND_SUFFIXES = {".html", ".css", ".jsx", ".tsx", ".vue", ".svelte"}
DATA_SUFFIXES = {".sql"}
DATA_SOURCE_SUFFIXES = {".c", ".cpp", ".cs", ".go", ".java", ".js", ".jsx", ".php", ".py", ".rb", ".rs", ".ts", ".tsx"}
DATA_MANIFEST_NAMES = {"docker-compose.yml", "docker-compose.yaml", "package.json", "pyproject.toml", "pom.xml", "requirements.txt"}
DATA_DIRECTORIES = {"migration", "migrations", "schema", "schemas"}
IGNORED_DATA_DIRECTORIES = {".git", ".venv", "docs", "skills", "tests"}
DATABASE_IMPORT = re.compile(
    r"(?:import\s+(?:sqlite3|sqlalchemy|psycopg|pymongo|redis)|"
    r"from\s+(?:django\.db|sqlalchemy|psycopg|pymongo|redis)|"
    r"require\(['\"](?:pg|mysql|sequelize|prisma|redis)['\"]\))",
    re.IGNORECASE,
)
SELF_NAME = "review-context.py"
DATABASE_SQL = re.compile(r"\b(?:create\s+table|alter\s+table|select\s+.+\s+from|insert\s+into)\b", re.IGNORECASE)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git(repo: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        return "unavailable"


def tracked_files(repo: Path) -> list[str]:
    return [line for line in git(repo, "ls-files", "-z").split("\0") if line]


def file_has_data_signal(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if parts & IGNORED_DATA_DIRECTORIES or path.name == SELF_NAME or (
        ".github" in parts and "scripts" in parts
    ):
        return False
    if parts & DATA_DIRECTORIES or path.suffix.lower() in DATA_SUFFIXES:
        return True
    if path.name.lower() not in DATA_MANIFEST_NAMES and path.suffix.lower() not in DATA_SOURCE_SUFFIXES:
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return bool(DATABASE_IMPORT.search(text) or DATABASE_SQL.search(text))


def build_context_from_files(repo: Path, files: list[str], prompt: Path | None = None) -> dict:
    frontend = [name for name in files if Path(name).suffix.lower() in FRONTEND_SUFFIXES]
    data = [name for name in files if file_has_data_signal(repo / name)]
    config = repo / "fitness-config.json"
    context = {
        "commit": git(repo, "rev-parse", "HEAD") if (repo / ".git").exists() else "not-a-git-checkout",
        "tree_sha256": sha256_bytes("\n".join(files).encode()),
        "tracked_file_count": len(files),
        "config_sha256": sha256_bytes(config.read_bytes()) if config.is_file() else None,
        "prompt_sha256": sha256_bytes(prompt.read_bytes()) if prompt and prompt.is_file() else None,
        "applicability": {
            DATA_NAME: bool(data),
            ACCESSIBILITY_NAME: bool(frontend),
        },
        "signals": {DATA_NAME: data, ACCESSIBILITY_NAME: frontend},
    }
    return context


def build_context(repo: Path, prompt: Path | None = None) -> dict:
    return build_context_from_files(repo, tracked_files(repo), prompt)


def render(context: dict) -> str:
    applicability = context["applicability"]
    data_reason = "database/data signals found" if applicability[DATA_NAME] else "no database code detected"
    frontend_reason = "frontend files found" if applicability[ACCESSIBILITY_NAME] else "no frontend code detected"
    return "\n".join([
        "## Deterministic Review Context",
        "Use these machine-generated facts as review constraints; do not override applicability.",
        f"- Reviewed commit: `{context['commit']}`",
        f"- Tracked file inventory: `{context['tracked_file_count']}` files; SHA-256 `{context['tree_sha256']}`",
        f"- Root fitness-config.json SHA-256: `{context['config_sha256'] or 'absent'}`",
        f"- Prompt SHA-256 before this context is added: `{context['prompt_sha256'] or 'unknown'}`",
        f"- Data domain: `{'applicable' if applicability[DATA_NAME] else 'N/A'} — {data_reason}`",
        f"- Accessibility domain: `{'applicable' if applicability[ACCESSIBILITY_NAME] else 'N/A'} — {frontend_reason}`",
        "If a domain is N/A here, report it as skipped and do not assign it a score.",
        "",
    ])


# --- scope inventory -------------------------------------------------------

SKIPPED_DIRECTORIES = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "vendor", "third_party",
    "dist", "build", "target", "_build", "deps", "obj", "__pycache__", ".tox",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".next", ".terraform", "coverage",
}
LANGUAGES = {
    ".py": "Python", ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".go": "Go",
    ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".rb": "Ruby", ".php": "PHP",
    ".cs": "C#", ".c": "C", ".h": "C", ".cpp": "C++", ".cc": "C++", ".hpp": "C++",
    ".swift": "Swift", ".ex": "Elixir", ".exs": "Elixir", ".sh": "Shell",
    ".bash": "Shell", ".zsh": "Shell", ".sql": "SQL", ".html": "HTML", ".css": "CSS",
    ".scss": "CSS", ".vue": "Vue", ".svelte": "Svelte", ".tf": "Terraform",
    ".md": "Markdown", ".yml": "YAML", ".yaml": "YAML", ".json": "JSON", ".toml": "TOML",
}
LOCKFILES = {
    "package.json": ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "bun.lock"),
    "pyproject.toml": ("uv.lock", "poetry.lock", "pdm.lock"),
    "Pipfile": ("Pipfile.lock",),
    "go.mod": ("go.sum",),
    "Cargo.toml": ("Cargo.lock",),
    "Gemfile": ("Gemfile.lock",),
    "composer.json": ("composer.lock",),
    "mix.exs": ("mix.lock",),
}
UNLOCKED_MANIFESTS = re.compile(r"^(requirements.*\.txt|pom\.xml|build\.gradle(\.kts)?|.+\.csproj)$")
LOCKFILE_NAMES = {name for names in LOCKFILES.values() for name in names}
TEST_RUNNERS = [
    ("pytest", re.compile(r"^(test_.+|.+_test)\.py$")),
    ("go test", re.compile(r"_test\.go$")),
    ("js/ts", re.compile(r"\.(test|spec)\.(js|jsx|mjs|cjs|ts|tsx)$")),
    ("ExUnit", re.compile(r"_test\.exs$")),
    ("RSpec", re.compile(r"_spec\.rb$")),
    ("minitest", re.compile(r"_test\.rb$")),
    ("JUnit", re.compile(r"Tests?\.(java|kt)$")),
    ("dotnet", re.compile(r"Tests?\.cs$")),
    ("PHPUnit", re.compile(r"Test\.php$")),
    ("BDD", re.compile(r"\.feature$")),
    ("bats", re.compile(r"\.bats$")),
    ("shell", re.compile(r"^(test[_-].+|.+[_-]tests?)\.sh$")),
]
TEST_CONFIG = re.compile(
    r"^(pytest\.ini|tox\.ini|\.coveragerc|phpunit\.xml(\.dist)?|\.mocharc.*|"
    r"(jest|vitest|playwright|cypress|karma)\.config\..+)$"
)
CI_NAMES = {
    ".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml", ".travis.yml",
    "bitbucket-pipelines.yml", ".pre-commit-config.yaml",
}
CONTAINER = re.compile(r"^(Dockerfile.*|Containerfile.*|.+\.dockerfile|(docker-)?compose.*\.ya?ml)$", re.IGNORECASE)
IAC_NAMES = {"Chart.yaml", "kustomization.yaml", "kustomization.yml", "Pulumi.yaml", "serverless.yml"}
IAC_SUFFIXES = {".tf", ".tfvars", ".bicep"}
IAC_DIRECTORIES = {"k8s", "kubernetes", "manifests", "helm"}
MIGRATION_DIRECTORIES = {"migrations", "migration", "migrate", "alembic"}
SCHEMA_NAMES = {"schema.rb", "schema.sql", "structure.sql"}
SCHEMA_SUFFIXES = {".sql", ".prisma"}
MAX_LINE_COUNT_BYTES = 1_000_000
LIST_CAP = 5
CATEGORIES = ["ci", "containers", "iac", "migrations/schemas", "test config"]


def list_files(target: Path) -> tuple[Path, list[str], str]:
    """Return (root, paths relative to root, source) for a directory or file target."""
    directory = target if target.is_dir() else target.parent
    pathspec = [] if target.is_dir() else ["--", target.name]
    try:
        root = subprocess.check_output(
            ["git", "-C", str(directory), "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        out = subprocess.check_output(
            ["git", "-C", str(directory), "ls-files", "-z", "--full-name", "-co", "--exclude-standard", *pathspec],
            text=True, stderr=subprocess.DEVNULL,
        )
        return Path(root), sorted({name for name in out.split("\0") if name}), "git"
    except (subprocess.CalledProcessError, OSError):
        pass
    if target.is_file():
        return directory, [target.name], "walk"
    names = []
    for current, dirs, files in os.walk(target):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        names.extend(str((Path(current) / name).relative_to(target)) for name in files)
    return target, sorted(names), "walk"


def count_lines(path: Path) -> int:
    try:
        if path.stat().st_size > MAX_LINE_COUNT_BYTES:
            return 0
        return path.read_bytes().count(b"\n")
    except OSError:
        return 0


def classify(name: str) -> list[str]:
    path = Path(name)
    parts = {part.lower() for part in path.parts[:-1]}
    base, suffix = path.name, path.suffix.lower()
    found = []
    if base in CI_NAMES or ".circleci" in parts or ".buildkite" in parts or (
        {".github", "workflows"} <= parts and suffix in {".yml", ".yaml"}
    ):
        found.append("ci")
    if CONTAINER.match(base):
        found.append("containers")
    if base in IAC_NAMES or suffix in IAC_SUFFIXES or (parts & IAC_DIRECTORIES and suffix in {".yml", ".yaml"}):
        found.append("iac")
    if parts & MIGRATION_DIRECTORIES or base in SCHEMA_NAMES or suffix in SCHEMA_SUFFIXES:
        found.append("migrations/schemas")
    return found


def is_test_config(path: Path) -> bool:
    if TEST_CONFIG.match(path.name):
        return True
    if path.name not in {"pyproject.toml", "setup.cfg"}:
        return False
    try:
        return bool(re.search(r"^\[(tool[.:]pytest|tool\.coverage|coverage:)", path.read_text(errors="ignore"), re.MULTILINE))
    except OSError:
        return False


def build_inventory(target: Path) -> dict:
    root, names, source = list_files(target)
    skipped: Counter = Counter()
    kept = []
    for name in names:
        hit = next((part for part in Path(name).parts[:-1] if part in SKIPPED_DIRECTORIES), None)
        if hit:
            skipped[hit] += 1
        else:
            kept.append(name)
    languages: dict[str, list[int]] = {}
    tests: dict[str, list[str]] = {}
    categories: dict[str, list[str]] = {key: [] for key in CATEGORIES}
    manifests = []
    present = set(kept)
    for name in kept:
        path = Path(name)
        language = LANGUAGES.get(path.suffix.lower())
        if language and path.name not in LOCKFILE_NAMES:
            entry = languages.setdefault(language, [0, 0])
            entry[0] += 1
            entry[1] += count_lines(root / name)
        runner = next((label for label, pattern in TEST_RUNNERS if pattern.search(path.name)), None)
        if runner:
            tests.setdefault(runner, []).append(name)
        for key in classify(name):
            categories[key].append(name)
        if is_test_config(root / name):
            categories["test config"].append(name)
        if path.name in LOCKFILES:
            lock = next((lock for lock in LOCKFILES[path.name] if str(path.parent / lock) in present), None)
            manifests.append([name, lock or "NO LOCKFILE"])
        elif UNLOCKED_MANIFESTS.match(path.name):
            manifests.append([name, None])
    return {
        "target": str(target.relative_to(root)) if target.is_relative_to(root) else str(target),
        "source": source,
        "files": len(kept),
        "skipped": dict(sorted(skipped.items())),
        "languages": {key: {"files": value[0], "lines": value[1]} for key, value in languages.items()},
        "tests": tests,
        "categories": categories,
        "manifests": manifests,
        "frontend": [name for name in kept if Path(name).suffix.lower() in FRONTEND_SUFFIXES],
        "data": [name for name in kept if file_has_data_signal(root / name)],
    }


def capped(names: list[str], show_all: bool) -> str:
    if not names:
        return "none"
    shown = names if show_all else names[:LIST_CAP]
    more = len(names) - len(shown)
    return f"{len(names)}: " + ", ".join(shown) + (f", +{more} more" if more else "")


def render_inventory(inventory: dict, show_all: bool = False) -> str:
    skipped = inventory["skipped"]
    skipped_text = ", ".join(f"{name} {count}" for name, count in skipped.items()) or "none"
    languages = sorted(inventory["languages"].items(), key=lambda item: (-item[1]["lines"], item[0]))
    lines = [
        "## Scope Inventory",
        "Machine-generated; trust it instead of running ls, find, wc, or git ls-files.",
        f"- target: {inventory['target']} (from the repository root; listed by {inventory['source']})",
        f"- files: {inventory['files']}; skipped in build/vendor dirs: {skipped_text}",
        "- languages (files/lines): "
        + (", ".join(f"{name} {value['files']}/{value['lines']}" for name, value in languages) or "none"),
    ]
    if inventory["tests"]:
        for runner, names in sorted(inventory["tests"].items()):
            directories = Counter(str(Path(name).parent) for name in names)
            top = sorted(directories.items(), key=lambda item: (-item[1], item[0]))
            shown = top if show_all else top[:LIST_CAP]
            more = len(top) - len(shown)
            lines.append(
                f"- tests, {runner}: {len(names)} files in "
                + ", ".join(f"{directory}/ {count}" for directory, count in shown)
                + (f", +{more} more dirs" if more else "")
            )
    else:
        lines.append("- tests: none")
    for key in CATEGORIES:
        lines.append(f"- {key}: {capped(inventory['categories'][key], show_all)}")
    manifests = [f"{name} [{lock}]" if lock else name for name, lock in inventory["manifests"]]
    lines.append(f"- manifests [lockfile]: {capped(manifests, show_all)}")
    lines.append(f"- frontend files: {capped(inventory['frontend'], show_all)}")
    lines.append(f"- data signals: {capped(inventory['data'], show_all)}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("--prompt", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--inventory", action="store_true", help="print the scope inventory instead")
    parser.add_argument("--all", action="store_true", help="with --inventory: do not cap lists")
    args = parser.parse_args()
    if not args.repo.exists():
        print(f"error: target not found: {args.repo}", file=sys.stderr)
        return 2
    if args.inventory:
        inventory = build_inventory(args.repo.resolve())
        text = json.dumps(inventory, indent=2, sort_keys=True) + "\n" if args.json else render_inventory(inventory, args.all)
        print(text, end="")
        return 0
    context = build_context(args.repo.resolve(), args.prompt.resolve() if args.prompt else None)
    print(json.dumps(context, indent=2, sort_keys=True) if args.json else render(context), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
