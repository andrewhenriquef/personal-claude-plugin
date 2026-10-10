# Check catalog

Categories used in the inventory and in the gap analysis. Each category says what it protects, the signal that makes it apply, common tools, and the default priority.

**Priority:**

- **must**: a missing check here lets a real defect or exposure reach `main`.
- **should**: a missing check here costs review time or lets a whole class of bugs through.
- **could**: useful, but only after the must and should checks are in place.

**Tool choice order:** a tool already in the repo (dependency, config, or image) → the ecosystem default in this table → a cross-language tool. Suggest one tool per category.

Use the category names below as the `category` value in the inventory.

## Code

| Category | Protects against | Applies when | Tools by ecosystem | Default priority |
|---|---|---|---|---|
| `format` | Diff noise, style review churn | Any source code | Go: `gofmt`/`gofumpt`. Ruby: RuboCop `Layout/` or `standardrb`. JS/TS: Prettier, Biome. Python: `ruff format`, Black. Shell: `shfmt`. Terraform: `terraform fmt` | should |
| `lint` | Bug patterns, unsafe idioms | Any source code | Go: `golangci-lint`. Ruby: RuboCop with the extensions in the Gemfile. JS/TS: ESLint, Biome. Python: Ruff. Shell: ShellCheck. YAML: yamllint. Markdown: markdownlint | must |
| `type-check` | Type errors at runtime | TypeScript, typed Python, Sorbet/RBS. Go and other compiled languages get this from `build` | `tsc --noEmit`, mypy, pyright, `srb tc`, Steep | must when the config exists, could otherwise |
| `build` | Code that does not compile or package | Compiled languages, frontend bundles, Docker images, gems or packages that publish | `go build ./...`, `go vet ./...`, `npm run build`, `docker build`, `gem build` | must |

## Tests

| Category | Protects against | Applies when | Tools | Default priority |
|---|---|---|---|---|
| `unit-test` | Regressions in logic | Any source code with a test directory or framework | RSpec, Minitest, `go test ./...`, Jest, Vitest, pytest | must |
| `integration-test` | Broken contracts with DB, cache, queue, external APIs | Compose services, CI `services:`, DB config, HTTP clients | Same runners with real services. Testcontainers. Request specs | must when services exist |
| `e2e-test` | Broken user flows | Web UI or public API with a deploy target | Playwright, Cypress, Capybara system specs | could, should for a customer-facing UI |
| `coverage` | Untested new code | `unit-test` exists | SimpleCov with `minimum_coverage`, `go test -coverprofile` with a threshold, Jest `coverageThreshold`, Codecov patch status | should. Report a check with no threshold as partial |
| `flaky-test` | Order-dependent or random failures | `unit-test` exists | Random order (`--order random`, `go test -shuffle=on`), repeat runs (`-count`), `rspec --bisect` | could |
| `mutation-test` | Tests that pass without asserting | Critical domain code | mutant, go-mutesting, Stryker, mutmut | could. Never higher |

## Security

| Category | Protects against | Applies when | Tools | Default priority |
|---|---|---|---|---|
| `sast` | Injection, unsafe deserialization, auth bugs in code | Any server code | Ruby/Rails: Brakeman. Go: gosec (standalone or through golangci-lint). JS/TS: `eslint-plugin-security`, Semgrep. Python: Bandit. Cross-language: Semgrep, CodeQL | must for web or API services, should otherwise |
| `secrets-scan` | Committed credentials | Always | Gitleaks, TruffleHog, GitHub secret scanning with push protection | must |
| `dependency-audit` | Known vulnerable packages | Any lockfile | Go: `govulncheck`. Ruby: `bundler-audit`. JS: `npm audit`, `pnpm audit`, `yarn npm audit`. Python: `pip-audit`. Cross-language: OSV-Scanner, Trivy `fs` | must |
| `dependency-review` | New risky or vulnerable packages in a PR | GitHub repo with a lockfile | `actions/dependency-review-action` | should |
| `license-check` | Licenses the company cannot ship | Distributed software, or a stated license policy | `license_finder`, `go-licenses`, `license-checker`, ScanCode, Trivy `--scanners license` | could, should for distributed software |
| `sbom` | No record of what ships | Container images or packages that ship to customers | Syft, Trivy `sbom`, `cyclonedx-*` | could |
| `container-scan` | Vulnerable base images, bad Dockerfile practice | `Dockerfile*` | Lint: Hadolint. Scan: Trivy `image`, Grype | should |
| `iac-scan` | Open buckets, wide IAM, public endpoints | `*.tf`, Helm, Kubernetes manifests, CloudFormation | `terraform validate` + TFLint, Checkov, Trivy `config`, kube-linter | must when IaC deploys production, should otherwise |
| `ci-security` | Script injection and unpinned actions in CI itself | `.github/workflows/` | zizmor, actionlint, pinning actions to a commit SHA | should |

Deeper review of findings in these areas belongs to `security-analysis` and `dependency-analysis`. This skill only records which checks exist.

## Data

| Category | Protects against | Applies when | Tools | Default priority |
|---|---|---|---|---|
| `migration-safety` | Locking or rewriting tables in production, unsafe deploy order | Migration directory | Rails: `strong_migrations`. Postgres SQL: Squawk. Go/SQL: Atlas `migrate lint`. Schema drift: `db:schema:load` + compare | must when production DB is Postgres or MySQL with real traffic, should otherwise |
| `schema-consistency` | Missing constraints, indexes, foreign keys | Rails or ORM models | `database_consistency`, `active_record_doctor` | could |

Deeper review belongs to `data-and-migration-analysis`.

## Interfaces

| Category | Protects against | Applies when | Tools | Default priority |
|---|---|---|---|---|
| `api-contract` | Breaking changes for API clients | OpenAPI, protobuf, GraphQL schema in the repo | Spectral + `oasdiff breaking`, `buf lint` + `buf breaking`, GraphQL Inspector | should, must for public APIs |
| `generated-code` | Committed generated code that is stale | Code generators (`go generate`, protobuf, OpenAPI clients, `sqlc`) | Run the generator, then `git diff --exit-code` | should |

## Hygiene

| Category | Protects against | Applies when | Tools | Default priority |
|---|---|---|---|---|
| `commit-lint` | Commit history that breaks release tooling | Release tooling reads commits (semantic-release, release-please, changesets) | commitlint | could, should when release tooling exists |
| `docs-lint` | Broken links, bad Markdown | `docs/` with many pages | markdownlint, lychee, Vale | could |
| `lockfile-sync` | Manifest and lockfile out of sync | Any lockfile | `bundle install --frozen` (`BUNDLE_FROZEN=true`), `npm ci`, `go mod tidy` + `git diff --exit-code` | should |
| `performance-budget` | Bundle size or benchmark regressions | Frontend bundle, or benchmarks in the repo | size-limit, bundlewatch, `go test -bench` with benchstat | could |

## Partial coverage

A check that exists can still be a gap. Suggest tightening when:

- It runs on `push` to `main` only, and not on pull requests.
- It is `allow_failure` or `continue-on-error` with no reason in the config.
- It is not in the branch protection required checks while similar checks are.
- It runs on changed files only in CI, so old violations in touched files pass. Report this only. It can be a deliberate choice.
- Its ignore or baseline file is large (state the count).
- Its tool version is unpinned.
