# Compose patterns

YAML patterns for `build-pipelines`. Copy the shape, not the values. Every value comes from the project's CI and the scan.

## The `x-pipelines` block

Every service this skill adds has an `x-pipelines` block. Compose ignores fields that start with `x-`. `document-pipelines` and `run-pipelines` read them.

```yaml
x-pipelines:
  category: lint                                  # category from scan-pipelines catalog
  source: .github/workflows/ci.yml:42             # the CI line this mirrors; "suggested" for new checks
  ci_version: "1.66.1"                            # tool version in CI; null if CI does not run it
  blocking: required                              # required | fails-job | allow-failure | local-only
  full: bundle exec rubocop --parallel            # whole-suite command
  changed: bundle exec rubocop --force-exclusion {files}   # null if the tool cannot take files
  files: '\.(rb|rake|gemspec)$|(^|/)(Gemfile|Rakefile)$'   # regex on repo-relative paths
  triggers: []                                    # paths that force the full command when changed (lockfiles, configs)
  writes: false                                   # true if the command edits files (formatters, autocorrect)
  requires: []                                    # env var names that must be set (secrets)
```

Rules:

- `full` and `changed` are the arguments after `docker compose --profile pipelines run --rm <service>`. They replace the service `command`.
- `{files}` is replaced by `run-pipelines` with space-separated repo-relative paths that match `files`.
- `{dirs}` is replaced with the unique directories of those paths, as `./dir`. Use it for tools that work on packages (Go: `go test {dirs}`).
- `changed: null` means: run `full` when any file matches `files` or `triggers`, skip otherwise.
- `files: null` (with `changed: null`) means: full mode only. In changed mode the check runs only when a `triggers` path changed. Use it for whole-suite numbers that a partial run cannot judge, like coverage, so a one-file change does not run the whole suite twice.
- Avoid `$` in `full` and `changed`. Compose interpolates `x-` fields too, so `$VAR` is replaced (or needs `$$`), and the doc and the manifest would show a different string. Put shell logic in a script under `docker/pipelines/` and call it, as the coverage gate does.
- `triggers` lists files that change the result of the whole check: the tool config (`.rubocop.yml`), the lockfile (`Gemfile.lock`), the Dockerfile. A change there runs `full`.

## Shared anchors

Put shared values once, at the top level, as `x-` anchors.

```yaml
x-pipelines-base: &pipelines-base
  profiles: [pipelines]
  working_dir: /app
  volumes:
    - .:/app
  entrypoint: []
```

Replace `/app` with the app service's own mount path and `working_dir` when it has one (for example `/rails`). Pattern 1 checks run in the app image, and the image installs its dependencies under that path. Use `/app` only when the app service has no mount.

`entrypoint: []` clears the image entrypoint, so `full` and `changed` are the whole command. Every tool image has a different entrypoint. Do not rely on it.

If a command needs shell features (globs, pipes, `&&`), use an image variant with a shell (`-alpine`, `-debian`) and write the command as `sh -c '<command>'`.

## Pattern 1: check in the app image

For tests, linters in the app's dependencies, Brakeman, `bundler-audit`, `go vet`, ESLint, `tsc`.

```yaml
services:
  # existing service, untouched
  web:
    build: .
    depends_on: [db]

  # --- pipelines (managed by build-pipelines) ---
  rubocop:
    <<: *pipelines-base
    extends:
      service: web
    depends_on: !reset []
    x-pipelines:
      category: lint
      source: .github/workflows/ci.yml:42
      ci_version: "1.66.1"
      blocking: required
      full: bundle exec rubocop --parallel
      changed: bundle exec rubocop --force-exclusion {files}
      files: '\.(rb|rake|gemspec)$|(^|/)(Gemfile|Rakefile)$'
      triggers: [.rubocop.yml, Gemfile.lock]
      writes: false
      requires: []
```

Notes:

- Do not mount a cache volume over the path where the app image installs its dependencies (`/usr/local/bundle`, `node_modules`). A named volume is filled from the image only once. After a lockfile change and a rebuild it still hides the new gems or packages, so the check runs old versions or fails. The image is the dependency cache for pattern 1.
- `extends` copies the base service. Set `depends_on`, `ports`, `command`, and `environment` explicitly when the check needs something else. Use `!reset` to drop a list or map from the base. Run `docker compose config` and read the merged result.
- If the Dockerfile has a `test` or `ci` stage, use `build: { context: ., target: test }` instead of `extends`.
- If the app image does not have the dev and test dependencies (production image), add a build with the stage that has them, or a Dockerfile (pattern 3).

