# Security Scoring Rubric

Hand-maintained scoring rubric. sync-wisdom does not regenerate this file.

Use this file to assign severities and dimension scores. `checklist.md` lists what to check; `wisdom.md` is optional background.

## Severity

| Severity | Definition | Examples |
|----------|------------|----------|
| CRITICAL | An unauthenticated or low-privilege attacker can execute code, take over the repository or accounts, or read secrets, with no unusual preconditions. | `${{ github.event.issue.title }}` inside a `run:` script in a workflow with write permissions; a live API key or signing secret committed in source. |
| HIGH | Exploitable from external input but needs one precondition (an authenticated user, a specific config, a victim click), or exposes sensitive data at scale. | IDOR on `/api/orders/<id>` with no ownership check; passwords hashed with unsalted SHA-256; `pickle.loads` on a request body behind login. |
| MEDIUM | A real weakness whose impact is limited or that needs several preconditions; a missing defense-in-depth layer on an exposed surface. | XSS from model output rendered with `innerHTML` that has partial escaping; no CSP on a page that renders user content; `actions/checkout` without `persist-credentials: false` in a job that runs untrusted code. |
| LOW | Hardening or hygiene gap with no demonstrated exploit path. | Third-party `uses:` pinned to a tag instead of a SHA; server version banner in responses; missing lock file in a tool with two dependencies. |

A hardcoded credential is CRITICAL when it looks live (provider prefix, high entropy, used in an outbound auth header) and HIGH when it is plausibly a placeholder but still committed. Severity never depends on whether you can prove the key is valid.

## Dimension anchors

Score the dimension on the worst confirmed finding first, then adjust up or down one point for breadth of good practice. A dimension cannot score above the ceiling set by its worst finding: CRITICAL caps it at 2, HIGH at 4, MEDIUM at 6, LOW at 8.

### 1. Input Validation (injection in app code and in CI)

- **9-10:** Every external input reaching SQL, shell, HTML, file paths, deserializers, or URL fetches goes through parameterization, allowlists, or context-aware encoding. In workflows, untrusted `${{ }}` values reach `run:` only through `env:`.
- **7-8:** Safe patterns throughout; one LOW gap (e.g. missing length limit, CSP absent on a page with no user content).
- **5-6:** One MEDIUM injection vector, or validation is inconsistent across entry points.
- **3-4:** A reachable HIGH injection (SQLi, command injection, stored XSS, SSRF to metadata) on one entry point.
- **1-2:** CRITICAL injection: unauthenticated RCE, or attacker-controlled `github.event.*` text interpolated into a privileged `run:` step.

### 2. Authentication and Authorization (including CI token scope)

- **9-10:** Password hashing with bcrypt cost >= 10, scrypt, or argon2id; session cookies `HttpOnly`, `Secure`, `SameSite`; authorization enforced centrally with default deny; workflows declare least-privilege `permissions:` per job.
- **7-8:** Sound design with one LOW gap (e.g. no absolute session timeout; workflow permissions declared at workflow level but read-only).
- **5-6:** One MEDIUM gap: authorization checks scattered per handler, JWT without explicit algorithm, workflow-level `write` permissions with no injection path.
- **3-4:** HIGH: IDOR or vertical privilege escalation on one endpoint; fast hash for passwords; `pull_request_target` that checks out the PR head without running untrusted code.
- **1-2:** CRITICAL: authentication bypass, plaintext passwords, `alg: none` accepted, or `pull_request_target` that checks out and executes PR head code with secrets or write tokens.

### 3. Data Protection

- **9-10:** PII inventory or clear minimization; TLS enforced with HSTS; no passwords, tokens, or PII in logs; deletion path exists.
- **7-8:** One LOW gap (e.g. emails logged in debug only, no documented retention).
- **5-6:** MEDIUM: tokens or PII logged at info level, or sensitive fields stored unencrypted with no compensating control.
- **3-4:** HIGH: credentials or full card/government IDs logged, or sensitive data sent over plain HTTP.
- **1-2:** CRITICAL: bulk sensitive data publicly exposed (open bucket, unauthenticated export endpoint).

### 4. Dependency and Supply-Chain Security

- **9-10:** Lock files committed and used in CI (`npm ci`, hashes); a scanner (pip-audit, npm audit, osv-scanner, Dependabot) runs in CI; third-party actions pinned to full commit SHAs; base images pinned by digest or exact tag.
- **7-8:** Lock files present and scanner in CI; some actions or images pinned to tags only.
- **5-6:** No lock file or no scanner, or a MEDIUM known CVE in a direct dependency without mitigation.
- **3-4:** A HIGH or critical CVE in a reachable direct dependency, or unpinned (`@main`/`@master`) third-party actions in a job with secrets.
- **1-2:** Known-malicious or typosquatted package, or a CRITICAL CVE exploitable in this code path.

Mark scanner-free CVE claims "unverified" and cap their confidence at 7.

### 5. Error Handling and Logging

- **9-10:** Generic error responses with correlation IDs; debug mode off in production config; auth failures, authorization denials, and privilege changes are logged; failures deny by default.
- **7-8:** One LOW gap (e.g. framework version header, inconsistent error format).
- **5-6:** MEDIUM: stack traces or exception messages returned to clients, or no security event logging at all.
- **3-4:** HIGH: debug server or interactive debugger enabled in the deploy config (Flask `debug=True`, Werkzeug console reachable), or catch blocks that skip authorization on error.
- **1-2:** CRITICAL: fail-open authorization on error reachable by any user, or debug console exposed publicly.

### 6. Cryptography and Secrets Management

Hardcoded secrets belong here (key management), not under Authentication.

- **9-10:** AES-GCM or ChaCha20-Poly1305; RSA >= 2048 or Ed25519; CSPRNG for tokens; TLS >= 1.2; secrets from env or a secrets manager; a secret scanner in CI or pre-commit.
- **7-8:** Sound choices; one LOW gap (no rotation story, no secret scanner).
- **5-6:** MEDIUM: `Math.random()`/`random` for a low-value token, TLS verification disabled in a non-production path, MD5/SHA-1 for integrity.
- **3-4:** HIGH: ECB mode, DES/3DES/RC4, RSA-1024, hardcoded placeholder-looking secret, TLS verification disabled in production code.
- **1-2:** CRITICAL: live-looking secret or private key committed to source or git history.

## Not applicable (N/A)

Mark a dimension `N/A — <reason>` when nothing in scope can be evaluated for it, for example Cryptography on a workflows-only target that handles no keys or secrets, or Authentication on a static site generator with no login. Do not give a placeholder score: a guessed 7 skews the average and review-full.

A dimension that should exist but does not is not N/A; that absence is a finding. Cite the place it should be, for example `.github/workflows/ (no dependency scan step)` or `requirements.txt (no hashes, no lock file)`.

## Overall score

- Overall = mean of the scored (non-N/A) dimensions, rounded to one decimal. State which dimensions were averaged.
- If any CRITICAL finding exists, cap the overall at 4.0 and say so on the overall line.
- Status bands: a score at or above `statusThresholds.healthy[0]` is Healthy, at or above `statusThresholds.needsAttention[0]` is Needs Attention, anything lower is Critical (defaults 8 / 5 when the resolver gives none). Only the lower bounds count, so a fractional score such as 7.5 is Needs Attention, never a gap; review-full uses the same rule.
