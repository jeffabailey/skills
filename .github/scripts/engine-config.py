#!/usr/bin/env python3
"""Output engine-specific configuration as GitHub Actions outputs.

Usage:
    python3 .github/scripts/engine-config.py --engine claude|copilot|codex

Writes key=value pairs to $GITHUB_OUTPUT (or stdout when run locally).
The workflow calls this once, then references the outputs everywhere.
"""

import argparse
import os
import sys

# ---------------------------------------------------------------------------
# Allowed tools — agent step
# ---------------------------------------------------------------------------

CLAUDE_AGENT_ALLOWED_TOOLS = ",".join([
    "Bash", "BashOutput", "Edit", "ExitPlanMode", "Glob", "Grep",
    "KillBash", "LS", "MultiEdit", "NotebookEdit", "NotebookRead",
    "Read", "Task", "TodoWrite", "Write",
    "mcp__github__download_workflow_run_artifact",
    "mcp__github__get_code_scanning_alert",
    "mcp__github__get_commit",
    "mcp__github__get_dependabot_alert",
    "mcp__github__get_discussion",
    "mcp__github__get_discussion_comments",
    "mcp__github__get_file_contents",
    "mcp__github__get_job_logs",
    "mcp__github__get_label",
    "mcp__github__get_latest_release",
    "mcp__github__get_me",
    "mcp__github__get_notification_details",
    "mcp__github__get_pull_request",
    "mcp__github__get_pull_request_comments",
    "mcp__github__get_pull_request_diff",
    "mcp__github__get_pull_request_files",
    "mcp__github__get_pull_request_review_comments",
    "mcp__github__get_pull_request_reviews",
    "mcp__github__get_pull_request_status",
    "mcp__github__get_release_by_tag",
    "mcp__github__get_secret_scanning_alert",
    "mcp__github__get_tag",
    "mcp__github__get_workflow_run",
    "mcp__github__get_workflow_run_logs",
    "mcp__github__get_workflow_run_usage",
    "mcp__github__issue_read",
    "mcp__github__list_branches",
    "mcp__github__list_code_scanning_alerts",
    "mcp__github__list_commits",
    "mcp__github__list_dependabot_alerts",
    "mcp__github__list_discussion_categories",
    "mcp__github__list_discussions",
    "mcp__github__list_issue_types",
    "mcp__github__list_issues",
    "mcp__github__list_label",
    "mcp__github__list_notifications",
    "mcp__github__list_pull_requests",
    "mcp__github__list_releases",
    "mcp__github__list_secret_scanning_alerts",
    "mcp__github__list_starred_repositories",
    "mcp__github__list_tags",
    "mcp__github__list_workflow_jobs",
    "mcp__github__list_workflow_run_artifacts",
    "mcp__github__list_workflow_runs",
    "mcp__github__list_workflows",
    "mcp__github__pull_request_read",
    "mcp__github__search_code",
    "mcp__github__search_issues",
    "mcp__github__search_orgs",
    "mcp__github__search_pull_requests",
    "mcp__github__search_repositories",
    "mcp__github__search_users",
])

CLAUDE_DETECTION_ALLOWED_TOOLS = ",".join([
    "Bash(cat)", "Bash(grep)", "Bash(head)", "Bash(jq)",
    "Bash(ls)", "Bash(tail)", "Bash(wc)",
    "BashOutput", "ExitPlanMode", "Glob", "Grep",
    "KillBash", "LS", "NotebookRead", "Read", "Task", "TodoWrite",
])

# ---------------------------------------------------------------------------
# Domain allowlists
# ---------------------------------------------------------------------------

# Shared infrastructure: CRL/OCSP, package managers, GitHub, Docker, etc.
COMMON_DOMAINS = [
    "api.github.com", "api.snapcraft.io",
    "archive.ubuntu.com", "azure.archive.ubuntu.com",
    "crl.geotrust.com", "crl.globalsign.com", "crl.identrust.com",
    "crl.sectigo.com", "crl.thawte.com", "crl.usertrust.com",
    "crl.verisign.com", "crl3.digicert.com", "crl4.digicert.com",
    "crls.ssl.com", "github.com", "host.docker.internal",
    "json-schema.org", "json.schemastore.org", "keyserver.ubuntu.com",
    "ocsp.digicert.com", "ocsp.geotrust.com", "ocsp.globalsign.com",
    "ocsp.identrust.com", "ocsp.sectigo.com", "ocsp.ssl.com",
    "ocsp.thawte.com", "ocsp.usertrust.com", "ocsp.verisign.com",
    "packagecloud.io", "packages.cloud.google.com",
    "packages.microsoft.com", "ppa.launchpad.net",
    "raw.githubusercontent.com", "registry.npmjs.org",
    "s.symcb.com", "s.symcd.com", "security.ubuntu.com",
    "ts-crl.ws.symantec.com", "ts-ocsp.ws.symantec.com",
]

