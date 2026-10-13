---
name: github-pipelines
description: Add the checks that the project runs locally but GitHub CI does not run yet to a new GitHub Actions workflow, reproducing the local setup with native actions. Reads the manifest in docs/pipelines.md, the `x-pipelines` blocks of the compose file, and the scan-pipelines inventory of existing CI; sets up only the missing checks and never edits existing workflows. Each job uses the same runtime, tool versions, services, env names, and full command as the local check, with actions pinned to commit SHAs of their latest stable release, read-only permissions, and secrets by name. Validates the workflow with actionlint and zizmor, then, with approval, pushes a branch and opens a draft PR: done only when every new job returns the same verdict on GitHub as locally (pass or findings, never broken). Use when the user asks to set up GitHub Actions for the checks, reproduce the local pipelines in CI, add the missing checks to CI, or create the .github workflows.
---

# GitHub Pipelines

Put the checks that run on a laptop but not in CI into GitHub Actions, so the pull request gate matches the local one.

This is the fifth skill of the `continuous-integration` family:

| Skill | Job |
|---|---|
| `scan-pipelines` | Inventory, drift, and gaps. Read-only |
| `build-pipelines` | One compose service per check, with an `x-pipelines` block |
| `document-pipelines` | Writes `docs/pipelines.md`, with the manifest |
| `run-pipelines` | Runs the checks locally, on changed files by default |
| `github-pipelines` | This skill. Adds the missing checks to GitHub Actions |

## Why this process

1. **Only the missing checks.** The existing workflows are the team's. They stay as they are. This skill fills the gap between what runs locally and what runs in CI.
2. **Same check, two runners.** Native actions are fast and cache well. The price is a second definition of each check, so every job copies the local runtime version, tool version, services, env names, and full command. A version or flag that differs is drift on day one.
3. **CI is the contract.** Pull requests run the full command of every check. A changed-files gate lets old violations in touched files pass.
4. **A workflow that never ran is not done.** YAML that parses can still fail on the runner. The job must run on GitHub and return the same verdict as the local run.
5. **CI is an attack surface.** Unpinned actions, write permissions, and untrusted input in `run:` lines are how CI gets compromised. Every generated workflow starts hardened.

## When to use

- The user asks to set up GitHub Actions for the checks, or to create the `.github` workflows.
- The user wants the local pipelines reproduced in CI, or the missing checks added to CI.
- The `build-pipelines` report lists checks under "CI suggestions" and the user wants them applied.

## When NOT to use

- The project is not on GitHub. This skill writes GitHub Actions only.
- The user wants an existing workflow changed or fixed. This skill never edits existing workflows.
- The user wants the checks run now. Use `run-pipelines`.
- No local pipelines exist yet. Step 0 calls the earlier skills first.

## Rules that never change

- **Never edit an existing workflow, action, or CI file.** Write only `.github/workflows/pipelines.yml` (and update it when it carries the managed header). The only other edits are the `x-pipelines` updates and the doc refresh in Step 8. A check that existing CI already runs is out of scope, even when the local command differs. Report the difference instead.
- **Same as local.** Runtime version, tool version, services and their image tags, env names, and the full command come from the compose file and the manifest. Never a newer version, never a different flag.
- **Full suite on pull requests and on pushes to the default branch.** Never the `changed` command in CI.
- **Pin every action to a full commit SHA** of its latest stable release, looked up in this run, with the version as a comment. Never a tag or a branch.
- **Least privilege.** Top-level `permissions: contents: read`. A job gets more only when its tool needs it, with the reason in a comment. `actions/checkout` with `persist-credentials: false`. Never `pull_request_target`.
- **Never put `${{ ... }}` expressions from event data inside `run:`.** Pass values through `env:`.
- **Secrets by name only.** `${{ secrets.NAME }}` for every name in `requires`. Never a value, never a secret in a `run:` line.
- **Never weaken a check** to get green: no `continue-on-error`, no ignore entries, no lower thresholds.
- **Ask before you write, and again before anything leaves the machine.** Show the plan in Step 4. Commit, push, and opening a PR need the user's approval: one approval in Step 7 that lists every action, in order.
- **Keep the run state on disk.** The ledger lives in the run directory (Step 0.6). Read it, not the conversation, to see where the run is.
- **Never change repository settings** (branch protection, required checks, secrets). Report what the user should set.

