---
name: security-analysis
description: Review code changes for exploitable security vulnerabilities, with evidence and low false positives. Use when the user asks for a security review, security audit of a diff, branch, PR, or files, or mentions OWASP, injection, XSS, authz, authentication, secrets, SSRF, or "is this safe". Read-only, reports findings, does not fix.
---

# Security Code Review

> Strategy sources are in [docs/research/ai-code-review-strategies.md](../../../docs/research/ai-code-review-strategies.md). Methodology adapted in part from [anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review).

Find vulnerabilities an attacker can exploit. Do not list theoretical risks. Every finding needs a source, a sink, a missing control, and an exploit scenario.

This skill is read-only. Report findings. Do not edit code unless the user asks for a fix after the report.

## Why this process

Three facts shape every step:

1. **Vague prompts fail.** "Find all vulnerabilities" gives generic pattern matches. Narrow slices with a threat model give real findings.
2. **Long context hurts.** Models miss issues buried in large inputs. Review one attack surface at a time.
3. **Detection and verification are different jobs.** One pass finds candidates (high recall). A second pass tries to refute each one (high precision). Do not merge them.

## When to use

- A diff, branch, or PR needs a security pass before merge.
- The user names files or a feature and asks if it is safe.
- A change touches auth, input parsing, file or network access, crypto, or data export.

## When NOT to use

- The user wants fixes applied. Review first, then fix as a separate step.
- The user wants dependency CVE triage only. Use the project's scanner directly (`osv-scanner`, `bundler-audit`, `govulncheck`, `npm audit`).
- General quality or style review. Use a general code review skill.

## Process

### Step 0: Set scope

1. Use the files or range the user names.
2. If none: `git diff` plus `git diff --staged`, or the branch diff against the main branch.
3. Large scope (over about 20 changed files or 1500 lines): do not read it all at once. Go to Step 2 and review slice by slice. Tell the user the scope you chose.
4. Skip files that are only tests, docs, or generated code. Say that you skipped them.

### Step 1: Build a one-page threat model

Keep it short. Long scaffolding makes results worse. Write these four lines in your working notes, from the code and `CLAUDE.md`/README, not from guesses:

- **Entry points:** HTTP routes, RPC handlers, CLI args, queue consumers, webhooks, file uploads.
- **Trust boundaries:** where untrusted data enters (request, file, external API, DB content written by users) and what is trusted (env vars, CLI flags, internal services).
- **Attacker model:** anonymous, authenticated user, other tenant, malicious dependency. Pick the realistic ones.
- **High-risk operations:** SQL or query building, shell or process calls, deserialization, templating, file paths, outbound HTTP, crypto, token or session handling, authorization checks.

If the project has past security fixes (`git log --grep -i "security\|cve\|vuln"`), read two or three. Repeat bugs cluster.

### Step 2: Learn the repo's security patterns

Before you judge new code, find how the repo already protects itself:

- Framework protections in use (auto-escaping, ORM parameterization, CSRF middleware, strong params).
- Shared helpers for validation, sanitization, authz (policies, middleware, decorators).
- Where those helpers are applied in existing code.

Missing use of an established helper in new code is a strong signal. A framework default that already blocks the attack is a reason to drop a candidate.

### Step 3: Detect candidates, one slice at a time

A **slice** is one entry point and everything it reaches, or one high-risk operation and its callers. Do not review "the whole diff" as one block.

For each slice:

1. **Trace the data flow.** Start at the untrusted source. Follow it through every function to the sink. Read the callee code. Do not guess what a helper does.
2. **Think like the attacker.** Ask "how would I break this?", not "is this secure?". State the attacker model first. Ask what input reaches the sink, what control sits in the path, and whether the control can be bypassed.
3. **Compare with a secure pattern.** Ask how this code differs from the standard secure version, or from how the repo does the same thing elsewhere.
4. **Check each category** in [references/owasp-2025.md](references/owasp-2025.md). Read only the rows that match the slice. The list is a prompt for questions, not a pattern-match checklist.
5. **Use tools as candidate generators when they exist.** If the project already has a scanner configured (`semgrep`, `brakeman`, `gosec`, `bandit`, `eslint-plugin-security`, `gitleaks`), run it on the slice. Treat its output as unverified candidates. Do not install new tools without asking.

Write each candidate as one line: `file:line, category, source -> sink, suspected missing control`. Be generous here. Step 4 removes the noise.

After the last slice, do one more pass: "What else could an attacker do in this change that I have not listed?" Stop after one extra pass.

### Step 4: Verify each candidate (try to refute it)

This is a separate pass. Treat each candidate as a claim to disprove. For each, answer all five:

