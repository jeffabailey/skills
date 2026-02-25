# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

This is a content-only repository of Markdown-based AI agent skill definitions for code review. There is no application server, database, or build system. The "product" is the collection of `SKILL.md` files and reference checklists consumed by AI coding agents (Cursor, Claude Code, VS Code/Copilot, Neovim/Avante) and CI pipelines.

### Running tests

The only automated test suite is `tests/workflow-tests.sh`. It validates the GitHub Actions workflow structure and runs `engine-config.py` for each engine. It requires:

- **Python 3** (for `.github/scripts/engine-config.py`)
- **`act`** (for workflow parsing / `act --list`; install via `curl -fsSL https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash -s -- -b /usr/local/bin`)
- **Docker** (required by `act`)

Run the tests from the repo root:

```bash
bash tests/workflow-tests.sh
```

All 40 checks should pass. The test script exits non-zero on any failure.

### Linting

There is no formal linter configured. Content is Markdown; validate manually or with a Markdown linter like `markdownlint` if desired.

### Key conventions

- Skill directories follow the `review-<domain>/` naming pattern.
- Each skill has `SKILL.md` and optionally `references/checklist.md`.
- `review-full` and `review-jit-test-gen` do not have `references/` directories.
- Scoring weights in `review-full/SKILL.md` must stay consistent with `README.md`.
- See `CONTRIBUTING.md` for full contribution conventions.

### Docker in nested containers

When running in Cursor Cloud (Docker-in-Docker inside Firecracker), Docker requires `fuse-overlayfs` as the storage driver and `iptables-legacy`. The daemon config is at `/etc/docker/daemon.json`. After starting `dockerd`, you may need to `chmod 666 /var/run/docker.sock` for non-root access.
