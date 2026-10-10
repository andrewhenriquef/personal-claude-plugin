---
name: run-pipelines
description: Run a project's quality checks locally in Docker, from the manifest in docs/pipelines.md. Default scope is the files changed in the current branch and the staging area against main; each check runs on the matching files only, runs its whole suite when a trigger file (lockfile, tool config) changed, and is skipped when nothing relevant changed. Say "full" to run every check on the whole codebase. If the doc is missing it calls document-pipelines, which calls build-pipelines and scan-pipelines as needed. Runs every check even after a failure, never edits code or config to make a check pass, never triggers remote CI, and reports pass, fail, skipped, and error per check with the skill to use for each failure. Use when the user asks to run the checks, the pipelines, the quality gates, CI locally, or to verify a branch before a PR.
---

# Run Pipelines

Run the project's quality checks the way CI runs them, on a laptop, before the push.

This is the fourth skill of the `continuous-integration` family:

| Skill | Job |
|---|---|
| `scan-pipelines` | Inventory, drift, and gaps. Read-only |
| `build-pipelines` | One compose service per check, with an `x-pipelines` block |
| `document-pipelines` | Writes `docs/pipelines.md`, with the manifest |
| `run-pipelines` | This skill. Runs the checks from the manifest |

## Why this process

1. **Changed files first.** Most runs are "is my branch OK". Running only what the change touches makes that fast enough to do every time.
2. **Triggers keep the fast path honest.** A lockfile or a tool config change can break any file. When one changes, the check runs its whole suite.
3. **Run everything, then report.** Stopping at the first failure hides the next ones and costs another round.
4. **A check result is a fact.** The skill reports it. Changing code or config to turn it green is a different job, for a different skill, after the user decides.

## When to use

- The user asks to run the checks, the pipelines, the quality gates, the linters and tests, or "CI locally".
- The user wants to verify a branch before a commit, a push, or a PR.

## When NOT to use

- The user wants a remote CI run. This skill never triggers remote CI.
- The user wants findings fixed. Run this skill, then use the skill named in the report for each failure.

## Rules that never change

- **Never edit code, tests, tool configs, the compose file, or CI to make a check pass.** No suppression comments, no ignore entries, no skipped tests.
- **Never trigger remote CI.**
- **Never print secret values.** Test whether a variable is set without printing it.
- **Never stop the developer's own containers.** Stop and remove only the services the run started (see Step 6).
- **Run every selected check**, even after one fails, unless the user said "fail fast".
- **Checks with `writes: true` run only when the user says "fix"**, because they edit the working tree.
- **Report what ran.** A skipped check is never reported as passed.
- **Do not commit or push.**

## Process

### Step 0: Find the manifest

1. The doc is `docs/pipelines.md`, or the path the user names.
2. **The doc is missing**, or it has no `pipelines:manifest` markers: tell the user, then **Claude Code:** call `Skill(skill: "document-pipelines")`. **Cursor:** read and follow the `document-pipelines` skill's `SKILL.md` in full. `document-pipelines` calls `build-pipelines` when no services exist, and `build-pipelines` calls `scan-pipelines`. Start again at step 1 when it is done. If the user stops the chain, stop.
3. Parse the YAML between `<!-- pipelines:manifest:start -->` and `<!-- pipelines:manifest:end -->`. If it does not parse, report **Blocked** with the parse error and suggest `document-pipelines`.

### Step 1: Preflight and drift

1. Run `docker version` and `docker compose version`. If Docker is missing or the daemon is down, report **Blocked** with the exact error.
2. Read the services: `docker compose --profile pipelines config --no-interpolate --format json`. `--no-interpolate` keeps secrets out of the output.
3. Compare each manifest entry with the `x-pipelines` block of the service with the same `id`:
   - **Manifest entry with no service:** the service was removed or never built. Skip that check as `error`, and suggest `build-pipelines`.
   - **Service with no manifest entry, or a field differs:** the doc is stale. Tell the user, call `document-pipelines` to refresh it, and use the refreshed manifest. The compose file is what runs, so it wins.

### Step 2: Set the scope

**Mode.**

- **full:** the user said "full", "whole suite", "everything", "completo", "tudo", or similar. Every check runs its `full` command. Skip to Step 3.
- **changed:** everything else. This is the default.
- **fix:** the user said "fix". Same scope as the mode it is combined with. `writes: true` checks also run.

**Changed files** (changed mode). Read [references/selection.md](references/selection.md) first.

```
base=
for b in main master origin/main origin/master; do
  git rev-parse --verify -q "$b" >/dev/null && { base=$b; break; }
done
[ -n "$base" ] || { echo "no base branch found" >&2; exit 1; }
{
  git diff --name-only --diff-filter=d "$base"...HEAD
  git diff --staged --name-only --diff-filter=d
} | sort -u
```

