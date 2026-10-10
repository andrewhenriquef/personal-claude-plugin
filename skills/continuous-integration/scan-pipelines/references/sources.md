# Sources of checks

Where a check can live, and what to extract from each source. Read every group. List the files you did not find.

## 1. Agent and contributor docs

| File | Extract |
|---|---|
| `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/`, `.github/copilot-instructions.md` | Commands agents must run before a commit or a PR |
| `README*`, `CONTRIBUTING*`, `docs/` | "How to test", "how to lint" sections. Compare them with CI in Drift |
| `.github/pull_request_template.md` | Checklist items that imply a check (for example "ran migrations") |

## 2. CI configs

| System | Files | Extract |
|---|---|---|
| GitHub Actions | `.github/workflows/*.yml` | `on:` triggers and `paths:` filters, `jobs.<id>.steps[].run`, `uses:` actions and their `with:` inputs, `services:`, `container:`, `env:`, `secrets.*` names, `continue-on-error`, `if:` conditions, `matrix` |
| GitHub reusable workflows | `uses: ./.github/workflows/x.yml` or `owner/repo/.github/workflows/x.yml@ref` | Follow local ones. For remote ones, record the ref and put the content under "Needs human check" |
| GitHub composite actions | `.github/actions/*/action.yml` | `runs.steps[].run` |
| GitLab CI | `.gitlab-ci.yml`, `include:` files | `stages`, `script`, `rules`/`only`/`except`, `services`, `image`, `allow_failure`, `needs`. Follow local `include:` files. GitLab templates (`template: Security/SAST.gitlab-ci.yml`) count as a check: record the template name |
| CircleCI | `.circleci/config.yml` | `jobs.*.steps[].run`, `orbs`, `workflows` filters, `docker` images |
| Jenkins | `Jenkinsfile` | `stages`, `sh` steps, `when`, `post` |
| Buildkite | `.buildkite/pipeline.yml` | `steps[].command`, `plugins`, `soft_fail` |
| Azure Pipelines | `azure-pipelines.yml` | `steps[].script`, `task:`, `condition`, `continueOnError` |
| Bitbucket | `bitbucket-pipelines.yml` | `pipelines.*.step.script`, `services` |
| Drone, Woodpecker | `.drone.yml`, `.woodpecker.yml`, `.woodpecker/` | `steps[].commands` |
| Travis | `.travis.yml` | `script`, `before_script`, `allow_failures` |

Resolve every command to the real tool call. `make lint` becomes the Makefile recipe. `npm run test` becomes the `package.json` script. `bin/ci` becomes the commands in that script. Record each hop in the sources.

## 3. Task runners and scripts

| File | Extract |
|---|---|
| `Makefile`, `*.mk` | Targets with lint, test, check, ci, audit, scan, verify, fmt in their name or recipe |
| `justfile`, `Taskfile.yml`, `magefile.go` | Same |
| `package.json` | `scripts`, plus `lint-staged` config |
| `Rakefile`, `lib/tasks/*.rake` | Tasks that run test, lint, or audit tools. The `default` task |
| `bin/`, `script/`, `scripts/` | Shell scripts named `ci`, `test`, `lint`, `check`, `setup`, `verify` |
| `tox.ini`, `noxfile.py`, `pyproject.toml [tool.*]` | Environments and sessions |
| `Procfile*`, `Earthfile`, `dagger.json` | Pipeline steps defined outside the CI system |

## 4. Git hooks

| File | Extract |
|---|---|
| `.pre-commit-config.yaml` | `repos[].hooks[].id`, `rev`, `args`, `stages`, `files`/`exclude` |
| `lefthook.yml` | `pre-commit`/`pre-push` commands, `glob`, `run` |
| `.husky/*` | Hook scripts |
| `.overcommit.yml` | Enabled hooks and their commands |
| `package.json` `simple-git-hooks`, `lint-staged` | Commands and globs |

Hooks in `.git/hooks/` are not versioned. Do not count them.

## 5. Tool configs

A config file shows a tool is set up. It is a check only if something in groups 2 to 4 runs it. Otherwise report it in Drift.

| Area | Files |
|---|---|
| Lint and format | `.rubocop.yml`, `.standard.yml`, `.golangci.yml`, `.eslintrc*`, `eslint.config.*`, `biome.json`, `.prettierrc*`, `ruff.toml`, `.flake8`, `.editorconfig`, `.stylelintrc*`, `.markdownlint*`, `.yamllint*`, `.shellcheckrc`, `.hadolint.yaml` |
| Types | `tsconfig.json`, `mypy.ini`, `pyrightconfig.json`, `sorbet/`, `rbs_collection.yaml`, `steep` |
| Tests and coverage | `.rspec`, `spec/spec_helper.rb`, `.simplecov`, `jest.config.*`, `vitest.config.*`, `playwright.config.*`, `cypress.config.*`, `pytest.ini`, `codecov.yml`, `.nycrc` |
| Security | `config/brakeman.yml`, `.gosec.json`, `.semgrep.yml`, `.gitleaks.toml`, `.trufflehog*`, `.snyk`, `.trivyignore`, `.bundler-audit.yml`, `osv-scanner.toml` |
| Migrations | `config/initializers/strong_migrations.rb`, `.squawk.toml`, `atlas.hcl` |
| IaC | `.tflint.hcl`, `.checkov.yml`, `.kube-linter.yaml` |
| API | `.spectral.yaml`, `buf.yaml`, `buf.gen.yaml` |
| Commits | `commitlint.config.*`, `.commitlintrc*`, `.gitmessage` |

Ignore and baseline files (`.rubocop_todo.yml`, `.trivyignore`, `.gitleaksignore`, `.semgrepignore`) are not checks. Count their entries and report the count, because a large count weakens the check.

## 6. Containers

| File | Extract |
|---|---|
| `Dockerfile*` | Base image and tag, `RUN` steps that run checks, multi-stage `test` or `lint` targets |
| `docker-compose*.yml`, `compose*.yml` | Services (DB, cache, queue) and their images. Services with a `test`, `lint`, or `ci` profile or name |
| `.devcontainer/devcontainer.json` | `postCreateCommand`, features, image |

Record the images. `build-pipelines` reuses them.

## 7. Bots and hosted services

| File or setting | Extract |
|---|---|
| `.github/dependabot.yml` | Ecosystems, schedule. Covers dependency updates, not vulnerability audit in CI |
| `renovate.json`, `.github/renovate.json5` | Same |
| `codecov.yml` | Coverage targets and whether the status blocks |
| `sonar-project.properties` | Quality gate and analyzed paths |
| `.github/codeql/`, CodeQL workflow | Languages analyzed |
| `.snyk` | Snyk project policy |

Hosted checks that run outside the repo (CodeQL default setup, Snyk app, SonarCloud app) show up only in branch protection. Put any you suspect under "Needs human check".

## 8. Branch protection and rulesets

Run only when `gh auth status` succeeds. GET requests only.

```
gh api repos/{owner}/{repo}/branches/{default_branch}/protection/required_status_checks
gh api repos/{owner}/{repo}/rulesets
gh api repos/{owner}/{repo}/rulesets/{id}
```

Get `{owner}/{repo}` from `git remote get-url origin` and the default branch from `git symbolic-ref refs/remotes/origin/HEAD`. A 404 or 403 means no protection or no permission. Report which one is not known, under "Needs human check".

Match each required check name (`contexts`, `checks[].context`) to a CI job. A required name with no matching job is Drift.

For GitLab, read the project settings by hand. Report "merge request pipelines must succeed" as "Needs human check" unless the user gives it.
