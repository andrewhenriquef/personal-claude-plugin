# Selection rules

How `run-pipelines` turns changed files into commands.

## Matching

- `files` is a regex on repo-relative paths. Match with extended regex (`grep -E`). An empty match list means the check has nothing to do in changed mode.
- `triggers` is a list of exact repo-relative paths. A path that ends with `/` matches anything under that directory.
- Check triggers against all changed paths, deleted ones included. A deleted tool config is a trigger.

## Placeholders

| Placeholder | Replaced by | Use |
|---|---|---|
| `{files}` | The matching files, space-separated, repo-relative | Linters, formatters, file scanners, test runners that take files |
| `{dirs}` | The unique directories of the matching files, as `./dir`, space-separated (`.` for the root) | Go: `go test {dirs}`, `go vet {dirs}`, `golangci-lint run {dirs}` |

Quoting:

- If the command is plain arguments, pass each path as its own argument.
- If the command is `sh -c '...'`, the paths sit inside the outer single quotes, so a plain `'path'` closes them. Write each path as `'\''path'\''` (the inner shell sees `'path'`). A single quote inside a path becomes `'\''\'\'''\''`. Paths with no space, quote, or shell character can go in as they are.
- If there are more than 500 paths, run the command in batches of 500. All batches must pass.

## Mapping source files to tests

For `unit-test` and `integration-test` checks, `files` matches test files. Add the tests for the changed source files before you match:

| Stack | Source file | Test file |
|---|---|---|
| RSpec | `app/<path>/<name>.rb` | `spec/<path>/<name>_spec.rb` |
| RSpec | `lib/<path>/<name>.rb` | `spec/lib/<path>/<name>_spec.rb` |
| RSpec request specs | `app/controllers/<path>/<name>_controller.rb` | also `spec/requests/<path>/<name>_spec.rb` |
| Minitest | `app/<path>/<name>.rb` | `test/<path>/<name>_test.rb` |
| Go | `<dir>/<name>.go` | the package: `{dirs}` covers it |
| Jest, Vitest | `src/<path>/<name>.ts` | `src/<path>/<name>.test.ts`, `src/<path>/<name>.spec.ts`, `src/<path>/__tests__/<name>.test.ts` |
| pytest | `<pkg>/<path>/<name>.py` | `tests/<path>/test_<name>.py` |

Rules:

- Add a mapped test only if the file exists.
- A changed test file runs as it is.
- A changed file under `spec/support/`, `spec/factories/`, `test/fixtures/`, `conftest.py`, `spec_helper.rb`, `rails_helper.rb`, or `test_helper.rb` affects many tests. Treat it as a trigger: run `full`.
- A source file with no mapped test goes to "Not covered" in the report. Do not search for a test by content.
- If the project has its own mapping (a `Guardfile`, a test-impact tool), use it instead and say so.

## Run order

Cheap and fast first, so the report fills quickly:

1. `format`, `lint`, `type-check`, `commit-lint`, `docs-lint`
2. `secrets-scan`, `sast`, `ci-security`, `iac-scan`
3. `dependency-audit`, `dependency-review`, `license-check`, `lockfile-sync`
4. `build`, `generated-code`, `api-contract`
5. `container-scan`, `sbom`
6. `migration-safety`, `schema-consistency`
7. `unit-test`, `coverage`, `flaky-test`
8. `integration-test`, `e2e-test`, `performance-budget`, `mutation-test`

Within a group, `blocking: required` first, then by `id`.

## Next skill per failure

| Category | Next |
|---|---|
| `format`, `lint`, `type-check` | `static-analysis` |
| `sast`, `secrets-scan`, `ci-security`, `iac-scan` | `security-analysis`. For a leaked secret: rotate it first, then remove it from history |
| `dependency-audit`, `dependency-review`, `license-check`, `lockfile-sync`, `container-scan`, `sbom` | `dependency-analysis` |
| `migration-safety`, `schema-consistency` | `data-and-migration-analysis` |
| `unit-test`, `integration-test`, `e2e-test`, `flaky-test` | Debug the failing test first. `test-analysis` when the question is whether the tests are right |
| `coverage`, `mutation-test` | `test-analysis` |
| `performance-budget` | `performance-analysis` |
| `build`, `generated-code`, `api-contract`, `commit-lint`, `docs-lint` | Fix by hand, from the log |
| any `error` | `build-pipelines` if the service or image is wrong. Otherwise fix the environment (Docker, network, secrets) |
