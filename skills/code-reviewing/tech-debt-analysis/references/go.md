# Go

Use with `tech-debt-analysis` when the scope has a `go.mod` or `*.go` files. The commands are starting points. Check flags with `--help` on the installed version. Run a tool only if it is already installed. Never run `go test`, `go generate`, or `go mod tidy`.

## Skip these paths

`vendor/`, `testdata/`, files with `// Code generated` in the first lines (`*.pb.go`, `*_gen.go`, `*.gen.go`, `zz_generated*`), mocks (`mock_*.go`, `*_mock.go`, `mocks/`), `go.sum`.

Find generated files with:

```sh
git grep -lE '^// Code generated .* DO NOT EDIT' -- '*.go'
```

**Config-like, change by design:** route tables, wire files, registries of handlers. Keep them out of the hotspot list.

## Complexity proxy

1. Check `.golangci.yml` for `gocyclo`, `gocognit`, `cyclop`, `funlen`, `nestif`. The limits there are the project's thresholds. A `nolint` on them is a window (W4).
2. Read without fixing:
   - `gocyclo -top 20 .` (cyclomatic)
   - `gocognit -top 20 .` (cognitive)
   - `golangci-lint run --out-format json` with the project's config, if it is part of the pipeline. Never pass `--fix`.
3. Fall back to lines of code.

## Dead code and duplication

- `deadcode ./...` (from `golang.org/x/tools/cmd/deadcode`) lists functions that cannot be reached from `main`. Add `-test` to count code reached only by tests. It is conservative: reflection and `go:linkname` can hide callers, and it can miss some dead code. A reported function is reliable evidence. `deadcode -whylive=<pkg.Func> ./...` explains why a function is live.
- With `golangci-lint`, the `unused` linter finds unexported identifiers nobody uses. Exported identifiers in a library are the public API, not dead code.
- `dupl -t 100 .` finds duplicated blocks, if installed. Read both blocks before you call it duplicated knowledge.

## Window patterns (set C)

Use `git grep -nwE` for words and `[[:space:]]` for spaces (see the portability note in [broken windows](broken-windows.md)).

- **W2:** `TODO|FIXME|HACK|XXX` (whole word).
- **W3:** `t\.Skip(f|Now)?\(`, and `testing\.Short\(\)` guards that skip by default.
- **W4:** `//nolint`, `// nolint`, `#nosec`, `//lint:ignore`, and `issues.exclude-rules` entries in `.golangci.yml`.
- **W5:** `_ = .*err`, `_, _ =`, `recover\(\)` with no log or re-panic. An empty `if err != nil {}` spans lines: use `git grep -n -A1 'if err != nil'` and read each hit.
- **W6:** CI `continue-on-error`, `allow_failure`, commented jobs.
- **Leftovers:** `panic\("TODO`, `fmt\.Print` in non-`main` packages, `log\.Fatal` in library code.
- **Deprecated:** `// Deprecated:` on identifiers that the code still calls (`git grep` the name).

## Map a source file to its test

| Source | Test |
|---|---|
| `<dir>/<name>.go` | `<dir>/<name>_test.go`, or any `*_test.go` in the same directory (Go tests are per package) |

Check the package, not only the file. A package with tests in an external `_test` package (`package foo_test`) still counts.

## Traps

- Functions that satisfy an interface look unused to a name search. Check the interface before you call them dead.
- `init()` functions, build tags, and code behind `//go:build` may not be in your default analysis.
- Packages that are only `main` entry points can be small and still the hottest files. Judge them by churn.
- Table-driven tests make long test files. Length alone is not debt.
