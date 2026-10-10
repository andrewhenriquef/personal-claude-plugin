---
name: scan-pipelines
description: Read-only inventory of every quality check a project defines (lint, format, type check, tests, integration tests, coverage, security, secrets, dependency audit, migrations, containers, IaC, and more) across CI configs, task runners, git hooks, tool configs, containers, and bots, plus drift between them and suggestions for missing checks that fit the stack. Reports in chat only. Never runs a check, installs a tool, writes a file, or triggers remote CI. Use when the user asks what checks or pipelines a repo has, to audit CI, to list quality gates, or which checks are missing.
---

# Scan Pipelines

Find every quality check the project already defines. Put them in one inventory. Show where the sources disagree. Suggest the checks that are missing for this stack.

This is the first skill of the `continuous-integration` family:

| Skill | Job |
|---|---|
| `scan-pipelines` | This skill. Inventory, drift, and gaps. Read-only |
| `build-pipelines` | Planned. Sets up each check to run locally in Docker |
| `document-pipelines` | Planned. Writes the checks, setup, and run commands to a docs file |
| `run-pipelines` | Planned. Runs the checks from that docs file |

## Why this process

1. **Checks live in many places.** CI holds the ones that block a merge. Hooks, Makefiles, and package scripts hold others. A tool config with no command that runs it is a check nobody runs. Read all of them.
2. **CI is the contract.** The command in CI is the command that must pass. A README or Makefile command that differs from CI is drift, not a second truth.
3. **The next skills need facts, not guesses.** `build-pipelines` and `document-pipelines` build on this inventory. Every record needs its exact command and its source line.
4. **Suggestions must fit the stack.** A generic wishlist is noise. Each suggestion needs evidence from the repo that the check applies.

## When to use

- The user asks what checks, gates, or pipelines a repo runs.
- The user wants to audit CI or find missing checks.
- Before `build-pipelines` or `document-pipelines`, to know what exists.

## When NOT to use

- The user wants to run the checks. Use `run-pipelines`.
- The user wants the checks set up in Docker. Use `build-pipelines`.
- The user wants lint errors fixed. Use `static-analysis`.
- The user wants a security, dependency, or migration review of code. Use `security-analysis`, `dependency-analysis`, or `data-and-migration-analysis`. This skill only reports which tools exist for those areas.

## Rules that never change

- **Read-only.** Do not run a check, install a tool, pull an image, write or edit a file, or trigger remote CI (`gh workflow run`, pipeline APIs, re-runs).
- **Allowed commands:** `git` read commands, `ls`, `find`, `grep`, `cat`, `head`, `sed -n`, and `gh api` GET requests when `gh` is authenticated. Nothing else.
- **Cite every check.** Each inventory row names its source as `file:line`. If you cannot point to a line, it is not in the inventory.
- **No invented checks.** A tool in the dependencies with no command that runs it goes to Drift, not to the inventory.
- **Secrets by name only.** Record the names of env vars and CI secrets. Never print a value, even if one is committed. If a value is committed, report it as a security finding by file and line, without the value.
- **Suggestions need a signal.** Each suggestion names the file or dependency that shows it applies.

## Process

### Step 0: Set scope

1. Scope is the whole repository. Checks are defined at repo level, so a diff scope does not apply.
2. If the user names a package or directory, scan only the checks that apply to it, plus the repo-wide ones.
3. Detect a monorepo: workspaces in `package.json`, `pnpm-workspace.yaml`, `go.work`, several `go.mod` or `Gemfile` files, `nx.json`, `turbo.json`, Bazel, or Pants. If found, inventory per package and keep repo-wide checks in their own group.
4. Skip vendored and generated directories (`vendor/`, `node_modules/`, `dist/`, `build/`, `tmp/`). Say that you skipped them.

### Step 1: Detect the stack

Record, with the file that shows each one:

- Languages and versions (`go.mod`, `.ruby-version`, `.tool-versions`, `.nvmrc`, `pyproject.toml`).
- Frameworks and package managers.
- Databases and services (CI `services:`, `docker-compose*.yml`, `config/database.yml`, connection env vars).
- Containers (`Dockerfile*`, compose files, `.devcontainer/`).
- Infrastructure as code (`*.tf`, Helm charts, Kubernetes manifests, CloudFormation).
- API specs (OpenAPI, protobuf, GraphQL schema).
- Migrations (`db/migrate/`, `migrations/`, `*.sql`).

The stack drives Step 5. Read it before you suggest anything.

### Step 2: Collect sources

Read [references/sources.md](references/sources.md) before this step. It lists every place a check can live and what to extract from each.

Read the sources in this order:

1. Agent and contributor docs: `CLAUDE.md`, `AGENTS.md`, `README`, `CONTRIBUTING`.
2. CI configs. Follow reusable workflows, composite actions, `include:` files, and templates to their real commands.
3. Task runners: `Makefile`, `justfile`, `Taskfile.yml`, `package.json` scripts, `Rakefile`, `bin/`, `scripts/`.
4. Git hooks: `.pre-commit-config.yaml`, `lefthook.yml`, `.husky/`, `.overcommit.yml`.
5. Tool configs: linter, formatter, type checker, test, coverage, and scanner configs.
6. Containers: `Dockerfile*`, compose files, `.devcontainer/`.
7. Bots and services: Dependabot, Renovate, Codecov, SonarQube, CodeQL default setup.
8. Branch protection: required status checks through `gh api` (see sources.md). If `gh` is missing or not authenticated, put this under "Needs human check".