## Process

### Step 0: Inputs

1. **Manifest.** Read `docs/pipelines.md`, between `<!-- pipelines:manifest:start -->` and `<!-- pipelines:manifest:end -->`. If the doc or the markers are missing, tell the user, then **Claude Code:** call `Skill(skill: "document-pipelines")`. **Cursor:** read and follow the `document-pipelines` skill's `SKILL.md` in full. It calls `build-pipelines` and `scan-pipelines` when needed. Start again when it is done.
2. **Compose.** `docker compose --profile pipelines config --no-interpolate --format json`. For each check, take the image or build, the services it depends on (with their image tags and healthchecks), the environment names, and the `x-pipelines` block. If the manifest and the compose file differ, the compose file wins: call `document-pipelines` to refresh the doc, as `run-pipelines` does.
3. **Existing CI.** Reuse the `scan-pipelines` report from this session if nothing changed since, or the newest `$(git rev-parse --absolute-git-dir)/pipelines/build-*/scan.md` when its `Commit:` line is the current `HEAD`. Otherwise **Claude Code:** call `Skill(skill: "scan-pipelines")`. **Cursor:** read and follow the `scan-pipelines` skill's `SKILL.md` in full. You need its inventory of checks that CI runs, and the branch protection result.
4. **Remote.** `git remote get-url origin` must point to GitHub. If not, stop and report **Blocked**. Find the default branch: `git symbolic-ref refs/remotes/origin/HEAD`, or `gh repo view --json defaultBranchRef`.
5. **Files the jobs need.** The jobs run on what is committed, not on the working tree. List the files the added checks use besides the app code: `docker/pipelines/coverage-gate.sh`, `docker/pipelines/Dockerfile.*`, new tool configs, and the baseline app changes (`Gemfile`, lockfile, `spec_helper.rb`). For each, check it is committed (`git status --porcelain -- <path>` is empty) and on the base branch (`git cat-file -e origin/<default>:<path>`). A file that is uncommitted or missing from the base branch goes into the Step 7 commit, with the user's approval. Say which in the plan.
6. **Run directory.** Create it in the git directory, outside the working tree. Each shell command starts a new shell, so start every later command that uses it with `run=<the printed path>`:
   ```
   run="$(git rev-parse --absolute-git-dir)/pipelines/github-$(date -u +%Y%m%dT%H%M%SZ)"; mkdir -p "$run" && echo "$run"
   ```
   Keep `$run/ledger.md` current after every step and every CI round:
   ```
   # github-pipelines run
   Run dir: <path>. Step: <N>.
   Needs from you: <the open question, or "nothing">
   Plan (approved <date>): <job: version, command>
   Approved actions (Step 7): <list, or "not asked yet">
   Branch: ci/pipelines. PR: <url>. Runs: <ids>
   | job | round | GitHub verdict | local verdict | log lines |
   ```

### Step 1: Select the missing checks

For each manifest check, decide:

| Situation | Action |
|---|---|
| An existing workflow job runs the same tool on the same scope (scan inventory, trigger `pull_request` or `push`) | Skip. Reason: already in CI at `<file:line>` |
| CI runs it only on a schedule, or only on `main` | Skip, and report it as partial: "runs in CI only on <trigger>" |
| `source` is `suggested`, a hook, a Makefile, or a script, and no workflow runs it | **Add** |
| `requires` a secret that only a paid service provides | Add, and list the secret name for the user |
| `writes: true` | Skip. It is the fix twin of a check service (pattern 5 of compose-patterns.md), and CI runs the check form. No twin: skip, and report that the check form needs a service first (`build-pipelines`) |
| The check cannot run on a GitHub-hosted runner (needs local hardware, a private network) | Skip, and say why |