## Pattern 2: official tool image

For standalone tools. Pin the tag to the CI version for an existing check, or the latest stable release for a new one.

```yaml
  gitleaks:
    <<: *pipelines-base
    image: zricethezav/gitleaks:v8.21.2
    x-pipelines:
      category: secrets-scan
      source: .github/workflows/security.yml:18
      ci_version: "8.21.2"
      blocking: required
      full: gitleaks git --redact --verbose .
      changed: null
      files: '.*'
      triggers: [.gitleaks.toml]
      writes: false
      requires: []
```

Gitleaks reads git history, so the repo mount must include `.git`. A bind mount of `.` does.

`changed` is `null` because `gitleaks dir` takes one path, not a list of files. Before you write a `{files}` command for any tool, check in its `--help` that it accepts several paths.

## Pattern 3: new Dockerfile

When no image fits. Base it on the CI runtime image (the project runtime version when CI has none). Pin the tool version: the CI version for an existing check, the latest stable release for a new one (see "Versions" in tool-images.md).

```dockerfile
# docker/pipelines/Dockerfile.govulncheck
# Managed by build-pipelines. Mirrors .github/workflows/ci.yml:57.
FROM golang:1.23.2
RUN go install golang.org/x/vuln/cmd/govulncheck@v1.1.3
WORKDIR /app
```

```yaml
  govulncheck:
    <<: *pipelines-base
    build:
      context: .
      dockerfile: docker/pipelines/Dockerfile.govulncheck
    volumes:
      - .:/app
      - pipelines-gomod:/go/pkg/mod
    x-pipelines:
      category: dependency-audit
      source: .github/workflows/ci.yml:57
      ci_version: "1.1.3"
      blocking: fails-job
      full: govulncheck ./...
      changed: null
      files: '\.go$'
      triggers: [go.mod, go.sum]
      writes: false
      requires: []
```

For Python or Node tools, start from the matching `python:<v>-slim` or `node:<v>-slim` image and `pip install <tool>==<v>` or `npm install -g <tool>@<v>`.

## Pattern 4: test services

Integration tests need the database, cache, or queue from CI `services:`.

```yaml
  db-pipelines:
    profiles: [pipelines]
    image: postgres:16.4
    environment:
      POSTGRES_PASSWORD: postgres        # test-only value, local service
    tmpfs:
      - /var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 2s
      timeout: 3s
      retries: 15

  rspec:
    <<: *pipelines-base
    extends:
      service: web
    depends_on: !override
      db-pipelines:
        condition: service_healthy
    environment:
      RAILS_ENV: test
      DATABASE_URL: postgres://postgres:postgres@db-pipelines:5432/app_test
    x-pipelines:
      category: unit-test
      source: .github/workflows/ci.yml:71
      ci_version: null
      blocking: required
      full: sh -c 'bin/rails db:prepare && bundle exec rspec'
      changed: sh -c 'bin/rails db:prepare && bundle exec rspec {files}'
      files: '^spec/.*_spec\.rb$'
      triggers: [Gemfile.lock, db/schema.rb, db/structure.sql]
      writes: false
      requires: []
```

Notes:

- Use the same image and version as CI `services:`. Do not reuse the developer's database service: tests may wipe it.
- `tmpfs` keeps test data off disk and makes runs faster.
- `run-pipelines` maps changed source files to spec files. `files` here matches spec files only.

## Pattern 5: checks that write files

Formatters and autocorrect write to the bind mount. Run them as the developer, or the files end up owned by root on Linux.

Shells do not export `UID`, and `GID` is not set at all, so Compose sees neither and falls back to `1000`. `run-pipelines` runs `writes: true` checks with `env UID="$(id -u)" GID="$(id -g)" docker compose ...`. Developers who run them by hand must do the same, or set both in `.env`.

```yaml
  prettier-write:
    <<: *pipelines-base
    image: node:20.17-slim
    user: "${UID:-1000}:${GID:-1000}"
    x-pipelines:
      writes: true
      # ...
```

Keep the check (no write) and the fix (write) as two services only if CI runs the check form. Otherwise one service with `writes: false` is enough.

## Pattern 6: secrets