CLAUDE_EXTRA_DOMAINS = [
    "*.githubusercontent.com",
    "anthropic.com", "api.anthropic.com",
    "cdn.playwright.dev", "codeload.github.com",
    "files.pythonhosted.org",
    "ghcr.io", "github-cloud.githubusercontent.com",
    "github-cloud.s3.amazonaws.com",
    "lfs.github.com", "objects.githubusercontent.com",
    "playwright.download.prss.microsoft.com",
    "pypi.org",
    "sentry.io", "statsig.anthropic.com",
]

COPILOT_EXTRA_DOMAINS = [
    "api.business.githubcopilot.com", "api.enterprise.githubcopilot.com",
    "api.githubcopilot.com", "api.individual.githubcopilot.com",
    "telemetry.enterprise.githubcopilot.com",
]

CODEX_EXTRA_DOMAINS = [
    "api.openai.com",
    "cdn.playwright.dev", "codeload.github.com",
    "files.pythonhosted.org",
    "ghcr.io", "objects.githubusercontent.com",
    "pypi.org",
]


def _domains(extra: list[str]) -> str:
    return ",".join(sorted(set(COMMON_DOMAINS + extra)))


CLAUDE_DOMAINS = _domains(CLAUDE_EXTRA_DOMAINS)
COPILOT_DOMAINS = _domains(COPILOT_EXTRA_DOMAINS)
CODEX_DOMAINS = _domains(CODEX_EXTRA_DOMAINS)

# ---------------------------------------------------------------------------
# CLI commands — agent (the inner command after awf --)
# ---------------------------------------------------------------------------

# Adds hostedtoolcache bin dirs and GOROOT to PATH so the agent can find
# language runtimes (node, python, go, etc.) installed by setup-* actions.
_TOOLCACHE_PATH = (
    "export PATH=\"$(find /opt/hostedtoolcache -maxdepth 4"
    " -type d -name bin 2>/dev/null | tr '\"'\"'\\n'\"'\"' '\"'\"':'\"'\"'"
    ")$PATH\"; [ -n \"$GOROOT\" ] && export PATH=\"$GOROOT/bin:$PATH\" || true"
)

# Claude Code agent: set up PATH, run claude with MCP, allowed tools,
# bypass permissions, and stream-json output.  Reads prompt from file.
CLAUDE_AGENT_CLI = (
    f"/bin/bash -c '{_TOOLCACHE_PATH}"
    " && claude --print --disable-slash-commands --no-chrome"
    " --mcp-config /tmp/gh-aw/mcp-config/mcp-servers.json"
    f" --allowed-tools {CLAUDE_AGENT_ALLOWED_TOOLS}"
    " --debug-file /tmp/gh-aw/agent-stdio.log --verbose"
    " --permission-mode bypassPermissions --output-format stream-json"
    " \"$(cat /tmp/gh-aw/aw-prompts/prompt.txt)\""
    "${GH_AW_MODEL_AGENT_CLAUDE:+ --model \"$GH_AW_MODEL_AGENT_CLAUDE\"}'"
)

# Copilot agent: run copilot CLI with workspace dirs, full tool/path access,
# and prompt from file.  No PATH setup needed (copilot is pre-installed).
COPILOT_AGENT_CLI = (
    "/bin/bash -c '/usr/local/bin/copilot --add-dir /tmp/gh-aw/"
    " --log-level all --log-dir /tmp/gh-aw/sandbox/agent/logs/"
    " --add-dir \"${GITHUB_WORKSPACE}\""
    " --disable-builtin-mcps --allow-all-tools --allow-all-paths"
    " --prompt \"$(cat /tmp/gh-aw/aw-prompts/prompt.txt)\""
    "${GH_AW_MODEL_AGENT_COPILOT:+ --model \"$GH_AW_MODEL_AGENT_COPILOT\"}'"
)

