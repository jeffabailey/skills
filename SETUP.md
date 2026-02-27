# Project Fitness Review Skills — Setup Guide

This guide covers installing and using the skills across **pipelines** (GitHub Actions, GitHub Agentic Workflows, Claude Code Action) and **IDEs** (Cursor, Claude Code, Visual Studio Code, Neovim with Avante).

## Quick reference

| Platform | Skills location | Notes |
|----------|-----------------|-------|
| Cursor | `~/.cursor/skills/` or `.cursor/skills/` | Project or user scope |
| Claude Code | `~/.claude/skills/` or `.claude/skills/` | Project or user scope |
| VS Code (Copilot) | `~/.copilot/skills/` or `.github/skills/` | Same SKILL.md format |
| Neovim (Avante) | Project `avante.md` or custom prompt | See Avante section |

---

## Pipeline setup

### Option A: GitHub Agentic Workflows (recommended)

Uses [gh-aw](https://github.github.io/gh-aw/) with multiple engine support (Claude, Copilot, Codex).

**Prerequisites:**

- `gh` CLI v2.0.0+
- At least one engine secret:

| Engine | Secret | Source |
|--------|--------|--------|
| Claude (default) | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |
| Copilot | `COPILOT_GITHUB_TOKEN` | GitHub PAT with `copilot-requests` scope |
| Codex | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/) |

**Install:**

```bash
gh extension install github/gh-aw
```

**Add the fitness review workflow:**

```bash
cd your-repo
gh aw add jeffabailey/skills/fitness-review
gh aw secrets set ANTHROPIC_API_KEY --value "YOUR_ANTHROPIC_KEY"
```

**Commit and push:**

```bash
git add .github/workflows/fitness-review.yml
git commit -m "Add fitness review workflow"
git push
```

**Trigger:**

```bash
gh aw run fitness-review
```

Or via **Actions** → **Project Fitness Review** → **Run workflow**.

**Using in this repo (skills):** The workflow is already in `.github/workflows/`. You must add a secret first:

```bash
gh aw secrets set ANTHROPIC_API_KEY --value "YOUR_ANTHROPIC_KEY"
# Optional: add secrets for alternative engines
gh aw secrets set COPILOT_GITHUB_TOKEN --value "YOUR_COPILOT_TOKEN"
gh aw secrets set OPENAI_API_KEY --value "YOUR_OPENAI_KEY"
```

Then trigger via `gh aw run fitness-review` or the Actions tab. Select the engine from the dropdown (default: Claude). See `.github/RUN.md` for details. If Claude returns 529 Overloaded, re-run or try a different engine.

---

### Option B: Claude Code GitHub Action

Uses [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action) with explicit skills install.

**Prerequisites:**

- `ANTHROPIC_API_KEY` in repository secrets

**Workflow example:**

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install project fitness review skills
        run: bash scripts/install-skills.sh "$GITHUB_WORKSPACE" "$HOME/.claude/skills"
        # If skills are in a separate checkout (e.g. path: skills), use SOURCE_DIR="$GITHUB_WORKSPACE/skills" and run the script from that checkout.

      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: "Run a full project fitness review. Use the review-full skill. Write the unified report to docs/fitness-report.md."
          claude_args: "--max-turns 15"

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: fitness-report
          path: docs/fitness-report.md
        continue-on-error: true
```

---

### Option C: Cursor pipeline (self-hosted or automation)

Skills can be used in Cursor-based automation by symlinking into `~/.cursor/skills/` before the agent runs. Use the same install pattern as Option B but target `~/.cursor/skills` instead of `~/.claude/skills`.

---

## IDE setup

### Cursor

**User-level (all projects):**

```bash
bash ~/Projects/skills/scripts/install-skills.sh --clone ~/Projects/skills ~/.cursor/skills
```

If the repo was moved, the script removes the existing clone directory first so the clone succeeds.

**Project-level (one repo):**

```bash
# If the directory already exists (e.g. repo was moved), remove it first so clone succeeds:
rm -rf .cursor/skills-source
git clone https://github.com/jeffabailey/skills.git .cursor/skills-source
bash .cursor/skills-source/scripts/install-skills.sh "$(pwd)/.cursor/skills-source" "$(pwd)/.cursor/skills"
```

Run from your project root. Add `.cursor/skills-source/` to `.gitignore` if you don’t want to commit the clone.

---

### Claude Code

**User-level:**

```bash
bash ~/Projects/skills/scripts/install-skills.sh --clone ~/Projects/skills ~/.claude/skills
```

(Clone runs from the script; if the directory already exists it is removed first.)

**Project-level:** same pattern but use `$(pwd)/.claude/skills` as DEST and clone into e.g. `.claude/skills-source`.

---

### Visual Studio Code (GitHub Copilot)

Uses the same [SKILL.md agentskills format](https://code.visualstudio.com/docs/copilot/customization/agent-skills).

**User-level:**

```bash
bash ~/Projects/skills/scripts/install-skills.sh --clone ~/Projects/skills ~/.copilot/skills
```

**Project-level:** use `.github/skills/` or `.claude/skills/` in the repo. Copilot checks both.

**Extra paths:** set `chat.agentSkillsLocations` in VS Code settings to add more locations.

---

### Neovim with Avante

[Avante.nvim](https://github.com/yetone/avante.nvim) uses a project instruction file (`avante.md`) rather than a skills directory. To use the reviews in Avante:

**Option 1 — Add review instructions to `avante.md`:**

Create or edit `avante.md` in the project root and add a section that references the review workflow:

```markdown
## Project fitness reviews

For comprehensive code reviews, ask me to:

1. Review architecture (coupling, cohesion, layering, modularity, naming, API design)
2. Review security (input validation, auth, dependencies, crypto)
3. Review reliability (observability, CI/CD, incident readiness)
4. Review testing (pyramid balance, coverage, CI integration)
5. Review performance (algorithms, database design, caching, scalability)
6. Review algorithms (correctness, data structures, concurrency)
7. Review data (schema, migrations, integrity)
8. Review accessibility (semantic HTML, a11y, contrast)
9. Review process (documentation, workflow, code review)

Produce scores (1–10) per dimension with file:line evidence and prioritized action items.
Write the unified report to docs/fitness-report.md.
```

**Option 2 — Reference the skills repo:**

Add a note in `avante.md`:

```markdown
## Review reference

Use the Project Fitness Review methodology from https://github.com/jeffabailey/skills.
Review domains: architecture, security, reliability, testing, performance, algorithms, data, accessibility, process.
```

---

## Skill list

All skills live under `src/`. The install commands above symlink every directory in `src/` (no hardcoded list). Current skills:

- `src/review-architecture`
- `src/review-security`
- `src/review-reliability`
- `src/review-testing`
- `src/review-performance`
- `src/review-algorithms`
- `src/review-data`
- `src/review-accessibility`
- `src/review-process`
- `src/review-maintainability`
- `src/review-full`
- `src/review-jit-test-gen`
- `src/review-apply`

---

## Troubleshooting

**Skills not loading in Cursor/Claude:** Check `~/.cursor/skills/` or `~/.claude/skills/` exists and symlinks resolve (`ls -la`). Restart the IDE or agent.

**GitHub Agentic Workflow fails:** Ensure the secret for your selected engine is set (`ANTHROPIC_API_KEY` for Claude, `COPILOT_GITHUB_TOKEN` for Copilot, `OPENAI_API_KEY` for Codex). Edit `.github/workflows/fitness-review.yml` directly (no compilation needed). Engine config lives in `.github/scripts/engine-config.py`.

**Claude Code Action OIDC error:** Add `id-token: write` to workflow permissions (see Option B).
