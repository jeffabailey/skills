"""Import the resolver package (scripts/fitness_config) for the unit tests.

The package sits beside the scripts/fitness-config.py entry point, outside
any installed distribution, so the scripts directory goes on sys.path once
here. Tests do `from ._loader import resolution, render, ...`.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parents[3] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from fitness_config import (audit, model, render, resolution,  # noqa: E402
                            validation, write_gate)

__all__ = ["audit", "model", "render", "resolution", "validation", "write_gate"]