```yaml
  snyk:
    <<: *pipelines-base
    image: snyk/snyk:ruby-3.3
    environment:
      SNYK_TOKEN: ${SNYK_TOKEN}
    x-pipelines:
      requires: [SNYK_TOKEN]
      # ...
```

Use plain `${VAR}`, never `${VAR:?message}`. Compose interpolates the whole file before it applies profiles, so a `:?` on a missing secret breaks every command: `docker compose up` for the app and every other check. `run-pipelines` skips the check when a name in `requires` is not set. Never write the value.

## Pattern 7: complexity (baseline)

Only when the linter config does not already enable complexity rules. Turn the rules on from the command line. Never edit the linter config.

```yaml
  complexity:
    <<: *pipelines-base
    extends:
      service: web
    x-pipelines:
      category: complexity
      source: suggested
      ci_version: null
      blocking: local-only
      full: npx eslint --no-config-lookup --rule 'complexity: [error, 10]' .
      changed: npx eslint --no-config-lookup --rule 'complexity: [error, 10]' {files}
      files: '\.(js|jsx|mjs|cjs)$'
      triggers: [package-lock.json]
      writes: false
      requires: []
```

Command-line forms by tool:

| Tool | Command |
|---|---|
| Ruff | `ruff check --select C901 .` (threshold: `--config 'lint.mccabe.max-complexity = 10'`) |
| ESLint | `eslint --no-config-lookup --rule 'complexity: [error, 10]'` (flat config, v9+). `--no-config-lookup` keeps the project's other rules out of this check. TypeScript files also need the parser: use lizard if that gets in the way |
| golangci-lint | v2: `golangci-lint run --enable-only gocyclo,gocognit`. v1: `golangci-lint run --disable-all -E gocyclo -E gocognit` |
| Any language (RuboCop projects included) | lizard in its own Dockerfile (pattern 3): `lizard -C 15 -w <dirs>` |

For RuboCop, prefer lizard: a `.rubocop.yml` that disables the `Metrics/` cops would need a config edit. In Step 6 the output must show the complexity rules ran. A clean run of the wrong rules is `broken`.

## Pattern 8: coverage with a minimum (baseline)

The `coverage` service runs the full suite with coverage, then a gate script fails when line coverage is under the minimum. The gate keeps the minimum out of the project's own config, so this skill never edits it.

The gate, created once at `docker/pipelines/coverage-gate.sh`:

```sh
#!/bin/sh
# Managed by build-pipelines. Fails when line coverage is below the minimum.
# Usage: coverage-gate.sh <simplecov|go|istanbul|coveragepy> <report> <minimum>
# Exit: 0 at or above the minimum, 1 below it, 2 when the report cannot be read.
# No `set -e`: a failed read must exit 2 below, never 1.
set -u
kind=$1 report=$2 min=$3
[ -f "$report" ] || { echo "coverage report not found: $report" >&2; exit 2; }
case $kind in
  simplecov)  pct=$(ruby -rjson -e 'r = JSON.parse(File.read(ARGV[0]))["result"]; puts r["line"] || r["covered_percent"]' "$report") ;;
  go)         pct=$(go tool cover -func="$report" | awk '/^total:/ { sub(/%/, "", $3); print $3 }') ;;
  istanbul)   pct=$(node -e 'console.log(require(require("path").resolve(process.argv[1])).total.lines.pct)' "$report") ;;
  coveragepy) pct=$(python -c 'import json, sys; print(json.load(open(sys.argv[1]))["totals"]["percent_covered"])' "$report") ;;
  *) echo "unknown report kind: $kind" >&2; exit 2 ;;
esac
[ -n "$pct" ] || { echo "no line coverage in $report" >&2; exit 2; }
echo "line coverage: ${pct}% (minimum ${min}%)"
awk -v p="$pct" -v m="$min" 'BEGIN { exit !(p + 0 >= m + 0) }' || { echo "coverage ${pct}% is below the minimum ${min}%"; exit 1; }
```

The service. `;` after the test command is on purpose: failing tests are the `unit-test` check's verdict. This check judges coverage only. Remove the old report first, so a crashed run cannot pass on a stale one.