If nothing is missing, say so, show the table of checks and where CI runs each, and stop.

### Step 2: Map each check to native actions

Read [references/workflow-patterns.md](references/workflow-patterns.md) before this step.

For each check to add, plan one job. Its id is the check id, so the status check name is stable for branch protection.

1. **Runtime.** The check runs in the app image locally: use the setup action for the language, with the version read from the same file the app image uses (`.ruby-version`, `.nvmrc`, `go.mod`, `.python-version`, `.tool-versions`). If the Dockerfile pins a version that no file states, use that version, written in the workflow with a comment pointing to the Dockerfile line.
2. **Dependencies.** Install them as the app image does (`bundle install` with the lockfile, `npm ci`, `go mod download`), through the setup action's cache.
3. **Standalone tool images** (Gitleaks, Trivy, Hadolint, golangci-lint): run the same image and tag as the compose service with `docker run`, or the tool's official action **only if** it takes the exact tool version as an input. A version the action picks for you is drift.
4. **Checks built from `docker/pipelines/Dockerfile.<id>`** (govulncheck, lizard, zizmor, Squawk): install the tool natively with the same install line and version as the Dockerfile, after the setup action for the Dockerfile's base runtime (`go install ...@v<x>`, `pip install <tool>==<x>`, `npm install -g <tool>@<x>`). Or build and run the same Dockerfile (`docker build -f docker/pipelines/Dockerfile.<id> -t <id> .` then `docker run`), when the install has more than one step.
5. **Services.** Each compose dependency service (for example `db-pipelines`) becomes a job `services:` entry with the same image and tag, the same test-only env values, a healthcheck in `options`, and a mapped port. Rewrite host names in the env from the compose service name to `localhost`.
6. **Env.** Copy the variable names and test-only values from the compose service. Each `requires` name becomes `${{ secrets.NAME }}` at job level.
7. **Command.** The manifest `full` command, unchanged. Use the same coverage gate (`docker/pipelines/coverage-gate.sh`) and the same minimum. A command that starts with `sh -c '...'` becomes the multi-line `run:` body.
8. **Report readers** (`reads: <id>`, the coverage check). The suite runs once in CI too:
   - **`<id>` is added by this workflow:** its job uploads the report as an artifact after the tests, even when they fail (`if: ${{ !cancelled() }}`). The reader's job has `needs: <id>` and `if: ${{ !cancelled() }}`, downloads the artifact to the same path, sets up only the runtime the gate needs (no dependency install, no services), and runs the manifest `full` command: the gate. Pattern D in workflow-patterns.md.
   - **`<id>` already runs in existing CI:** that job cannot be edited, so its report is not shared. The reader's job runs the `<id>` full command, then the gate, in one job. Report the double run, and suggest (not applied) an upload step in the existing job.
9. **Version check.** Compare each job's runtime and tool version with the local service (image tag, lockfile, Dockerfile). Any difference must be fixed in the plan, not reported.
10. **Pins.** Look up the latest stable release and its commit SHA for every action you use (see workflow-patterns.md). If the lookup fails, say so in the plan, and ask for the SHA in the Step 4 approval. Never write a SHA from memory.

### Step 3: Check the plan for conflicts

- The workflow file `.github/workflows/pipelines.yml` exists and has no managed header: it is the team's. Ask for another name (`pipelines-local.yml`).
- A job id equals a job id in another workflow: status check names collide. Prefix with `local-`, and say so.
- A check needs a secret that the repository may not have: list it under "Secrets to add".
- Pull requests from forks get no secrets. A job with `requires` skips its command when the secret is empty, and prints why. It never passes silently: the skip step writes a warning annotation.

### Step 4: Show the plan and wait

```
| job (check) | category | runtime / image | version (local = CI) | services | command | secrets |
|---|---|---|---|---|---|---|

Skipped (already in CI or not runnable):
- <id>: <reason, file:line>.

Actions (pinned):
- actions/checkout@<sha> # v<x.y.z>

Files:
- create .github/workflows/pipelines.yml
```

Wait for the user to approve. Apply only what they approve.

