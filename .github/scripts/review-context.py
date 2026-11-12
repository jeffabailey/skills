#!/usr/bin/env python3
"""Build deterministic scope and provenance facts for the fitness review agent."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

DATA_NAME = "data"
ACCESSIBILITY_NAME = "accessibility"
FRONTEND_SUFFIXES = {".html", ".css", ".jsx", ".tsx", ".vue", ".svelte"}
DATA_SUFFIXES = {".sql"}
DATA_TERMS = ("create table", "alter table", "sqlalchemy", "django", "prisma", "alembic", "flyway", "sequelize", "gorm", "diesel")


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
    if path.suffix.lower() in DATA_SUFFIXES:
        return True
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False
    return any(term in text for term in DATA_TERMS) or any(
        part.lower() in {"migrations", "migration", "schema"} for part in path.parts
    )


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("--prompt", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    context = build_context(args.repo.resolve(), args.prompt.resolve() if args.prompt else None)
    print(json.dumps(context, indent=2, sort_keys=True) if args.json else render(context), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
