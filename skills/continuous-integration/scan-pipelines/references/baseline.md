# Minimum baseline

The checks every project must run. `scan-pipelines` reports each item as met, partial, or missing. `build-pipelines` sets up every item that is not met. A project with a missing item does not meet the baseline, whatever else it runs.

Baseline items are always priority `must` in the scan, even when the catalog default is lower.

## Items

| # | Item | Category | Applies when | Met when |
|---|---|---|---|---|
| 1 | Lint | `lint` | Any source code | A linter runs on every language with source code in the repo |
| 2 | Complexity | `complexity` | Any source code | Complexity rules run: in the linter (enabled in its config) or as a separate tool |
| 3 | Security: code | `sast` | Any source code | A SAST tool runs on the code |
| 4 | Security: secrets | `secrets-scan` | Always | A secrets scanner runs on the repo |
| 5 | Dependency audit | `dependency-audit` | Any lockfile | An audit runs for every lockfile in the repo |
| 6 | Unit tests | `unit-test` | Any source code | A test suite runs, and it has at least one test |
| 7 | Integration tests | `integration-test` | The app uses a database, cache, queue, or search service (compose services, CI `services:`, DB config) | Tests run against the real services, not mocks |
| 8 | Parallel tests | property of items 6 and 7 | **Needed** (see below) | The suite runs in parallel workers or shards |
| 9 | Coverage with a minimum | `coverage` | Item 6 applies | Coverage is measured and the run fails below a minimum that is at least the current coverage |

One check can meet several items. RSpec with request specs against the test database can meet 6 and 7. golangci-lint with `gosec` and `gocyclo` enabled can meet 1, 2, and 3. Cite the config line that shows it.

## Item rules

### Complexity

- **In the linter** when its config enables complexity rules: RuboCop `Metrics/CyclomaticComplexity`, `Metrics/PerceivedComplexity`, `Metrics/AbcSize`. golangci-lint `gocyclo`, `gocognit`, `cyclop`. ESLint `complexity`. Ruff `C901`. Cite the config line.
- **Not in the linter:** the scan suggests a separate `complexity` check. `build-pipelines` turns the rules on through the command line, without editing the linter config (`ruff check --select C901`, `eslint --rule 'complexity: [error, 10]'`, `golangci-lint run --enable-only gocyclo,gocognit` on v2, `--disable-all -E gocyclo -E gocognit` on v1). If the linter cannot do it from the command line, use lizard (`lizard -C 15 -w`), which covers most languages.
- Thresholds: the tool's default or recommended value. Existing code over the threshold is findings, which is the check working. The report counts them as a backlog.

### Unit tests

- No tests in the repo: the item is missing, and `build-pipelines` cannot fix it. A service with no tests to run is `broken` ("0 examples"). Report it as **Baseline not met: no tests**, and point to the TDD skills.

### Integration tests

- The test services must match production: same engine and major version as CI `services:`, or as the app's compose file.
- A suite that mocks every call to the database or cache does not meet the item. Say which files show it.

### Parallel tests: when needed

Parallel is **needed** when either is true:

- CI already runs the suite in parallel or in shards (a matrix over test groups, `parallel_tests`, Knapsack, `parallelize` in `test_helper.rb`, `pytest -n`, `--shard`). Local must run the same way.
- The serial full run takes more than 5 minutes. The scan can only guess this from the number of test files and the CI test job duration (`gh api repos/{owner}/{repo}/actions/runs/<id>/jobs`, GET, when `gh` is authenticated). `build-pipelines` measures it in Step 6.

When parallel is not needed, the item is met with "not needed" and the reason.

Parallel tools by ecosystem, built-in first:

| Ecosystem | Built-in | Needs a dependency |
|---|---|---|
| Rails Minitest | `parallelize(workers: :number_of_processors)` | — |
| RSpec | — | `parallel_tests` (`parallel_rspec`), or the `turbo_tests` gem |
| Go | Packages run in parallel by default (`-p`); `t.Parallel()` inside a package | — |
| Jest, Vitest | Workers by default (`--maxWorkers`, `--pool`) | — |
| pytest | — | `pytest-xdist` (`-n auto`) |

Each worker needs its own database. Rails `parallelize` creates them. `parallel_tests` needs `TEST_ENV_NUMBER` in `config/database.yml`.

### Coverage minimum

- **The minimum is the current coverage.** `build-pipelines` measures line coverage from a full run of the suite and sets the minimum to that value, rounded down to one decimal (87.46% becomes 87.4%).
- **Never lower an existing minimum.** If the project already has a minimum higher than the current coverage, keep it. If it is lower, the local check uses the current coverage, and the report suggests raising the project minimum.
- **The scan cannot measure coverage** (it is read-only). It reports: no coverage (missing), coverage with no minimum (partial), or coverage with a minimum of N% (met, to be checked against the current value by `build-pipelines`).
- With parallel tests, coverage must merge the results of all workers. If it cannot, the coverage check runs the suite serially.

## Report shape

The scan and the build report the baseline the same way:

```
### Baseline: <met | not met (N missing, M partial)>
| # | item | status | runs in | check-id | evidence or reason |
|---|---|---|---|---|---|
| 1 | lint | met | CI + local | rubocop | .github/workflows/ci.yml:42, docker-compose.yml:88 |
| 2 | complexity | partial | CI + local | rubocop | Metrics cops disabled in .rubocop.yml:12 |
| 8 | parallel tests | not needed | — | — | serial full run 2m10s, CI not sharded |
| 9 | coverage | met | local only | coverage | minimum 87.4% (current 87.46%), docker-compose.yml:140 |
```

`runs in`: `CI`, `local only`, or `CI + local`. An item met `local only` meets the baseline on the laptop but does not gate merges: `github-pipelines` adds it to CI.

Status values: `met`, `partial`, `missing`, `not needed` (item 8 only), `not applicable` (the "applies when" signal is absent, with the evidence of absence).
