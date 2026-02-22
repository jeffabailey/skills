# Security Fitness Review

## Summary

**Overall fitness score: 8.7 / 10**

This repository is a **skills library** (SKILL.md markdown files and checklists) with one GitHub Actions workflow. The threat surface is narrow: the workflow, configuration files, and workflow-triggered agent execution. There is no application runtime, database, API server, or user-facing web interface.

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Input Validation | 9/10 | No injection vectors; workflow context from GitHub; safe output validation with sanitize and maxLength |
| Authentication/Authorization | 9/10 | No app auth; workflow uses minimal permissions and validates COPILOT_GITHUB_TOKEN |
| Data Protection | 9/10 | Secrets via GitHub Secrets; generated keys masked; redaction step for logs |
| Dependency Security | 8/10 | All actions pinned with full SHA; gh-aw locked; no application dependencies |
| Error Handling/Logging | 8/10 | Secret redaction on logs; no user-facing error responses |
| Cryptography | 9/10 | openssl rand -base64 45 for ephemeral keys; no weak algorithms |

---

## Detailed Findings

### Finding 1: Catalog project-slug may cause broken links (informational)
- **Severity:** LOW (configuration, not security)
- **Confidence:** 8/10
- **Dimension:** Data Protection / Configuration
- **Location:** catalog-info.yaml:12, 26, 33
- **Description:** `github.com/project-slug: jeffabailey/skills` and `owner: jeffabailey` appear in catalog-info.yaml. If the intended GitHub username is `jeffbailey`, these links would 404. Verify the correct org/user name.
- **Evidence:** `github.com/project-slug: jeffabailey/skills`
- **Remediation:** Confirm the correct GitHub org and update project-slug, owner, and links if needed.

### Input Validation (9/10)

**Evidence:** `.github/workflows/fitness-review.lock.yml`

- **No injection vectors in project code:** No SQL, shell execution, HTML rendering, file path construction from user input, or deserialization of untrusted data. The repository contains markdown and YAML only.
- **Workflow input handling:** GitHub context (`github.actor`, `github.repository`, etc.) flows into the prompt from trusted GitHub; no attacker-controlled input is interpolated into commands. Template placeholders (lines 155–177) are substituted with context variables.
- **Safe output validation:** create_issue, missing_tool, noop tools have `sanitize: true` and `maxLength` constraints (body 65000, title 128, labels 128 per item) in validation.json (lines 363–421). Agent-generated issue bodies are validated before creation.
- **No external user input to workflow:** Triggers are schedule and workflow_dispatch; no `inputs` from users are passed into sensitive steps.

**Recommendations:** None for current scope. If workflow inputs are added in the future, validate them before use in prompts or commands.

---

### Authentication and Authorization (9/10)

**Evidence:** `.github/workflows/fitness-review.lock.yml`

- **No application auth:** Skills are documentation; there is no login, session, or JWT implementation.
- **Workflow token handling:** `COPILOT_GITHUB_TOKEN` is validated before execution (lines 353–357, 987–991). Tokens are referenced via `${{ secrets.X }}`, not hardcoded.
- **Principle of least privilege:** Top-level `permissions: {}` (line 37); jobs request only what they need: activation `contents: read`; agent `contents: read`, `issues: read`, `pull-requests: read`; conclusion `contents: read`, `issues: write` (lines 47, 252–254, 583–584).
- **Token fallback chain:** `secrets.GH_AW_GITHUB_MCP_SERVER_TOKEN || secrets.GH_AW_GITHUB_TOKEN || secrets.GITHUB_TOKEN` (lines 301, 624, 700) allows flexibility without exposing multiple tokens unnecessarily.

**Recommendations:** Ensure `COPILOT_GITHUB_TOKEN` (or `GH_AW_GITHUB_TOKEN`) is configured in repository secrets per SETUP.md. Rotate tokens periodically.

---

### Data Protection (9/10)

**Evidence:** `.github/workflows/fitness-review.lock.yml`, `.claude/settings.local.json`, SETUP.md

