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

For standalone tools. Pin the tag to the CI version.

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

When no image fits. Base it on the CI runtime image. Pin the tool version.

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

## Volumes

Declare the caches once, at the bottom, with a `pipelines-` prefix. Use them only for caches that a tool fills at run time (Go module cache, Trivy database), never over dependencies the image installs:

```yaml
volumes:
  pipelines-gomod:
  pipelines-trivy-cache:
```

## Creating a new compose file

If the project has no compose file, create `docker-compose.yml` with only the anchors, the pipelines services, and the volumes. Every service still has `profiles: [pipelines]`, so `docker compose up` starts nothing.
