# Go test analysis

Commands, smells, and mutation tools for `test-analysis`. The project's own test conventions and CI command win over everything here. Run only tools the project already uses, or ask first.

## Detect the setup

- Tests: `*_test.go` files next to the code, the `testing` package.
- `github.com/stretchr/testify` in `go.mod`: `assert` and `require`.
- `go.uber.org/mock` or `github.com/golang/mock` (gomock), or `mockery`: generated mocks.
- `net/http/httptest`: HTTP handler and client tests.
- A `test` target in `Makefile` or `Taskfile`, or a `go test` step in `.github/workflows`.
- The `go` directive in `go.mod`. Below `1.22`, the loop variable is shared across iterations (see Smells).

## Scope unit

Go tests run per package. The scope is the packages that contain the changed files (production and test). Take the unique directories from the file lists, and pass each as `./dir/...`.

## Commands

| Goal | Command |
|---|---|
| Normal run, no cache | `go test -count=1 ./dir/...` |
| Random order and race detector | `go test -race -shuffle=on -count=1 ./dir/...` |
| Replay an order | `go test -race -shuffle=<seed> -count=1 ./dir/...` (the seed prints when a shuffled run fails) |
| Repeat to find flakiness | `go test -count=3 -shuffle=on ./dir/...` |
| One test, verbose | `go test -run '^TestName$' -v -count=1 ./dir/...` |
| Coverage by function | `go test -coverprofile="$(mktemp)" ./dir/...`, then `go tool cover -func=<that file>` |

Notes:

- `-count=1` turns off the test cache. A cached pass proves nothing about the current code.
- `-race` needs cgo. If it is not available, say so in the report and run without it.
- Write the coverage profile to a temp file, not into the repo.
- If the project uses build tags for integration tests (`//go:build integration`), the normal command skips them. Say so in "Not covered".

## Smells in Go tests

Each shows a weak sample and a stronger one.

### `assert` continues after a failure

```go
// Weak: after a failed assert, the next line panics on a nil pointer and hides the cause
got, err := svc.Find(ctx, id)
assert.NoError(t, err)
assert.Equal(t, "ana", got.Name)

// Stronger: require stops the test at the first failure
got, err := svc.Find(ctx, id)
require.NoError(t, err)
require.Equal(t, "ana", got.Name)
```

### Error case checks only that an error happened

```go
// Weak: any error passes, including the wrong one
{name: "expired token", token: expired, wantErr: true}
...
if (err != nil) != tc.wantErr { t.Fatalf(...) }

// Stronger: check which error
require.ErrorIs(t, err, auth.ErrTokenExpired)
```

### Table test with only happy rows

Look at the table. Is there a row for empty input, `nil`, the boundary on both sides, a duplicate, and a denied caller? A table with five valid rows is one test, not five.

### Loop variable capture (Go below 1.22)

```go
// Bug when go.mod says go < 1.22: every parallel subtest sees the last tc
for _, tc := range tests {
	t.Run(tc.name, func(t *testing.T) {
		t.Parallel()
		check(t, tc)
	})
}

// Fix for older Go
for _, tc := range tests {
	tc := tc
	t.Run(tc.name, func(t *testing.T) { ... })
}
```

With `go 1.22` or later in `go.mod`, each iteration has its own variable, so this is not a finding.

### Assertion in another goroutine

`t.Fatal` and `require` must run in the test goroutine. In a goroutine they do not stop the test, and if the test ends first, the assertion never runs. Send the result over a channel, or use `errgroup` or `sync.WaitGroup` and assert after `Wait`.

### Sleep instead of a signal

```go
// Flaky
go worker.Start()
time.Sleep(100 * time.Millisecond)
assert.True(t, worker.Done())

// Stronger: wait for a condition, with a timeout
require.Eventually(t, worker.Done, time.Second, 10*time.Millisecond)
```

Better still: wait on a channel the code closes, or inject a fake clock.

### Shared state

- `os.Setenv` without restore. Use `t.Setenv`.
- Files in a fixed path. Use `t.TempDir()`.
- Cleanup with `defer` in a helper. Use `t.Cleanup`.
- Package-level variables changed by a test and not reset.

### Mocks

- The struct under test is mocked, or its methods are stubbed.
- A strict call-count expectation (`.Times(1)`) on an internal call. A correct refactor breaks it.
- A mock of `http.Client` or a database. A fake or `httptest.NewServer` tests more of the real path.
- An `any` matcher for every argument. The test does not check what was sent.

### Other

- A test helper with no `t.Helper()`. Failures point at the helper line, not the test line.
- `t.Skip` with no reason, or `testing.Short()` that skips the only test for the change.
- Golden files and an `-update` flag. Check the golden diff in the change, line by line.
- `assert.True(t, err == nil)`, `assert.True(t, len(x) == 3)`. Use `NoError` and `Len`. The message is better when it fails.

## Test linters

These run in `static-analysis` when the project config enables them. Do not edit config from here.

- `testifylint`: wrong or weak `testify` usage, `assert` where `require` is needed.
- `thelper`: helpers with no `t.Helper()`.
- `tparallel`: wrong use of `t.Parallel()`.
- `paralleltest`: missing `t.Parallel()`.

## Mutation tools

Use a tool only if the project already has it. Otherwise follow `references/mutation-checks.md` with hand-picked mutants.

- `gremlins` ([go-gremlins/gremlins](https://github.com/go-gremlins/gremlins)): `gremlins unleash`, with a diff mode that limits mutants to code changed against a base (`--diff origin/main`). Check the flag with `gremlins unleash --help` on the installed version.
- `go-mutesting`: no diff mode, so a whole-package run is slow and noisy. Prefer hand-picked mutants.

## Tests

The test command above is the safety net for every mutant. Mutants run in a worktree only.

## My preferences

Owner's preferences for Go tests. This section is empty until the owner fills it in. The project conventions still win when they disagree. Suggested topics:

- Preferred assertion library: standard `testing`, `testify`, or other.
- Table-driven test layout and naming.
- Mocks or fakes: when to use each.
- Policy on `t.Parallel()`.
- How many mutants to run, and which operators matter most.
- Anything to always flag in the report.
