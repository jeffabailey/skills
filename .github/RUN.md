# Running the Fitness Review

The fitness review runs in **GitHub Actions** (multiple engine support) or **locally** via the Claude Code CLI.

## File layout

| File | Purpose |
|------|---------|
| `.github/workflows/fitness-review.yml` | GitHub Actions workflow (multi-engine) |
| `.github/scripts/engine-config.py` | Engine-specific configuration (claude, copilot, codex) |
| `.github/fitness-review-prompt.md` | Standalone prompt for Claude Code CLI (local use) |

## GitHub Actions

Runs weekly on Sunday and on manual dispatch via [gh-aw](https://github.github.io/gh-aw/).

**Prerequisites:**
- `gh` CLI v2.0+ and `gh extension install github/gh-aw`
- At least one engine secret (see below)

**Engine secrets:**

| Engine | Secret | Where to get it |
|--------|--------|-----------------|
| Claude (default) | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |
| Copilot | `COPILOT_GITHUB_TOKEN` | GitHub PAT with `copilot-requests` scope |
| Codex | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/) |

**Run (default — Claude):**
```bash
gh aw run fitness-review
# Or: Actions → Project Fitness Review → Run workflow
```

**Run with a specific engine:**
```bash
# Via Actions tab: select engine from the dropdown
# Or: Actions → Project Fitness Review → Run workflow → engine: copilot
```

## Local (Claude Code CLI)

```bash
# Install skills (see SETUP.md), then:
claude --prompt "$(cat .github/fitness-review-prompt.md)"
```

## Troubleshooting

### 529 Overloaded (Claude/Anthropic)

If the agent job fails with `API Error: 529` or `overloaded_error`:

- **Cause:** Anthropic's API was temporarily overloaded (transient).
- **Fix:** Re-run the workflow — usually succeeds on retry. Actions → Re-run failed jobs.
- **Alternative:** Re-run with `engine: copilot` or `engine: codex` if overload persists.

### Agent Timeout

If the agent job exceeds the workflow timeout:

- **Cause:** The review scope is too large for a single pass, or the agent is stuck in a loop.
- **Fix:** Re-run the workflow. If it times out again, reduce scope by running individual domain reviews instead of `review-full`.

### MCP Server Failure

If the agent step fails with `MCP connection error`, `MCP server unavailable`, or `tool not found`:

- **Cause:** The MCP Gateway server could not start or lost connection mid-run.
- **Fix:** Re-run the workflow — MCP server failures are usually transient.
- **If persistent:** Verify the `mcp_config_path` in `engine-config.py` matches the engine's expected path. Claude: `/tmp/gh-aw/mcp-config/mcp-servers.json`. Copilot: `/home/runner/.copilot/mcp-config.json`.

### Workflow Concurrency Queue

If the workflow is queued but never starts:

- **Cause:** The concurrency group (`gh-aw-${{ github.workflow }}`) limits to one concurrent run. A previous run may be stuck.
- **Fix:** Cancel the stuck run from the Actions tab, then re-trigger.

### Skill Installation Failure

If the agent produces no scores or cannot find skills:

- **Cause:** The skill symlink step failed, or skills are not in the expected directory.
- **Fix:** Check the install step logs. Verify that the `for skill in ...` loop completed without errors and that skill directories exist in the checked-out workspace.

### Engine Secret Missing or Invalid

If the workflow fails at the `Validate context variables` step:

- **Cause:** The secret for the selected engine is not set or has expired.
- **Fix:** Re-add the secret: `gh aw secrets set <SECRET_NAME> --value "YOUR_KEY"`. See the engine secrets table above.
