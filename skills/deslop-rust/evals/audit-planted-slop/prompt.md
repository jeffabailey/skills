---
tags: [skill-creator]
max_turns: 80
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

our cartcalc crate's test suite has gotten bloated and slow and I suspect half of it is copy-paste. can you go through the tests in this repo and tell me what's redundant, weak or slow, and whether there's dead code lying around? use real evidence (timings, coverage, mutation testing), not just eyeballing

Input files: Cargo.toml, Cargo.lock, .gitignore, src/lib.rs, tests/integration.rs