List every source you looked for and did not find. "No CI config found" is a result.

### Step 3: Normalize each check

One record per check. A CI job that runs three tools is three records. Record:

| Field | Content |
|---|---|
| id | Short slug, unique (`rubocop`, `rspec-unit`, `gitleaks`) |
| category | From [references/catalog.md](references/catalog.md) |
| tool | Name and pinned version, or "unpinned" |
| command | The exact command, after you resolve script and Makefile indirection |
| trigger | `pull_request`, `push <branches>`, `schedule`, `manual`, `pre-commit hook`, `pre-push hook`, or `local only` |
| blocking | `required` (branch protection), `fails job`, `allow_failure`, `continue-on-error`, or `unknown` |
| changed-files scope | `yes` and how (path filter, `--diff`, `git diff` input), or `no` |
| services | Databases, caches, queues the check needs |
| env and secrets | Names only |
| runtime | Image or runtime version the check runs on |
| local-runnable | `yes`, or `no` plus the blocker (cloud credential, paid SaaS token, OS-specific runner) |
| source | `file:line`, plus every other source that runs the same check |

When the same check appears in several sources (CI and a hook and the Makefile), keep one record and list all sources. Use the CI command as the canonical one.

### Step 4: Find drift

Report each case with both sources:

- A tool config exists, and no CI job, hook, or script runs the tool.
- A tool is in the dependencies, and nothing runs it.
- A hook runs a check that CI does not, or CI runs a check that no hook or script lets a developer run locally.
- The CI command and the Makefile, script, or README command differ (flags, paths, version).
- Tool versions differ between CI, the lockfile, and the container image.
- A required status check name matches no job in the CI config.
- A check is marked `allow_failure` or `continue-on-error` and nothing explains why.
- A CI job is commented out or disabled.

### Step 5: Find gaps

Read [references/catalog.md](references/catalog.md). For each category:

1. Check whether the stack has the signal that makes the category apply.
2. If it applies and no check covers it, add a suggestion.
3. If a check covers it only partially (runs on `main` only, not on pull requests, or is non-blocking), add a suggestion to tighten it.

For each suggestion record: category, evidence (`file` or dependency), recommended tool, priority, and effort.

- **Tool choice.** Prefer a tool already in the dependencies or configs. Then the ecosystem standard from the catalog. Do not suggest two tools for one category.
- **Priority.** Use the default in the catalog. Raise or lower it only with a reason from the repo, and state the reason.
- **Effort.** `S`: add a step that uses existing config. `M`: new config or a service in CI. `L`: new infrastructure, a paid service, or a big first-run fix backlog.

### Step 6: Report

Use this template. Keep tables short. Do not repeat a check in two sections.

```
## Pipeline scan: <repo or package>

### Stack
- <language/framework/service>: <evidence file>

### Sources
Read: <list>.
Not found: <list>.
Skipped: <vendored / generated dirs>.

### Inventory (<N> checks)
| id | category | tool@version | command | trigger | blocking | changed-files | local | source |
|---|---|---|---|---|---|---|---|---|

Services and secrets per check (names only):
- <id>: services <list>; env <list>.

### Drift
- <what differs>: `<file:line>` vs `<file:line>`.

### Suggested checks
| priority | category | tool | evidence | effort |
|---|---|---|---|---|
Must first, then should, then could.

### Needs human check
- <item you could not verify, and why> (for example branch protection without `gh`).

### Next step
`build-pipelines` (planned) sets up these checks in Docker. `document-pipelines` (planned) writes them to a docs file.
```

If the repo has no checks at all, say so plainly. Then list the must-priority suggestions only.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "I will run the linter to see if it works." | Read-only. Running is `run-pipelines`. |
| "This repo surely runs tests in CI." | Cite the line or do not list it. |
| "`.rubocop.yml` exists, so RuboCop is a check." | Only if something runs it. Otherwise it is Drift. |
| "The Makefile and CI do the same thing." | Compare the commands. Flags and paths often differ. |
| "Every repo needs every category." | Suggest only with a stack signal. |
| "I will show the secret so the user can rotate it." | Never print a value. File and line are enough. |

## Red flags

- An inventory row with no `file:line`.
- A command that is still `make lint` or `npm run test` and not resolved to the real tool call.
- A suggestion with no evidence.
- Two tools suggested for one category.
- A secret value in the report.
- Any command run that is not in the allowed list.
- "Branch protection: required" with no `gh api` result behind it.

## Verification

- [ ] Every source in sources.md was checked, and the misses are listed.
- [ ] Every inventory row has a resolved command and a `file:line`.
- [ ] Duplicate checks are merged, with all sources listed.
- [ ] Drift lists both sides of each mismatch.
- [ ] Every suggestion has evidence, one tool, a priority, and an effort.
- [ ] No secret values in the report.
- [ ] No check was run and no file was written.
