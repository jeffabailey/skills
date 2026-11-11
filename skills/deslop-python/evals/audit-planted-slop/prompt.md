---
tags: [skill-creator]
max_turns: 80
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

our cartcalc python package's test suite has gotten bloated and slow and I suspect half of it is copy-paste. can you go through the tests in this repo and tell me what's redundant, weak or slow, and whether there's dead code or unused deps lying around? use real evidence (timings, coverage, mutation testing), not just eyeballing

Input files: pyproject.toml, uv.lock, README.md, .gitignore, src/cartcalc/__init__.py, src/cartcalc/core.py, src/cartcalc/cli.py, src/cartcalc/py.typed, tests/test_core.py, tests/test_integration.py, tests/test_bench.py
