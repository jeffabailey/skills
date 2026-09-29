"""CI audit: refuse inline weight tables and direct config loads in skill prose."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_INLINE_WEIGHTS = re.compile(r'"weights"\s*:\s*\{')
_DIRECT_LOAD = re.compile(r"(json\.load.*fitness-config\.json|open.*fitness-config\.json)")

Hit = tuple[Path, int, str]


def _audited_files(repo_root: Path) -> list[Path]:
    """The review skills, the fitness-config-init guide (BR-2) and the canonical prompt."""
    files: list[Path] = []
    skills = repo_root / "skills"
    if skills.is_dir():
        files.extend(sorted(skills.glob("review-*/SKILL.md")))
        init_guide = skills / "fitness-config-init" / "SKILL.md"
        if init_guide.is_file():
            files.append(init_guide)
    prompt = repo_root / ".github" / "fitness-review-prompt.md"
    if prompt.is_file():
        files.append(prompt)
    return files


def _lines_of(path: Path) -> list[str]:
    """The file's lines; an unreadable or non-UTF-8 file has none to audit."""
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return []


def _matching_lines(texts: list[tuple[Path, list[str]]], pattern: re.Pattern) -> list[Hit]:
    return [(path, lineno, line.strip())
            for path, lines in texts
            for lineno, line in enumerate(lines, start=1)
            if pattern.search(line)]


def _report(title: str, hits: list[Hit], fix: str) -> None:
    print(title, file=sys.stderr)
    for path, lineno, line in hits:
        print(f"  {path}:{lineno}: {line}", file=sys.stderr)
    print(fix, file=sys.stderr)


def cmd_audit(repo_root: Path) -> int:
    """`audit` (BR-5 / FR-7 / US-08), run by CI: fail when skill prose inlines weights
    or reads the config directly.

    Flags an inline `"weights": {` table (ADR-002) or a direct json.load/open of
    the config file (AC-08.4) and names every offender. Exit 0 = clean.
    """
    files = _audited_files(repo_root)
    texts = [(path, _lines_of(path)) for path in files]
    inline_hits = _matching_lines(texts, _INLINE_WEIGHTS)
    direct_hits = _matching_lines(texts, _DIRECT_LOAD)

    if not inline_hits and not direct_hits:
        print(f"Audit clean: scanned {len(files)} SKILL.md / prompt files; "
              "no inline weight tables, no direct config loads.")
        return 0
    if inline_hits:
        _report("Inline weight tables found (forbidden by ADR-002 / FR-7):", inline_hits,
                "  Fix: replace the inline table with a CLI invocation: "
                "python3 scripts/fitness-config.py show --path <target>")
    if direct_hits:
        _report("Direct fitness-config.json loads found (forbidden by US-08 / AC-08.4):", direct_hits,
                "  Fix: invoke the resolver CLI instead of reading the file directly.")
    return 1