- **Secrets management:** All sensitive values use `${{ secrets.X }}`; no credentials in source or config.
- **Generated keys:** Ephemeral API keys use `openssl rand -base64 45` (~360 bits entropy) and are masked immediately with `::add-mask::` (lines 583–586, 631–634).
- **Log redaction:** `redact_secrets.cjs` runs on `always()` with `GH_AW_SECRET_NAMES` (lines 742–756) covering `COPILOT_GITHUB_TOKEN`, `GH_AW_GITHUB_MCP_SERVER_TOKEN`, `GH_AW_GITHUB_TOKEN`, `GITHUB_TOKEN`.
- **Settings file:** `.claude/settings.local.json` contains only permission allowlists (WebFetch, Bash commands); no API keys. File is gitignored via global gitignore.
- **Documentation:** SETUP.md (lines 26–27, 41–44) instructs users to store API keys in repository secrets, not in files.

**Recommendations:** Continue masking any new secret names in `GH_AW_SECRET_NAMES` when adding workflow steps that use secrets.

---

### Dependency Security (8/10)

**Evidence:** `.github/workflows/fitness-review.lock.yml`, `.github/aw/actions-lock.json`

- **Action pinning:** All actions use full SHA pins (e.g., `actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd`, `github/gh-aw/actions/setup@0eb518a648ba8178f4f42559a4c250d3e513acd1`).
- **Lock file:** `.github/aw/actions-lock.json` locks gh-aw setup version. The `.lock.yml` file is generated by `gh aw compile` and pins all action references.
- **No application dependencies:** No package.json, requirements.txt, go.mod, Cargo.toml, or similar. No npm/pip/go audit required for project-owned code.
- **External trust:** The workflow relies on `github/gh-aw/actions` and third-party actions. Pinning reduces supply-chain risk but does not eliminate it.

**Recommendations:** Run `gh aw compile` after changing the workflow source to refresh the lock file. Monitor gh-aw and actions for security advisories.

---

### Error Handling and Logging (8/10)

**Evidence:** `.github/workflows/fitness-review.lock.yml`

- **Secret redaction:** The redact_secrets step (lines 742–756) runs on `always()` so logs are sanitized even when earlier steps fail.
- **No user-facing errors:** There is no web app or API; workflow output is limited to Actions UI and artifacts.
- **Fail behavior:** Validation and secret checks run before agent execution; missing `COPILOT_GITHUB_TOKEN` stops the workflow before costly steps.
- **No stack traces or internal paths:** The project does not expose error details to end users.

**Recommendations:** None critical. If adding new logging, avoid logging secrets, tokens, or PII.

---

### Cryptography (9/10)

**Evidence:** `.github/workflows/fitness-review.lock.yml`

- **Random generation:** Ephemeral API keys use `openssl rand -base64 45` (lines 585, 632) for Safe Outputs and MCP Gateway.
- **Key masking:** Generated keys are masked immediately with `echo "::add-mask::${API_KEY}"` before use.
- **No weak algorithms:** No MD5, SHA-1, DES, RC4, or ECB in project code.
- **No hardcoded keys:** No encryption keys or API secrets in source; all come from `secrets.*` or runtime generation.

**Recommendations:** Continue using `openssl rand` or equivalent for any new ephemeral secrets. Do not introduce custom crypto.

---

## Top 5 Action Items (by impact)

1. **[LOW]** Verify `catalog-info.yaml` project-slug and owner — catalog-info.yaml:12, 26, 33 — Ensure GitHub links use the correct org/user (`jeffabailey` vs `jeffbailey`).
2. **[LOW]** Add project `.gitignore` — No project .gitignore — Add entries for `.claude/settings.local.json` (and other local config) so contributors without a global gitignore do not accidentally commit sensitive files.
3. **[LOW]** Document secret rotation — SETUP.md — Add guidance for rotating `COPILOT_GITHUB_TOKEN` and other workflow secrets (e.g., annual rotation).
4. **[INFO]** Monitor gh-aw and actions — .github/workflows — Subscribe to GitHub Advisory or Dependabot for `github/gh-aw/actions` and third-party actions used in the workflow.
5. **[INFO]** Validate workflow inputs if extended — .github/workflows — If `workflow_dispatch` inputs are added, validate and sanitize them before use in prompts or commands.

---

## Checklist Reference

See `review-security/references/checklist.md` for the full security checklist.

---

## Reference

Based on guidance from https://jeffbailey.us/categories/fundamentals/
