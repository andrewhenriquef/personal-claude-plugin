# Reading the change

Use in Steps 0 to 3 of `flow-diff`. All commands are read-only.

## Scope

Find the main branch: `main`, else `master`, else `git symbolic-ref refs/remotes/origin/HEAD`.

| The user gives | Head | Base |
|---|---|---|
| Nothing | `HEAD` plus the uncommitted work | merge base of `HEAD` and the main branch |
| A PR number or URL | the PR head (`gh pr view <n> --json headRefName,headRefOid,baseRefName,title,body,files`) | merge base with the PR's `baseRefName` |
| A branch name | that branch | merge base with the main branch |
| A commit range `a..b` | `b` | `a` |
| File paths | as above, filtered to those files | as above |

```sh
base_sha=$(git merge-base origin/main HEAD)   # or the local main branch if there is no remote
git diff --name-status -M "$base_sha"...HEAD  # committed changes, with renames
git diff --name-status -M                     # unstaged
git diff --name-status -M --staged            # staged
git ls-files --others --exclude-standard      # new, untracked
```

For a PR that is not checked out, read its diff with `gh pr diff <n>` and its files at the head with `git show <headRefOid>:<path>` after `git fetch origin <headRefName>`. A fetch is read-only on the working tree. If the head commit is not available locally and a fetch is not possible, explain from `gh pr diff` and write that limit under "Not verified".

Read a file on the base with `git show "$base_sha":<path>`. For a renamed file, use the old path on the base. Get line numbers with `git show "$base_sha":<path> | nl -ba | sed -n '<from>,<to>p'`.

If `main` moved past the merge base in a changed file (`git diff --name-only "$base_sha" origin/main -- <files>`), the AS IS is the code the branch started from, not the current `main`. Say so in the header.

## Files to set aside

Set aside, and list in the header: vendored code (`vendor/`, `node_modules/`), generated code (`*.pb.go`, `*_gen.go`, `db/schema.rb` and `structure.sql` when a migration explains them, compiled assets), and snapshots. A lockfile change is a dependency change: put it in the "Other changes" table with the packages and versions that changed, not the raw lines.

## Group into flows

- Start from the files with the most logic changes. Each one usually anchors a unit.
- Pull in what serves the same behavior: its migration, its model or struct changes, the contract (route, schema, interface, proto), the callers that changed for it, and its tests.
- A file that serves two units goes in the unit where its main change belongs; mention it in the other.
- Folders are evidence, not rules.
- Aim for 1 to 6 units. More than 6 means a large change: keep the units, and say in the general context that the branch mixes several changes.

## Classify

| Class | Signal | Diagrams |
|---|---|---|
| Changed flow | An existing entry point now behaves differently: new or removed hop, changed decision, changed side effect, changed error | AS IS and TO BE |
| New flow | A new entry point: route, job, consumer, command, event | TO BE only |
| Removed flow | An entry point is deleted or no longer reached | AS IS only |
| No flow change | Same behavior: rename, extract method, formatting, config with no behavior effect, docs, tests only, dependency bump | None; one row in "Other changes" |

A refactor is "no flow change" only if the trace shows the same hops and the same results. If you are not sure, trace it and say what you found.

## Order

Order the units for a reader: data and contracts, then the core logic, then the entry points, callers, and UI. Within a unit, the reading order is: the test that shows the intent, the main logic file, then the rest.
