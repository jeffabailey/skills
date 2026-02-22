# Running the Fitness Review

The fitness review can run with **GitHub agents**, **Cursor agents**, or **Claude agents**. Use the `agent_type` input (GitHub) or choose your runner (Cursor/Claude) when running locally.

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
- Secret: `ANTHROPIC_API_KEY` (for claude engine) or `COPILOT_GITHUB_TOKEN` (for copilot engine)

**Run:**
```bash
gh aw run fitness-review
# Or: Actions → Project Fitness Review → Run workflow
# Select agent_type: github | claude | cursor
```

**Note:** `agent_type` is passed for documentation/tracking. The engine (claude/copilot) is set in the `.md` frontmatter; change `engine: claude` to `engine: copilot` and recompile if you prefer Copilot. `agent_type=cursor` means run locally — see below.

## agent_type: claude

Runs via Claude (API, Claude Code, or gh-aw with engine: claude).

**Via gh-aw (GitHub Actions):** Same as above; set `engine: claude` in the .md frontmatter (default).

**Via Claude Code (local or CI):**
```bash
# Install skills (see SETUP.md), then:
claude --prompt "$(cat .github/fitness-review-prompt.md)"
# Or use anthropics/claude-code-action with that prompt
```

## agent_type: cursor

Runs in Cursor IDE — **not in GitHub Actions**. Cursor is a local/desktop tool.

**Run:**
1. Open `.github/fitness-review-prompt.md` in Cursor
2. In Composer (Cmd+I), paste or @-mention the prompt and say: "Run this fitness review on this repository. Write the report to docs/fitness-report.md."
3. Or use the review-full skill: `/review:review-full` (if skills are installed)

The prompt adapts output: GitHub creates an issue; Cursor/Claude writes to `docs/fitness-report.md`.
