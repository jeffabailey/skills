# Security Fitness Checklist

Detailed checklist for reviewing code against security fundamentals. Use alongside the review-security skill to systematically evaluate each dimension. Based on the TFDM loop: identify threats, find vulnerabilities, implement defenses, monitor and respond.

---

## 1. Input Validation

### SQL Injection
- [ ] **String concatenation in SQL** -- Any pattern where user input is concatenated or interpolated into a SQL string (f-strings, string formatting, plus operator) is a SQL injection vector. Replace with parameterized queries or ORM parameter binding.
- [ ] **ORM raw query methods** -- ORM methods that accept raw SQL (e.g., `Model.objects.raw()`, `sequelize.query()`, `db.Exec()`) bypass parameter binding. Verify user input is never interpolated into raw SQL strings.
- [ ] **Stored procedures with dynamic SQL** -- Stored procedures that build SQL from input parameters using string concatenation are vulnerable even though the call to the procedure may be parameterized.
- [ ] **LIKE clauses with unescaped wildcards** -- User input in LIKE patterns without escaping `%` and `_` can cause excessive matching and information disclosure.

### Cross-Site Scripting (XSS)
- [ ] **Unencoded output in HTML** -- User input rendered in HTML templates without context-aware encoding. Check template engines for raw/unescaped output directives (e.g., `|safe` in Jinja2, `{!! !!}` in Blade, `dangerouslySetInnerHTML` in React, `v-html` in Vue).
- [ ] **JavaScript context injection** -- User input placed inside script tags or event handlers without JavaScript encoding. HTML entity encoding is not sufficient in JavaScript context.
- [ ] **URL context injection** -- User input in `href` or `src` attributes without URL encoding. Watch for `javascript:` protocol in user-supplied URLs.
- [ ] **DOM-based XSS** -- Client-side JavaScript that reads from `location`, `document.referrer`, or `postMessage` and writes to `innerHTML`, `document.write`, or `eval` without sanitization.
- [ ] **Content-Type and CSP headers** -- Responses serving user content set correct Content-Type headers. Content Security Policy (CSP) restricts inline scripts and untrusted sources.

### Command Injection
- [ ] **Shell execution with user input** -- Functions like `os.system()`, `subprocess.call(shell=True)`, `exec()`, `child_process.exec()`, or backtick execution with user-supplied arguments. Replace with parameterized command execution (e.g., `subprocess.call(["cmd", arg])` without `shell=True`).
- [ ] **Argument injection** -- Even without shell execution, user input as command arguments can inject flags (e.g., `--output=/etc/passwd`). Validate arguments against an allowlist of expected values.

### Path Traversal
- [ ] **File paths from user input** -- Any pattern where user input is used to construct file paths (e.g., `open(base_dir + filename)`) without canonicalization. An attacker can use `../` sequences to escape the intended directory.
- [ ] **Canonicalization check** -- After joining the base path and user input, resolve the canonical (absolute, symlink-resolved) path and verify it starts with the intended base directory.
- [ ] **Null byte injection** -- In some languages, null bytes in file paths can truncate the path. Reject null bytes in user-supplied filenames.

### XML and Deserialization
- [ ] **XML external entities (XXE)** -- XML parsers with default settings may resolve external entities, allowing file read, SSRF, or denial of service. Disable external entity resolution and DTD processing.
- [ ] **Unsafe deserialization** -- `pickle.loads()`, `yaml.load()` (without SafeLoader), Java `ObjectInputStream`, PHP `unserialize()` on untrusted data enable remote code execution. Use safe alternatives (JSON, YAML SafeLoader, allowlisted deserializers).
- [ ] **Server-side request forgery (SSRF)** -- User-supplied URLs fetched by the server without validation. Restrict allowed schemes (https only), validate against an allowlist of domains, or block internal network ranges (127.0.0.0/8, 10.0.0.0/8, 169.254.169.254).

