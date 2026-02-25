# Agents

## Cursor Cloud specific instructions

This is a **content-only repository** of AI agent skill definitions (Markdown files). There is no traditional application to build or run, no package manager, and no compiled artifacts.

### Repository structure

- 12 skill directories at root (`review-architecture/`, `review-security/`, etc.), each containing `SKILL.md` and optionally `references/checklist.md`
- `.github/scripts/engine-config.py` — Python 3 (stdlib only) helper for GitHub Actions engine configuration
- `.github/workflows/fitness-review.yml` — GitHub Actions workflow for CI-based reviews
- `tests/workflow-tests.sh` — bash test suite validating workflow structure and engine config

### Running tests

The primary test command is:

```bash
bash tests/workflow-tests.sh
```

This validates: file structure, `engine-config.py` outputs for all engines (claude/copilot/codex), workflow YAML structure, and `act` workflow parsing. Requires Python 3, bash, Docker, and `act` (https://github.com/nektos/act).

The engine config script can also be tested standalone:

```bash
python3 .github/scripts/engine-config.py --engine claude
python3 .github/scripts/engine-config.py --engine copilot
python3 .github/scripts/engine-config.py --engine codex
```

### Lint

YAML validation can be run with `yamllint` on the workflow file. The existing style (long lines in GitHub Actions YAML) is intentional — warnings are cosmetic. See `CONTRIBUTING.md` for content conventions.

### Gotchas

- `tests/workflow-tests.sh` uses `set -euo pipefail` — it will fail hard if `act` is not installed. Docker must be running before `act` can parse the workflow.
- The `act` test section requires the Docker daemon to be running and accessible. Start Docker before running tests.
- There are no dependencies to install — Python uses only stdlib, and `act` is the only external tool needed for the full test suite.