# Codex agent: set up PATH, run codex in full-auto JSON mode with prompt.
CODEX_AGENT_CLI = (
    f"/bin/bash -c '{_TOOLCACHE_PATH}"
    " && codex exec --full-auto --json"
    " \"$(cat /tmp/gh-aw/aw-prompts/prompt.txt)\""
    "${GH_AW_MODEL_AGENT_CODEX:+ --model \"$GH_AW_MODEL_AGENT_CODEX\"}'"
)

# ---------------------------------------------------------------------------
# CLI commands — detection (full run script, no awf wrapper)
# Detection commands run directly (not inside awf) with restricted tool sets
# and tee output to the detection log.
# ---------------------------------------------------------------------------

# Claude detection: restricted tools, tee to detection log.
CLAUDE_DETECTION_CLI = (
    "claude --print --disable-slash-commands --no-chrome"
    f" --allowed-tools '{CLAUDE_DETECTION_ALLOWED_TOOLS}'"
    " --debug-file /tmp/gh-aw/threat-detection/detection.log --verbose"
    " --permission-mode bypassPermissions --output-format stream-json"
    " \"$(cat /tmp/gh-aw/aw-prompts/prompt.txt)\""
    "${GH_AW_MODEL_DETECTION_CLAUDE:+ --model \"$GH_AW_MODEL_DETECTION_CLAUDE\"}"
    " 2>&1 | tee -a /tmp/gh-aw/threat-detection/detection.log"
)

# Copilot detection: set up dirs, allow only shell tools, tee to detection log.
COPILOT_DETECTION_CLI = (
    "COPILOT_CLI_INSTRUCTION=\"$(cat /tmp/gh-aw/aw-prompts/prompt.txt)\"\n"
    "mkdir -p /tmp/ /tmp/gh-aw/ /tmp/gh-aw/agent/ /tmp/gh-aw/sandbox/agent/logs/\n"
    "copilot --add-dir /tmp/ --add-dir /tmp/gh-aw/ --add-dir /tmp/gh-aw/agent/"
    " --log-level all --log-dir /tmp/gh-aw/sandbox/agent/logs/"
    " --disable-builtin-mcps"
    " --allow-tool 'shell(cat)' --allow-tool 'shell(grep)'"
    " --allow-tool 'shell(head)' --allow-tool 'shell(jq)'"
    " --allow-tool 'shell(ls)' --allow-tool 'shell(tail)'"
    " --allow-tool 'shell(wc)'"
    " --prompt \"$COPILOT_CLI_INSTRUCTION\""
    "${GH_AW_MODEL_DETECTION_COPILOT:+ --model \"$GH_AW_MODEL_DETECTION_COPILOT\"}"
    " 2>&1 | tee /tmp/gh-aw/threat-detection/detection.log"
)

# Codex detection: full-auto JSON mode, tee to detection log.
CODEX_DETECTION_CLI = (
    "codex exec --full-auto --json"
    " \"$(cat /tmp/gh-aw/aw-prompts/prompt.txt)\""
    "${GH_AW_MODEL_DETECTION_CODEX:+ --model \"$GH_AW_MODEL_DETECTION_CODEX\"}"
    " 2>&1 | tee -a /tmp/gh-aw/threat-detection/detection.log"
)

# ---------------------------------------------------------------------------
# Engine definitions
# ---------------------------------------------------------------------------

# Version constants — single source of truth for install_cmd strings
CLAUDE_VERSION = "2.1.50"
COPILOT_VERSION = "0.0.414"
CODEX_VERSION = "0.104.0"

