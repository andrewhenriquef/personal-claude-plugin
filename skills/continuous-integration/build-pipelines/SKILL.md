---
name: build-pipelines
description: Set up every quality check of a project to run locally in Docker, one service per check in the existing compose file under the `pipelines` profile, each with an `x-pipelines` block (category, full and changed-files commands). Runs scan-pipelines first, always sets up the minimum baseline (lint, complexity, SAST, secrets, dependency audit, unit and integration tests, parallel tests when needed, coverage with a minimum equal to current coverage), and asks which tool to use for each new check from a status table with one recommended. Existing checks keep the CI version; new ones use the latest stable release. Done only when every check runs and returns the tool's verdict (pass or findings), never an infrastructure error. Reports outdated tools. Never edits CI or existing services, never weakens a tool config. Use when the user asks to set up, build, dockerize, or containerize the project's checks or pipelines, or to make CI checks runnable locally.
---

# Build Pipelines

Make every quality check of the project runnable on a laptop with one command per check, the same way CI runs it.

```
docker compose --profile pipelines run --rm <check-id>
```

This is the second skill of the `continuous-integration` family:

| Skill | Job |
|---|---|
| `scan-pipelines` | Inventory, drift, and gaps. Read-only |
| `build-pipelines` | This skill. One compose service per check |
| `document-pipelines` | Writes the checks, setup, and run commands to `docs/pipelines.md` |
| `run-pipelines` | Runs the checks, on changed files by default |
| `github-pipelines` | Adds the checks missing from GitHub Actions to a new workflow |

## Why this process

1. **Local must equal CI.** A check that passes locally and fails in CI wastes a round trip. Same tool, same version, same flags, same config. That is why a check CI already runs keeps the CI version.
2. **New checks start current.** A check CI does not run has no version to match. Starting it on an old release only adds an upgrade later. Use the latest stable release.
3. **Docker removes "works on my machine".** Nobody needs the tools installed. The pinned image is the install.
4. **The app's compose file is the natural home.** Developers already run it. The `pipelines` profile keeps the new services out of `docker compose up`.
5. **The next skills read the compose file, not your memory.** The `x-pipelines` block on each service is the contract that `document-pipelines` and `run-pipelines` use.
6. **The baseline is the floor.** Every project gets static analysis (lint, complexity, SAST, secrets, dependency audit) and tests (unit, integration, parallel when needed, coverage). The coverage minimum is today's coverage, so it can only go up from here.
7. **A check that cannot run is not set up.** A version command proves the tool starts. Only a real run proves the image, mounts, config, services, and command fit together. A check is done when it returns the tool's verdict on the code: pass, or findings. Findings are fine. A broken check is not.

## When to use

- The user asks to set up, build, dockerize, or containerize the project's checks or pipelines.
- The user wants CI checks to run locally.
- `run-pipelines` finds no `pipelines` services and calls this skill.

## When NOT to use

- The user only wants to know what checks exist. Use `scan-pipelines`.
- The user wants to run the checks. Use `run-pipelines`.
- The user wants CI config changed. This skill never edits CI. Report the CI change as a suggestion. `github-pipelines` adds the missing checks to GitHub Actions.

## Rules that never change