Source: [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/)

---

## 2. Authentication Patterns

### Password Handling
- [ ] **Hashing algorithm** -- Passwords must be hashed with bcrypt (cost >= 10), scrypt, or argon2id. MD5, SHA-1, SHA-256 (even with salt) are too fast and vulnerable to brute force. Verify the cost factor is set explicitly, not relying on library defaults that may be outdated.
- [ ] **Plaintext password storage** -- Search for patterns that store passwords in database columns without hashing, or store them in configuration files, environment variables, or logs.
- [ ] **Password policy** -- Minimum length of 8+ characters enforced server-side (not just client-side). Check against known breached password lists when feasible.
- [ ] **Password transmission** -- Passwords are transmitted only over TLS. No password in URL query parameters (logged by proxies and browsers).

### Session Management
- [ ] **Token generation** -- Session tokens use cryptographically secure random generation (e.g., `crypto.randomBytes(32)`, `secrets.token_urlsafe(32)`). Tokens are not sequential, timestamp-based, or derived from user data.
- [ ] **Session expiration** -- Sessions expire after a defined period of inactivity and have an absolute maximum lifetime. Verify both idle timeout and absolute timeout are configured.
- [ ] **Session invalidation** -- Logout invalidates the session server-side (not just client-side cookie deletion). Password change invalidates all other active sessions.
- [ ] **Cookie security** -- Session cookies set `HttpOnly` (prevents JavaScript access), `Secure` (HTTPS only), `SameSite=Lax` or `Strict` (CSRF protection). Domain and path are scoped appropriately.

### Token Handling (JWT and API Keys)
- [ ] **JWT algorithm validation** -- The server specifies the expected algorithm and rejects tokens with `"alg": "none"` or unexpected algorithms. Never derive the algorithm from the token itself.
- [ ] **JWT expiry enforcement** -- Tokens have an `exp` claim and the server rejects expired tokens. Token lifetime is appropriate for the use case (short for access tokens, longer for refresh tokens).
- [ ] **JWT secret strength** -- Signing secrets are at least 256 bits of entropy for HMAC algorithms. RSA keys are 2048+ bits. Secrets are not hardcoded in source code.
- [ ] **Token revocation** -- A mechanism exists to revoke tokens before expiry (blocklist, short-lived tokens with refresh, or token versioning).
- [ ] **API key storage** -- API keys are hashed in the database (like passwords). Plaintext API keys are not stored or logged.

### Multi-Factor Authentication
- [ ] **MFA availability** -- MFA is available for sensitive accounts (admin, financial, data access). TOTP implementation uses a reasonable time window (30 seconds) and validates only once per window (prevents replay).
- [ ] **MFA bypass protection** -- Recovery codes are single-use, generated with cryptographic randomness, and stored hashed. No backdoor that skips MFA (e.g., a query parameter or header that disables the check).

Source: [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/)

---

## 3. Authorization

### Access Control Enforcement
- [ ] **Authorization on every endpoint** -- Every endpoint that accesses or modifies data has an authorization check. Check for routes that only verify authentication (is the user logged in?) but skip authorization (is this user allowed to do this?).
- [ ] **Centralized authorization** -- Authorization is enforced in middleware, decorators, or a central policy layer. Scattered per-handler checks are easy to miss on new endpoints. Verify that new routes automatically inherit the authorization requirement.
- [ ] **Default deny** -- The default behavior is to deny access. Routes must explicitly grant permissions, not explicitly deny them. Check for patterns where "everything is allowed unless blocked."

### RBAC and Privilege Escalation
- [ ] **Role assignment** -- Roles are assigned through a controlled process. Users cannot assign roles to themselves. Check for endpoints that accept a role parameter from user input.
- [ ] **Role hierarchy** -- If roles have a hierarchy (admin > editor > viewer), verify that higher roles cannot be reached by manipulating role identifiers or by accessing admin-only endpoints directly.
- [ ] **Horizontal privilege escalation** -- Users cannot access resources belonging to other users of the same role by changing IDs in requests.
- [ ] **Vertical privilege escalation** -- Regular users cannot access admin functionality by guessing URLs, manipulating tokens, or changing role claims in client-side storage.

