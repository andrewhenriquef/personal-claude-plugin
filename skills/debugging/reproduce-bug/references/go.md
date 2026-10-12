# Go: reproducing a bug

Use in Steps 0, 2, 4, and 5 of `reproduce-bug` when the code is Go (`go.mod`, `*.go`).

Sources: [go test flags](https://pkg.go.dev/cmd/go#hdr-Testing_flags), [Go testing package](https://pkg.go.dev/testing), [Go race detector](https://go.dev/doc/articles/race_detector), [Go fuzzing](https://go.dev/doc/security/fuzz/), [Go subtests and table tests](https://go.dev/blog/subtests), and the conventions in `reliability-analysis/references/go.md` of this plugin.

## Run one test, uncached

```sh
go test -run '^TestName$' -count=1 -v ./path/to/pkg
```

- `-run` takes a regular expression. Anchor it. `-run TestFoo` also runs `TestFooBar`.
- `-count=1` turns off the test result cache. Without it, a cached pass hides a flaky failure.
- Subtests: `-run '^TestName$/^case_name$'`.
- `-failfast` stops at the first failure.

## Write the test

- Put it in the package's `_test.go` file next to the code, or in a new `_test.go` file in the same package. Do not edit an existing test.
- Use a **table test** with `t.Run` when the bug depends on input. Add one row for the failing case.
- Assert with the repo's style (`testing` only, or `testify` if the repo uses it). Read the failure message you will get: name expected and actual values.
- Use `t.Helper()` in helpers so the failure points at the test line.
- Do not use `t.Skip` or `t.Fatal` to hide a failure.
- Pin time with an injected clock. Do not call `time.Now()` in the code path from the test. If the code calls it directly, that is a finding about the seam. Use the smallest change that fits the repo: a test that sets the value in a field, or a function variable the code already exposes.
- Isolate files with `t.TempDir()` and environment with `t.Setenv`.

## Flaky and concurrent bugs

```sh
go test -run '^TestName$' -count=30 -race ./path/to/pkg
```

- `-count=N` repeats the test N times in one run. Record how many failed.
- `-race` turns on the race detector. A race report is a finding, not a proof of the user's symptom: keep the assertion on the symptom too. The race detector reports only races that happen in that run.
- `-shuffle=on` randomises the order of tests and benchmarks. Go prints the seed (`-test.shuffle <seed>`). Re-run with `-shuffle=<seed>` to repeat a failing order.
- `-cpu 1,2,4` runs with different `GOMAXPROCS` values.
- Raise the rate: run with `t.Parallel()`, start more goroutines, shrink a timing window with a short `time.Sleep` or a channel barrier, use a small buffer.
- To find a test that leaks state, run the suite with `-shuffle=on` and `-count=1`, then reduce the failing order.

Newer Go versions have the `testing/synctest` package, which runs code with a fake clock inside a bubble. Use it for time-dependent concurrent code when the project's Go version supports it.

## Property and fuzz loops

```sh
go test -fuzz=FuzzName -fuzztime=30s ./path/to/pkg
```

- Write a `FuzzName(f *testing.F)` with `f.Add(...)` for known inputs and an invariant in `f.Fuzz`.
- A failing input is saved under `testdata/fuzz/FuzzName/`. That file is the reproduction: `go test -run '^FuzzName$' ./path/to/pkg` replays it.
- Fuzz runs write files into the repo. Leave them uncommitted, and mention them in the report.

## Bisect

```sh
#!/bin/sh
go build ./... || exit 125
go test -run '^TestName$' -count=1 ./path/to/pkg
```

`go test` exits `1` when a test fails, which git reads as bad. A build failure also exits non-zero, so check the build first and exit `125`. See [minimise.md](minimise.md).

## Other loops

- **HTTP:** `go run ./cmd/<app>` and `curl`, or `httptest.NewServer` / `httptest.NewRecorder` in a test (this is the better seam).
- **Replay a payload:** unmarshal the redacted JSON into the request type and call the handler with `httptest.NewRequest`.
- **Database:** use the repo's test database setup. Do not point a test at a shared database.
- **Logs:** if the repo uses `log/slog`, a test handler that records entries lets you assert on a log line.

## Common traps

- A cached pass: forgot `-count=1`.
- `-run` matches more tests than intended: anchor the pattern.
- A data race in the **test** (a goroutine writes a variable the test reads) makes the red a race in the test, not in the code.
- A test that passes because the failing goroutine outlives the test and its panic is lost: wait on it, or use `t.Cleanup`.
