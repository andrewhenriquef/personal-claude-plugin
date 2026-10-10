---
name: build-pipelines
description: Set up every quality check of a project to run locally in Docker. Runs scan-pipelines first, asks which suggested checks to add, then adds one service per check to the project's existing docker-compose file under the `pipelines` profile, reusing the app image for checks that need the app runtime and pinned official images for standalone tools, with a Dockerfile only when no image fits. Each service carries an `x-pipelines` block with its category, full-suite command, and changed-files command. Checks image availability locally and in the registry, then builds, pulls, and smoke-tests each service. Never edits CI config, never changes existing services, never weakens a tool config. Use when the user asks to set up, build, dockerize, or containerize the project's checks or pipelines, or to make CI checks runnable locally.
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

## Why this process

1. **Local must equal CI.** A check that passes locally and fails in CI wastes a round trip. Same tool, same version, same flags, same config.
2. **Docker removes "works on my machine".** Nobody needs the tools installed. The pinned image is the install.
3. **The app's compose file is the natural home.** Developers already run it. The `pipelines` profile keeps the new services out of `docker compose up`.
4. **The next skills read the compose file, not your memory.** The `x-pipelines` block on each service is the contract that `document-pipelines` and `run-pipelines` use.

## When to use

- The user asks to set up, build, dockerize, or containerize the project's checks or pipelines.
- The user wants CI checks to run locally.
- `run-pipelines` finds no `pipelines` services and calls this skill.

## When NOT to use

- The user only wants to know what checks exist. Use `scan-pipelines`.
- The user wants to run the checks. Use `run-pipelines`.
- The user wants CI config changed. This skill never edits CI. Report the CI change as a suggestion.

## Rules that never change

- **Never edit CI config.** `.github/workflows/`, `.gitlab-ci.yml`, and the other CI files stay as they are.
- **Never change an existing service.** Add new services only. Reuse existing ones through `extends` or the same `build`/`image`.
- **Every new service has `profiles: [pipelines]`.** `docker compose up` must start exactly the same services as before.
- **Pin every image.** Use the version CI uses. Never `latest`. No tag, no service.
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

Ask the user once, with all suggestions from the scan in one multi-select question, must first. Show the category, the tool, and the effort for each. Existing checks are always set up. Do not ask about them.

### Step 3: Plan each check

Read [references/compose-patterns.md](references/compose-patterns.md) and [references/tool-images.md](references/tool-images.md) before this step.

For each check (existing and chosen), pick the image in this order:

1. **App image.** The check needs the app runtime and its dependencies (tests, RuboCop, ESLint, Brakeman, `bundler-audit`, `go vet`). Reuse the app service through `extends`, or reuse its `build` with the `test` or `ci` target when the Dockerfile has one.
2. **Official tool image.** The check is a standalone tool (Gitleaks, Trivy, Hadolint, ShellCheck, golangci-lint). Use the image from tool-images.md, pinned to the CI version.
3. **New Dockerfile.** No image fits. Write `docker/pipelines/Dockerfile.<check-id>`, based on the CI runtime image, and install the tool at the CI version.

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
- **Not local-runnable.** A check that needs a cloud credential or a paid SaaS token gets a service that reads the secret through `${VAR}` and a `requires` entry in `x-pipelines`. If the check cannot run outside CI at all (for example CodeQL default setup), do not add a service. List it in the report.

### Step 4: Show the plan and wait

Show one table and the list of files to create or edit:

```
| check-id | category | image (source) | services | changed-files | new config |
|---|---|---|---|---|---|

Files:
- edit  docker-compose.yml   (+N services, +M volumes)
- create docker/pipelines/Dockerfile.<id>
- create <tool config>
```

Wait for the user to approve. Apply only what they approve.

### Step 5: Write

1. Add the services, volumes, and `x-pipelines` blocks to the compose file, using the patterns in compose-patterns.md. Keep the existing YAML style (indentation, quotes, key order). Add new services after the existing ones under a `# --- pipelines (managed by build-pipelines) ---` comment.
2. Write the Dockerfiles and tool configs.
3. If the project has `.dockerignore`, check it does not exclude files a check needs (for example `.git` for Gitleaks). If it does, mount the repo instead of copying it. Do not edit `.dockerignore`.

### Step 6: Build and smoke test

Run in this order. Stop at the first failure, fix your own file, and run again. Never fix by weakening a check.

1. `docker compose config --quiet`. The file must be valid.
2. `docker compose --profile pipelines pull --ignore-buildable <new services>`. Name the services, so the developer's own service images are not pulled to newer tags.
3. `docker compose --profile pipelines build <new services that build>`.
4. For each new service, run the tool's version command from tool-images.md. Compare it with the CI version.

A smoke test proves the tool runs. It does not run the check. Real runs are the job of `run-pipelines`.

### Step 7: Verify

1. `docker compose config --services` with no profile returns the same list as Step 0.
2. `docker compose --profile pipelines config --services` lists every planned check.
3. `git diff` touches only the compose file, the new Dockerfiles, and the new tool configs. No CI file, no existing service.
4. Each service has `profiles: [pipelines]`, a pinned image or a build, and an `x-pipelines` block.

### Step 8: Report

```
## Pipelines built: <repo>

### Services (<N>)
| check-id | category | image | version (CI / local) | changed-files | smoke |
|---|---|---|---|---|---|

### Files
- <created / edited files>

### Version mismatches
- <check-id>: CI <v>, local <v>, reason.

### Not set up
- <check-id>: <reason> (needs cloud credential, runs only in CI, user declined).

### Needs secrets to run
- <check-id>: <VAR names>. Put them in your shell or `.env`.

### CI suggestions (not applied)
- <CI change that would make CI match this setup, or add a missing check>.

### Next step
`document-pipelines` writes these checks and commands to `docs/pipelines.md`. Run one check now with:
docker compose --profile pipelines run --rm <check-id>
```

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "`latest` is fine for a dev tool." | Different version from CI means different results. Pin it. |
| "I will tidy the existing app service while I am here." | Never change an existing service. |
| "The check fails, so I will add an ignore entry." | This skill sets up checks. Fixing findings is `static-analysis` or the user's job. |
| "I will add the job to CI too, it is one line." | Never edit CI. Report it as a CI suggestion. |
| "The image tag looks right." | `docker manifest inspect` it. Wrong tags fail only on someone else's machine. |
| "Smoke test passed, so the check works." | It proves the tool starts. The first real run is `run-pipelines`. |

## Red flags

- A new service without `profiles: [pipelines]`.
- An image with no tag or with `latest`.
- A diff line inside an existing service or a CI file.
- A secret value in the compose file.
- A changed lint rule, ignore entry, or coverage threshold.
- A service with no `x-pipelines` block.
- `docker compose up` now starts more services than before.

## Verification

- [ ] Docker and Compose v2 checked.
- [ ] `scan-pipelines` ran, and the user chose the suggestions.
- [ ] The user approved the plan before any file was written.
- [ ] Every image is pinned and was found locally or in the registry.
- [ ] `docker compose config --quiet` passes.
- [ ] Every new service builds or pulls, and its smoke test prints the expected version.
- [ ] The no-profile service list is unchanged.
- [ ] No CI file and no existing service changed.
- [ ] The report lists mismatches, checks not set up, and secret names needed.