### Insecure Direct Object References (IDOR)
- [ ] **Object ownership verification** -- When an endpoint receives a resource ID from user input, it verifies that the requesting user owns or has explicit permission to access that resource. The check is not just "is this a valid ID?" but "is this the right user's ID?"
- [ ] **Enumeration protection** -- Sequential or predictable resource IDs (auto-increment integers) combined with missing authorization checks allow attackers to enumerate all resources. Use UUIDs or verify ownership regardless of ID format.
- [ ] **Batch operations** -- Bulk endpoints (e.g., "update these 10 items") verify ownership of every item in the batch, not just the first one.

Source: [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/)

---

## 4. Data Protection

### PII Handling
- [ ] **PII inventory** -- The team knows what personal data is collected: names, emails, phone numbers, addresses, government IDs, financial data, health data, IP addresses, device identifiers. There is a documented inventory of where each type lives.
- [ ] **Data minimization** -- Only data required for the feature is collected. No fields collected "just in case." Optional fields are clearly optional. Ask: could this feature work without this field?
- [ ] **Data purpose limitation** -- Data collected for one purpose is not repurposed without user awareness. Analytics tools do not receive personal data beyond what is needed for the stated analytics purpose.
- [ ] **PII in non-obvious places** -- Check for PII in URLs (email in query parameters), error messages, analytics events, exported reports, and support tool integrations.

### Encryption at Rest and in Transit
- [ ] **TLS enforcement** -- All external endpoints use HTTPS. HTTP requests are redirected to HTTPS. HSTS header is set with an appropriate max-age. Internal service-to-service communication uses TLS where sensitive data is transmitted.
- [ ] **Sensitive field encryption** -- Fields containing PII, financial data, or health data are encrypted in the database using application-level or transparent database encryption.
- [ ] **Key separation** -- Encryption keys for data at rest are separate from TLS keys. Different categories of data can use different keys to limit blast radius.
- [ ] **Backup encryption** -- Database backups and data exports are encrypted. Encryption keys for backups are stored separately from the backups themselves.

### Logging Sensitive Data
- [ ] **Never log passwords** -- Search log statements for password fields. Passwords must never appear in logs regardless of context (creation, change, failed login).
- [ ] **Never log authentication tokens** -- Session tokens, JWTs, API keys, OAuth tokens, and password reset tokens must not appear in logs. Log a truncated hash or token ID instead.
- [ ] **Never log payment card numbers** -- Full credit card numbers, CVVs, and bank account numbers must not appear in logs. Mask all but the last four digits if any card reference is needed.
- [ ] **Never log government identifiers** -- Social security numbers, national ID numbers, passport numbers, and driver license numbers must not appear in logs.
- [ ] **Redact PII in logs** -- Email addresses, phone numbers, and physical addresses should be masked or omitted from logs. Use structured logging with a redaction layer.
- [ ] **Log retention** -- Logs have a defined retention period. Logs are not kept indefinitely. Log retention aligns with data protection requirements.

### Data Lifecycle
- [ ] **Deletion capability** -- The system can delete a user's data when requested. Deletion covers primary database, caches, search indexes, analytics, and queues removal from backups via retention policies.
- [ ] **Data export** -- Users can export their data in a portable format (relevant for GDPR right of access).
- [ ] **Retention policies** -- Data has defined retention periods. Automated processes enforce expiration. Data does not accumulate indefinitely.
- [ ] **Vendor data sharing** -- Personal data sent to third-party services (analytics, support tools, email providers) is documented. Contracts include data processing terms. Deletion requests propagate to vendors.

