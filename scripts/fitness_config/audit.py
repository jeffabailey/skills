"""CI audit: refuse inline weight tables and direct config loads in skill prose."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_AUDIT_INLINE_WEIGHTS_PATTERN = r'"weights"\s*:\s*\{'
_AUDIT_DIRECT_LOAD_PATTERN = r"(json\.load.*fitness-config\.json|open.*fitness-config\.json)"


def cmd_audit(repo_root: Path) -> int:
    """`audit` (BR-5 / FR-7 / US-08), run by CI: fail when skill prose inlines weights or reads the config directly.

    Scans skills/review-*/SKILL.md, skills/fitness-config-init/SKILL.md (BR-2)
    and .github/fitness-review-prompt.md for an inline `"weights": {` table
    (ADR-002) or a direct json.load/open of the config file (AC-08.4); names
    every offender. Exit 0 = clean.
    """
    inline = re.compile(_AUDIT_INLINE_WEIGHTS_PATTERN)
    direct_load = re.compile(_AUDIT_DIRECT_LOAD_PATTERN)

    candidates: list[Path] = []
    src_dir = repo_root / "skills"
    if src_dir.is_dir():
        for skill in sorted(src_dir.glob("review-*/SKILL.md")):
            candidates.append(skill)
        init_guide = src_dir / "fitness-config-init" / "SKILL.md"
        if init_guide.is_file():
            candidates.append(init_guide)
    prompt = repo_root / ".github" / "fitness-review-prompt.md"
    if prompt.is_file():
        candidates.append(prompt)

    inline_hits: list[tuple[Path, int, str]] = []
    direct_hits: list[tuple[Path, int, str]] = []
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if inline.search(line):
                inline_hits.append((path, lineno, line.strip()))
            if direct_load.search(line):
                direct_hits.append((path, lineno, line.strip()))

    if not inline_hits and not direct_hits:
        print(f"Audit clean: scanned {len(candidates)} SKILL.md / prompt files; no inline weight tables, no direct config loads.")
        return 0

    if inline_hits:
        print("Inline weight tables found (forbidden by ADR-002 / FR-7):", file=sys.stderr)
        for path, lineno, line in inline_hits:
            print(f"  {path}:{lineno}: {line}", file=sys.stderr)
        print("  Fix: replace the inline table with a CLI invocation: python3 scripts/fitness-config.py show --path <target>", file=sys.stderr)

    if direct_hits:
        print("Direct fitness-config.json loads found (forbidden by US-08 / AC-08.4):", file=sys.stderr)
        for path, lineno, line in direct_hits:
            print(f"  {path}:{lineno}: {line}", file=sys.stderr)
        print("  Fix: invoke the resolver CLI instead of reading the file directly.", file=sys.stderr)

    return 1
