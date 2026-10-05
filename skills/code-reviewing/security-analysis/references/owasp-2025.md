# OWASP Top 10:2025 review questions

Use in Step 3 of `security-analysis`. Read only the rows that match the slice. Each row is a question to ask about the code, not a pattern to grep for. Source: [OWASP Top 10:2025](https://owasp.org/Top10/2025/).

| ID | Category | Ask |
|---|---|---|
| A01 | Broken Access Control (includes SSRF) | Does every handler check that this user may act on this object, on the server? Can a user change an ID to reach another user's or tenant's data (IDOR)? Are mass-assigned fields limited? Does an outbound request use a URL with an attacker-controlled host or scheme? Is there an allowlist? |
| A02 | Security Misconfiguration | Does the change enable debug mode, open CORS, permissive CSP, default credentials, public buckets, verbose errors, or disabled TLS verification? |
| A03 | Software Supply Chain Failures | Does the change add or bump a dependency, pin to a branch or `latest`, run install scripts, or change CI or build steps that pull code? Does a workflow use untrusted input in a shell step? For a full dependency review (advisories, new libraries, updates), use `dependency-analysis`. |
| A04 | Cryptographic Failures | Are secrets or PII sent or stored in clear text? Weak hash for passwords (MD5, SHA-1, unsalted)? ECB mode, static IV or nonce, hardcoded key? Non-crypto random for tokens? Certificate checks disabled? |
| A05 | Injection | Does untrusted data reach a SQL/NoSQL query, shell command, template, LDAP, XPath, XML parser (XXE), HTML output (XSS), header, or file path without parameterization or context-correct escaping? |
| A06 | Insecure Design | Does the feature lack a needed control by design: no limit on password or OTP attempts, no ownership check in the flow, trust in client-supplied price or role, a workflow step that can be skipped? |
| A07 | Authentication Failures | Can login, reset, or token flows be bypassed or brute-forced? Are sessions fixed, never expired, or not rotated on login? Is JWT signature or `alg` verified? Are tokens compared in constant time? |
| A08 | Software or Data Integrity Failures | Does the code deserialize untrusted data (pickle, Marshal, YAML load, Java serialization)? Does it load code or updates without signature checks? Does it trust unsigned data in cookies or hidden fields? |
| A09 | Security Logging and Alerting Failures | Are security events (login failure, access denied) lost? Do logs hold secrets or PII? Can user input forge log entries in a way that matters? Report logging gaps only with a concrete impact. |
| A10 | Mishandling of Exceptional Conditions | Does an error path fail open (grant access on exception)? Does a caught error skip a security check? Do error messages leak internals? Is a partial failure left in an unsafe state? For error handling that is not a security issue (timeouts, retries, leaks, observability), use `reliability-analysis`. |

## Cross-cutting questions

Ask these for every slice:

- **Secrets:** Is any key, token, or password in the diff, in a test fixture, or in a config file?
- **Trust:** Which value here did the user control? Which value did I assume was trusted without reading its source?
- **Order:** Does the security check run before the sensitive action, on every path (including error and retry paths)?
- **Parity:** If the repo protects one endpoint a certain way, do the new and the neighboring endpoints do the same?
- **Data out:** Does a response, log, or export return more fields than the caller needs?

## Language and framework hints

Language sinks, samples, and tools are in the language references. See "Language references" in `SKILL.md`.