### Step 5: Write

1. Write `.github/workflows/pipelines.yml` from the patterns, starting with the managed header comment.
2. One job per check, in the category order of `run-pipelines` (lint and security first, tests last). `timeout-minutes` on every job: twice the local full-run time, at least 10. Read the time from the newest `build-pipelines` ledger or `run-pipelines` `results.md` in `$(git rev-parse --absolute-git-dir)/pipelines/`. With no recorded time, use 30 and say so in the plan.
3. Do not touch any other file. The x-pipelines updates wait for Step 8.

### Step 6: Validate locally

Run both on the new file only, with the pinned images from `build-pipelines`' tool-images.md (latest stable when the project has no service for them):

1. `docker run --rm -v "$PWD:/repo" -w /repo rhysd/actionlint:<v> .github/workflows/pipelines.yml`. Must pass.
2. `docker run --rm -v "$PWD:/repo" -w /repo python:<v>-slim sh -c 'pip install -q zizmor==<v> && zizmor --offline --min-severity medium .github/workflows/pipelines.yml'`. No findings at medium or higher.
3. Fix every finding in your file and run both again. Never silence a rule.
4. Check for drift: every job's versions and command equal the local service's (Step 2.9).

### Step 7: Run it on GitHub (needs approval)

Ask once, before the first action that leaves the machine. Show the whole sequence, with the exact branch, files, and commands, and ask for one approval that covers all of it:

1. Create a branch `ci/pipelines` from the default branch (`origin/<default>`), so the PR shows only this change. Commit `.github/workflows/pipelines.yml` and the files Step 0.5 found missing from the base. If those files live on an unmerged branch instead, add that choice to the same question: base `ci/pipelines` on that branch, or wait until it is merged.
2. Push the branch.
3. Open a draft pull request against the default branch (`gh pr create --draft`), so the `pull_request` trigger runs.
4. Fix-up commits and pushes to this branch only, for broken jobs (at most three rounds per job).
5. The Step 8 commit: the `x-pipelines` updates of the added checks and the refreshed doc, on this branch.

If the user approves only part of the sequence, do only that part, and stop where the approval ends. Record the approved actions in the ledger.

Then wait for the run: `gh run list --branch ci/pipelines --workflow pipelines.yml`, then `gh run watch <id> --exit-status`. Read each job's conclusion and log: `gh run view <id> --log` (`--log-failed` for the failed ones).

If `gh` is missing or not authenticated: push only with approval, give the user the branch and the compare URL to open the PR, and ask them to paste the run result. Do not mark the work done without it.

Classify each job with "Reading a result" in `build-pipelines`' [tool-images.md](../build-pipelines/references/tool-images.md):

| Verdict | Meaning |
|---|---|
| `pass` | Job succeeded, and the log shows the tool checked something |
| `findings` | Job failed on the tool's findings exit code, with findings in the log |
| `broken` | Setup failed, service did not start, tool not found, wrong version, timeout, config error, or a pass with nothing checked |

**Parity.** Compare each job with the local verdict for the same commit (run the check locally with `run-pipelines` in full mode if there is no fresh result). The verdict and the finding count must match. A mismatch is `broken`: the job is not the same check.

Checks that read an online database (dependency audit, Trivy, OSV-Scanner, Semgrep registry rules) can differ when the database changed between the two runs. Run the local check again right after the GitHub run. If the counts then match, it is parity. If the difference is a new advisory, name it.

Fix a `broken` job in the workflow file, commit, push (the approval covers fix-up pushes to this branch only), and wait again. Record each round in the ledger. At most three rounds per job. Then report it as **Not done** with the log lines.

### Step 8: Record and document

When every new job has a verdict that matches local:

1. Update **only** the `x-pipelines` block of each added check in the compose file: `source` becomes `.github/workflows/pipelines.yml:<line of the job>`, `ci_version` becomes the CI version (equal to local), `blocking` becomes `fails-job`. Change nothing else in the compose file.
2. Refresh the doc: **Claude Code:** call `Skill(skill: "document-pipelines")`. **Cursor:** read and follow its `SKILL.md`.
3. Commit these two files on the same branch, if the Step 7 approval covered it (action 5). Otherwise show the diff and ask.

