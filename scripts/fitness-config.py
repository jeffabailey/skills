#!/usr/bin/env python3
"""Manage fitness-review config: validate, init, show, audit.

Place fitness-config.json in your project root to customize thresholds and
weights. Skills read it at runtime. No need to edit SKILL.md files.

Usage:
    python3 fitness-config.py validate [path]    # Validate JSON (default: fitness-config.json)
    python3 fitness-config.py init [path]        # Create default config
    python3 fitness-config.py show [path]        # Print effective config (merged with defaults)
    python3 fitness-config.py show --path TARGET # Resolve walk-up chain from TARGET, deep-merge, render
    python3 fitness-config.py audit              # CI gate: no inline weights or direct config loads

Works on Windows, macOS, and Linux. Requires Python 3.10+. Standard library only.

This file is the stable entry point. The logic lives in the fitness_config
package beside it (ADR-012); the package is found through this file's own
location, so the script works from any working directory.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fitness_config.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
