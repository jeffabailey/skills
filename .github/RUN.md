# Running the Fitness Review

The fitness review runs with **GitHub agents** (Claude or Copilot) in GitHub Actions, or **locally** via Claude Code CLI.

## File layout

| File | Purpose |
|------|---------|
| `.github/workflows/fitness-review.yml` | Claude workflow (primary, deterministic YAML) |
| `.github/workflows/fitness-review-copilot.yml` | Copilot workflow (fallback when Claude returns 529) |
| `.github/fitness-review-prompt.md` | Standalone prompt for Claude Code CLI (local use) |

## agent_type: claude (default)

Runs in GitHub Actions via [gh-aw](https://github.github.io/gh-aw/) with Claude Code.

**Prerequisites:**
- `gh` CLI v2.0+ and `gh extension install github/gh-aw`
- Secret: `ANTHROPIC_API_KEY`

**Run:**
```bash
gh aw run fitness-review
# Or: Actions → Project Fitness Review → Run workflow
# Select agent_type: claude or copilot
```

**Via Claude Code (local or CI):**
```bash
# Install skills (see SETUP.md), then:
claude --prompt "$(cat .github/fitness-review-prompt.md)"
# Or use anthropics/claude-code-action with that prompt
```

## agent_type: copilot

Fallback when Claude returns 529 Overloaded. Runs via a separate workflow using GitHub Copilot.

**Prerequisites:**
- `COPILOT_GITHUB_TOKEN` (PAT with `copilot-requests` scope)

**Run:**
```bash
gh workflow run "Project Fitness Review (Copilot)" -f agent_type=copilot
# Or: Actions → Project Fitness Review (Copilot) → Run workflow
```

## Troubleshooting

### 529 Overloaded (Claude/Anthropic)

If the agent job fails with `API Error: 529` or `overloaded_error`:

- **Cause:** Anthropic's API was temporarily overloaded (transient).
- **Fix 1:** Re-run the workflow (often succeeds on retry): Actions → Re-run failed jobs.
- **Fix 2:** Use the Copilot fallback: run **Project Fitness Review (Copilot)** instead. Requires `COPILOT_GITHUB_TOKEN` (PAT with `copilot-requests` scope). Trigger via Actions or `gh workflow run "Project Fitness Review (Copilot)" -f agent_type=copilot`.