Source: [Fundamentals of Privacy and Compliance](https://jeffbailey.us/blog/2025/12/19/fundamentals-of-privacy-and-compliance/), [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/)

---

## 5. Dependency Security

### Lock Files and Pinning
- [ ] **Lock file exists** -- package-lock.json, yarn.lock, Pipfile.lock, poetry.lock, go.sum, Cargo.lock, or equivalent is present and committed to version control.
- [ ] **Lock file integrity** -- Lock file is not gitignored. CI installs from the lock file (e.g., `npm ci` not `npm install`, `pip install -r requirements.txt` with hashes).
- [ ] **Version pinning** -- Direct dependencies use exact versions or narrow ranges. Wide ranges like `>=1.0` without a lock file allow untested upgrades.

### Known Vulnerabilities
- [ ] **Automated vulnerability scanning** -- CI runs a dependency audit tool: `npm audit`, `pip-audit`, `govulncheck`, `cargo audit`, `bundle audit`, or a commercial scanner (Snyk, Dependabot).
- [ ] **No critical CVEs in direct dependencies** -- The project has no unaddressed critical or high-severity CVEs in direct dependencies. If a CVE cannot be patched immediately, there is a documented mitigation.
- [ ] **Transitive dependency awareness** -- The team monitors vulnerabilities in transitive (indirect) dependencies, not just direct ones. Audit tools typically cover this.

### Supply Chain
- [ ] **Dependency count awareness** -- The team knows how many direct and transitive dependencies exist. A high count (hundreds of transitive deps for a simple project) increases supply chain risk.
- [ ] **Post-install scripts** -- npm packages with post-install scripts can execute arbitrary code on install. Review or disable post-install scripts for unfamiliar packages.
- [ ] **Deprecated or archived packages** -- Dependencies that are deprecated, archived, or have had no release in over two years increase risk. Look for maintained alternatives.
- [ ] **Typosquatting awareness** -- Package names are verified against official registries. Watch for packages with names similar to popular packages (e.g., `lodahs` instead of `lodash`).

Source: [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/)

---

## 6. Error Handling and Logging

### Error Responses
- [ ] **No stack traces in production responses** -- Error responses to users contain a generic message and a correlation ID, not a stack trace, SQL error, or file path. Check for debug mode flags that may be enabled in production.
- [ ] **No database errors in responses** -- Database error messages (e.g., "column users.password does not exist") reveal schema information. Catch database errors and return generic messages.
- [ ] **No internal paths in responses** -- File system paths (e.g., `/var/www/app/src/auth.py`) in error responses reveal server structure. Strip paths from error output.
- [ ] **No version information in responses** -- Server headers, error pages, and API responses should not reveal framework version, language version, or server software version.
- [ ] **Consistent error format** -- All error responses use the same structure regardless of the error type. Inconsistent formats can leak information about which subsystem failed.

### Security Event Logging
- [ ] **Authentication events** -- Log successful and failed login attempts with username (never password), IP address, timestamp, and user agent. Multiple failures from the same IP or account should be detectable from logs.
- [ ] **Authorization denials** -- Log when a user attempts to access a resource they are not authorized for, including the user identity, the resource, and the requested action.
- [ ] **Input validation failures** -- Log when input validation rejects user input, including what type of validation failed (but not the full malicious input, which could be an injection attempt against the logging system).
- [ ] **Privilege changes** -- Log when roles or permissions are changed, including who made the change, what was changed, and when.
- [ ] **Account lifecycle events** -- Log account creation, password changes, email changes, MFA enrollment and removal, and account deletion.

### Fail-Secure Behavior
- [ ] **Default deny on error** -- When an authorization check fails due to an error (exception, timeout, service unavailable), the system denies access rather than allowing it. Check for `catch` blocks that return `true` or skip authorization.
- [ ] **No silent error swallowing** -- Empty catch blocks or generic exception handlers that log nothing and continue processing can hide security failures. Every catch block should log or re-throw.
- [ ] **Graceful degradation preserves security** -- When dependencies fail and the system degrades, security controls remain active. Caching authorization decisions requires careful invalidation.

Source: [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/)

---

## 7. Cryptography

### Algorithm Selection
- [ ] **Symmetric encryption** -- Use AES-256-GCM or ChaCha20-Poly1305. These provide authenticated encryption (confidentiality and integrity). Never use ECB mode. Never use DES, 3DES, or RC4.
- [ ] **Asymmetric encryption** -- Use RSA-2048+ (preferably 4096) or Ed25519/X25519 for modern systems. Never use RSA-1024 or DSA.
- [ ] **Hashing for integrity** -- Use SHA-256 or SHA-3. Never use MD5 or SHA-1 for security-critical hashing (file integrity, digital signatures). MD5 for non-security checksums (e.g., ETags) is acceptable.
- [ ] **Password hashing** -- Use bcrypt (cost >= 10), scrypt, or argon2id. Never use fast hash functions (MD5, SHA-family) for passwords, even with salt. The purpose of password hashing is to be slow.

### Key Management
- [ ] **No hardcoded keys** -- Search source code for patterns that look like encryption keys, API secrets, or signing keys as string literals. Keys must come from environment variables, secrets managers, or HSMs.
- [ ] **No keys in version control** -- Check git history for committed secrets. Use tools like git-secrets, trufflehog, or gitleaks. Even if removed from current files, keys in git history are compromised.
- [ ] **Key rotation** -- The system supports key rotation without downtime. Data encrypted with old keys can be re-encrypted or decrypted with the old key during a transition period.
- [ ] **Key access control** -- Only the services that need encryption keys have access to them. Keys are not shared across environments (dev keys differ from production keys).

### Random Number Generation
- [ ] **Cryptographic RNG for security values** -- Tokens, keys, nonces, salts, and session IDs use a cryptographic random number generator: `crypto.randomBytes()` (Node.js), `secrets` module (Python), `crypto/rand` (Go), `SecureRandom` (Java/Ruby). Never use `Math.random()`, `random.random()`, or similar for security-sensitive values.
- [ ] **Unique IVs and nonces** -- Initialization vectors are generated fresh for each encryption operation. Nonces are never reused with the same key. Counter-based nonces increment reliably without wrap-around.

### TLS Configuration
- [ ] **Minimum TLS version** -- TLS 1.2 is the minimum accepted version. TLS 1.0 and 1.1 are disabled. TLS 1.3 is preferred where supported.
- [ ] **Cipher suite selection** -- Weak cipher suites are disabled (RC4, DES, 3DES, NULL ciphers, export-grade ciphers). Forward secrecy is enabled (ECDHE or DHE key exchange).
- [ ] **Certificate validation** -- TLS clients validate server certificates (chain, expiry, hostname). Self-signed certificates are not accepted in production unless pinned.

Source: [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/)

---

## 8. Privacy and Compliance Signals

### GDPR Signals
- [ ] **Lawful basis for processing** -- Each type of personal data processing has a documented legal basis (consent, contract, legitimate interest). This is typically a legal decision, but engineering needs to implement the controls.
- [ ] **Consent collection** -- Where consent is the legal basis, consent is collected before processing. Consent is specific (per purpose), informed (clear explanation), and revocable (users can withdraw).
- [ ] **Right of access** -- Users can request a copy of their personal data. The system can export user data in a portable format.
- [ ] **Right to erasure** -- Users can request deletion of their personal data. The system can delete data across primary stores, replicas, caches, and queue deletion from backups.
- [ ] **Data processing records** -- A record of processing activities exists, documenting what data is processed, why, by whom, and for how long.
- [ ] **Data breach notification capability** -- The system can identify what data was affected in a breach and which users were impacted. Notification can be sent within required timeframes (72 hours under GDPR).

### CCPA Signals
- [ ] **Do Not Sell/Share** -- If the system shares personal information with third parties for cross-context behavioral advertising, a "Do Not Sell or Share My Personal Information" mechanism exists.
- [ ] **Disclosure of data categories** -- The system can report what categories of personal information are collected and for what purposes.
- [ ] **Right to delete** -- Users can request deletion. The system can process deletion requests within required timeframes (45 days under CCPA).

### General Privacy Practices
- [ ] **Data inventory** -- A documented inventory of personal data: what is collected, where it is stored, who has access, how long it is retained, and what vendors receive it. Treat changes to the inventory like code changes.
- [ ] **Data minimization in practice** -- New features are reviewed for data collection. Fields are challenged: "Is this required to deliver the feature, or nice to have?" Can it be computed on-device instead of stored?
- [ ] **Propagation control** -- Personal data does not propagate unchecked into logs, analytics, data warehouses, and vendor tools. Each destination is intentional and documented.
- [ ] **Vendor assessment** -- Third-party services that receive personal data have data processing agreements. Deletion requests propagate to vendors.

Source: [Fundamentals of Privacy and Compliance](https://jeffbailey.us/blog/2025/12/19/fundamentals-of-privacy-and-compliance/), [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/)

---

## OWASP Top 10 Quick Reference

Patterns to look for in code, mapped to the OWASP Top 10 (2021):

1. **A01: Broken Access Control** -- Missing authorization checks on endpoints, IDOR, privilege escalation, CORS misconfiguration, forced browsing to admin pages. (Checklist sections 3, 2)
2. **A02: Cryptographic Failures** -- Plaintext data transmission, weak algorithms, hardcoded keys, missing encryption at rest. (Checklist sections 7, 4)
3. **A03: Injection** -- SQL injection, command injection, XSS, LDAP injection, header injection. (Checklist section 1)
4. **A04: Insecure Design** -- Missing threat model, no rate limiting on sensitive operations, no principle of least privilege. (Checklist sections 2, 3)
5. **A05: Security Misconfiguration** -- Default credentials, unnecessary features enabled, overly permissive CORS, verbose error messages, missing security headers. (Checklist section 6)
6. **A06: Vulnerable and Outdated Components** -- Known CVEs in dependencies, unmaintained packages, no lock files. (Checklist section 5)
7. **A07: Identification and Authentication Failures** -- Weak passwords, missing MFA, credential stuffing, broken session management. (Checklist section 2)
8. **A08: Software and Data Integrity Failures** -- Unsigned updates, untrusted deserialization, CI/CD pipeline without integrity verification. (Checklist sections 1, 5)
9. **A09: Security Logging and Monitoring Failures** -- No login failure logging, no authorization denial logging, no incident detection capability. (Checklist section 6)
10. **A10: Server-Side Request Forgery** -- User-supplied URLs fetched by the server without validation, internal network access via SSRF. (Checklist section 1)

---

## Quick Reference: The Five Most Common Security Problems in Code

1. **SQL injection** -- User input concatenated into SQL queries. Fix: parameterized queries.
2. **Missing authorization checks** -- Endpoints verify authentication but not authorization. Fix: verify ownership or permission on every data access.
3. **Sensitive data in logs** -- Passwords, tokens, or PII appear in application logs. Fix: structured logging with a redaction layer.
4. **Hardcoded secrets** -- API keys, encryption keys, or passwords as string literals in source code. Fix: environment variables or secrets manager.
5. **Outdated dependencies with known CVEs** -- Direct or transitive dependencies with published vulnerabilities. Fix: automated scanning in CI with a policy to address critical CVEs.

---

## Source Articles

- [Fundamentals of Software Security](https://jeffbailey.us/blog/2025/12/02/fundamentals-of-software-security/)
- [Fundamentals of Privacy and Compliance](https://jeffbailey.us/blog/2025/12/19/fundamentals-of-privacy-and-compliance/)