- **Never edit CI config.** `.github/workflows/`, `.gitlab-ci.yml`, and the other CI files stay as they are.
- **Never change an existing service.** Add new services only. Reuse existing ones through `extends` or the same `build`/`image`.
- **Every new service has `profiles: [pipelines]`.** `docker compose up` must start exactly the same services as before.
- **Pin every image and tool to an exact version.** Never `latest`, `edge`, `nightly`, a branch name, or a pre-release (`-rc`, `-beta`, `-alpha`, `.pre`, `-dev`). No tag, no service.
- **Existing check: CI version.** A check CI already runs uses the version CI uses, even when a newer one exists. Report the newer one in Step 8.
- **New check: latest stable.** A check CI does not run (a chosen suggestion, or a check from a hook or script only) uses the latest stable release, looked up in this run (see tool-images.md). Never from memory.
- **Never bump the app's dependencies.** Tools that come from the lockfile (`Gemfile.lock`, `package-lock.json`, `go.sum`) keep the lockfile version. Report newer stable versions only.
- **Done means every check runs.** Each service returns the tool's verdict in Step 6. A check that errors is not done.
- **The baseline is always set up.** Every applicable item of `scan-pipelines`' [baseline.md](../scan-pipelines/references/baseline.md) gets a service. The user can decline one only in Step 4, and the report then says **Baseline not met**.
- **Coverage minimum = current coverage.** Measured in Step 6, rounded down to one decimal. Never lower a minimum the project already has.
- **The user picks every new tool.** A check or library the project does not have yet gets a status table (stars, last commit, latest release, status) and a question, with one recommended option. This includes libraries a baseline item needs (coverage, parallel runner) and ones found later, in Step 6. Never pick a new tool silently.
- **App changes only for the baseline, only with approval.** A baseline item may need a test-only dependency (`simplecov`, `parallel_tests`, `pytest-cov`, `pytest-xdist`) or a test setup line (`SimpleCov.start`, `TEST_ENV_NUMBER` in `config/database.yml`). List each one in Step 4 as its own line. Add it only on approval, and no other locked version may change.
- **Never weaken a tool config.** Do not disable a rule, add an ignore entry, or lower a threshold to make a check pass.
- **Secrets by reference only.** Write `${VAR}` and let the developer's environment or `.env` supply it. Never write a secret value. Test-only values for services that this file starts (for example the local test database URL) are allowed.
- **Ask before you write.** Show the plan in Step 4 and wait for approval.
- **Do not commit** unless the user asks.

## Process

### Step 0: Preflight

1. Run `docker version` and `docker compose version`. Compose v2.24.4 or later is required (`profiles`, `extends`, `x-` fields, and the `!reset` and `!override` tags; `!override` arrived in v2.24.4). If the version is older, avoid the tags and write the services out in full.
2. If Docker is missing or the daemon is not running, stop. Report **Blocked** with the exact error.
3. Find the compose file: `compose.yaml`, `compose.yml`, `docker-compose.yaml`, `docker-compose.yml`, in that order (the Compose default). If none exists, the plan creates `docker-compose.yml` with only the `pipelines` services. Say so in the plan.
4. Record the services that start today with no profile: `docker compose config --services`. Step 7 compares against this list.

### Step 1: Scan

1. **Claude Code:** call `Skill(skill: "scan-pipelines")`. **Cursor:** read and follow the `scan-pipelines` skill's `SKILL.md` in full.
2. If the user already ran it in this session and nothing changed since, reuse that report.
3. If the compose file already has `pipelines` services, list them. A service with an `x-pipelines` block is owned by this skill and can be updated. Leave every other service alone.

### Step 2: Choose suggested checks

1. **Baseline suggestions are not optional.** Take every `missing` or `partial` baseline item from the scan's Baseline table. They go into the plan without a question.
2. Ask the user once about the other suggestions, in one multi-select question, must first. Show the category, the recommended tool, and the effort for each.
3. **Choose the tool for each new check.** For every check going into the plan with no tool in the project (baseline items included), show the scan's status table from its Tool options section, then ask which tool to use, as in "Asking the user" of `scan-pipelines`' [tool-research.md](../scan-pipelines/references/tool-research.md). The recommended tool is always the first option. If the scan has no table for a check, or it is from an earlier session, research it now with the same file.
4. Existing checks are always set up. Do not ask about them.

### Step 3: Plan each check

Read [references/compose-patterns.md](references/compose-patterns.md) and [references/tool-images.md](references/tool-images.md) before this step.

For each check (existing and chosen), pick the image in this order:

1. **App image.** The check needs the app runtime and its dependencies (tests, RuboCop, ESLint, Brakeman, `bundler-audit`, `go vet`). Reuse the app service through `extends`, or reuse its `build` with the `test` or `ci` target when the Dockerfile has one.
2. **Official tool image.** The check is a standalone tool (Gitleaks, Trivy, Hadolint, ShellCheck, golangci-lint). Use the image from tool-images.md, pinned to the version chosen below.
3. **New Dockerfile.** No image fits. Write `docker/pipelines/Dockerfile.<check-id>`, based on the CI runtime image (or the project runtime version when CI has none), and install the tool at the version chosen below.

Pick the version for each check, with the lookups in tool-images.md ("Versions"):

