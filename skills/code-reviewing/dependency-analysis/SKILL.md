---
name: dependency-analysis
description: Review the dependencies of a project for known vulnerabilities, supply-chain risk, maintenance and license health, and safe updates. Reviews dependency changes in the current branch by default, audits the whole tree on request, and updates or fixes packages on request using the minimal patched version. Maps each dependency to how the code uses it, traces vulnerable transitive dependencies to the direct package that pulls them in, and uses the project's own scanners and update tools. Use when the user asks to review, audit, update, bump, or fix dependencies, gems, modules, or packages, mentions CVEs, advisories, Dependabot, Renovate, lockfiles, or supply chain, adds a new library, or asks "is this package safe or maintained".
---

# Dependency Analysis

> Evidence sources: [govulncheck](https://go.dev/doc/tutorial/govulncheck), [bundler-audit](https://github.com/rubysec/bundler-audit), [OSV-Scanner](https://google.github.io/osv-scanner/), [OpenSSF Scorecard](https://github.com/ossf/scorecard), [GitHub dependency review](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-review), [Bundler lockfile checksums](https://blog.rubygems.org/2024/12/19/bundler-v2-6.html), and the Go modules reference ([go.dev/ref/mod](https://go.dev/ref/mod)). Update and triage flows adapted in part from [dependabot-triage](https://github.com/akshayrao14/git-practices/tree/main/skills/dependabot-triage) and [updating-npm-package](https://github.com/spencerpauly/awesome-cursor-skills/blob/main/resources/updating-npm-package/SKILL.md).

A dependency is code you did not write, running with the same rights as your own. Review it like code: who wrote it, what it does, how it reaches your system, and what happens when it is wrong.

This skill works in three modes. The user's request picks the mode:

| Mode | When | What it does |
|---|---|---|
| **Review** (default) | The user names no mode | Reviews the dependency changes in the current branch and uncommitted files. Read-only |
| **Audit** | "Audit the dependencies", "any vulnerable packages", "what is outdated" | Reviews the whole dependency tree. Read-only |
| **Fix** | "Update X", "fix this advisory", "bump", "triage this Dependabot alert or PR" | Applies the smallest safe update, then verifies. Changes manifests and lockfiles only |

Review and Audit never edit files. Fix mode edits only manifests and lockfiles, and only after the confirmations in Step 6.

## Why this process

1. **Severity scores alone mislead.** A critical advisory in code that never runs matters less than a medium one on the request path that attackers already exploit. Weigh reachability and exploit evidence, not only the score.
2. **Most risk is transitive.** The vulnerable package is often two or three levels down. The fix is usually to update the direct package that pulls it in.
3. **A new dependency is a new trust decision.** It brings its own code, its own maintainers, and its own dependencies. Review it before it lands.
4. **The smallest fix is the safest fix.** Take the lowest version that clears all the advisories, not the newest release. A wider jump has a wider breakage surface.
5. **Scanners find known problems only.** They miss typosquats, hijacked accounts, and unpinned sources. Check those by reading.

## When to use

- A change adds, removes, or updates a dependency, or edits a manifest or lockfile.
- The user asks if a package is safe, maintained, or still needed.
- An advisory, a scanner result, or a Dependabot or Renovate alert needs triage.
- The user wants outdated or vulnerable dependencies found or fixed.

## When NOT to use

- The user wants the application code checked for injection, access control, and similar. Use `security-analysis`.
- The user wants a migration guide followed across a large codebase for a major upgrade. This skill produces the report and the plan. The code changes are a separate task.
- The project has no dependency manifest. There is nothing to review.

## Process

### Step 0: Set scope, mode, and facts

1. Pick the mode from the user's request (see the table above). When unclear, use Review.
2. **Review scope.** Use the files the user names. If none, use the current change. That is the files not committed yet (`git diff --name-only`, `git diff --staged --name-only`, and new files from `git ls-files --others --exclude-standard`) plus the branch diff against the main branch (`git diff --name-only main...HEAD`; use `master` if the repo has no `main`). Keep the manifests and lockfiles, and the code that adds a new import. If no dependency file changed, tell the user there is nothing to review, and offer an Audit.
3. **Audit and Fix scope.** The whole project, or the packages the user names.
4. Detect the language and package manager (see Language references). Read the matching reference now.
5. Find these facts. Look in `CLAUDE.md`, README, CI config, Dockerfiles, and version files:

| Fact | Why it matters |
|---|---|
| Ecosystem, package manager, and its version | Commands and lockfile format differ |
| Manifest and lockfile paths. More than one lockfile for the same package? | Parity between lockfiles (Step 6) |
| Language runtime version, and whether it is still supported | An old runtime has its own advisories, and blocks updates |
| How CI and deploys install: frozen lockfile, or free resolution | A lockfile that CI ignores protects nothing |
| Which dependencies ship in production, and which are build or test only | Decides exposure |
| Policies: allowed licenses, update cadence, ignore lists | The project's rules win |

If a fact is missing, ask the user once for the whole list. Mark anything you assume.

### Step 1: Find and run the project's existing tools

Find the dependency tools the project already uses. Do not rely only on the tools named in this skill or in the references. Look in:

- Dependency manifests and lockfiles, and the tool configs next to them.
- CI config (`.github/workflows`, `.gitlab-ci.yml`), `Makefile`, `Taskfile`, `Rakefile`, and pre-commit config.
- Update bots: `.github/dependabot.yml`, `renovate.json`, and similar.
- Scanner config: `osv-scanner.toml`, `.bundler-audit.yml`, a Scorecard or dependency-review workflow, a license checker, an SBOM step.

Sort what you find into groups:

| Group | Examples | What to do |
|---|---|---|
| Vulnerability scanners | Advisory-database checks, call-graph scanners | Run as candidate generators |
| Update tools and bots | Dependabot, Renovate, native update commands | Read their config. Learn the cadence and the grouping rules |
| Policy and license checks | License allow lists, review actions | Apply the project's policy |
| Integrity features | Lockfile checksums, module checksum database | Check that they are on and intact |

For a tool the references do not name, read its README or `--help`, find how to run it, and use it the same way. Check its config for settings that weaken it (ignore lists, old suppressions with no reason or expiry), and report them. Do not change them.

Rules for running tools:

- Do not install anything. Treat all output as unverified candidates.
- Scanners that read manifests, lockfiles, and an advisory database are safe to run. Some fetch the advisory database from the network. That is fine. Say so.
- **Do not run code from a dependency you are reviewing.** Do not install a new, unreviewed package to look at it. Native extensions and install scripts run code on install. Read the package source without executing it (the language references show how).
- Never run an update command against a lockfile in Review or Audit mode.

If the project has no scanner, say so, and continue with Step 2.

### Step 2: Build the inventory

For each dependency in scope, record:

| Field | Question |
|---|---|
| Name and version change | Added, removed, or changed from which version to which? Patch, minor, or major? |
| Direct or transitive | Does the manifest name it, or does another package pull it in? Which one? |
| Role | Runtime, or build, test, or tooling only? |
| Source | The official registry, a git URL, a local path, a fork or replace, or a private registry? |
| Pin | Exact, a range, a branch, or a floating tag such as `latest`? Does the lockfile resolve it to one version? |
| Lockfile | Is the lockfile changed together with the manifest? Does it match? |

In Audit mode, list the direct dependencies first, then the transitive ones that carry findings. Do not list the whole tree.

### Step 3: Detect candidates, one dependency at a time

A **slice** is one dependency (or one cluster of advisories on the same package) and everything that depends on it. Work through [references/dependency-checks.md](references/dependency-checks.md), and read only the sections that match:

1. **Known vulnerabilities.** Advisories that affect the resolved version.
2. **Supply-chain risk.** Mostly for new or changed dependencies and sources.
3. **Health.** Deprecated, retracted, yanked, unmaintained, end-of-life, license, size, and overlap.
4. **Update and compatibility.** Bump class, breaking changes, constraints, lockfile consistency, unused and undeclared dependencies.
5. **Chains.** Which direct dependency pulls in each vulnerable or risky transitive one, and what update clears the whole chain.

Write each candidate as one line: `package version, category, short reason, where it comes from`. Be generous. Step 4 removes the noise. After the last slice, do one more pass: "Which dependency could hurt this project that I have not listed?"

### Step 4: Verify each candidate (try to refute it)

Treat each candidate as a claim to disprove. Answer all five:

| Check | Question |
|---|---|
| Resolved | Does the lockfile really resolve the affected version? A range that allows a bad version is not a bad version. Check the resolved one. |
| Applies | Does the advisory apply to this platform, this feature, and this configuration? Read the advisory text, not only the title. |
| Exposure | Does the code use the package on a path an attacker or a user can reach? Map the import sites into the exposure buckets in the reference. |
| Evidence | Is there reachability evidence (a call-graph result, an import site), exploit evidence (known exploited, a public exploit), or only a score? |
| Fix | Does a patched version exist, and what is the smallest update that clears it? |

Then apply the exclusions and the priority rules in the reference.

Decide per candidate:

- **Report:** the affected version is resolved, the advisory applies, and exposure or exploit evidence supports the severity.
- **Needs human check:** you cannot tell from the repo (a feature flag, a deployment fact, a registry detail you cannot reach). Report it with the exact question. **Fail open: never drop a candidate only because you could not verify it.**
- **Drop:** a check fails with evidence (the lockfile resolves a patched version, the advisory is for another platform, it was withdrawn). Keep a one-line reason for the count.

Reachability that says "not called" lowers priority. It does not make a package safe. List it as informational, and still recommend the update when it is cheap.

### Step 5: Report (Review and Audit)

Sort by severity, then by evidence. Use the format below. In Fix mode, use it for the "before" state, then continue to Step 6.

```
## Dependency review: <scope>

Mode: <Review | Audit>. Scope: <manifests, lockfiles, range>. Skipped: <vendored / generated>.
Ecosystem: <language, package manager, runtime version, supported or end-of-life>.
Tools run: <name, version, result, or "none available">.

### Findings

Dep 1: <Category>: `<package>` <version> (<direct | transitive via X>, <runtime | dev>)
- Severity: HIGH | MEDIUM | LOW
- Issue: <advisory ID and summary, or the risk in one line>
- Exposure: <buckets and sample import sites, or "no direct import">
- Evidence: <reachability, exploit signal, score, or the registry fact>
- Fix: <the smallest update, or the action. Name the direct package to bump for a transitive one>
- Risk of the fix: <bump class, breaking-change flags>

### New dependencies (Review mode)
| Package | Version | Why added | Source | Health | Verdict |

### Needs human check
- `<package>`: <what you could not verify and the exact question>

### Improvements
- <unused dependency, undeclared import, loose constraint, overlap, missing integrity feature, tool config that weakens a check>

### Summary
Candidates: <N>. Reported: <N>. Needs check: <N>. Dropped: <N> (<top reasons>).
Not covered: <private registries, vendored code, container base images, areas out of scope>.
```

If there are no findings, say so plainly, with what you checked. Do not invent findings.

**Severity**

- **HIGH:** an advisory that is known exploited, or high or critical with a reachable path on the request path. A malicious, typosquatted, or hijacked package. A broken integrity check (checksum mismatch, a branch-pinned git source in production code). A dependency-confusion exposure.
- **MEDIUM:** a high or critical advisory with no reachable path found, or in a runtime dependency with unclear use. A runtime or framework past its support end. An abandoned package on the request path. A license that conflicts with the project's policy.
- **LOW:** outdated with no advisory, a vulnerability in build or test tooling with no exposure, an unused or overlapping dependency, metadata and hygiene. Report LOW only when the user asked for it, or when it is a cheap improvement.

### Step 6: Fix (Fix mode only)

Read [references/update-playbook.md](references/update-playbook.md) first. The short form:

1. **Choose the target.** The lowest version that clears every advisory on the package, not the latest. For a transitive package, update the direct parent first. Use an override or a replace only as a last resort, with a note.
2. **Classify the bump.** Patch and minor: continue. Major, or a bump that raises the runtime requirement: stop. Produce the migration report from the playbook and ask the user before you apply.
3. **Choose the track.** Standard track by default: read the changelog, flag the keywords, and confirm. Fast track only for a patch or minor bump of a package used only in build or test, with no high or critical advisory. Fast track skips the changelog read. It never skips the tests or the lockfile check.
4. **Confirm before editing.** Say the package, the from and to versions, the bump class, and the exposure. Wait for a yes. Ask twice if the changelog has breaking-change flags.
5. **Apply with the narrowest command** from the language reference. One package per change. Do not run a blanket update. Do not use `latest`.
6. **Check the lockfile diff.** It must contain the intended package and only the transitive changes it needs. If it holds more, find out why.
7. **Check lockfile parity** when more than one lockfile or package manager covers the same package. If they disagree, stop and report it. Do not leave a half-fixed state.
8. **Verify.** Re-run the scanner. The advisory is gone, and no new advisory appeared. Build, run the tests, and run the linter. Compare against the baseline you took before the change.
9. **Commit only if the user asked.** One package per commit or pull request.

Never add an ignore entry, a suppression, or a lower severity in scanner config to make a finding go away. If no patched version exists, report it under "Needs decision", with the mitigation and the exposure.

## Language references

Detect the project language and package manager from the manifests (`go.mod`, `Gemfile`, `Gemfile.lock`) and the files in scope. Read **only** the matching reference before Step 1. If the scope spans several ecosystems, read each one:

| Language | Detect | Reference |
|---|---|---|
| Go | `go.mod`, `go.sum` | [references/go.md](references/go.md) |
| Ruby / Rails | `Gemfile`, `Gemfile.lock` | [references/ruby.md](references/ruby.md) |

Each reference holds the manifests and lockfiles, the commands (inventory, outdated, why, scan, integrity, update), how to map exposure, how to read a package without running it, and traps for that ecosystem. It is a starting point, not a complete list. Tools the project uses that are not listed there are handled in Step 1.

**Precedence when rules conflict:**

1. The project's own policies, tool config, and `CLAUDE.md`.
2. The defaults in the references.

If the language has no reference, apply the process above with the shared references and the project's own tools.

To add a language: create `references/<language>.md` with the same sections and add a row to this table.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The score is only 5.3, so skip it." | Check reachability and exploit evidence. Score is not exposure. |
| "It is only a dev dependency." | Build and test tools run on developer and CI machines with secrets. Lower the priority, do not ignore it. Check what the tool can reach. |
| "The scanner is clean, so it is safe." | Scanners know published advisories only. Read new dependencies and sources. |
| "Just update to latest." | A wider jump means more breakage. Take the minimal patched version. |
| "It is transitive, so we cannot fix it." | Update the direct parent. Use an override only as the last resort. |
| "Not called, so not vulnerable." | Reachability analysis misses dynamic use. List it as informational and update when it is cheap. |
| "It is a popular package." | Popular packages are the targets of account takeovers. Check recent maintainer and release changes. |
| "I will add it to the ignore list for now." | Never without the user's approval, a reason, and an expiry. |

## Red flags

- A finding names an advisory but not the resolved version.
- A finding rests on a score and says nothing about exposure.
- A new dependency was installed or run to inspect it.
- The fix is "latest" or a blanket update.
- The lockfile diff holds changes you cannot explain.
- An ignore entry or a suppression was added to scanner config.
- A major bump was applied without the migration report and a yes.
- A transitive finding names no direct package.
- The update raised the language runtime requirement and the report does not say so.
- Two lockfiles disagree and the change went ahead.

## Verification

- [ ] Mode, scope, and ecosystem are stated.
- [ ] Runtime version and its support status are stated.
- [ ] The project's own tools were found, and their config was read.
- [ ] Every finding names the resolved version, the source of the dependency, and its role (runtime or build).
- [ ] Every vulnerability finding has an exposure statement and an evidence line, not a score alone.
- [ ] Transitive findings name the direct package that pulls them in.
- [ ] New dependencies were read without running them.
- [ ] Unverifiable candidates are under "Needs human check", not dropped.
- [ ] Review and Audit: no file was modified.
- [ ] Fix mode: minimal target, confirmation, narrow command, lockfile diff checked, parity checked, scanner re-run, tests and build pass.
- [ ] No ignore entry or suppression was added.
- [ ] Report says what was not covered.
