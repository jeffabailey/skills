---
name: review-security
description: Analyzes code, CI/CD workflows, and container config for security vulnerabilities and compliance risks, producing fitness scores (1-10) across input validation, authentication/authorization, data protection, dependency security, error handling/logging, and cryptography. Use when the user says "security review", "check vulnerabilities", "audit security", "security issues", /review:review-security, asks to audit GitHub Actions workflows or a Dockerfile for security, or wants security fitness scores before shipping. Only reports findings with confidence >= 7/10.
---

# Security Fitness Review

Analyze the codebase (or specified files/modules) for security fitness.

Reference: [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/) — see also [Fundamentals of Privacy and Compliance](https://jeffbailey.us/blog/2025/12/19/fundamentals-of-privacy-and-compliance/) and [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

- `references/rubric.md` is the scoring source: severity definitions, 1-10 anchors per dimension, the N/A rule, and the overall-score formula. It is short; read it first so scores are repeatable across runs.
- `references/checklist.md` is what to check during each workflow step, including section 9 (CI/CD and containers) with ready-made grep patterns.
- `references/wisdom.md` is optional background, auto-synced from the two articles above. It has no rubric. Grep it by heading for a specific question (`grep -n '^##' references/wisdom.md`); never read it whole, it is about 15k tokens.

## Configuration

Invoke the resolver CLI to obtain the effective `security.confidenceThreshold`. Never load `fitness-config.json` directly.

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py" show --path <target>
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; the resolver ships two levels up in the plugin's `scripts/`. If your agent does not expand the variable, substitute the directory containing this `SKILL.md`.

Read `effective.security.confidenceThreshold` from the JSON block delimited by `<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->` / `<!-- END_EFFECTIVE_CONFIG_JSON -->`. The default is 7. Include the `Config:` and `Effective weights:` lines from the resolver within the first 10 lines of the report as the provenance trail (AC-03.1, AC-08.2).

## Workflow

1. **Load the rubric** — Read `references/rubric.md`, and skim the section headings of `references/checklist.md` so you know where each step's checks live.

2. **Identify scope and threat surface** — Use Grep/Glob to find request handlers, API endpoints, authentication flows, data access layers, form handlers, configuration files, dependency manifests, `.github/workflows/`, `Dockerfile*`, and `docker-compose*.yml`. Map the attack surface: external inputs (including issue/PR text that workflows consume), trust boundaries, data stores, third-party integrations. For very large generated files (e.g. compiled workflow lock files), grep for expressions, `permissions:`, and `uses:` rather than reading them end to end.

3. **Decide applicability** — For each of the six dimensions, decide whether anything in scope can be evaluated. Mark the rest `N/A — <reason>` per rubric.md. A workflows-only target usually scores Input Validation, Auth/Authz (token scope), Dependency Security (action pinning), and Cryptography only if secrets are handled.

4. **Run scanners that are installed** — Check with `command -v` and run what exists; scanner output is evidence, not a verdict, so confirm each hit in the code:
   - Secrets: `gitleaks detect --no-banner --redact -s <target>` (always `--redact`).
   - Dependencies: `pip-audit -r requirements.txt`, `npm audit --omit=dev` (needs a lock file), or `osv-scanner -r <target>`.
   - Workflows: `zizmor <target>/.github/workflows`; `actionlint` if zizmor is absent.

   If none is installed, review manually and label CVE claims "unverified (no scanner available)". Name the scanners you ran, or that none were available, in the report.

5. **Analyze input handling** — Trace user-supplied data from each entry point to SQL, shell, HTML, file paths, deserializers, and outbound URLs (checklist section 1). Before flagging, confirm the input is attacker-controlled and reaches the sink without validation; do not flag code that already validates (length/type checks, allowlists) as a vulnerability.

6. **Audit CI/CD and containers** — Apply checklist section 9. Run its greps for `${{ github.event.* }}` / `github.head_ref` inside `run:` or `github-script`, `pull_request_target` with a head checkout, workflow-level or missing `permissions:`, third-party `uses:` not pinned to a SHA, missing `persist-credentials: false`, and Dockerfile `USER`, `ENV` secrets, debug `CMD`, and `:latest` bases. Choice/boolean `inputs.*` and `github.sha`-style contexts are not injection.

7. **Audit authentication and authorization** — Checklist sections 2 and 3: password hashing, session management, tokens, authorization on every route, IDOR.

8. **Evaluate data protection and privacy** — Checklist sections 4 and 8: where PII and credentials are collected, stored, transmitted, logged; retention and deletion.

9. **Scan dependency security** — Checklist section 5: lock files, pinning, scanner results from step 4, supply chain.

10. **Review error handling and logging** — Checklist section 6: error responses leak nothing internal, security events are logged, failures deny.

11. **Assess cryptography and secrets** — Checklist section 7: algorithms, RNG, TLS, and hardcoded secrets (grep for `api_key|secret|token|password|BEGIN .*PRIVATE KEY` assigned to literals). Follow the secrets rule below.

12. **Score each dimension** with the anchors in `references/rubric.md` and file:line evidence. Compute the overall per rubric.md, including the CRITICAL cap.

13. **Self-check, then write the report** — Before writing, confirm: every cited file:line exists and says what the finding claims; every finding has confidence at or above the threshold; the overall equals the stated computation (and the cap is applied if any CRITICAL exists); no secret value appears anywhere in the report.

## Secrets rule

Reports land in the repository and get shared, so a reproduced secret is a second leak.

- Never reproduce a secret value, in full or in part beyond a provider prefix (e.g. `sk-...`, `AKIA...`). Cite it by file:line and variable name only. In Evidence, show the line with the value replaced by `<redacted>`.
- Always recommend rotating the credential, not only removing it: once committed, it lives in git history and any clones. Mention history rewriting (`git filter-repo`) as optional follow-up, never as a substitute for rotation.
- Recommend loading the value from the environment or a secrets manager, and adding a secret scanner (gitleaks) to pre-commit or CI.

## Confidence and Severity

Only report findings with confidence >= 7/10 (or the resolver's threshold). For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the vulnerable pattern actually reachable from an external input?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

Severity levels (CRITICAL, HIGH, MEDIUM, LOW) and their domain examples are defined in `references/rubric.md`. Any CRITICAL finding caps the overall score at 4.0, so a repository-takeover bug cannot hide behind good scores elsewhere.

## Scoring Dimensions (1-10 each)

Anchors for each score band are in `references/rubric.md`; the checks behind them are in `references/checklist.md`.

1. **Input Validation** — SQL injection, command injection, XSS, path traversal, XXE, deserialization, SSRF, and GitHub Actions expression injection
2. **Authentication and Authorization** — Password hashing, session management, token handling, authorization enforcement, IDOR, privilege escalation, CI token permissions and `pull_request_target`
3. **Data Protection** — PII handling, encryption at rest and in transit, log redaction, data minimization, retention, and deletion
4. **Dependency Security** — Lock files, known vulnerabilities, version pinning, supply chain, action and base-image pinning
5. **Error Handling and Logging** — Error response sanitization, security event logging, fail-secure behavior, debug servers in deploy config
6. **Cryptography** — Algorithm choices, key and secrets management (including hardcoded secrets), random number generation, TLS configuration

## Output Format

Write the report to `docs/security-review.md` at the root of the repository that contains the target, unless the user gives a path. For a review scoped to a subdirectory or file set, write `docs/security-review-<scope-slug>.md` (e.g. `docs/security-review-github.md` for `.github/`) so a scoped run does not replace the whole-repo report.

```markdown
# Security Fitness Review

**Target:** <path(s) or scope reviewed>
Config: <copied from resolver output>
Effective weights: <copied from resolver output>
**Scanners:** <tools run, or "none installed; manual review">

## Direct Answer

(Only if the user asked a specific question, e.g. "is this workflow safe to merge?": answer it in 1-3 sentences, citing the finding numbers.)

## Summary

Overall fitness score: X.X / 10 (mean of <list of scored dimensions>; capped at 4.0 due to CRITICAL finding N, if applicable)
Status: Healthy / Needs Attention / Critical

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Input Validation | X/10 | ... |
| Authentication/Authorization | X/10 | ... |
| Data Protection | X/10 or N/A — reason | ... |
| Dependency Security | X/10 | ... |
| Error Handling/Logging | X/10 | ... |
| Cryptography | X/10 or N/A — reason | ... |

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line
- **Description:** What the vulnerability is and why it matters.
- **Evidence:** The code pattern found, with any secret value replaced by `<redacted>`.
- **Exploit scenario:** How an attacker could exploit this in practice.
- **Remediation:** Concrete fix with code example or specific steps (for secrets: rotate first).

(repeat for each finding, ordered by severity)

### Input Validation (X/10)
- Evidence: file:line references (for an absence, cite where it should be, e.g. `.github/workflows/ (none)`)
- Issues found
- Recommendations

(repeat for each scored dimension; one line for each N/A dimension)

## Action Items (up to 5, by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...

## Reference

Based on [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/), [Fundamentals of Privacy and Compliance](https://jeffbailey.us/blog/2025/12/19/fundamentals-of-privacy-and-compliance/), and guidance from https://jeffbailey.us/categories/fundamentals/
```