| Check | Version to pin | Also record |
|---|---|---|
| CI already runs it | The CI version | Latest stable, for the Outdated report |
| New (suggestion, or hook/script only) | Latest stable release, looked up now | Nothing. It is current |
| Tool from the app lockfile | The lockfile version | Latest stable, for the Outdated report |
| Base image of a new Dockerfile | The project runtime version (`go.mod`, `.ruby-version`, `.nvmrc`, CI runtime) | Latest stable patch of that runtime, for the Outdated report |

If CI does not pin the tool (no version input, `latest`, unpinned install), the check is existing but has no CI version. Use the latest stable and record the CI side as "unpinned" in the report.

If the latest stable is a new major version and the check needs a config (golangci-lint v1 to v2, ESLint flat config), write the config for that major. Never reuse a config written for an older major.

If the lookup fails (no network, rate limit), say so in the plan and ask the user for the version. Never guess a version.

Check that each image exists before you plan it:

- Local: `docker image inspect <image:tag>`.
- Registry: `docker manifest inspect <image:tag>`.
- If neither finds it, the tag is wrong or private. Use option 3 for that check, and say why.

For each check also plan:

- **Services.** Integration tests need the database or cache. Reuse the existing service when it is safe for tests, or add a `<name>-pipelines` service with the same image as CI `services:`, on `tmpfs`, with a healthcheck. Use `depends_on` with `condition: service_healthy`.
- **Env.** Copy the variable names from CI. Fill test-only values that point at services in this file. Use `${VAR}` for every secret.
- **Mounts and caches.** Mount the repo at the same path for every check: the app service's own mount path and working directory when it has one (`/app` only when it has none). A different path hides the dependencies the app image installed under its working directory (`node_modules`, `vendor/bundle`). Named volumes only for caches a tool fills at run time (`pipelines-gomod`, `pipelines-trivy-cache`). Never mount a volume over dependencies the image installs (`/usr/local/bundle`, `node_modules`): it keeps the old versions after a rebuild.
- **User.** Checks that write files (formatters, autocorrect) run as `${UID:-1000}:${GID:-1000}` so the files belong to the developer. Shells do not export `UID` or `GID`, so the caller passes them (see pattern 5).
- **Commands.** The full-suite command is the CI command. The changed-files command takes `{files}` (or `{dirs}` for tools that work on directories or packages, like Go), keeps the same flags, and filters by the check's file pattern. If the tool cannot take files (whole-module scanners like `govulncheck`, `bundler-audit`), set `changed: null`. `run-pipelines` then runs the full command only when a relevant file changed (for example a lockfile).
- **New tool config.** Only for chosen suggestions that need one. Start from the tool's recommended preset. Never copy a config from another project.
- **Baseline items.** Read [baseline.md](../scan-pipelines/references/baseline.md), and use the patterns for them in compose-patterns.md:
  - **Complexity** (pattern 7): if the linter config already enables the rules, the lint check covers it. Otherwise add a `complexity` service that turns the rules on from the command line, or runs lizard. Never edit the linter config.
  - **Coverage** (pattern 8): the suite runs once. The test check writes the coverage report in its full run, and a `coverage` service with `reads: <test check id>` only runs the gate on that report. Pick a report directory that `.gitignore` already ignores. Add report flags to the test command only when it does not write the report already, and list them as a difference from CI. The minimum is a placeholder until Step 6 measures it. Say so in the plan.
  - **Parallel tests** (pattern 9): set it up now when the scan says `needed`. When the scan says "decided by build-pipelines", plan the serial suite, and decide in Step 6 from the measured time.
  - **Integration tests:** test services with the same engine and major version as CI (pattern 4).
  - **No tests in the repo:** do not add an empty test service. Report **Baseline not met: no tests**.
- **Not local-runnable.** A check that needs a cloud credential or a paid SaaS token gets a service that reads the secret through `${VAR}` and a `requires` entry in `x-pipelines`. If the check cannot run outside CI at all (for example CodeQL default setup), do not add a service. List it in the report.

### Step 4: Show the plan and wait

Show one table and the list of files to create or edit:

```
| check-id | category | baseline | image (source) | version (rule) | services | changed-files | new config |
|---|---|---|---|---|---|---|---|

version (rule): `1.66.1 (CI)`, `2.5.0 (latest stable)`, or `7.1.0 (lockfile)`.

Files:
- edit  docker-compose.yml   (+N services, +M volumes)
- create docker/pipelines/Dockerfile.<id>
- create <tool config>
- app change (baseline, needs your OK): add `simplecov` to the test group; `SimpleCov.start` in spec/spec_helper.rb
```

