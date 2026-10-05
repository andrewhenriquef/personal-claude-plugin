# Update playbook

Use in Step 6 (Fix mode) of `dependency-analysis`. The user asked to update a package or fix an advisory. This file says how to do it with the smallest safe change.

Adapted in part from the [dependabot-triage](https://github.com/akshayrao14/git-practices/tree/main/skills/dependabot-triage) and [updating-npm-package](https://github.com/spencerpauly/awesome-cursor-skills/blob/main/resources/updating-npm-package/SKILL.md) skills. The language references hold the exact commands.

## 1. Take a baseline

Before you change anything:

- Run the build, the tests, and the linter once. You need to know what is already red.
- Run the project's scanner and save the advisory list. After the update, compare.
- Save the resolved version of the target package and of its parents.
- Check the working tree is clean for the manifest and lockfile. If the user has uncommitted changes there, stop and tell them.

## 2. Choose the target version

**Minimal patched version.** The lowest version that fixes every advisory on the package.

- One advisory: the first patched version in the advisory.
- Several advisories on the same package: the highest of their first-patched versions. One update clears the cluster.
- Prefer a target in the current major version. Take a newer major only if no patched version exists in the current one.
- "Latest" is not a target. It is an option that the user may choose.

**Transitive packages.** In order of preference:

1. Update the direct parent to a version that pulls in a fixed child.
2. Update two parents together if both pull the child.
3. Use an override, replace, or constraint on the child, with a comment that says which advisory it fixes and when to remove it. This hides the real dependency graph, so use it last.
4. Replace the parent, only if it is abandoned. That is a separate task.

**No patched version.** Do not ignore the advisory. Report it under "Needs decision": the exposure, a mitigation (disable the feature, validate input, limit access), and an alternative package.

## 3. Classify the bump

| Class | Example | Handling |
|---|---|---|
| Patch | 1.2.3 to 1.2.4 | Apply. Run the checks |
| Minor | 1.2.3 to 1.3.0 | Apply. Read the changelog flags. Run the checks |
| Major | 1.2.3 to 2.0.0 | Stop. Produce the migration report. Ask before you apply |
| Runtime bump | The new version needs a newer language runtime | Stop. Report it. This is a project-wide decision |
| Pre-1.0 minor | 0.4.1 to 0.5.0 | Treat as major. Many pre-1.0 packages break in minors |

## 4. Choose the track

**Standard track** (default):

1. Fetch the release notes or changelog between the two versions, from the project's repository or the registry.
2. Search them for `BREAKING`, `DEPRECATED`, `MIGRATION`, `removed`, `dropped`. Show every flagged line verbatim.
3. Confirm with the user. If any line is flagged, ask a second time with the lines shown.
4. If the package has no direct import (purely transitive), say so, and one confirmation is enough.

**Fast track**, only when all are true:

- The bump is patch or minor.
- The package is used only in build or test (no request-path or runtime import).
- No advisory on it is high or critical.
- The user did not ask for the full process.

Fast track skips the changelog read and uses one confirmation. It never skips the baseline, the lockfile diff check, the scanner re-run, or the tests.

**Always standard track:** a high or critical advisory on a package with a request-path import, a major bump, or any change in a package that handles authentication, cryptography, parsing of untrusted input, or networking.

## 5. Confirm before you edit

Say, in a few lines:

- The package, from version, to version, and the bump class.
- Which advisories it fixes.
- The exposure buckets and the import count.
- The changelog flags, if any.
- The exact command you will run.

Wait for a clear yes. A vague reply is not a yes.

## 6. Apply

- Use the narrowest command in the language reference. One package per change.
- Do not run a blanket update, and do not use `latest` or an open range.
- Do not edit the lockfile by hand. Let the tool write it.
- Do not change unrelated dependencies, the runtime version, or tool config in the same change.

## 7. Check the lockfile diff

Read the diff of the lockfile (and the manifest). It must hold:

- The target package at the target version.
- Only the transitive changes that the update requires.
- A matching integrity hash or checksum for each changed package, where the ecosystem records one.

Investigate before you go on if the diff has: other packages at new versions, a changed source, a removed integrity hash, a runtime requirement bump, or a package you do not recognize.

## 8. Lockfile parity

If the project has more than one lockfile or package manager for the same packages (a monorepo with several manifests, two package managers, a vendored copy, a container build that resolves again), check that each one resolves the target package to the same version. If any two disagree, stop and report the mismatch and the likely cause. Do not commit a half-fixed state.

## 9. Verify

In order:

1. Re-run the scanner. The advisories you targeted are gone. No new advisory appeared.
2. Build.
3. Run the tests. Compare with the baseline. A new failure is caused by the update until you prove otherwise.
4. Run the linter and the formatter.
5. If the package has a major or minor bump, run the paths that use it (the import sites you mapped) if tests exist for them. If none exist, tell the user.

If anything fails, revert the manifest and lockfile to the baseline, and report. Do not leave a failed update in the tree.

## 10. Major-upgrade migration report

For a major bump, do not apply the change. Produce this report and wait:

```
## Migration report: <package> <from> to <to>

Why: <advisories fixed, or the reason>.
Smallest patched version in the current major: <version, or "none">.

### Breaking changes
- <verbatim line from the release notes or migration guide, with the link>

### Runtime and peer requirements
- <language version, platform, peer dependency changes>

### Usage in this project
- <count> import sites. Request path: <N>. Internal: <N>. Build and test: <N>.
- Files: <list, grouped by bucket>

### Plan
1. <step, in order, each small and testable>

### Verification
Build, tests, linter, scanner. Paths without tests: <list>.

### Decision needed
- <apply now, schedule, or take a different fix>
```

Find the migration guide in the package's documentation or repository (search for "<package> v<major> migration guide" or "upgrade guide"). Use a codemod if the project provides one. Quote the guide, do not paraphrase it.

## 11. Commit

Commit only if the user asked. One package per commit or pull request. The message states the package, the versions, the advisories, and the bump class. Find the base branch from the repository (do not assume `main`).
