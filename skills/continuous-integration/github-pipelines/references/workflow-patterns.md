# Workflow patterns

YAML patterns for `github-pipelines`. Copy the shape, not the values. Every version, image tag, env name, and command comes from the compose file and the manifest. Every `<sha>` comes from the lookup below, in this run.

## Pinning actions

For each action, find the latest stable release, then the commit it points to:

```
gh api repos/<owner>/<repo>/releases/latest --jq .tag_name
gh api repos/<owner>/<repo>/commits/<tag> --jq .sha
```

Without `gh`: `curl -fsSL https://api.github.com/repos/<owner>/<repo>/releases/latest` and `curl -fsSL https://api.github.com/repos/<owner>/<repo>/commits/<tag>` (fields `tag_name` and `sha`).

Write it as `uses: <owner>/<repo>@<40-char sha> # <tag>`. The comment lets Dependabot and Renovate update the pin.

Skip releases with a pre-release marker (see "Versions" in `build-pipelines`' tool-images.md). A new major version of a setup action can change its inputs: read its README for the inputs you use.

## Skeleton

```yaml
# Managed by github-pipelines. Generated from docs/pipelines.md.
# Adds the checks that run locally (docker compose --profile pipelines) but not in other workflows.
# Each job mirrors one compose service: same runtime, tool version, services, and command.
name: pipelines

on:
  pull_request:
  push:
    branches: [main]            # the default branch

permissions:
  contents: read

concurrency:
  group: pipelines-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  # one job per check, id = check id
```

## Setup actions by ecosystem

| Ecosystem | Action | Version from | Dependencies |
|---|---|---|---|
| Ruby | `ruby/setup-ruby` | `.ruby-version` (default) or `ruby-version:` input | `bundler-cache: true` (runs `bundle install` with the lockfile, cached) |
| Node | `actions/setup-node` | `node-version-file: .nvmrc` (or `.node-version`, `package.json`) | `cache: npm` (or `pnpm`, `yarn`), then `npm ci` |
| Go | `actions/setup-go` | `go-version-file: go.mod` | Module cache on by default, then `go mod download` |
| Python | `actions/setup-python` | `python-version-file: .python-version` (or `pyproject.toml`) | `cache: pip`, then the install command the app image uses |

When the app Dockerfile pins a runtime version that no version file states, pass it as the version input, with a comment: `# from Dockerfile:3`.

The app image may install system packages the tests need (`libpq-dev`, `imagemagick`). Read its `apt-get install` / `apk add` lines and install the same ones in a step before the dependencies.

## Pattern A: check in the app runtime

```yaml
  rubocop:
    name: rubocop
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@<sha> # <tag>
        with:
          persist-credentials: false
      - uses: ruby/setup-ruby@<sha> # <tag>
        with:
          bundler-cache: true
      - name: rubocop (lint)
        run: bundle exec rubocop --parallel     # manifest `full`, unchanged
```

Pin `runs-on` to a version (`ubuntu-24.04`), not `ubuntu-latest`, for the same reason images are pinned.

## Pattern B: standalone tool image

Same image and tag as the compose service. `docker run` keeps the version exact.

```yaml
  gitleaks:
    name: gitleaks
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@<sha> # <tag>
        with:
          persist-credentials: false
          fetch-depth: 0                        # gitleaks scans history; match the local mount of .git
      - name: gitleaks (secrets-scan)
        run: >-
          docker run --rm -v "$PWD:/repo" -w /repo
          zricethezav/gitleaks:<tag from compose>
          gitleaks git --redact --verbose .
```

The command after the image is the manifest `full`. Compose sets `entrypoint: []` on these services. Match it with `--entrypoint ""` when the image has an entrypoint that would wrap the command.

Use the tool's official action instead only when it takes the exact tool version as an input (for example `golangci/golangci-lint-action` with `version: v<x.y.z>`), and its arguments give the same command.

## Pattern C: tests with services

Each compose dependency service becomes a job service with the same image and tag.

```yaml
  rspec:
    name: rspec
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    services:
      postgres:
        image: postgres:16.4                    # same tag as db-pipelines in compose
        env:
          POSTGRES_PASSWORD: postgres           # test-only value, same as compose
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 2s
          --health-timeout 3s
          --health-retries 15
    env:
      RAILS_ENV: test
      DATABASE_URL: postgres://postgres:postgres@localhost:5432/app_test   # compose host db-pipelines -> localhost
    steps:
      - uses: actions/checkout@<sha> # <tag>
        with:
          persist-credentials: false
      - uses: ruby/setup-ruby@<sha> # <tag>
        with:
          bundler-cache: true
      - name: rspec (unit-test)
        run: |
          bin/rails db:prepare
          bundle exec rspec
```

Compose uses `tmpfs` for the database data. Job services are throwaway containers, so there is no equivalent to add.

Parallel test commands (pattern 9 in compose-patterns.md) run unchanged. The runner has the CPU count of its size, so the worker count can differ from a laptop. The test count must not.

## Pattern D: coverage reads the test job's report

The suite runs once, as it does locally (pattern 8 in compose-patterns.md). The test job uploads the report. The coverage job downloads it and runs only the gate. Two status checks, one suite run.

In the test job (Pattern C), after the test step:

```yaml
      - name: Upload coverage report
        if: ${{ !cancelled() }}                   # also when tests fail: the coverage job still judges coverage
        uses: actions/upload-artifact@<sha> # <tag>
        with:
          name: coverage-report
          path: coverage/.last_run.json           # the report path in the gate command
          if-no-files-found: error                # a crashed test run must not look like a missing upload
          retention-days: 1
```

The coverage job:

```yaml
  coverage:
    name: coverage
    needs: rspec                                  # the check in `reads`
    if: ${{ !cancelled() }}                       # run after failing tests too, as locally
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@<sha> # <tag>
        with:
          persist-credentials: false
      - uses: ruby/setup-ruby@<sha> # <tag>      # only the interpreter the gate needs: no bundler-cache, no services
      - uses: actions/download-artifact@<sha> # <tag>
        with:
          name: coverage-report
          path: coverage                          # same directory as the upload
      - name: coverage (coverage)
        run: sh docker/pipelines/coverage-gate.sh simplecov coverage/.last_run.json 87.4   # manifest `full`, unchanged
```

Rules:

- `PIPELINES_SINCE` is not set in CI: the artifact comes from this run, so it cannot be stale.
- When the test job crashes before the tests write a report, the upload fails (`if-no-files-found: error`), the download fails, and the coverage job fails. Classify it `broken` ("no report"), never a coverage verdict.
- The gate needs the source for `go` reports (`go tool cover` reads the files) and the interpreter for the others: checkout plus the setup action, nothing more.
- The upload path is the report file (or directory) in the gate command. Upload the directory for Go, Jest, Vitest, and pytest reports the same way.

**When the test check already runs in an existing workflow**, that job cannot be edited, so nothing uploads the report. The coverage job then runs the test check's full command and the gate in one job, with the test job's services and setup (Pattern C):

```yaml
      - name: coverage (coverage)
        run: |
          bin/rails db:prepare && bundle exec rspec || true   # the existing CI job owns the test verdict; this run only writes the report
          sh docker/pipelines/coverage-gate.sh simplecov coverage/.last_run.json 87.4
```

Report that the suite runs twice in CI, and suggest adding the upload step to the existing job.

## Pattern E: secrets

```yaml
  snyk:
    name: snyk
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    env:
      SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
    steps:
      - name: Secret missing (fork PR or not configured)
        if: env.SNYK_TOKEN == ''
        run: echo "::warning title=snyk skipped::SNYK_TOKEN is not available to this run"
      - uses: actions/checkout@<sha> # <tag>
        if: env.SNYK_TOKEN != ''
        with:
          persist-credentials: false
      - name: snyk (dependency-audit)
        if: env.SNYK_TOKEN != ''
        run: docker run --rm -e SNYK_TOKEN -v "$PWD:/project" -w /project snyk/snyk:<tag from compose> snyk test
```

`-e SNYK_TOKEN` passes the variable by name. The value never appears in the command.

## Pattern F: extra permissions

Only when the tool needs them, at job level, with the reason:

```yaml
    permissions:
      contents: read
      security-events: write     # upload SARIF to code scanning
```

## Things that differ from local, and how to keep them equal

| Local (compose) | GitHub (native) |
|---|---|
| App image built from the Dockerfile | Setup action with the same runtime version, plus the same system packages |
| `extends: web` env | Job `env:` with the same names and test-only values |
| Service host name (`db-pipelines`) | `localhost` and the mapped port |
| Repo mounted at the app working directory | Checkout at `$GITHUB_WORKSPACE`. Commands must use relative paths, as the manifest does |
| `.git` in the mount | `fetch-depth: 0` when the tool reads history (Gitleaks, commit-lint, `buf breaking`, oasdiff) |
| Cache volumes (`pipelines-gomod`) | The setup action's cache, or `actions/cache` with a key on the lockfile |
