# Go static analysis

Commands, autocorrect options, and rule classes for `static-analysis`. The project's own config and CI command win over everything here. Run only tools the project already uses, or ask first.

## Detect the setup

Look for, in this order:

- `.golangci.yml`, `.golangci.yaml`, `.golangci.toml`, `.golangci.json`. A `version: "2"` key means golangci-lint v2. No `version` key means v1.
- A `lint` or `check` target in `Makefile` or `Taskfile`.
- A golangci-lint step in `.github/workflows` (the action version shows the tool version).

Check the installed version with `golangci-lint --version`. v1 and v2 differ: in v2, formatters (`gofmt`, `goimports`, `gci`) live in a `formatters:` section and the `fmt` command exists. In v1, they are linters.

## Scope unit

Go tools work on packages. The scope is the packages that contain the changed files. Build the list from the scope:

```
git diff --name-only main...HEAD -- '*.go'            # branch changes
git diff --name-only -- '*.go'                         # unstaged
git diff --staged --name-only -- '*.go'                # staged
git ls-files --others --exclude-standard -- '*.go'     # new files
```

Take the unique directories (`dirname`), and pass each as `./dir/...`. Use `master` if the repo has no `main`.

## Commands

Always run with autocorrect on.

| Goal | Command |
|---|---|
| Lint with autocorrect (always) | `golangci-lint run --fix ./dir/...` |
| Format, v2 | `golangci-lint fmt ./dir/...` |
| Format check, v2 (final verify) | `golangci-lint fmt --diff ./dir/...` |
| Lint check with no edits (final verify) | `golangci-lint run ./dir/...` |
| JSON output (v2) | `golangci-lint run --output.json.path=stdout ./dir/...` |
| List configured formatters (v2) | `golangci-lint formatters` |

Notes:

- `golangci-lint run` reports and does not format. `run --fix` applies the fixes that linters support, and applies the configured formatters. Always read the diff after it.
- Not every linter can autocorrect. What `--fix` leaves is the work for Step 4.
- Do not run `golangci-lint migrate`. It edits the config.

### Fallback when the project has no golangci-lint config

Say in the report that you used the fallback. Do not add a config.

```
gofmt -w <changed files>
go vet ./dir/...
```

`gofmt -w` rewrites the files. `go vet` has no autocorrect, so fix its findings by hand. If `staticcheck` is already in the project tools or CI, run `staticcheck ./dir/...` and fix its findings by hand.

## Rules by class

Names are linters in golangci-lint. Which ones run depends on the project config. Treat this as a triage guide, not a list to enable.

| Class | Linters and what they find |
|---|---|
| Likely bug | `errcheck` (ignored error), `govet` (printf verbs, copylocks, loop variable capture, unreachable code), `staticcheck` (wrong API use, impossible conditions), `ineffassign` and `staticcheck` SA4006 (value never used), `bodyclose`, `rowserrcheck`, `sqlclosecheck` (resource not closed), `nilerr` (returns nil when err is set) |
| Manual fix | `unused` (dead code, confirm it is dead first, then delete it), `unparam`, `errorlint` (use `errors.Is` and `errors.As`, `%w` in `fmt.Errorf`), `wastedassign`, `prealloc` |
| Format | `gofmt`, `goimports`, `gci`, `gofumpt` |
| Design signal | `gocyclo`, `cyclop`, `gocognit`, `funlen`, `nestif`, `lll`. Refactor until the rule passes. Keep behavior |
| Style | `revive`, `stylecheck`, `godot` (comment endings), `misspell`, `whitespace` |
| Security | `gosec`. Fix it, and hand deeper review to `security-analysis` |

Fix the cause, not the symptom:

```go
// errcheck: error ignored
defer f.Close()

// Fix when the close error matters (writes): keep the error
defer func() {
	if cerr := f.Close(); cerr != nil && err == nil {
		err = cerr
	}
}()
```

For a read-only file, ignoring the close error can be correct. Then make the choice visible with `defer func() { _ = f.Close() }()`, and only if the project's `errcheck` settings accept it. Otherwise handle the error.

## Suppressions

We do not add suppressions. Do not write `//nolint`, `//nolint:<linter>`, or `//nolint:all`. Do not add `linters.exclusions` rules, path exclusions, or `issues` exclusions to the config. Fix the code.

Existing `//nolint` directives in the scope stay as they are, unless `nolintlint` reports one as unused. Then remove it. Mention existing ones you saw in the report.

## Tests

Run the project's test command after each group of fixes (`go test ./dir/...`, or the `Makefile` target). Run `go build ./...` when a fix changes imports or signatures.

## My preferences

Owner's preferences for Go. This section is empty until the owner fills it in. The project config still wins when it disagrees. Suggested topics:

- Which linters to run when the project has no config.
- Formatter choice: `gofmt`, `gofumpt`, `goimports`, `gci`.
- Preferred import grouping.
- How to fix `errcheck` findings (handle, wrap, or `_ =`).
- Refactor style for complexity rules (early return, extract function, table-driven).
- Anything to always flag in the report.
