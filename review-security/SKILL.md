---
name: review-security
description: Analyzes code for security vulnerabilities and compliance risks, producing fitness scores (1-10) across input validation, authentication/authorization, data protection, dependency security, error handling/logging, and cryptography. Use when the user says "security review", "check vulnerabilities", "audit security", "security issues", /review:review-security, or wants security fitness scores before shipping. Only reports findings with confidence >= 7/10.
---

# Security Fitness Review

Analyze the codebase (or specified files/modules) for security fitness. Identify vulnerabilities, insecure patterns, and compliance risks using evidence from the code. Follow the TFDM loop: identify threats, find vulnerabilities, evaluate defenses, and assess monitoring.

## Workflow

1. **Identify scope and threat surface** -- Use Grep/Glob to find request handlers, API endpoints, authentication flows, data access layers, form handlers, configuration files, and dependency manifests. These are the entry points where security matters most. Map the attack surface: external inputs, trust boundaries, data stores, and third-party integrations.

2. **Analyze input handling** -- For each entry point, trace how user-supplied data flows through the system. Check for parameterized queries vs string concatenation in SQL, command execution with user input, HTML output encoding, file path construction from user input, XML parsing configuration, and deserialization of untrusted data.

3. **Audit authentication and authorization** -- Find authentication implementations (login, signup, password reset, token generation). Check password hashing algorithms, session management, token handling (JWT validation, expiry, signing). Find authorization checks and verify they are present on every protected route. Look for IDOR patterns where object IDs from user input are used without ownership verification.

4. **Evaluate data protection** -- Identify where sensitive data (PII, credentials, financial data) is collected, stored, transmitted, and logged. Check for encryption at rest and in transit. Verify that logs do not contain passwords, tokens, credit card numbers, or government identifiers. Check data retention and deletion capabilities.

5. **Scan dependency security** -- Examine dependency manifests (package.json, requirements.txt, go.mod, Gemfile, pom.xml, Cargo.toml) for pinned versions, known vulnerable packages, and lock file presence. Check for use of deprecated or unmaintained libraries.

6. **Review error handling and logging** -- Check that error responses do not leak stack traces, database structure, file paths, or internal service details to users. Verify that security events (authentication failures, authorization denials, input validation failures) are logged with enough detail for incident response but without sensitive data.

7. **Assess cryptography** -- Check encryption algorithm choices (AES-256, RSA-2048+ or modern alternatives like ChaCha20, Ed25519). Look for hardcoded keys, keys in version control, weak random number generation, custom crypto implementations, and deprecated algorithms (MD5 for security, SHA-1 for signatures, DES, RC4).

8. **Check privacy and compliance signals** -- Look for PII handling patterns, consent collection, data inventory practices, data minimization, and deletion capabilities. Check for GDPR/CCPA relevant patterns: user data export, right-to-deletion, data processing records.

9. **Score each dimension** with specific file:line evidence.

10. **Produce the report** with scores, evidence, and prioritized action items.

## Confidence and Severity

### Confidence Threshold

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the vulnerable pattern actually reachable from an external input?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

### Severity Levels

- **CRITICAL** -- Directly exploitable with high impact. Remote code execution, SQL injection with database access, authentication bypass, hardcoded credentials in production code, unencrypted storage of passwords.
- **HIGH** -- Exploitable with significant impact under realistic conditions. Stored XSS, privilege escalation, IDOR on sensitive resources, missing authorization on data-modifying endpoints, sensitive data in logs.
- **MEDIUM** -- Exploitable with moderate impact or requires specific conditions. Reflected XSS, overly permissive CORS, missing rate limiting on authentication, verbose error messages exposing internals, weak but not broken cryptography.
- **LOW** -- Defense-in-depth improvements. Missing security headers, cookie flags not set, informational leakage in HTTP headers, minor configuration hardening.

## Scoring Dimensions (1-10 each)

Evaluate and score each dimension with evidence from the code.

### 1. Input Validation

What to check:
- SQL queries constructed with string concatenation or interpolation using user input
- OS command execution with user-supplied arguments (subprocess, exec, system calls)
- HTML output that includes user input without encoding (XSS vectors)
- File paths constructed from user input without canonicalization (path traversal)
- XML parsing that allows external entities (XXE)
- Deserialization of untrusted data (pickle, Java serialization, YAML load)
- Regular expressions vulnerable to ReDoS (catastrophic backtracking)
- Template injection through user-controlled template strings