### Step 9: Report

```
## GitHub pipelines: <repo>

Status: **Done** (every new job matches local) | **Not done** (<N> broken).
PR: <url> (draft). Run: <url>. Run directory: <path>.

### Needs from you
- Secrets to add (repository settings): <NAME>, used by <job>.
- Required checks to set (Settings → Branches): <job ids of blocking checks>. Ask me to show the `gh api` call.
- Broken jobs that need you: <job>: <what to do>.
Write "Nothing" when there is nothing.

### Added (<N>)
| job | category | version (local = CI) | GitHub verdict | local verdict | time |
|---|---|---|---|---|---|

### Skipped
- <id>: <already in CI at file:line | runs only on schedule/main | not runnable on GitHub, reason>.

### Broken (not done)
- <job>: <log lines>. Tried: <fixes>. Needs: <what the user must do>.

### Differences found in existing CI (not changed)
- <id>: CI at <file:line> runs <command/version>, local runs <command/version>.

### Suggestions (not applied)
- Keep the action pins current: add the `github-actions` ecosystem to `.github/dependabot.yml` (or Renovate), if it is not there.

### Next step
Mark the PR ready for review when the findings are fixed, or merge it to start gating with the findings visible.
```

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The existing job is outdated, I will fix it while I am here." | Never edit existing workflows. Report the difference. |
| "`actions/checkout@v5` is fine." | Tags move. Pin the commit SHA with the version as a comment. |
| "The action picks a sensible tool version." | That is a version you did not choose. Pass the exact version, or run the image. |
| "The setup action has a newer Ruby, close enough." | Same runtime as local, read from the same file. |
| "PRs are faster with the changed-files command." | CI runs the full suite. |
| "actionlint passed, so the workflow works." | It proves the YAML is valid. Only a run on GitHub with the local verdict proves the job. |
| "The job failed with findings, I will add `continue-on-error`." | Findings are the check working. Never weaken it. |
| "I will push the fix directly, it is the same branch." | Only fix-up pushes to the approved branch are covered. Anything else needs approval. |
| "I will mark the checks as required for the user." | Never change repository settings. Report the list. |

## Red flags

- A diff in any workflow file other than `.github/workflows/pipelines.yml`.
- An action reference that is not a 40-character SHA.
- `permissions: write-all`, a missing top-level `permissions`, or `pull_request_target`.
- `${{ github.event.` inside a `run:` line.
- A secret value or a `${{ secrets.X }}` inside a `run:` line.
- A job whose runtime, tool version, or command differs from the local service.
- `continue-on-error: true` on a check job.
- A coverage job that runs the test suite while the test job is in the same workflow. It must download the report.
- A job for a check that existing CI already runs.
- Status **Done** without a GitHub run, or with a GitHub verdict that differs from local.
- A push, PR, or commit made without the user's approval.

## Verification

- [ ] Manifest, compose config, and scan inventory were read, and they agree.
- [ ] Only checks missing from existing CI were added. Skips are listed with their reason.
- [ ] Every job matches the local check: runtime, tool version, services and tags, env names, full command.
- [ ] Every action is pinned to a commit SHA of its latest stable release, looked up in this run.
- [ ] Top-level `permissions: contents: read`, `persist-credentials: false`, no `pull_request_target`, no event data in `run:`.
- [ ] actionlint passes, and zizmor has no medium or higher findings.
- [ ] The user approved the plan in Step 4, and the Step 7 sequence in one approval. Nothing outside the approved actions was done.
- [ ] Every new job ran on GitHub, and its verdict and finding count match local.
- [ ] Only the `x-pipelines` blocks of added checks changed in the compose file, and the doc was refreshed.
- [ ] The report starts with "Needs from you" (secrets to add, required checks to set, broken jobs), and no repository setting was changed.
- [ ] The ledger records the plan, the approved actions, and every CI round.
