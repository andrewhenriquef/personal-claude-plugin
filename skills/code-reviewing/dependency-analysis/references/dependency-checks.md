# Dependency review questions

Use in Step 3 of `dependency-analysis`. Read only the sections that match the dependency. Each row is a question to ask, not a pattern to grep for. A row is a finding only when Step 4 confirms it.

Sources: [OpenSSF Scorecard checks](https://github.com/ossf/scorecard), [GitHub dependency review](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-review), the advisory databases that the scanners use, and common supply-chain attack patterns (typosquatting, dependency confusion, maintainer takeover, install-time code).

## 1. Known vulnerabilities

| Ask | Why it matters |
|---|---|
| Which version does the lockfile resolve? Is it in the advisory's affected range? | The manifest range is not the installed version |
| Are several advisories open on the same package? What is the highest first-patched version among them? | One update to that version clears the whole cluster. Several small updates waste work |
| Does the advisory apply to this platform, feature, and configuration? | Many advisories need a specific option, OS, or call pattern. Read the text |
| Is there exploit evidence: listed as known exploited, a public exploit, a high exploit-probability score? | Exploit evidence moves a medium advisory above a high one with no evidence |
| Is the vulnerable function reachable from the code? Does a call-graph tool say "called" or "imported but not called"? | "Called" raises priority. "Not called" lowers it. It does not clear it |
| Is the advisory about the standard library or the runtime? | The fix is a runtime update, not a package update |
| Does a patched version exist? Is it in the same major version? | Decides the size of the fix |
| Was the advisory withdrawn or disputed? | Drop it, with the reason |

**Prioritize with evidence, not with the score alone.** Order by: exploit evidence, then reachability on the request path, then impact (code execution above data theft above denial of service), then the severity score. Look the exploit and score data up in the advisory source or the scanner output. Do not write them from memory.

### Exposure buckets

Sort every import or use site into one bucket. Report the counts and a few sample paths. The user decides risk from the surface, not from a guess.

| Bucket | What it is |
|---|---|
| **Request path** | HTTP handlers, routes, middleware, webhooks, job consumers, parsers of data from outside. Attacker-controlled input can reach it |
| **Internal runtime** | Code that runs in production on trusted data: internal services, scheduled jobs, data pipelines |
| **Build and test** | Test suites, linters, code generators, CI scripts, dev servers. Not shipped, but they run with developer and CI secrets |
| **None** | Declared but never imported. Also an improvement: remove it |

A dependency that is only transitive has no import site. Say so, and follow the chain to the direct parent.

## 2. Supply-chain risk

Most useful for new or changed dependencies and sources. Read the package without running it (see the language references).

| Ask | Why it matters |
|---|---|
| Is the name close to a popular package (one letter off, swapped words, a different separator)? | Typosquatting: a malicious lookalike |
| Who publishes it? Is the publisher the known project, or a new account? Did the maintainer list change recently? | Account takeover and ownership transfer are common attack routes |
| How old is the package, and how many versions? Did a long-quiet package suddenly publish a new release? | A burst after a long silence is a warning sign |
| Did the new version add a dependency, an install-time step, a native extension, or a network call at install or load time? | That is where malicious code hides |
| Is the source the official registry? Or a git URL, a branch, a local path, a fork, or `http://`? | A branch moves under you. A fork has no review. `http://` can be tampered with |
| Is the version pinned, and does the lockfile record an integrity hash or checksum? Did a hash change with no version change? | A changed hash for the same version means tampering or a re-publish |
| Is the package name one that your private packages also use, with a public registry on the same resolution path? | Dependency confusion: the public package wins on a higher version number |
| Does the repository link match the package? Does the repository have a security policy and recent activity? | Mismatch is a sign of a fake. Scorecard checks cover maintenance, pinning, signed releases, and workflow safety |
| Does the package use a pre-release, a commit-hash version, or a floating tag? | Untagged code with no release process |
| Does the code in the diff import this package in a place that handles secrets, credentials, or network? | A new package in a sensitive place gets more review |

If the package does only something small (a few functions), ask if the standard library or an existing dependency already does it.

### Read a package without running it

Never install, require, or run a new dependency to see what it does. Fetch the source and read it. Read: the manifest or gemspec, install hooks and extension build files, entry points, any network or process or file access, and the list of its own dependencies. The language references give the commands.

## 3. Health

| Ask | Why it matters |
|---|---|
| Is the package deprecated, retracted, yanked, or archived? | The maintainers say do not use it. No more fixes |
| When was the last release and the last commit? Are issues and security reports answered? | An abandoned package never gets security fixes |
| One maintainer or many? | A single maintainer is a single point of failure and takeover |
| Is the language runtime or framework version still supported by its maintainers? Look up the support dates, do not rely on memory | An unsupported runtime has unfixed advisories, and blocks updates |
| What license does it have? Did the license change between versions? Does it fit the project's policy? | Legal risk, and a license change can come in a minor release |
| How many dependencies does it add to the tree? How big is it? | Each one adds risk and install time |
| Does it duplicate a package the project already has? | Two libraries for one job doubles the surface |
| Is it used at all? | An unused dependency is risk with no benefit |

## 4. Update and compatibility

| Ask | Why it matters |
|---|---|
| Is the bump a patch, minor, or major? Does the version number follow semantic versioning in practice? | Sets the review depth. Some projects break things in minors |
| Do the release notes between the two versions hold `BREAKING`, `DEPRECATED`, `MIGRATION`, `removed`, or `dropped`? | Quote those lines verbatim. Do not paraphrase |
| Does the new version raise the runtime requirement (language, platform, peer dependencies)? | It can force a runtime upgrade across the project |
| Is the constraint too loose (`>=`, `*`, `latest`, a branch)? | A fresh install can resolve to something you never tested |
| Is the constraint too tight (an exact pin, an upper cap) so that a security fix cannot be installed? | A pin that blocks the patch is a risk |
| Is there an override, replace, or pinned transitive version? Is it still needed? Does it have a note? | Forgotten overrides hide fixes and cause drift |
| Is the lockfile changed with no manifest change, or the reverse? | An unexplained lockfile change is a red flag. A manifest change with no lockfile change means CI and local resolve differently |
| Is more than one lockfile or package manager in use for the same project? Do they resolve the same version? | Drift between local and CI |
| Does the code import a package that the manifest does not declare (it works only because a transitive dependency provides it)? | It breaks when the parent changes |
| Is a package declared but never imported? | Remove it |

## 5. Chains

A vulnerable or risky package two or three levels down is the usual case.

1. Find the path from your direct dependency to the package (the language references have the command).
2. Find which direct dependency owns the path. If several paths exist, list each.
3. Check which version of the direct dependency pulls in a fixed version of the transitive one.
4. The fix, in order of preference: update the direct parent; update the direct parent and a second parent together; override the transitive version with a note and a removal condition; replace the parent.
5. After any fix, scan again. A fix must not trade one advisory for another.

## Exclusions and precedents

Do not report:

- An advisory that was withdrawn, or is disputed with no impact on this project.
- A resolved version that is already patched, shown in a stale alert or in an old range.
- An advisory for a platform or feature the project does not use, with the reason stated.
- A package only because it is new, or only because it is not the latest.
- A vulnerability in a build or test tool as HIGH, unless the tool processes untrusted input in CI or holds production secrets.
- A license or style preference that the project policy does not forbid.
- "Consider rewriting with the standard library" with no cost or risk named.

Precedents:

- A critical or high advisory on the request path is reported even when a call graph shows "not called". Dynamic use defeats call analysis. Mark the evidence honestly.
- An advisory you cannot place (unknown use, unknown feature flag) is "Needs human check", not a drop.
- A stale scanner alert for a version the lockfile no longer resolves is dropped, with the reason.
- A package with no advisories that is stable and small, with no recent releases, is LOW at most.
