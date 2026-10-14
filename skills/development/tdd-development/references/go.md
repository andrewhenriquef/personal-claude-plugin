# Go

Use with `tdd-development` when the work is in `*.go` files or has a `go.mod`. Project conventions and config win over this page. Commands are starting points: read the project's own first (`CLAUDE.md`, `Makefile`, `docs/pipelines.md`, CI). The red and green outputs below were run on Go 1.26.

## Commands

| Need | Command |
|---|---|
| One test | `go test ./path/to/pkg -run '^TestName$' -count=1` |
| One subtest | `go test ./path/to/pkg -run '^TestName$/^case_name$' -count=1` |
| The package | `go test ./path/to/pkg -count=1` |
| Everything | `go test ./... -count=1` |

`-count=1` turns off the test cache. Without it, a cached pass can hide that nothing ran. Add `-race` if the project's CI does. Add `-v` only when you need the test names. Prefer a `make` target or the Docker command from `docs/pipelines.md` when the project has one.

## What a red looks like

Go often gives two reds. Show both.

1. **Missing unit (build failed).** The test calls code that does not exist:

   ```
   ./add_test.go:6:12: undefined: Add
   FAIL	example.com/tdd [build failed]
   ```

   This is an acceptable first red. It is the stub exception in the rules: you may add the smallest signature that compiles, with a zero value, so the test can run.

2. **Assertion red.** After the stub (`func Add(a, b int) int { return 0 }`):

   ```
   --- FAIL: TestAdd (0.00s)
       add_test.go:7: Add(2, 3) = 0, want 5
   ```

   This is the red that proves the test checks the behavior. Compare it with the reason you wrote down.

**Not a red:** a compile error from a typo in the test, a missing import, `panic` from a nil in your test setup, a failure in `TestMain`.

## Conventions to follow

Read the neighbouring `*_test.go` files first. If there is no convention:

- Test file next to the code: `thing.go` and `thing_test.go`. For a black-box test at the seam, use the external package `package thing_test`. Use the internal package only for a reason.
- Table-driven tests with `t.Run(name, ...)` for variants of one behavior. Give each row a name that reads as a requirement. Do not put different behaviors in one table.
- `t.Helper()` in helpers. `t.Cleanup`, `t.TempDir()`, and `t.Setenv` for state.
- The standard `testing` package, and the assertion library only if it is already in `go.mod`. Do not add one.
- Failure messages with the input, the got value, and the want value: `Add(2, 3) = %d, want %d`.
- `t.Parallel()` only where the project uses it, and only for tests that share no state.

## Boundaries and fakes

- Define a small interface where the code **uses** a dependency, and pass it in. Fake it in the test with a plain struct. That is the Go form of "fake the boundary".
- HTTP servers and clients: `net/http/httptest` is real and fast. Prefer it to a mock of your own client.
- Time: inject a `func() time.Time` or a small clock interface. Never `time.Sleep` in a test.
- Do not mock your own packages. If a test needs a fake of an internal package, the seam is too deep.

## Freeze list

Add the `*_test.go` files of the slice, and any `testdata/` file (golden files, fixtures) the test reads. A golden file that is regenerated to make a test pass is a changed test: freeze it.

## Gate

At the end of each slice: the focused test, then `go vet` on the package, and the project's linter in check mode (`golangci-lint run` on the package, with the project's config, without `--fix`). If it fails, call `static-analysis`. Format with `gofmt -l` to list files, and let `static-analysis` fix them.