ENGINES = {
    "claude": {
        "engine_name": "Claude Code",
        "agent_version": CLAUDE_VERSION,
        "secret_name": "ANTHROPIC_API_KEY",
        "secret_env_name": "ANTHROPIC_API_KEY",
        "secret_docs_url": (
            "https://github.github.com/gh-aw/reference/engines/"
            "#anthropic-claude-code"
        ),
        "install_cmd": f"npm install -g --silent @anthropic-ai/claude-code@{CLAUDE_VERSION}",
        "setup_node": "true",
        "awf_extra_flags": "--tty",
        "model_env_var": "GH_AW_MODEL_AGENT_CLAUDE",
        "model_detection_env_var": "GH_AW_MODEL_DETECTION_CLAUDE",
        "mcp_config_path": "/tmp/gh-aw/mcp-config/mcp-servers.json",
        "log_parser": "parse_claude_log.cjs",
        "agent_log_path": "/tmp/gh-aw/agent-stdio.log",
        "concurrency_prefix": "gh-aw-claude",
        "extra_agent_env": "",
        "mcp_gateway_config_style": "claude",
        "allowed_domains": CLAUDE_DOMAINS,
        "cli_cmd": CLAUDE_AGENT_CLI,
        "detection_cli_cmd": CLAUDE_DETECTION_CLI,
    },
    "copilot": {
        "engine_name": "GitHub Copilot CLI",
        "agent_version": COPILOT_VERSION,
        "secret_name": "COPILOT_GITHUB_TOKEN",
        "secret_env_name": "COPILOT_GITHUB_TOKEN",
        "secret_docs_url": (
            "https://github.github.com/gh-aw/reference/engines/"
            "#github-copilot-default"
        ),
        "install_cmd": f"/opt/gh-aw/actions/install_copilot_cli.sh {COPILOT_VERSION}",
        "setup_node": "false",
        "awf_extra_flags": "",
        "model_env_var": "GH_AW_MODEL_AGENT_COPILOT",
        "model_detection_env_var": "GH_AW_MODEL_DETECTION_COPILOT",
        "mcp_config_path": "/home/runner/.copilot/mcp-config.json",
        "log_parser": "parse_copilot_log.cjs",
        "agent_log_path": "/tmp/gh-aw/sandbox/agent/logs/",
        "concurrency_prefix": "gh-aw-copilot",
        "extra_agent_env": "COPILOT_AGENT_RUNNER_TYPE=STANDALONE",
        "mcp_gateway_config_style": "copilot",
        "allowed_domains": COPILOT_DOMAINS,
        "cli_cmd": COPILOT_AGENT_CLI,
        "detection_cli_cmd": COPILOT_DETECTION_CLI,
    },
    "codex": {
        "engine_name": "OpenAI Codex CLI",
        "agent_version": CODEX_VERSION,
        "secret_name": "OPENAI_API_KEY",
        "secret_env_name": "OPENAI_API_KEY",
        "secret_docs_url": (
            "https://github.github.com/gh-aw/reference/engines/"
            "#openai-codex"
        ),
        "install_cmd": f"npm install -g --silent @openai/codex@{CODEX_VERSION}",
        "setup_node": "true",
        "awf_extra_flags": "",
        "model_env_var": "GH_AW_MODEL_AGENT_CODEX",
        "model_detection_env_var": "GH_AW_MODEL_DETECTION_CODEX",
        "mcp_config_path": "/tmp/gh-aw/mcp-config/mcp-servers.json",
        "log_parser": "parse_codex_log.cjs",
        "agent_log_path": "/tmp/gh-aw/agent-stdio.log",
        "concurrency_prefix": "gh-aw-codex",
        "extra_agent_env": "",
        "mcp_gateway_config_style": "claude",
        "allowed_domains": CODEX_DOMAINS,
        "cli_cmd": CODEX_AGENT_CLI,
        "detection_cli_cmd": CODEX_DETECTION_CLI,
    },
}


def write_outputs(engine_id: str, config: dict[str, str]) -> None:
    """Write config values to GITHUB_OUTPUT or stdout."""
    output_file = os.environ.get("GITHUB_OUTPUT")

    # Derive keys that always match their non-detection counterparts.
    # Kept as separate outputs so the workflow can reference them independently.
    config = {
        "engine_id": engine_id,
        "detection_install_cmd": config["install_cmd"],
        "detection_secret_name": config["secret_name"],
        "detection_setup_node": config["setup_node"],
        **config,
    }

    # Values longer than this use a heredoc delimiter in GITHUB_OUTPUT
    # to avoid shell quoting issues with long CLI command strings.
    heredoc_threshold = 200

    lines: list[str] = []
    for key, value in sorted(config.items()):
        value_str = str(value)
        if "\n" in value_str or len(value_str) > heredoc_threshold:
            lines.append(f"{key}<<GH_AW_EOF")
            lines.append(value_str)
            lines.append("GH_AW_EOF")
        else:
            lines.append(f"{key}={value_str}")

    text = "\n".join(lines) + "\n"

    if output_file:
        with open(output_file, "a") as f:
            f.write(text)
    else:
        # Local run — print to stdout for verification
        sys.stdout.write(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Output engine configuration")
    parser.add_argument(
        "--engine",
        choices=list(ENGINES.keys()),
        required=True,
        help="Engine to configure",
    )
    args = parser.parse_args()

    write_outputs(args.engine, ENGINES[args.engine])


if __name__ == "__main__":
    main()
