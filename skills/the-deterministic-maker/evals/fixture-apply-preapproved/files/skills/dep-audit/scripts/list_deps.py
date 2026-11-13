#!/usr/bin/env python3
"""List Python and npm dependencies and whether each is pinned.

Usage: list_deps.py <project-dir>
"""
import json
import re
import sys
from pathlib import Path


def python_deps(root: Path):
    path = root / "requirements.txt"
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        m = re.match(r"([A-Za-z0-9_.\-\[\]]+)\s*(.*)", line)
        yield m.group(1), m.group(2) or "*", "requirements.txt", m.group(2).startswith("==")


def npm_deps(root: Path):
    path = root / "package.json"
    if not path.is_file():
        return
    data = json.loads(path.read_text())
    for key in ("dependencies", "devDependencies"):
        for name, spec in sorted(data.get(key, {}).items()):
            yield name, spec, f"package.json:{key}", bool(re.match(r"\d", spec))


def main():
    if len(sys.argv) != 2 or not Path(sys.argv[1]).is_dir():
        sys.exit("usage: list_deps.py <project-dir>")
    root = Path(sys.argv[1])
    rows = sorted(list(python_deps(root)) + list(npm_deps(root)))
    for name, spec, source, pinned in rows:
        print(f"{name}\t{spec}\t{source}\t{'pinned' if pinned else 'unpinned'}")
    unpinned = sum(1 for r in rows if not r[3])
    print(f"total {len(rows)}, pinned {len(rows) - unpinned}, unpinned {unpinned}")


if __name__ == "__main__":
    main()