| Check | Question |
|---|---|
| Source | Can an attacker really control this input? Check the real caller, not the function signature. |
| Path | Does the data reach the sink unchanged? Read every step. |
| Control | Is there validation, escaping, parameterization, authz, or a framework default that blocks it? Search for it. |
| Exploit | Can you write a concrete request or input that triggers it? Write it out. |
| Impact | What does the attacker gain: data, code execution, privilege, account takeover? |

Then apply [references/false-positive-rules.md](references/false-positive-rules.md): hard exclusions, precedents, and the confidence scale.

Decide per candidate:

- **Report:** all five checks hold and confidence is 0.8 or higher.
- **Needs human check:** you cannot tell from the code (for example the control lives in config, infra, or a service you cannot read). Report it as such with the exact question. **Fail open: never drop a candidate only because you could not verify it.**
- **Drop:** a check fails with evidence (for example the ORM parameterizes this query). Keep a one-line reason for the "Dropped" count.

When your tool supports subagents and there are many candidates, verify each in a fresh context. A clean context refutes better than the context that produced the candidate.

Ask for evidence, not opinion. If a test or reproduction is cheap and safe (a unit test that calls the function with a malicious string), run it. Never run exploits against live or shared systems.

### Step 5: Report

Use this format. Sort by severity, then confidence.

```
## Security review: <scope>

Scope: <files / range>. Skipped: <test/doc/generated files>.
Threat model: <entry points, attacker model, one line each>

### Findings

Vuln 1: <Category>: `<file>:<line>`
- Severity: HIGH | MEDIUM | LOW
- Confidence: 0.0-1.0
- Source -> Sink: <where untrusted data enters -> where it is used unsafely>
- Missing control: <what should have blocked it>
- Exploit scenario: <concrete request or input and what the attacker gets>
- Recommendation: <specific fix, reference to the repo's existing helper if one exists>

### Needs human check
- `<file>:<line>`: <what you could not verify and the exact question to answer>

### Summary
Candidates: <N>. Reported: <N>. Needs check: <N>. Dropped: <N> (<top reasons>).
Tools run: <name and result, or "none available">.
Not covered: <areas out of scope, for example infra, runtime config, dependencies>.
```

If there are no findings, say so plainly, with what you checked. Do not invent low findings to fill the report.

**Severity**

- **HIGH:** directly exploitable. RCE, data breach, auth bypass, account takeover.
- **MEDIUM:** needs specific conditions, but the impact is significant.
- **LOW:** defense in depth, or low impact. Report LOW only when the user asked for it.

## Language references

Detect the project language from the files in the slice and manifests (`go.mod`, `Gemfile`, `*.rb`, `*.go`). Read **only** the matching reference before Step 3. If the scope spans several languages, read each one:

| Language | Detect | Reference |
|---|---|---|
| Go | `go.mod`, `*.go` | [references/go.md](references/go.md) |
| Ruby / Rails | `Gemfile`, `*.rb` | [references/ruby.md](references/ruby.md) |

Each reference holds the language's sinks, vulnerable and safe samples, and the scanner commands. If the language has no reference, apply the process above with the OWASP questions and follow the repo's own patterns.

To add a language: create `references/<language>.md` and add a row to this table.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The input looks sanitized." | Read the sanitizer. Many only cover one context (HTML escaping does not stop SQL injection). |
| "Only admins can call this." | Check that the admin check exists and runs before the sink. Check for horizontal access too. |
| "It matches a dangerous pattern, so report it." | A pattern is a candidate. No exploit path means no finding. |
| "I could not verify it, so drop it." | Unverified is not safe. Put it under "Needs human check". |
| "I will review the whole repo to be thorough." | Context rot hides real bugs. Review slices. |
| "More findings means a better review." | Noise makes people ignore the real finding. |

## Red flags

- A finding has no exploit scenario.
- A finding cites a function you did not read.
- The report lists generic advice ("validate all input") with no file and line.
- You flagged something the framework already handles.
- You reported hardening gaps as vulnerabilities.
- You dropped a candidate without a stated reason.
- You ran a scanner and pasted its output without verifying it.

## Verification

- [ ] Scope and skipped files are stated.
- [ ] Threat model has entry points, trust boundaries, attacker model, high-risk operations.
- [ ] Review ran per slice, not on the whole diff at once.
- [ ] Every reported finding has source, sink, missing control, exploit scenario, confidence.
- [ ] Every reported finding has confidence 0.8 or higher.
- [ ] Unverifiable candidates are under "Needs human check", not dropped.
- [ ] No code was modified.
- [ ] Report says what was not covered.