The `baseline` column names the baseline items the check meets (`1, 2`), or `—`.

Wait for the user to approve. Apply only what they approve.

### Step 5: Write

1. Add the services, volumes, and `x-pipelines` blocks to the compose file, using the patterns in compose-patterns.md. Keep the existing YAML style (indentation, quotes, key order). Add new services after the existing ones under a `# --- pipelines (managed by build-pipelines) ---` comment.
2. Write the Dockerfiles and tool configs.
3. If the project has `.dockerignore`, check it does not exclude files a check needs (for example `.git` for Gitleaks). If it does, mount the repo instead of copying it. Do not edit `.dockerignore`.

### Step 6: Build and run every check

The work is done only when every new service passes this step. Run in this order. When a step breaks, fix your own file and run again. Never fix by weakening a check.

1. `docker compose config --quiet`. The file must be valid.
2. `docker compose --profile pipelines pull --ignore-buildable <new services>`. Name the services, so the developer's own service images are not pulled to newer tags.
3. `docker compose --profile pipelines build <new services that build>`.
4. **Version.** For each new service, run the tool's version command from tool-images.md. It must print the version planned in Step 3. A different version is a bug in your file (wrong tag, wrong install line, app image not rebuilt).
5. **Full run.** For each new service with `writes: false`, one at a time (`writes: true` services follow step 9): `docker compose --profile pipelines run --rm -T <id> <full>`. A service with `reads: <id>` runs right after that check's full run, with `PIPELINES_SINCE` set to the time that run started, minus 5 seconds: `env PIPELINES_SINCE=<epoch> docker compose ...`. Save the output to a log in a temp directory outside the repo (`mktemp -d`). Record the exit code. Use a long timeout for test suites. Never shorten the command to make it faster.
6. **Changed-files run.** For each `writes: false` service with `changed` not null, pick one tracked file that matches `files` (`git ls-files | grep -E '<files>' | head -1`), put it in `{files}` (or its directory in `{dirs}`), and run `changed` the same way. If no tracked file matches, say so and skip this run.
7. **Classify** each run with "Reading a result" in tool-images.md:

| Verdict | Meaning | Done? |
|---|---|---|
| `pass` | Exit 0, and the output shows the tool checked something (files inspected, examples run, a summary line) | Yes |
| `findings` | The tool ran and reported problems in the code in its own format (offenses with `file:line`, failing examples, vulnerabilities), with the exit code the tool documents for findings | Yes. Findings are the check working. Record the count. Do not fix them |
| `broken` | Anything else: exit 125, 126, or 127, the tool's own error exit code, config or load errors, a missing dependency, a service that does not connect, a crash, a timeout, exit 0 with nothing checked ("0 files", "No examples found") | No |

