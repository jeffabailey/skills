"""Shared fixtures for fitness-config-per-directory acceptance tests.

Driving port: the `fitness-config.py` CLI invoked as a real subprocess.
Storage adapter: the real filesystem, isolated under pytest's `tmp_path`.

No mocks are used at the acceptance level. Every scenario exercises:
  - real Python subprocess invocation of `python3 scripts/fitness-config.py`
  - real `fitness-config.json` files written to a temporary directory tree
  - real stdout/stderr/exit-code observation

This matches Strategy C (real-services) declared in DISTILL wave-decisions.md.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import pytest

# ---------------------------------------------------------------------------
# Paths to production code under test
# ---------------------------------------------------------------------------

# Resolve the skills repo root from this file's location:
# tests/acceptance/fitness-config-per-directory/steps/conftest.py -> repo root
REPO_ROOT = Path(__file__).resolve().parents[4]
FITNESS_CONFIG_SCRIPT = REPO_ROOT / "scripts" / "fitness-config.py"


# ---------------------------------------------------------------------------
# Default config constants — keep aligned with scripts/fitness-config.py
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS = {
    "architecture": 14,
    "security": 14,
    "reliability": 10,
    "testing": 10,
    "performance": 10,
    "algorithms": 10,
    "data": 10,
    "accessibility": 8,
    "process": 8,
    "maintainability": 6,
}

DEFAULT_STATUS_THRESHOLDS = {
    "healthy": [8, 10],
    "needsAttention": [5, 7],
    "critical": [1, 4],
}

DEFAULT_SECURITY = {"confidenceThreshold": 7}
DEFAULT_SCORING = {"goodRange": [8, 10], "badRange": [1, 3]}


# ---------------------------------------------------------------------------
# CLI runner — the driving port adapter
# ---------------------------------------------------------------------------

@dataclass
class CliResult:
    """Outcome of one CLI invocation. Tests assert on these fields only."""

    args: list[str]
    exit_code: int
    stdout: str
    stderr: str
    cwd: Path

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0

    @property
    def combined_output(self) -> str:
        return self.stdout + self.stderr


def run_cli(cwd: Path, *args: str) -> CliResult:
    """Invoke `python3 scripts/fitness-config.py <args>` as a real subprocess.

    The subprocess inherits a clean environment except PATH and HOME, so
    tests cannot accidentally couple to the developer's shell state.
    """
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "PYTHONIOENCODING": "utf-8",
    }
    completed = subprocess.run(
        [sys.executable, str(FITNESS_CONFIG_SCRIPT), *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return CliResult(
        args=list(args),
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        cwd=cwd,
    )


# ---------------------------------------------------------------------------
# Repo-tree builder — real filesystem, isolated under tmp_path
# ---------------------------------------------------------------------------

@dataclass
class RepoTree:
    """A throwaway repo rooted at tmp_path. All paths are RELATIVE inside it."""

    root: Path
    last_results: list[CliResult] = field(default_factory=list)

    # ---- file/directory writers -----------------------------------------

    def write_root_config(self, *, weights: dict | None = None,
                          status: dict | None = None,
                          security: dict | None = None,
                          scoring: dict | None = None,
                          version: int = 1) -> Path:
        cfg: dict = {"version": version}
        if weights is not None:
            cfg["weights"] = weights
        if status is not None:
            cfg["statusThresholds"] = status
        if security is not None:
            cfg["security"] = security
        if scoring is not None:
            cfg["scoring"] = scoring
        return self.write_config_at("fitness-config.json", cfg)

    def write_default_root_config(self) -> Path:
        return self.write_root_config(
            weights=dict(DEFAULT_WEIGHTS),
            status=dict(DEFAULT_STATUS_THRESHOLDS),
            security=dict(DEFAULT_SECURITY),
            scoring=dict(DEFAULT_SCORING),
        )

    def write_config_at(self, relative_path: str, config: dict) -> Path:
        target = self.path_at(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return target

    def write_raw_at(self, relative_path: str, content: str) -> Path:
        target = self.path_at(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def touch_file(self, relative_path: str) -> Path:
        target = self.path_at(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
        return target

    def make_dir(self, relative_path: str) -> Path:
        target = self.path_at(relative_path)
        target.mkdir(parents=True, exist_ok=True)
        return target

    # ---- inspection -----------------------------------------------------

    def path_at(self, relative_path: str) -> Path:
        return self.root / relative_path

    def exists(self, relative_path: str) -> bool:
        return self.path_at(relative_path).exists()

    def read_json(self, relative_path: str) -> dict:
        return json.loads(self.path_at(relative_path).read_text(encoding="utf-8"))

    def read_text(self, relative_path: str) -> str:
        return self.path_at(relative_path).read_text(encoding="utf-8")

    # ---- driving-port invocation ---------------------------------------

    def run(self, *args: str) -> CliResult:
        result = run_cli(self.root, *args)
        self.last_results.append(result)
        return result

    @property
    def last_result(self) -> CliResult:
        if not self.last_results:
            raise AssertionError("No CLI invocation has been made yet.")
        return self.last_results[-1]


# ---------------------------------------------------------------------------
# pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repo(tmp_path: Path) -> RepoTree:
    """A fresh, isolated repo tree per scenario.

    tmp_path is pytest's per-test temporary directory — guaranteed unique and
    auto-cleaned. This is the integration boundary for the filesystem
    adapter: real I/O, isolated.
    """
    return RepoTree(root=tmp_path)


@pytest.fixture
def context() -> dict:
    """Per-scenario shared state for step methods (parsed values, last preview, etc.)."""
    return {}


# ---------------------------------------------------------------------------
# Helpers shared by step modules
# ---------------------------------------------------------------------------

def parse_weights_string(spec: str) -> dict:
    """Parse a Gherkin string like 'data=30, reliability=20' into a dict."""
    out: dict = {}
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        key, _, value = chunk.partition("=")
        out[key.strip().strip('"')] = float(value) if "." in value else int(value)
    return out


def parse_int_pair(spec: str) -> list:
    """Parse a Gherkin string like '[8,10]' into a 2-element list of ints."""
    inner = spec.strip().strip("[]")
    return [int(x.strip()) for x in inner.split(",")]


def find_embedded_json_block(stdout: str) -> dict | None:
    """Return the parsed dict from the BEGIN/END_EFFECTIVE_CONFIG_JSON sentinel block."""
    begin = "<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->"
    end = "<!-- END_EFFECTIVE_CONFIG_JSON -->"
    if begin not in stdout or end not in stdout:
        return None
    block = stdout.split(begin, 1)[1].split(end, 1)[0].strip()
    return json.loads(block)


def assert_text_contains_all(haystack: str, needles: Iterable[str]) -> None:
    missing = [n for n in needles if n not in haystack]
    if missing:
        raise AssertionError(
            f"Expected substrings missing from output: {missing}\n"
            f"--- output ---\n{haystack}\n--- end ---"
        )