- Branch commits plus the staging area, against `main`, then `master`, `origin/main`, `origin/master`, the first that exists. If none exists, report **Blocked** and ask for the base.
- Deleted files are dropped (`--diff-filter=d`). A deleted file can still be a trigger: check triggers against `git diff --name-only` without the filter.
- Unstaged edits to files in the list are included in the run, because the repo is mounted as it is on disk. Say so in the report.
- Untracked files are not in scope. If the user says "include unstaged" or "include untracked", add `git diff --name-only` and `git ls-files --others --exclude-standard`.
- If the user names files or a directory, use those instead.
- **Empty scope:** say so and stop. Offer "full".

### Step 3: Select the checks

For each manifest entry, decide with the rules in selection.md:

| Situation | Action |
|---|---|
| Mode is full | Run `full` |
| A changed file matches `triggers` | Run `full`. Reason: the trigger file |
| Files match `files`, `changed` is not null | Run `changed` with those files |
| Files match `files`, `changed` is null | Run `full` |
| No file matches | Skip. Reason: no relevant change |
| `writes: true`, and the mode is not fix | Skip. Reason: edits files, say "fix" to run |
| A name in `requires` is not set | Skip. Reason: missing `<VAR>` |
| The user named checks ("only rubocop") | Run only those |

Map changed source files to their tests for `unit-test` and `integration-test` checks, with the rules in selection.md. Report source files with no test found.

Check `requires` without printing values: `[ -n "${VAR+x}" ]` in the shell, or `grep -q '^VAR=' .env` when a `.env` file exists.

### Step 4: Run

1. Order: the category order in selection.md (fast and cheap first: format, lint, secrets, then build and tests). Within a category, `blocking: required` first.
2. Build the command: `docker compose --profile pipelines run --rm -T <id> <command>`, with `{files}` and `{dirs}` replaced as in selection.md. `-T` gives clean, non-interactive output. For `writes: true` checks, prefix it with `env UID="$(id -u)" GID="$(id -g)"`: shells do not export these, and without them Compose runs the check as `1000:1000`.
3. Save each check's full output to a log in a temp directory outside the repo (`mktemp -d`). Record exit code and duration.
4. One check at a time. Checks share test services, and parallel runs fight over them.
5. **fail fast** (only when asked): stop after the first `blocking: required` failure.

### Step 5: Classify each result

| Result | Meaning |
|---|---|
| `pass` | Exit code 0 |
| `fail` | The tool ran and found problems (non-zero exit, tool output shows findings) |
| `error` | The check could not run: image missing, compose error, exit 125, 126, or 127, service dependency unhealthy, network failure. Not a verdict on the code |
| `skipped` | Not run, with the reason from Step 3 |

A `fail` with no findings in the output (crash, out of memory, timeout) is an `error`. Read the log tail before you classify.

### Step 6: Clean up

Stop and remove only the dependency services the run started (for example `db-pipelines`):

```
docker compose --profile pipelines rm -sf <service> [<service> ...]
```

Never run `docker compose down`. It also stops the developer's own app containers.

### Step 7: Report

```
## Pipelines run: <changed | full | fix> on <branch>

Scope: <N files, base main> or <full suite>. Unstaged edits to in-scope files were included.
Blocking checks: PASS | FAIL (<N> failed).

| check | result | mode | files | time | log |
|---|---|---|---|---|---|
| <id> | fail | changed | 4 | 12s | <path> |

### Failures
#### <id> (<category>, blocks merge)
<the key lines from the log: first findings, at most 20 lines>
Next: <skill to use, from selection.md>.

### Errors
- <id>: <what broke>. Fix: <build-pipelines re-run, start Docker, set network, etc.>.

### Skipped
- <id>: <reason>.

### Not covered
- Source files with no test found: <list>.
- Checks that run only in CI: see docs/pipelines.md.
```

Put blocking failures first. If all selected checks pass, say so plainly, and list what was skipped, so "all green" is not read as "everything ran".

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "One rule fails, I will disable it to get green." | Never. Report it. The user decides, then `static-analysis` fixes the code. |
| "Tests are slow, I will skip them in changed mode." | Changed mode selects by files and triggers, not by speed. |
| "The lockfile changed but only one gem, changed mode is enough." | A trigger runs the whole suite. |
| "The image is missing, I will install the tool on the host." | That is a different version from CI. Report `error` and suggest `build-pipelines`. |
| "`docker compose down` is the clean way to stop." | It stops the developer's app too. Remove only what the run started. |
| "It failed, but the failure looks unrelated to the change." | Report it as a failure. Say it may be pre-existing, with evidence (it fails on `main` too) only if you checked. |

## Red flags

- A diff in code, config, compose, or CI after the run (other than `writes: true` checks in fix mode).
- A check reported `pass` with no exit code behind it.
- `skipped` checks missing from the report.
- `docker compose down` in the commands run.
- A secret value in the output or the report.
- A tool installed on the host.
- A `gh workflow run` or any remote CI call.

## Verification

- [ ] The manifest was read from the doc and matches the compose services.
- [ ] Mode and scope are stated, with the base branch.
- [ ] Each check has a result, a mode, and a reason when skipped.
- [ ] Every selected check ran, unless fail fast was asked.
- [ ] `fail` and `error` are separated.
- [ ] Only the services the run started were removed.
- [ ] No file changed, except by `writes: true` checks in fix mode.
- [ ] Each failure names the next skill.
