# Go: confirming a root cause

Use in Steps 0 and 2 of `confirm-root-cause` when the code is Go.

Sources: [Delve](https://github.com/go-delve/delve/tree/master/Documentation/cli), [Go race detector](https://go.dev/doc/articles/race_detector), [runtime/pprof and net/http/pprof](https://pkg.go.dev/runtime/pprof), [Go diagnostics](https://go.dev/doc/diagnostics), [log/slog](https://pkg.go.dev/log/slog), [goleak](https://github.com/uber-go/goleak), and `reliability-analysis/references/go.md` in this plugin.

## Debugger: Delve

```sh
dlv test ./path/to/pkg -- -test.run '^TestName$'
```

Useful commands inside `dlv`:

- `break path/file.go:LINE` or `break pkg.Function`: set a breakpoint.
- `continue` (`c`), `next` (`n`), `step` (`s`), `stepout`: move.
- `print expr` (`p`), `locals`, `args`: inspect values.
- `stack` (`bt`): the call stack. `frame N`: move to a caller frame.
- `goroutines`, `goroutine N`: see all goroutines and switch. Use these for deadlocks and leaks.
- `condition <breakpoint> expr`: stop only when an expression is true. Use this when the bug needs the 500th call.
- `trace pkg.Function`: print a line each time the function runs, without stopping.

`dlv` needs an interactive terminal. In a non-interactive run, use a probe.

Build with `-gcflags="all=-N -l"` if the optimizer hides variables.

## Targeted probe

```go
// [DEBUG-a4f2]
slog.Debug("[DEBUG-a4f2] before total", "items", len(items), "sum", sum)
```

- Use the repo's logger. If it uses `slog`, pass the context (`slog.DebugContext(ctx, ...)`).
- For a quick local probe, `fmt.Fprintf(os.Stderr, "[DEBUG-a4f2] ...\n", ...)` is fine, and is removed after.
- Run tests with `-v` and `-count=1` to see the output.

## Races and ordering

```sh
go test -race -run '^TestName$' -count=30 ./path/to/pkg
```

- A race report names two stack traces: the read and the write. It is strong evidence for a race **between those two lines**. It is not evidence that this race causes the user's symptom: check that the symptom stops when the race is removed (counterfactual patch).
- A clean `-race` run proves nothing. It reports only races that happened in that run.
- To test a "happens before" claim, add a channel or a `sync.WaitGroup` barrier at the point in the **test**, and see whether the failure changes.

## Goroutine and memory evidence

- **Leaks:** `go.uber.org/goleak` in a test (`defer goleak.VerifyNone(t)`) fails when goroutines remain. Use it if the repo has it. Or print `runtime.NumGoroutine()` before and after N calls.
- **Profiles:** `go test -run '^TestName$' -cpuprofile cpu.out -memprofile mem.out` then `go tool pprof -top cpu.out`. Compare against a baseline.
- **Traces:** `go test -trace trace.out` then `go tool trace trace.out` for scheduling and blocking.
- **Deadlock dump:** send `SIGQUIT` to a hung test binary, or run with `GOTRACEBACK=all`, to print all goroutine stacks.

## Errors

- `errors.Is` / `errors.As` show the real cause when errors are wrapped. A probe that prints `fmt.Sprintf("%+v", err)` (with a stack package) or `errors.Unwrap` chain tells you where the error came from.
- A swallowed error (`_ = f()`, `if err != nil { return nil }`) is a classic cause. Search the call chain for them. A probe on the discarded `err` confirms.

## Time

- `time.Now()` inside the code path makes the bug depend on the clock. A probe that prints the instant used shows it. To test the boundary, run with the clock injected (see [reproduce-bug go.md](../../reproduce-bug/references/go.md)).

## Cleanup

```sh
git grep -n --untracked -I "DEBUG-a4f2" -- . ':!docs/<slug>/'
```

must return nothing. Run `gofmt -l .` on the files you touched, to be sure the cleanup left them formatted.
