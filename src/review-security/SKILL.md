---
name: review-security
description: Analyzes code for security vulnerabilities and compliance risks, producing fitness scores (1-10) across input validation, authentication/authorization, data protection, dependency security, error handling/logging, and cryptography. Use when the user says "security review", "check vulnerabilities", "audit security", "security issues", /review:review-security, or wants security fitness scores before shipping. Only reports findings with confidence >= 7/10.
---

# Security Fitness Review

Analyze the codebase (or specified files/modules) for security fitness.

Reference: [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/) — see also [Fundamentals of Privacy and Compliance](https://jeffbailey.us/blog/2025/12/19/fundamentals-of-privacy-and-compliance/) and [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

For detailed scoring rubrics, severity definitions, what-good-looks-like / what-bad-looks-like criteria, and domain expertise, read `references/wisdom.md` before scoring. That file is auto-generated from:

- [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/)
- [Fundamentals of Privacy and Compliance](https://jeffbailey.us/blog/2025/12/19/fundamentals-of-privacy-and-compliance/)

Use the wisdom reference when evaluating code and assigning dimension scores.

## Configuration

If the project root contains `fitness-config.json` or `.fitness-config.json`, read it and use `security.confidenceThreshold` (default 7) for the minimum confidence to report findings. Otherwise use 7/10.

## Workflow

1. **Read domain knowledge** — Read `references/wisdom.md` to load scoring rubrics, thresholds, and severity definitions. Follow the TFDM loop: identify threats, find vulnerabilities, evaluate defenses, and assess monitoring.

2. **Identify scope and threat surface** — Use Grep/Glob to find request handlers, API endpoints, authentication flows, data access layers, form handlers, configuration files, and dependency manifests. Map the attack surface: external inputs, trust boundaries, data stores, and third-party integrations.

3. **Analyze input handling** — For each entry point, trace how user-supplied data flows through the system. Apply the rubrics/thresholds from the wisdom reference to evaluate input validation patterns.

4. **Audit authentication and authorization** — Find authentication implementations (login, signup, password reset, token generation). Apply the rubrics/thresholds from the wisdom reference to evaluate password hashing, session management, token handling, and authorization checks.

5. **Evaluate data protection** — Identify where sensitive data (PII, credentials, financial data) is collected, stored, transmitted, and logged. Apply the rubrics/thresholds from the wisdom reference to evaluate encryption, logging hygiene, data retention, and deletion capabilities.

6. **Scan dependency security** — Examine dependency manifests (package.json, requirements.txt, go.mod, Gemfile, pom.xml, Cargo.toml) for pinned versions, known vulnerable packages, and lock file presence. Apply the rubrics/thresholds from the wisdom reference.

7. **Review error handling and logging** — Check that error responses do not leak internals to users and that security events are logged appropriately. Apply the rubrics/thresholds from the wisdom reference.

8. **Assess cryptography** — Check encryption algorithm choices, key management, and random number generation. Apply the rubrics/thresholds from the wisdom reference.

9. **Check privacy and compliance signals** — Look for PII handling patterns, consent collection, data minimization, and deletion capabilities. Apply the rubrics/thresholds from the wisdom reference.

10. **Score each dimension** with file:line evidence, using the rubrics from `references/wisdom.md`.

11. **Produce the report** with scores, evidence, and prioritized action items.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the vulnerable pattern actually reachable from an external input?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

For severity level definitions (CRITICAL, HIGH, MEDIUM, LOW) with domain-specific examples, consult `references/wisdom.md`.

## Scoring Dimensions (1-10 each)

Dimensions to score (detailed rubrics including what-to-check, what-good-looks-like, and what-bad-looks-like are in `references/wisdom.md`):

1. **Input Validation** — SQL injection, command injection, XSS, path traversal, XXE, deserialization, and other input-driven vulnerabilities
2. **Authentication and Authorization** — Password hashing, session management, token handling, authorization enforcement, IDOR, privilege escalation
3. **Data Protection** — PII handling, encryption at rest and in transit, log redaction, data minimization, retention, and deletion
4. **Dependency Security** — Lock files, known vulnerabilities, dependency maintenance, version pinning, supply chain risks
5. **Error Handling and Logging** — Error response sanitization, security event logging, fail-secure behavior, log content safety
6. **Cryptography** — Algorithm choices, key management, random number generation, TLS configuration, custom crypto avoidance

## Output Format

Write the report to `docs/security-review.md` with this structure:

```markdown
# Security Fitness Review

## Summary

Overall fitness score: X.X / 10 (average of dimensions)

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Input Validation | X/10 | ... |
| Authentication/Authorization | X/10 | ... |
| Data Protection | X/10 | ... |
| Dependency Security | X/10 | ... |
| Error Handling/Logging | X/10 | ... |
| Cryptography | X/10 | ... |

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line
- **Description:** What the vulnerability is and why it matters.
- **Evidence:** The specific code pattern found.
- **Exploit scenario:** How an attacker could exploit this in practice.
- **Remediation:** Concrete fix with code example or specific steps.

(repeat for each finding, ordered by severity)

### Input Validation (X/10)
- Evidence: file:line references
- Issues found
- Recommendations

(repeat for each dimension)

## Top 5 Action Items (by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...

## Checklist Reference

See references/checklist.md for the full security checklist.

## Reference

Based on [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/), [Fundamentals of Privacy and Compliance](https://jeffbailey.us/blog/2025/12/19/fundamentals-of-privacy-and-compliance/), and guidance from https://jeffbailey.us/categories/fundamentals/
```

Refer to the security checklist at `review-security/references/checklist.md` for detailed checks within each dimension.
