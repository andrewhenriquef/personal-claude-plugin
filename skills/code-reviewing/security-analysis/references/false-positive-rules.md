# False-positive rules

Apply these in Step 4 of `security-analysis`. They remove noise. They do not replace judgment: if the user's project makes an excluded item exploitable, report it.

Adapted from [anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review). Project rules in `CLAUDE.md` or a user instruction win over this list.

## Confidence scale

| Score | Meaning | Action |
|---|---|---|
| 0.9-1.0 | Exploit path is certain, or tested | Report |
| 0.8-0.9 | Clear vulnerable pattern with a known exploit method | Report |
| 0.7-0.8 | Suspicious, needs specific conditions | "Needs human check" if the missing condition is unknown. Drop if you know it does not hold |
| below 0.7 | Speculative | Drop |

## Hard exclusions (do not report by default)

1. Denial of service and resource exhaustion (CPU, memory, file descriptors, rate limiting).
2. Secrets on disk that are otherwise protected (permissions, secret manager).
3. Missing hardening with no concrete vulnerability (missing headers, no audit logs).
4. Theoretical race conditions and timing attacks.
5. Outdated third-party libraries. Use a dependency scanner for these.
6. Memory safety issues in memory-safe languages.
7. Files that are only tests or test infrastructure.
8. Log spoofing.
9. SSRF where the attacker controls only the path, not host or scheme.
10. User-controlled text inside AI prompts.
11. Regex injection and ReDoS.
12. Markdown and documentation files.
13. Missing input validation on non-security fields with no proven impact.

## Precedents

- Logging secrets, passwords, or PII in plaintext is a vulnerability. Logging URLs or non-PII data is not.
- UUIDs (v4) are unguessable.
- Environment variables and CLI flags are trusted.
- React and Angular escape output by default. Report XSS only on `dangerouslySetInnerHTML`, `bypassSecurityTrustHtml`, or the same kind of escape hatch.
- Client-side permission checks are not vulnerabilities by themselves. The server must enforce the rule. Report the missing server check.
- Subtle web issues (tabnabbing, XS-Leaks, prototype pollution, open redirects): report only with very high confidence and a concrete impact.
- CI workflow and shell script issues need a concrete path from untrusted input (for example a PR title in a `run:` step).
- Report MEDIUM findings only when they are obvious and concrete.

## Cases these rules must not hide

- Missing authorization on an endpoint that returns or changes another user's data. This is access control, not hardening.
- A "trusted" value that is attacker-controlled in practice (an env var set from a request header, a "CLI flag" built from user input).
- Unauthenticated endpoints that trigger expensive work with no limit **and** have a direct financial or availability impact the project cares about. Raise as "Needs human check", not as a finding.
- Secrets committed to the repo (they stay in git history even after deletion).

## Precision tips

- Same syntax, different context: `exec(cmd)` with a constant is safe, with request data it is not. Judge the data, not the call.
- Policy-dependent bugs (trust boundaries, tenant isolation, business-logic authorization) are where pattern-based detection is weakest. Read the policy code and the data model, and ask what the intended rule is. If the rule is unclear, ask the user or use "Needs human check".
