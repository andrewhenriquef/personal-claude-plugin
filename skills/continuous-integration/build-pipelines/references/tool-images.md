# Tool images

Where each tool runs, which version to pin, and how to tell a working check from a broken one. Image names are a starting point. Always confirm the tag with `docker manifest inspect <image:tag>` before you write it. If the image moved or the tag is missing, use a Dockerfile (pattern 3 in compose-patterns.md).

## Versions

Which version to pin:

| Check | Pin |
|---|---|
| CI already runs it | The CI version. Find it in the CI step (`version:` input of the action, the `image:`, or the install command) |
| New check | The latest stable release, looked up now with the commands below |
| Tool from the app lockfile | The lockfile version. Never bump it |
| Base image of a new Dockerfile | The project runtime version |

For every pinned item, also look up the latest stable release. Step 8 reports the ones that are behind.

**Stable** means a released version with no pre-release marker (`-rc`, `-beta`, `-alpha`, `.pre`, `-dev`, `-next`, `-canary`), not a moving tag (`latest`, `edge`, `nightly`, `main`, `stable`), and not a draft. Compare by version number, not by date: the newest upload can be a patch for an old major.

Look up the latest stable release. Never write a version from memory.

| Source | Command | Field |
|---|---|---|
| GitHub releases (most standalone tools) | `gh api repos/<owner>/<repo>/releases/latest --jq .tag_name`, or `curl -fsSL https://api.github.com/repos/<owner>/<repo>/releases/latest` | `tag_name`. GitHub's "latest" skips drafts and pre-releases |
| RubyGems | `curl -fsSL https://rubygems.org/api/v1/gems/<gem>.json` | `version` |
| npm | `curl -fsSL https://registry.npmjs.org/<package>/latest` | `version`. Check it has no pre-release marker |
| PyPI | `curl -fsSL https://pypi.org/pypi/<package>/json` | `info.version` |
| Go modules | `curl -fsSL https://proxy.golang.org/<module>/@latest` | `Version`. Write capital letters in the module path as `!` plus the lowercase letter |
| Docker Hub image | `curl -fsSL 'https://hub.docker.com/v2/repositories/<namespace>/<repo>/tags?page_size=100&ordering=last_updated'` (official images: namespace `library`; add `&name=<prefix>` to filter, for example `1.23` for the latest Go 1.23 patch) | `results[].name`. Keep exact version tags only, take the highest |

Then:

1. Map the release to the image tag. Release `v8.21.2` can be tag `v8.21.2` or `8.21.2`, and some images add a suffix (`-alpine`). Use the form in the image column below.
2. Confirm the tag with `docker manifest inspect <image:tag>`. An image can lag the release by hours. If the tag is missing, use the newest stable tag that exists and say why.
3. A new major version can change the config format (golangci-lint v1 to v2, ESLint 8 to 9). For a new check, write the config for that major. For an existing check, flag the major jump in the Outdated report.
4. If a lookup fails (no network, rate limit), say so and ask the user. Never guess.

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
| lizard (complexity) | `python:<v>-slim` | `pip install lizard==<v>` |
| license_finder | the app Ruby image | `gem install license_finder -v <v>` |

## Reading a result

Step 6 of the skill classifies each run as `pass`, `findings`, or `broken`. Read the exit code **and** the output. Neither is enough alone.

- `pass`: exit 0, and the output shows the tool checked something: a file count, an example count, a summary line. Exit 0 with nothing checked is `broken` (wrong mount, path, or pattern).
- `findings`: the documented findings exit code, and findings in the tool's own format in the output.
- `broken`: everything else, including any exit 125 (Docker could not start the container), 126 (command not executable), or 127 (command not found).

Exit codes of common tools:

| Tool | pass | findings | broken | Output that shows findings |
|---|---|---|---|---|
| RuboCop, Standard | 0 | 1 | 2 | `N files inspected, M offenses detected` |
| ESLint | 0 | 1 | 2 | `file:line:col  error  <message>  <rule>`, `✖ N problems` |
| Prettier `--check` | 0 | 1 | 2 | `[warn] <file>`, `Code style issues found` |
| Ruff | 0 | 1 | 2 | `file:line:col: <code> <message>`, `Found N errors` |
| golangci-lint | 0 | 1 | 3 and higher | `file:line:col: <message> (<linter>)` |
| ShellCheck | 0 | 1 | 2, 3, 4 | `In <file> line N:` and `SC<code>` |
| Hadolint | 0 | 1 | other | `<file>:N DL<code>` or `SC<code>` |
| actionlint | 0 | 1 | 2, 3 | `file:line:col: <message> [<rule>]` |
| markdownlint-cli2 | 0 | 1 | 2 | `file:line <rule>` |
| Semgrep `--error` | 0 | 1 | 2 and higher | `N Code Findings` |
| Brakeman | 0 | 3 | any other non-zero (errors, no Rails app found) | `== Warnings ==`, `Security Warnings: N` |
| govulncheck | 0 | 3 | any other non-zero | `Vulnerability #N: GO-...` |
| RSpec | 0 | 1 | 1 with load errors | Findings: `N examples, M failures`. Broken: `An error occurred while loading`, `errors occurred outside of examples`, `0 examples` |
| `go test` | 0 | 1 | 1 with setup errors | Findings: `--- FAIL:`. Broken: `[setup failed]`, a module download error. A compile error in the project's code is a finding |
| Jest, Vitest | 0 | 1 | 1 with no tests run | Findings: `Tests: N failed`. Broken: `No tests found`, a config error |
| Gitleaks | 0 | 1 | 1 with an error message | Findings: `leaks found: N`. Broken: `fatal`, `ERR` before any scan line |
| bundler-audit | 0 | 1 | 1 with an error message | `Vulnerabilities found!` |
| npm audit | 0 | 1 | 1 with an error message | `N vulnerabilities` |
| Trivy | 0 | 0, or the `--exit-code` value | 1 with an error message | A vulnerability table. Without `--exit-code`, Trivy exits 0 even with findings: classify from the table |
| `tsc --noEmit` | 0 | 1, 2 | 3, 4, or no `error TS` line |
| lizard `-w` | 0 | non-zero with `warning:` lines | non-zero with no `warning:` line |
| `coverage-gate.sh` (pattern 8) | 0 | 1 (below the minimum) | 2 (report missing, unreadable, or older than this run) | `file(line,col): error TS<code>` |

For a tool not in this table, read its docs for the exit codes before you classify, and say which doc you used.

A finding is a fact about the code, not about your setup. Never fix it here. A broken run is a fact about your setup. Fix it here.

## Reading coverage

The coverage gate (pattern 8 in compose-patterns.md) reads the report the test check wrote, and prints `line coverage: <pct>% (minimum <min>%)`. Step 6 runs it once with minimum `0` to measure, then writes the minimum. It exits 2 on a missing report, or on one older than `PIPELINES_SINCE`. Line coverage is the number used everywhere: SimpleCov `result.line` (older versions `result.covered_percent`), the Go `total:` line of `go tool cover -func`, Istanbul `total.lines.pct`, coverage.py `totals.percent_covered`.

## Network

Some checks need network on every run (advisory databases, rule registries, link checks). They work in Docker by default. Say in the report which checks need network, because they fail offline.
