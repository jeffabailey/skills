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

Uses [gh-aw](https://github.github.io/gh-aw/) — Markdown workflows with Copilot, Claude, or Codex.

**Prerequisites:**

- `gh` CLI v2.0.0+
- One of:
  - **Copilot**: `COPILOT_GITHUB_TOKEN` (PAT with `copilot-requests` scope)
  - **Claude**: `ANTHROPIC_API_KEY`
  - **Codex**: `OPENAI_API_KEY`

**Install:**

```bash
gh extension install github/gh-aw
```

**Add the fitness review workflow:**

```bash
cd your-repo
gh aw add jeffabailey/skills/fitness-review
# REQUIRED: Configure one secret (set engine in .md frontmatter first):
gh aw secrets set ANTHROPIC_API_KEY --value "YOUR_ANTHROPIC_KEY"   # engine: claude (default)
# Or for Copilot: engine: copilot → gh aw secrets set COPILOT_GITHUB_TOKEN --value "YOUR_PAT"
# Or for Codex:   engine: codex   → gh aw secrets set OPENAI_API_KEY --value "YOUR_OPENAI_KEY"
```

**Compile and commit:**

```bash
gh aw compile
git add .github/workflows/fitness-review.md .github/workflows/fitness-review.lock.yml
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
```

Then trigger via `gh aw run fitness-review` or the Actions tab. Get an API key at [console.anthropic.com](https://console.anthropic.com/). See `.github/RUN.md` for agent_type (github/claude/codex/cursor) and running with Cursor or Claude locally.

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
        run: |
          mkdir -p ~/.claude/skills
          for skill in review-architecture review-security review-reliability review-testing review-performance review-algorithms review-data review-accessibility review-process review-maintainability review-full review-jit-test-gen; do
            ln -sf "$GITHUB_WORKSPACE/$skill" ~/.claude/skills/$skill
          done
        # If skills are in a separate checkout:
        # with:
        #   repository: jeffabailey/skills
        #   path: skills
        #   Then: ln -sf "$GITHUB_WORKSPACE/skills/$skill" ...

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
git clone https://github.com/jeffabailey/skills.git ~/Projects/skills

for skill in review-architecture review-security review-reliability review-testing review-performance review-algorithms review-data review-accessibility review-process review-maintainability review-full review-jit-test-gen; do
  ln -sf ~/Projects/skills/$skill ~/.cursor/skills/$skill
done
```

**Project-level (one repo):**

```bash
git clone https://github.com/jeffabailey/skills.git .cursor/skills-source

for skill in review-architecture review-security review-reliability review-testing review-performance review-algorithms review-data review-accessibility review-process review-maintainability review-full review-jit-test-gen; do
  ln -sf "$(pwd)/.cursor/skills-source/$skill" .cursor/skills/$skill
done
```

Add `.cursor/skills-source/` to `.gitignore` if you don’t want to commit the clone.

---

### Claude Code

**User-level:**

```bash
git clone https://github.com/jeffabailey/skills.git ~/Projects/skills

for skill in review-architecture review-security review-reliability review-testing review-performance review-algorithms review-data review-accessibility review-process review-maintainability review-full review-jit-test-gen; do
  ln -sf ~/Projects/skills/$skill ~/.claude/skills/$skill
done
```

**Project-level:** same pattern but use `.claude/skills/` in the project root.

---

### Visual Studio Code (GitHub Copilot)

Uses the same [SKILL.md agentskills format](https://code.visualstudio.com/docs/copilot/customization/agent-skills).

**User-level:**

```bash
git clone https://github.com/jeffabailey/skills.git ~/Projects/skills

mkdir -p ~/.copilot/skills
for skill in review-architecture review-security review-reliability review-testing review-performance review-algorithms review-data review-accessibility review-process review-maintainability review-full review-jit-test-gen; do
  ln -sf ~/Projects/skills/$skill ~/.copilot/skills/$skill
done
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

All skills are in the repo root. Use these names when symlinking:

- `review-architecture`
- `review-security`
- `review-reliability`
- `review-testing`
- `review-performance`
- `review-algorithms`
- `review-data`
- `review-accessibility`
- `review-process`
- `review-maintainability`
- `review-full`
- `review-jit-test-gen`

---

## Troubleshooting

**Skills not loading in Cursor/Claude:** Check `~/.cursor/skills/` or `~/.claude/skills/` exists and symlinks resolve (`ls -la`). Restart the IDE or agent.

**GitHub Agentic Workflow fails:** Ensure one of `COPILOT_GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY` is set in repository secrets. Run `gh aw compile` after editing the workflow.

**Claude Code Action OIDC error:** Add `id-token: write` to workflow permissions (see Option B).