What good looks like (8-10):
- All database queries use parameterized queries or an ORM with parameter binding
- User input is validated against an allowlist of expected formats before use
- HTML output uses context-aware encoding (HTML entity encoding in HTML context, JavaScript encoding in script context, URL encoding in href context)
- File operations use a base directory with path canonicalization and containment checks
- XML parsers are configured to disable external entities and DTD processing
- No deserialization of untrusted data, or only safe formats (JSON) with schema validation

What bad looks like (1-3):
- SQL strings built with f-strings, string concatenation, or percent formatting using user input
- User input passed directly to shell commands, eval, or exec
- User input rendered in HTML without any encoding
- File paths joined with user input and no traversal protection (e.g., open(base + user_input))
- XML parsed with default settings that allow external entities
- pickle.loads or yaml.load called on data from external sources

### 2. Authentication and Authorization

What to check:
- Password hashing algorithm (bcrypt, scrypt, argon2 vs MD5, SHA-1, SHA-256 without salt)
- Password policy enforcement (minimum length, complexity)
- Multi-factor authentication availability for sensitive operations
- Session token generation (cryptographically secure randomness vs predictable)
- Session expiration and invalidation on logout
- JWT implementation (algorithm validation, expiry checks, secret strength, "none" algorithm rejection)
- Authorization checks on every endpoint that accesses or modifies data
- IDOR patterns: using user-supplied IDs to fetch resources without verifying ownership
- Role-based access control consistency (RBAC checks in middleware vs scattered in handlers)
- Privilege escalation paths (can a regular user reach admin functionality?)
- Password reset flow security (token expiry, one-time use, secure delivery)

What good looks like (8-10):
- Passwords hashed with bcrypt (cost >= 10), scrypt, or argon2
- Sessions use cryptographically random tokens (e.g., crypto.randomBytes, secrets.token_urlsafe)
- JWTs validate algorithm, issuer, audience, and expiry; reject "none" algorithm
- Every data-access endpoint verifies the requesting user owns or has permission to access the resource
- Authorization is enforced in middleware or a central layer, not scattered per-handler
- Principle of least privilege: default deny, explicit grants

What bad looks like (1-3):
- Passwords stored in plaintext, or hashed with MD5/SHA-1/SHA-256 without salt
- Session tokens are sequential, timestamp-based, or use weak random sources
- JWTs do not validate algorithm or accept "none"; secrets are short or hardcoded
- Endpoints fetch resources by ID from request parameters without ownership checks
- No consistent authorization layer; some routes are unprotected
- Admin routes accessible without role verification

### 3. Data Protection

What to check:
- PII (personally identifiable information) identification: names, emails, phone numbers, addresses, government IDs, financial data, health data, biometric data
- Encryption at rest for sensitive data in databases and file storage
- Encryption in transit (TLS enforcement, HTTPS redirects, HSTS headers)
- Sensitive data in logs (passwords, tokens, credit card numbers, SSNs)
- Data minimization: collecting only what is needed for the feature
- Data retention: explicit policies and automated deletion
- Data export and deletion capabilities (GDPR right of access, right to erasure)
- Vendor data sharing: what personal data is sent to third-party services
- Backup and replica handling of sensitive data

What good looks like (8-10):
- Sensitive fields are encrypted at rest using application-level or database-level encryption
- All external communication uses TLS; HTTP is redirected to HTTPS; HSTS is enabled
- Logs redact sensitive fields by default (emails masked, tokens truncated, no passwords or card numbers)
- Data inventory exists documenting what PII is collected, where it lives, and how long it is retained
- Account deletion removes data from primary stores, caches, and queues deletion from warehouses and backups
- Only data needed for the feature is collected; optional fields are clearly optional

What bad looks like (1-3):
- Sensitive data stored in plaintext in the database with no encryption
- HTTP endpoints serve sensitive data without TLS
- Passwords, tokens, or credit card numbers appear in application logs
- No documented data inventory; personal data copied to analytics, warehouses, and vendor tools without tracking
- No account deletion capability, or deletion only removes the primary record leaving copies everywhere
- Fields collected "just in case" with no documented purpose

