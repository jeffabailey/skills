"""Shared support for the fitness-config-init acceptance suite.

Driving port: `python3 scripts/fitness-config.py` run as a real subprocess
with cwd = the project's anchor (the folder that plays the git top-level).
Driven adapter: the real filesystem under pytest's tmp_path. No mocks.

This module is imported by bare name (the steps/ directory is not a package,
to avoid clashing with the `steps` package of fitness-config-per-directory).
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# tests/acceptance/fitness-config-init/steps/fci_support.py -> repo root
REPO_ROOT = Path(__file__).resolve().parents[4]
RESOLVER = REPO_ROOT / "scripts" / "fitness-config.py"
EXAMPLE_CONFIG = REPO_ROOT / "fitness-config.example.json"
SKILL_DIR = REPO_ROOT / "skills" / "fitness-config-init"
SKILL_GUIDE = SKILL_DIR / "SKILL.md"
PROFILE_CATALOGUE = SKILL_DIR / "references" / "purpose-profiles.md"
SIGNAL_GUIDE = SKILL_DIR / "references" / "purpose-signals.md"
CONFIG = "fitness-config.json"

# Canonical domain order (DEFAULT_WEIGHTS order == example file order).
DOMAINS = [
    "architecture", "security", "reliability", "testing", "performance",
    "algorithms", "data", "accessibility", "process", "maintainability",
]
ARCHETYPES = [
    "database-backend", "web-frontend", "cli-tool",
    "library-sdk", "data-pipeline", "api-service",
]

# Test-side expectations of the built-in defaults (the tests may know them;
# the skill must not). Kept aligned with scripts/fitness_config/model.py.
DEFAULT_WEIGHTS = dict(zip(DOMAINS, [14, 14, 10, 10, 10, 10, 10, 8, 8, 6]))
DEFAULT_STATUS = {"healthy": [8, 10], "needsAttention": [5, 7], "critical": [1, 4]}
DEFAULT_SECURITY = {"confidenceThreshold": 7}
DEFAULT_SCORING = {"goodRange": [8, 10], "badRange": [1, 3]}


def weights(*values: int) -> dict:
    assert len(values) == 10, values
    return dict(zip(DOMAINS, values))


def complete_config(w: dict, *, status: dict | None = None,
                    security: dict | None = None, scoring: dict | None = None) -> dict:
    return {
        "version": 1,
        "weights": dict(w),
        "statusThresholds": copy.deepcopy(status or DEFAULT_STATUS),
        "security": dict(security or DEFAULT_SECURITY),
        "scoring": copy.deepcopy(scoring or DEFAULT_SCORING),
    }


# ---------------------------------------------------------------------------
# Named proposals (from the DISCUSS domain examples)
# ---------------------------------------------------------------------------

PROPOSALS = {
    # US-02 example 1: ledgerd, database-backed service with no UI
    "database-service": complete_config(weights(10, 14, 18, 10, 10, 8, 18, 1, 6, 5)),
    # US-02 example 2: jeffbaileyblog, public static site
    "public-site": complete_config(weights(10, 10, 8, 8, 14, 4, 4, 18, 12, 12)),
    # homelab-cli, Go CLI tool
    "cli-tool": complete_config(weights(12, 12, 10, 14, 8, 10, 4, 4, 12, 14)),
    # fieldnotes/services/billing override
    "billing": complete_config(weights(10, 18, 16, 12, 8, 8, 16, 2, 5, 5)),
}

# ledgerd's June config (US-04): five values differ from "database-service".
JUNE_LEDGERD = complete_config(weights(14, 14, 12, 10, 10, 8, 12, 4, 6, 10))
FIELDNOTES_ROOT = complete_config(weights(12, 14, 12, 10, 10, 8, 14, 8, 6, 6))
STRAY_ABOVE_ANCHOR = {"version": 1, "weights": weights(10, 10, 10, 5, 5, 5, 5, 40, 5, 5)}

for _name, _cfg in {**PROPOSALS, "june": JUNE_LEDGERD, "fieldnotes": FIELDNOTES_ROOT,
                    "stray": STRAY_ABOVE_ANCHOR}.items():
    assert sum(_cfg["weights"].values()) == 100, _name


def proposal(name: str) -> dict:
    return copy.deepcopy(PROPOSALS[name])


# ---------------------------------------------------------------------------
# Realistic, minimal project fixtures (acceptance-criteria.md fixture list)
# ---------------------------------------------------------------------------

PROJECT_FILES: dict[str, dict[str, str]] = {
    "ledgerd": {
        "go.mod": "module github.com/priya/ledgerd\n\ngo 1.22\n\nrequire (\n\tgithub.com/jackc/pgx/v5 v5.5.0\n\tgithub.com/golang-migrate/migrate/v4 v4.17.0\n)\n",
        "migrations/0001_create_accounts.up.sql": "CREATE TABLE accounts (id bigserial PRIMARY KEY);\n",
        "migrations/0002_create_entries.up.sql": "CREATE TABLE entries (id bigserial PRIMARY KEY);\n",
        "deploy/k8s/statefulset.yaml": "kind: StatefulSet\n---\nkind: PodDisruptionBudget\n",
        "README.md": "# ledgerd\n\nDouble-entry ledger service backed by Postgres.\n",
    },
    "jeffbaileyblog": {
        "hugo.toml": "baseURL = 'https://jeffbailey.us/'\n",
        "content/posts/hello.md": "---\ntitle: Hello\n---\n",
        "layouts/_default/single.html": "<article>{{ .Content }}</article>\n",
        ".github/workflows/deploy.yml": "name: Deploy to GitHub Pages\n",
    },
    "homelab-cli": {
        "go.mod": "module github.com/tomas/homelab-cli\n\nrequire github.com/spf13/cobra v1.8.0\n",
        ".goreleaser.yaml": "builds:\n  - main: ./cmd\n",
        "cmd/root.go": "package cmd\n",
    },
    "fieldnotes": {
        "Gemfile": "gem 'rails'\ngem 'pg'\n",
        "app/views/pages/home.html.erb": "<h1>Field notes</h1>\n",
        "services/billing/invoice.rb": "class Invoice; end\n",
        "services/search/indexer.rb": "class Indexer; end\n",
    },
    "geo-notes": {"README.md": "TODO\n"},
}


@dataclass(frozen=True)
class FileState:
    sha256: str
    mtime_ns: int


@dataclass
class ResolverRun:
    args: list[str]
    exit_code: int
    stdout: str
    stderr: str

    @property
    def output(self) -> str:
        return self.stdout + self.stderr

    def describe(self) -> str:
        return (f"fitness-config.py {' '.join(self.args)} -> exit {self.exit_code}\n"
                f"--- stdout ---\n{self.stdout}--- stderr ---\n{self.stderr}")


def run_resolver(cwd: Path, *args: str, stdin_text: str | bytes | None = None) -> ResolverRun:
    """Run the resolver; bytes on stdin are passed through raw (e.g. not UTF-8)."""
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "PYTHONIOENCODING": "utf-8",
    }
    if isinstance(stdin_text, bytes):
        done = subprocess.run(
            [sys.executable, str(RESOLVER), *args],
            cwd=str(cwd), env=env, input=stdin_text, capture_output=True, timeout=30,
        )
        return ResolverRun(list(args), done.returncode,
                           done.stdout.decode("utf-8", errors="replace"),
                           done.stderr.decode("utf-8", errors="replace"))
    done = subprocess.run(
        [sys.executable, str(RESOLVER), *args],
        cwd=str(cwd), env=env, input=stdin_text,
        capture_output=True, text=True, timeout=30,
    )
    return ResolverRun(list(args), done.returncode, done.stdout, done.stderr)


def fingerprint_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Resolver output contract (data-models.md section 6)
# ---------------------------------------------------------------------------

@dataclass
class GateReport:
    """Parsed stdout of `init --path T [--from -] [--dry-run|--expect]`."""

    run: ResolverRun
    status: str | None
    fingerprint: str | None
    header: list[str]
    canonical_text: str | None

    @property
    def diff_lines(self) -> list[str]:
        return [ln for ln in self.header
                if " -> " in ln or re.match(r"^\(\d+ values? unchanged\)$", ln)]

    def header_value(self, key: str) -> str | None:
        for ln in self.header:
            if ln.startswith(f"{key}:"):
                return ln.split(":", 1)[1].strip()
        return None


def parse_gate_report(run: ResolverRun) -> GateReport:
    lines = run.stdout.splitlines(keepends=True)
    status = fingerprint = None
    json_start = None
    for idx, raw in enumerate(lines):
        line = raw.rstrip("\n")
        if status is None and (m := re.match(r"^STATUS:\s*(\S+)", line)):
            status = m.group(1)
        if fingerprint is None and (m := re.match(r"^Proposal:\s*([0-9a-f]{12})\b", line)):
            fingerprint = m.group(1)
        if line == "{":
            json_start = idx
            break
    header_src = lines if json_start is None else lines[:json_start]
    header = [ln.rstrip("\n") for ln in header_src]
    canonical = None if json_start is None else "".join(lines[json_start:])
    return GateReport(run, status, fingerprint, header, canonical)


def require_status(report: GateReport, *allowed: str) -> None:
    assert report.status in allowed, (
        f"expected status {' or '.join(allowed)}, got {report.status!r}\n{report.run.describe()}"
    )


# ---------------------------------------------------------------------------
# Workspace: one folder holding the persona projects (and what sits above them)
# ---------------------------------------------------------------------------

@dataclass
class Workspace:
    root: Path
    read_only_dirs: list[Path] = field(default_factory=list)

    def project(self, name: str) -> Path:
        return self.root / name

    def split_target(self, target: str) -> tuple[Path, str]:
        """'fieldnotes/services/billing' -> (anchor=<ws>/fieldnotes, 'services/billing')."""
        name, _, rest = target.partition("/")
        return self.project(name), (rest or ".")

    def config_path(self, target: str) -> Path:
        anchor, rel = self.split_target(target)
        return (anchor / rel / CONFIG).resolve() if rel != "." else anchor / CONFIG

    def create_project(self, name: str) -> Path:
        anchor = self.project(name)
        anchor.mkdir(parents=True, exist_ok=True)
        for rel, text in PROJECT_FILES.get(name, {}).items():
            path = anchor / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return anchor

    def write_config(self, where: Path, config: dict) -> Path:
        where.mkdir(parents=True, exist_ok=True)
        path = where / CONFIG
        path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return path

    def write_raw(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def make_read_only(self, path: Path) -> None:
        path.chmod(0o555)
        self.read_only_dirs.append(path)

    def restore_permissions(self) -> None:
        for path in self.read_only_dirs:
            if path.exists():
                path.chmod(0o755)

    def snapshot(self) -> dict[str, FileState]:
        """Every file in the workspace: the observable universe for state deltas."""
        out: dict[str, FileState] = {}
        for path in sorted(self.root.rglob("*")):
            if path.is_file():
                stat = path.stat()
                out[path.relative_to(self.root).as_posix()] = FileState(
                    sha256_of_bytes(path.read_bytes()), stat.st_mtime_ns)
        return out

    def key(self, path: Path) -> str:
        return path.resolve().relative_to(self.root.resolve()).as_posix()

    def run_in(self, target: str, *args: str, stdin_text: str | None = None) -> ResolverRun:
        anchor, _ = self.split_target(target)
        return run_resolver(anchor, *args, stdin_text=stdin_text)


def to_stdin(config: dict | str | bytes) -> str | bytes:
    return config if isinstance(config, (str, bytes)) else json.dumps(config)


# Bytes that are not UTF-8 text: a config saved in Latin-1 with an accented note.
NOT_UTF8_CONFIG = b'{"$comment": "r\xe9vis\xe9 en juin", "version": 1}\n'


def json_with_key_twice(value, key: str) -> str:
    """JSON text of value in which the first object holding `key` (depth-first,
    at any depth) sets it twice. Stdlib json cannot emit this, so serialize by hand."""
    text, found = _dump_with_key_twice(value, key)
    assert found, f"no key {key!r} to repeat"
    return text


def _dump_with_key_twice(value, key: str, found: bool = False) -> tuple[str, bool]:
    if isinstance(value, dict):
        members = []
        for name, item in value.items():
            item_text, found_below = _dump_with_key_twice(item, key, found)
            member = f"{json.dumps(name)}: {item_text}"
            members.append(member)
            if name == key and not found:
                members.append(member)
                found_below = True
            found = found_below
        return "{" + ", ".join(members) + "}", found
    if isinstance(value, list):
        parts = []
        for item in value:
            item_text, found = _dump_with_key_twice(item, key, found)
            parts.append(item_text)
        return "[" + ", ".join(parts) + "]", found
    return json.dumps(value), found


# ---------------------------------------------------------------------------
# Markdown helpers for the static skill artifacts
# ---------------------------------------------------------------------------

def read_required(path: Path, what: str) -> str:
    assert path.is_file(), f"{what} not found at {path.relative_to(REPO_ROOT)} (not yet delivered)"
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "skill guide has no YAML frontmatter block"
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"')
    return fields


def parse_profile_table(text: str) -> tuple[list[str], dict[str, dict[str, str]]]:
    """Return (domain columns, {archetype: {domain: raw cell}}) from the first
    markdown table whose header starts with `archetype`."""
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].lower() == "archetype":
            columns = [c for c in cells[1:] if c.lower() != "sum"]
            rows: dict[str, dict[str, str]] = {}
            for row in lines[idx + 2:]:
                if not row.strip().startswith("|"):
                    break
                values = [c.strip() for c in row.strip().strip("|").split("|")]
                rows[values[0].strip("`")] = dict(zip(columns, values[1:1 + len(columns)]))
            return columns, rows
    raise AssertionError("profile catalogue has no table headed 'archetype'")