```yaml
  # coverage minimum 87.4%: measured 87.46% on 2026-10-11
  coverage:
    <<: *pipelines-base
    extends:
      service: web
    depends_on: !override
      db-pipelines:
        condition: service_healthy
    environment:
      RAILS_ENV: test
      DATABASE_URL: postgres://postgres:postgres@db-pipelines:5432/app_test
    x-pipelines:
      category: coverage
      source: suggested
      ci_version: null
      blocking: local-only
      full: sh -c 'rm -f coverage/.last_run.json; bin/rails db:prepare && bundle exec rspec; sh docker/pipelines/coverage-gate.sh simplecov coverage/.last_run.json 87.4'
      changed: null
      files: null                                 # full mode only
      triggers: [Gemfile.lock, .simplecov, spec/spec_helper.rb, spec/rails_helper.rb]
      writes: false
      requires: []
```

Test command and report by runner. Write reports to `/tmp` inside the container when the runner allows it, so the run leaves nothing in the repo:

| Runner | Test command with coverage | Gate |
|---|---|---|
| RSpec, Minitest + SimpleCov | the CI test command (SimpleCov starts in the test helper) | `simplecov coverage/.last_run.json` |
| Go | `go test -coverprofile=/tmp/cover.out ./...` | `go /tmp/cover.out` |
| Jest | `npx jest --coverage --coverageReporters=json-summary --coverageDirectory=/tmp/coverage` | `istanbul /tmp/coverage/coverage-summary.json` |
| Vitest | `npx vitest run --coverage.enabled --coverage.reporter=json-summary --coverage.reportsDirectory=/tmp/coverage` | `istanbul /tmp/coverage/coverage-summary.json` |
| pytest + pytest-cov | `pytest --cov --cov-report=json:/tmp/coverage.json` | `coveragepy /tmp/coverage.json` |

Rules:

- `{min}` starts as `0` in the plan. Step 6 measures and writes the real value, rounded down to one decimal, and the comment above the service.
- A project minimum higher than the measured value wins (SimpleCov `minimum_coverage`, Jest `coverageThreshold`, `fail_under`). Use it in the gate.
- SimpleCov writes `coverage/` in the repo. Check it is in `.gitignore`. If not, say so in the report. Do not edit `.gitignore`.
- No coverage tool in the project (no SimpleCov, no pytest-cov): adding it is an app change. List it in Step 4 for approval.
- `changed: null` and `files: null`: coverage is a whole-suite number. `run-pipelines` runs it in full mode, and in changed mode only when a trigger changed. The `unit-test` check covers the changed files.

## Pattern 9: parallel tests (baseline, when needed)

Use the built-in parallel mode first. Keep the serial check, and change only its command and services.

| Runner | Parallel command | Per-worker database |
|---|---|---|
| Rails Minitest | `bin/rails test` with `parallelize(workers: :number_of_processors)` in `test_helper.rb` (app change: needs approval if missing) | Rails creates `app_test-0`, `app_test-1`, ... |
| RSpec + `parallel_tests` | `sh -c 'bundle exec rake parallel:setup && bundle exec parallel_rspec spec'` | `TEST_ENV_NUMBER` in `config/database.yml` |
| Go | `go test -p <n> ./...` (default `-p` is the CPU count) | Tests that share a DB need their own schema or `-p 1` for that package |
| Jest | `npx jest --maxWorkers=50%` | One DB per worker through `JEST_WORKER_ID` |
| Vitest | `npx vitest run --pool=forks` | One DB per worker through `VITEST_POOL_ID` |
| pytest + pytest-xdist | `pytest -n auto` | One DB per worker through `PYTEST_XDIST_WORKER` |

Rules:

- Match CI. If CI shards (a matrix over test groups), use the same tool and the same split, not a new one.
- Workers in one container share its CPU and memory. Set `cpus` on the service only if the developer asks.
- The test database service must allow one database per worker (Postgres does by default).
- The parallel run must report the same number of tests as the serial run. Fewer means tests were lost between workers.
- Coverage with parallel workers must merge the results of all workers (SimpleCov merges `.resultset.json` by default; Jest, Vitest, Go, and pytest-cov with xdist merge on their own). If the merge cannot be made to work, the `coverage` service runs the suite serially.

## Volumes

Declare the caches once, at the bottom, with a `pipelines-` prefix. Use them only for caches that a tool fills at run time (Go module cache, Trivy database), never over dependencies the image installs:

```yaml
volumes:
  pipelines-gomod:
  pipelines-trivy-cache:
```

## Creating a new compose file

If the project has no compose file, create `docker-compose.yml` with only the anchors, the pipelines services, and the volumes. Every service still has `profiles: [pipelines]`, so `docker compose up` starts nothing.