### 4. Dependency Security

What to check:
- Lock file presence and integrity (package-lock.json, yarn.lock, Pipfile.lock, go.sum, Cargo.lock)
- Known vulnerabilities in dependencies (CVE database, GitHub advisories)
- Dependency age and maintenance status (last release date, open security issues)
- Dependency pinning (exact versions vs ranges that auto-update)
- Number of transitive dependencies and supply chain depth
- Use of deprecated or archived packages
- Post-install scripts in npm packages or similar auto-execution vectors

What good looks like (8-10):
- Lock files are present and committed to version control
- Dependency audit shows no known high or critical vulnerabilities
- Dependencies are actively maintained (recent releases, responsive maintainers)
- Versions are pinned or use narrow ranges with lock files ensuring reproducibility
- Automated vulnerability scanning runs in CI (npm audit, pip-audit, govulncheck, cargo audit)

What bad looks like (1-3):
- No lock file; dependency resolution varies between installs
- Known critical CVEs in direct dependencies with no plan to update
- Dependencies abandoned by maintainers with open security issues
- Wide version ranges without lock files (e.g., ">=1.0" with no upper bound)
- No automated vulnerability scanning in CI or development workflow

### 5. Error Handling and Logging

What to check:
- Error responses returned to users: do they contain stack traces, SQL errors, file paths, or internal service names?
- Generic error pages vs detailed error information in production
- Security event logging: authentication successes and failures, authorization denials, input validation failures, password changes, privilege changes
- Log content: do logs contain sensitive data (passwords, tokens, PII)?
- Log access controls: who can read production logs?
- Fail-secure behavior: when an error occurs, does the system default to deny or allow?
- Exception handling that silently swallows errors, hiding security failures

What good looks like (8-10):
- Users see generic error messages (e.g., "Something went wrong") with no internal details
- Detailed errors are logged server-side with request IDs for correlation
- Authentication failures are logged with username (not password), IP, and timestamp
- Authorization denials are logged with user, resource, and requested action
- Logs never contain passwords, session tokens, or unmasked PII
- On error, the system defaults to deny access (fail closed)

What bad looks like (1-3):
- Stack traces, SQL error messages, or file paths returned in API responses
- Debug mode enabled in production, exposing detailed error information
- No logging of authentication failures or authorization denials
- Passwords, tokens, or full credit card numbers appear in logs
- Errors silently caught and ignored, masking security failures
- On error, the system defaults to allow access (fail open)

### 6. Cryptography

What to check:
- Encryption algorithms: AES-256-GCM, ChaCha20-Poly1305 for symmetric; RSA-2048+, Ed25519 for asymmetric; SHA-256+ for hashing
- Deprecated algorithms: MD5 (for security purposes), SHA-1 (for signatures), DES, 3DES, RC4, ECB mode
- Key management: hardcoded keys in source code, keys in version control, key rotation capability
- Random number generation: cryptographic RNG (crypto.randomBytes, secrets module, /dev/urandom) vs math.random or similar
- Custom cryptography implementations vs established libraries
- TLS configuration: minimum version (TLS 1.2+), cipher suite selection, certificate validation
- Initialization vectors: unique per encryption operation, never reused with the same key

What good looks like (8-10):
- Established cryptographic libraries used (libsodium, OpenSSL, built-in crypto modules)
- AES-256-GCM or ChaCha20-Poly1305 for encryption; no ECB mode
- Keys stored in environment variables, secrets managers, or HSMs; never in code or version control
- Key rotation is supported and documented
- All random values for security use cryptographic RNG
- TLS 1.2+ enforced; weak cipher suites disabled

What bad looks like (1-3):
- MD5 or SHA-1 used for password hashing or digital signatures
- DES, 3DES, or RC4 used for encryption; AES in ECB mode
- Encryption keys hardcoded in source files or committed to version control
- Math.random() or similar non-cryptographic RNG used for tokens, keys, or nonces
- Custom encryption algorithm implementation ("rolling your own crypto")
- TLS 1.0/1.1 accepted; self-signed certificates accepted without pinning

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

Based on guidance from https://jeffbailey.us/categories/fundamentals/
```

Refer to the security checklist at `review-security/references/checklist.md` for detailed checks within each dimension.
