# Tool images

Where each tool runs, and how to smoke-test it. Image names are a starting point. Always confirm the tag with `docker manifest inspect <image:tag>` before you write it. If the image moved or the tag is missing, use a Dockerfile (pattern 3 in compose-patterns.md).

Pin the tag to the version CI uses. Find it in the CI step (`version:` input of the action, the `image:`, or the install command) or in the lockfile.

## Runs in the app image

These tools come from the project's own dependencies. Run them in the app image (pattern 1), so the version is the lockfile version.

| Tool | Version command | Notes |
|---|---|---|
| RuboCop, Standard | `bundle exec rubocop --version` | Extensions load from the Gemfile |
| RSpec, Minitest | `bundle exec rspec --version` | Needs test services (pattern 4) |
| Brakeman | `bundle exec brakeman --version` | If not in the Gemfile, use `presidentbeef/brakeman:<v>` |
| bundler-audit | `bundle exec bundle-audit version` | Needs network to update the advisory DB (`bundle-audit update`) |
| strong_migrations, database_consistency, active_record_doctor | `bundle exec rails runner 'puts StrongMigrations::VERSION'` | Needs the test database |
| ESLint, Prettier, Biome, `tsc`, Jest, Vitest | `npx <tool> --version` | Use the project's package manager (`pnpm exec`, `yarn`) |
| Playwright | `npx playwright --version` | Use `mcr.microsoft.com/playwright:v<version>-jammy` as the base, matching the package version |
| `go test`, `go vet`, `gofmt` | `go version` | Use `golang:<version from go.mod or CI>` |
| pytest, Ruff, mypy, Bandit, pip-audit | `<tool> --version` | In the app image if they are dev dependencies. Otherwise a `python:<v>-slim` Dockerfile |

## Official tool images

Standalone tools. Set `entrypoint: []` and call the binary by name.

| Tool | Image | Version command | Notes |
|---|---|---|---|
| golangci-lint | `golangci/golangci-lint:v<v>` | `golangci-lint version` | Mount the Go module cache. v1 and v2 configs differ: match the CI major |
| Gitleaks | `zricethezav/gitleaks:v<v>` | `gitleaks version` | Also `ghcr.io/gitleaks/gitleaks`. Needs `.git` in the mount |
| TruffleHog | `trufflesecurity/trufflehog:<v>` | `trufflehog --version` | |
| Trivy | `aquasec/trivy:<v>` | `trivy --version` | Cache volume at `/root/.cache/trivy`. Image scans need the Docker socket mounted read-only |
| Grype | `anchore/grype:v<v>` | `grype version` | |
| Syft | `anchore/syft:v<v>` | `syft version` | |
| Hadolint | `hadolint/hadolint:v<v>-alpine` | `hadolint --version` | The plain tag has no shell |
| ShellCheck | `koalaman/shellcheck-alpine:v<v>` | `shellcheck --version` | The `koalaman/shellcheck` tag has no shell |
| Semgrep | `semgrep/semgrep:<v>` | `semgrep --version` | Formerly `returntocorp/semgrep`. Rule packs from the registry need network |
| OSV-Scanner | `ghcr.io/google/osv-scanner:v<v>` | `osv-scanner --version` | |
| Checkov | `bridgecrew/checkov:<v>` | `checkov --version` | |
| TFLint | `ghcr.io/terraform-linters/tflint:v<v>` | `tflint --version` | `tflint --init` needs network for plugins |
| Terraform | `hashicorp/terraform:<v>` | `terraform version` | For `fmt -check` and `validate` |
| kube-linter | `stackrox/kube-linter:v<v>` | `kube-linter version` | |
| actionlint | `rhysd/actionlint:<v>` | `actionlint -version` | |
| buf | `bufbuild/buf:<v>` | `buf --version` | `buf breaking` needs the base branch: mount `.git` |
| Spectral | `stoplight/spectral:<v>` | `spectral --version` | |
| oasdiff | `tufin/oasdiff:v<v>` | `oasdiff --version` | Needs the base spec: `git show main:<path>` into a temp file first |
| lychee | `lycheeverse/lychee:<v>` | `lychee --version` | Needs network |
| markdownlint-cli2 | `davidanson/markdownlint-cli2:v<v>` | `markdownlint-cli2 --help` (first line prints the version) | |

## Needs a Dockerfile

No maintained official image, or the tool is a package. Write `docker/pipelines/Dockerfile.<check-id>` (pattern 3).

| Tool | Base image | Install |
|---|---|---|
| govulncheck | `golang:<v>` | `go install golang.org/x/vuln/cmd/govulncheck@v<v>` |
| gosec (outside golangci-lint) | `golang:<v>` | `go install github.com/securego/gosec/v2/cmd/gosec@v<v>` |
| go-licenses | `golang:<v>` | `go install github.com/google/go-licenses@v<v>` |
| Squawk | `node:<v>-slim` | `npm install -g squawk-cli@<v>` |
| commitlint | `node:<v>-slim` | `npm install -g @commitlint/cli@<v> @commitlint/config-conventional@<v>` |
| zizmor | `python:<v>-slim` | `pip install zizmor==<v>` |
| yamllint | `python:<v>-slim` | `pip install yamllint==<v>` |
| license_finder | the app Ruby image | `gem install license_finder -v <v>` |

## Network

Some checks need network on every run (advisory databases, rule registries, link checks). They work in Docker by default. Say in the report which checks need network, because they fail offline.