8. **Fix every `broken` check** and run steps 1 to 7 again for it. The cause is almost always your file: image, mount path, working directory, env, service, command, or new config. At most three attempts per check. If it is still broken, or the cause is outside your files (the app does not boot on `main` either, a secret is missing, the project's own config is invalid), stop that check, and report it as **Not done** with the error lines from the log.
9. **Checks with `writes: true`** edit the working tree, so never run them in steps 5 and 6. A `writes: true` service is the fix twin of a check service (pattern 5): the twin's verdict proves the tool. With no twin, run the tool's check form (`--check`, `--dry-run`, `-l`, RuboCop without `-a`) in the same service, or ask the user before you run the write form, and show `git status --short` before and after.
10. **Parallel tests, when Step 3 left the decision here.** Read the duration of the serial full run of each test check. Over 5 minutes, parallel is needed. If the runner has no built-in parallel mode, research the parallel libraries and ask which one, as in Step 2. Show the parallel setup (pattern 9) and any app change it needs, wait for approval as in Step 4, apply it, and run steps 1 to 8 again for that check. Under 5 minutes, record `not needed` with the time.
11. **Parallel check.** For every parallel test check, the parallel run must report the same number of tests as the serial run (no test lost between workers), and must be faster. If not, it is `broken`.
12. **Coverage minimum.**
    1. Take the step 5 gate run of the `coverage` service (placeholder minimum `0`), right after the test check's full run. Read the line coverage from its log ("Reading coverage" in tool-images.md).
    2. Minimum = that value rounded down to one decimal. If the project already sets a higher minimum, keep the project's.
    3. Write the minimum into the `full` command, with a comment above the service: `# coverage minimum <min>%: measured <value>% on <YYYY-MM-DD>`.
    4. Run the gate again on the same report (no new test run), with the same `PIPELINES_SINCE`. It must be `pass`. A failure there is `broken` (wrong report path, workers not merged).
    5. Prove the suite runs once: the coverage log shows no test output, only the gate line.
    6. If the suite has failing tests, coverage was measured anyway. Say so in the report, because the minimum may rise once they are fixed.
13. **Clean up.** Remove only the dependency services the runs started: `docker compose --profile pipelines rm -sf <service> ...`. Never `docker compose down`.

A version command proves the tool starts. Only the full and changed runs prove the check works. `run-pipelines` uses these services later. It must never be the first to find a broken one.

### Step 7: Verify

1. `docker compose config --services` with no profile returns the same list as Step 0.
2. `docker compose --profile pipelines config --services` lists every planned check.
3. `git diff` touches only the compose file, the new Dockerfiles, the new tool configs, and the app changes the user approved for the baseline. No CI file, no existing service, no other dependency version.
4. Each service has `profiles: [pipelines]`, a pinned image or a build, and an `x-pipelines` block.
5. Every new service has a `pass` or `findings` verdict from Step 6 for its full command, and for its changed command when it has one. Any `broken` check makes the status **Not done**.
6. `git status --short` shows no file changed by a check run.
7. Every applicable baseline item is `met` by a service with a `pass` or `findings` verdict, or the status is **Baseline not met** with the reason.

### Step 8: Report

```
## Pipelines built: <repo>

Status: **Done** (every check returns a verdict) | **Not done** (<N> broken, listed below).
Baseline: **met** | **not met** (<items>, reasons below).

### Baseline
| # | item | status | runs in | check-id | evidence or reason |
|---|---|---|---|---|---|
| 8 | parallel tests | not needed | — | rspec | serial full run 2m10s |
| 9 | coverage | met | local only | coverage | minimum 87.4% (measured 87.46%) |
Same shape as baseline.md. One row per item.

### Services (<N>)
| check-id | category | image | version (rule) | full run | changed run | log |
|---|---|---|---|---|---|---|
| rubocop | lint | app image | 1.66.1 (CI) | findings: 12 offenses | pass: 1 file | <path> |
| gitleaks | secrets-scan | zricethezav/gitleaks:v8.x.y | 8.x.y (latest stable) | pass: no leaks | n/a | <path> |

Findings are the check working on today's code. Fix them with `static-analysis` or the skill `run-pipelines` names, not here.

### Files
- <created / edited files>

### Broken (not done)
- <check-id>: <error lines from the log>. Tried: <fixes>. Needs: <what the user must do>.

### Version mismatches
- <check-id>: CI <v>, local <v>, reason.

### Outdated (reported after the checks run; not changed)
| what | kind | pinned | latest stable | where to bump |
|---|---|---|---|---|
| rubocop | lockfile lib | 1.66.1 | <v> | `Gemfile.lock` |
| golangci-lint | CI tool | 1.61.0 | <v> | `.github/workflows/ci.yml:42`, then this service |
| golang | base image | 1.23.2 | 1.23.<n> | `go.mod` / CI runtime |
Write "All current" when nothing is behind. Flag a new major version, because it can need a config migration.

### Not set up
- <check-id>: <reason> (needs cloud credential, runs only in CI, user declined).

### Needs secrets to run
- <check-id>: <VAR names>. Put them in your shell or `.env`.

### CI suggestions (not applied)
Checks that run locally but not in CI can be added to GitHub Actions with `github-pipelines`.
- <CI change that would make CI match this setup, or add a missing check>.

### Next step
`document-pipelines` writes these checks and commands to `docs/pipelines.md`. Run one check now with:
docker compose --profile pipelines run --rm <check-id>
```

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "`latest` is fine for a dev tool." | Different version from CI means different results. Pin it. |
| "I know the latest version of this tool." | Versions move every week. Look it up in this run. |
| "A newer version exists, so I will use it for the CI check too." | An existing check keeps the CI version. Report the newer one under Outdated. |
| "The lockfile version is old, I will bump the gem." | Never change app dependencies. Report it. |
| "I will tidy the existing app service while I am here." | Never change an existing service. |
| "The check fails, so I will add an ignore entry." | This skill sets up checks. Fixing findings is `static-analysis` or the user's job. |
| "I will add the job to CI too, it is one line." | Never edit CI. Report it as a CI suggestion. |
| "The image tag looks right." | `docker manifest inspect` it. Wrong tags fail only on someone else's machine. |
| "SimpleCov is the only option, no need to ask." | Show its status and ask. With one candidate the options are "Use it" and "Skip". |
| "The coverage service can run the suite itself, it is simpler." | Then the suite runs twice in full mode. Read the test check's report. |
| "The project has no coverage minimum, I will leave it that way." | Coverage is baseline. The minimum is the current coverage. |
| "I will set the coverage minimum a bit lower, to leave room." | The minimum is the current value, rounded down to one decimal. Lower lets coverage drop. |
| "Complexity is noisy, I will skip it." | Complexity is baseline. Existing findings are a backlog, not a reason to skip. |
| "I will enable the complexity cops in `.rubocop.yml`." | Never edit the linter config. Turn them on from the command line, or use lizard. |
| "Parallel is faster, I will add `parallel_tests` to the Gemfile." | App changes only for the baseline, only when parallel is needed, only with approval. |
| "The version command works, so the check works." | It proves the tool starts. Only a full run that returns a verdict proves the check works. |
| "Exit 0, done." | Exit 0 with "0 files inspected" is a broken path or glob. Read the output. |
| "It exits 1, so the check is broken." | Exit 1 with offenses or failing tests is the check working. Read the output. |
| "The full test suite takes 20 minutes, the version check is enough." | Not done until it runs. Use a long timeout. |
| "The check is broken, I will exclude the failing files." | That weakens the check. Fix your file, or report Not done. |

## Red flags

- A new service without `profiles: [pipelines]`.
- An image with no tag or with `latest`.
- A diff line inside an existing service or a CI file.
- A secret value in the compose file.
- A changed lint rule, ignore entry, or coverage threshold.
- A service with no `x-pipelines` block.
- `docker compose up` now starts more services than before.
- A new check pinned to an old version with no reason, or any version written from memory.
- A lockfile, Gemfile, or `package.json` diff that the user did not approve as a baseline app change, or that changes any other locked version.
- Status **Done** while a check has no full-run verdict, or is `broken`.
- A `pass` whose output shows nothing was checked.
- Outdated items missing from the report.
- A report with no Baseline section, or a baseline item with no row.
- A coverage minimum lower than the measured coverage rounded down, or lower than the project's own minimum.
- A `coverage` service that runs the test suite itself instead of reading the test check's report.
- A parallel run that reports fewer tests than the serial run.
- A dependency or test-setup change that was not approved in the plan.
- A new tool in the plan with no status table, or no question to the user.

## Verification

- [ ] Docker and Compose v2 checked.
- [ ] `scan-pipelines` ran, and the user chose the suggestions.
- [ ] For every new tool, the user saw a status table and picked from options with one recommended.
- [ ] The user approved the plan before any file was written.
- [ ] Every image is pinned and was found locally or in the registry.
- [ ] Existing checks use the CI version, new checks the latest stable looked up in this run, lockfile tools the lockfile version.
- [ ] `docker compose config --quiet` passes.
- [ ] Every new service builds or pulls, and its version command prints the planned version.
- [ ] Every new service ran its full command, and its changed command when it has one, and each returned `pass` or `findings`.
- [ ] No `broken` check left, or the status is **Not done** with the cause.
- [ ] Every applicable baseline item has a service with a verdict, or the report says **Baseline not met** and why.
- [ ] The coverage minimum equals the measured coverage rounded down to one decimal (or the project's higher minimum), and the second run passes it.
- [ ] The `coverage` service has `reads:` set and runs only the gate: the suite runs once per run.
- [ ] Parallel tests are set up when needed, and report the same test count as the serial run.
- [ ] The no-profile service list is unchanged.
- [ ] No CI file and no existing service changed.
- [ ] The report lists verdicts, mismatches, outdated items, checks not set up, and secret names needed.
