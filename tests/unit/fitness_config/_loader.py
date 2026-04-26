"""Shared loader for the hyphenated fitness-config.py production module.

The production file lives at `scripts/fitness-config.py`. The hyphenated name
prevents a normal `import fitness_config`, so every unit test module needs the
same importlib boilerplate to load it. This helper extracts that boilerplate
to a single place; tests do:

    from tests.unit.fitness_config._loader import fitness_config

The module is loaded once at import time, registered in sys.modules under the
name `fitness_config` so subsequent imports from any test module reuse the
same object (preserving identity for isinstance/`is` checks).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Resolve the skills repo root: this file lives at
# tests/unit/fitness_config/_loader.py, so parents[3] is the repo root.
_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "fitness-config.py"

if "fitness_config" in sys.modules:
    fitness_config = sys.modules["fitness_config"]
else:
    _spec = importlib.util.spec_from_file_location("fitness_config", _SCRIPT)
    fitness_config = importlib.util.module_from_spec(_spec)
    sys.modules["fitness_config"] = fitness_config
    _spec.loader.exec_module(fitness_config)

__all__ = ["fitness_config"]
