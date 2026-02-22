# Running the Fitness Review

The fitness review can run with **GitHub agents** (Copilot, Claude, or Codex), or **Cursor** locally. Use the `agent_type` input (GitHub) or choose your runner when running locally.

## File layout

| File | Purpose |
|------|---------|
| `.github/workflows/fitness-review.md` | gh-aw config + prompt (source for GitHub) |
| `.github/workflows/fitness-review.lock.yml` | Compiled workflow (auto-generated; run `gh aw compile` to regenerate) |
| `.github/fitness-review-prompt.md` | Standalone prompt for Cursor/Claude (same content as the .md body) |

## agent_type: github

Runs in GitHub Actions via [gh-aw](https://github.github.io/gh-aw/) with Copilot or Claude.

**Prerequisites:**
- `gh` CLI v2.0+ and `gh extension install github/gh-aw`
- One secret (per engine):
  - **Claude**: `ANTHROPIC_API_KEY`
  - **Copilot**: `COPILOT_GITHUB_TOKEN` (PAT with `copilot-requests` scope)
  - **Codex (OpenAI)**: `OPENAI_API_KEY`

**Run:**
```bash
gh aw run fitness-review
# Or: Actions → Project Fitness Review → Run workflow
# Select agent_type: github | claude | codex | cursor
```

**Note:** `agent_type` is passed for documentation/tracking. The engine is set in the `.md` frontmatter (`engine: claude` | `engine: copilot` | `engine: codex`). Change it and run `gh aw compile` to use a different engine. `agent_type=cursor` means run locally — see below.

## agent_type: claude

Runs via Claude (API, Claude Code, or gh-aw with engine: claude).

**Via gh-aw (GitHub Actions):** Set `engine: claude` in the .md frontmatter (default), add `ANTHROPIC_API_KEY` secret, then `gh aw compile`.

**Via Claude Code (local or CI):**
```bash
# Install skills (see SETUP.md), then:
claude --prompt "$(cat .github/fitness-review-prompt.md)"
# Or use anthropics/claude-code-action with that prompt
```

## agent_type: codex

Runs in GitHub Actions via gh-aw with [OpenAI Codex](https://github.github.com/gh-aw/reference/engines/).

**Via gh-aw (GitHub Actions):** Set `engine: codex` in the .md frontmatter, add `OPENAI_API_KEY` secret, then `gh aw compile`.

## agent_type: cursor

Runs in Cursor IDE — **not in GitHub Actions**. Cursor is a local/desktop tool.

**Run:**
1. Open `.github/fitness-review-prompt.md` in Cursor
2. In Composer (Cmd+I), paste or @-mention the prompt and say: "Run this fitness review on this repository. Write the report to docs/fitness-report.md."
3. Or use the review-full skill: `/review:review-full` (if skills are installed)

The prompt adapts output: GitHub creates an issue; Cursor/Claude writes to `docs/fitness-report.md`.
