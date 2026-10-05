# Go reliability analysis

Tools, commands, and Go-specific traps for `reliability-analysis`. The project's own conventions and tool config win over everything here. Run only tools the project already uses, or ask first.

## Detect the setup

- `go.mod` for the module and the Go version. Some traps depend on the version (loop variables, timers).
- `.golangci.yml` and which error and concurrency linters it enables.
- Resilience libraries: `cenkalti/backoff`, `avast/retry-go`, `hashicorp/go-retryablehttp`, `sony/gobreaker`, `failsafe-go/failsafe-go`, `golang.org/x/sync/errgroup`, `golang.org/x/time/rate`.
- Error helpers: `pkg/errors`, `samber/oops`, `cockroachdb/errors`, `hashicorp/go-multierror`.
- Logging: `log/slog`, `zap`, `zerolog`, `logrus`.
- Datadog (the default stack): `github.com/DataDog/dd-trace-go/v2`, `github.com/DataDog/datadog-go` (DogStatsD), `orchestrion.tool.go`, and the `DD_*` variables in deploy config. See `datadog.md` for the full setup checks.
- Other metrics and tracing: `prometheus/client_golang`, `go.opentelemetry.io/otel`, `statsd`.
- Error trackers: `getsentry/sentry-go`, `bugsnag`, `rollbar`.
- Leak and race tools in tests: `go.uber.org/goleak`, the `-race` flag in the `Makefile` or CI.
- The shared HTTP client or client factory, and the `http.Server` setup (its timeouts).
- The job or consumer library: `asynq`, `river`, `machinery`, a Kafka, NATS, or SQS client.

## Scope unit

Go tools work on packages. The scope is the packages that contain the changed files. Pass each as `./dir/...`. See `static-analysis` (section "Scope unit") for the commands that build the list.

## Read-only linter run

Error and concurrency linters are candidate generators. Run them without `--fix` and without editing the config. `--enable-only` limits the run to the named linters, and their settings still come from the project config.

```
golangci-lint run --enable-only=errcheck,errorlint,wrapcheck,nilerr,contextcheck,noctx,bodyclose,sqlclosecheck,rowserrcheck,govet ./dir/...
```

- `errcheck`: an error value that the code does not check.
- `errorlint`: error comparison with `==` or type assertion where `errors.Is` or `errors.As` is needed, and `fmt.Errorf` that uses `%v` where `%w` is meant.
- `wrapcheck`: an error returned from another package without wrapping. It is noisy in code that already wraps at a boundary, so apply the repo's practice first.
- `nilerr`: code that returns `nil` when an error is not `nil`.
- `contextcheck`: a function that gets a `context` but passes a new one to a callee.
- `noctx`: an HTTP request built without a `context`.
- `bodyclose`, `sqlclosecheck`, `rowserrcheck`: a response body, `sql.Rows`, or `sql.Stmt` that is not closed, and `rows.Err()` not checked.
- `govet` includes `lostcancel` (a `cancel` function that is never called), `copylocks` (a mutex copied by value), and `loopclosure`.
- If a linter is not in your golangci-lint version or config, skip it. Do not edit the config. List it under "Linter rules to consider".

How to read the results: each hit is a pattern. Apply the exclusions in `reliability-checks.md` and trace the failure. `errcheck` on `defer f.Close()` for a read-only file is not a finding. `errcheck` on `Close` of a file that the code wrote is one: buffered data can fail at close.

## Prove it

Write outputs to a temporary directory, not into the repo: `tmp=$(mktemp -d)`.

| Goal | Command |
|---|---|
| Race detector on the covering tests, repeated | `go test -race -count=5 -run '<regex>' ./dir/...` |
| Shuffle test order to expose hidden state | `go test -shuffle=on -count=3 ./dir/...` |
| Timeout on a stuck test | add `-timeout 60s` so a blocked goroutine ends the run with a stack dump |
| Leak check | `goleak.VerifyNone(t)` in a test, or `goleak.VerifyTestMain(m)`, if the project already imports `goleak` |
| Goroutine count before and after | `runtime.NumGoroutine()` in a throwaway test, with a short wait for goroutines to end |
| Vet checks | `go vet ./dir/...` |

Notes:

- `-race` needs cgo on most platforms, and it slows the run and uses more memory. Run it on the package, not the whole repository.
- A report names two stacks (the conflicting write and read). Read both before you name the shared variable.
- To force a timeout or a slow dependency, use `net/http/httptest` with a handler that sleeps or blocks, or a listener that accepts and never replies. Set a short deadline in the test.
- To force an error, pass a fake that implements the interface the code takes. Do not patch the real dependency.
- Do not run `go test -race` on a path that talks to a shared database or a real provider. Use the project's local test setup.

## Go traps

### Error handling

```go
// Cause is lost. The caller cannot use errors.Is, and the log has no operation
if err != nil {
	return fmt.Errorf("save failed: %v", err)
}

// Keeps the cause and adds context
if err != nil {
	return fmt.Errorf("save order %s: %w", orderID, err)
}
```

- `%v` or `%s` in `fmt.Errorf` instead of `%w`: the chain breaks, and `errors.Is` and `errors.As` fail upstream.
- `if err != nil { log.Error(err) }` and then the code goes on as if nothing happened.
- The single handling rule: handle an error once. Log it or return it, not both at every layer. Log at the layer that decides what happens next.
- `_ = something()` on an operation that can fail and that matters.
- `err` shadowed by `:=` in an inner scope, so the outer `err` stays `nil` and the function returns success.
- A function that returns `(T, error)` where the caller uses `T` before it checks `err`.
- Comparing errors with `==` against a wrapped error. Use `errors.Is`.
- `panic` for an expected failure (bad input, a failed call). Return an error.
- `recover()` that swallows a panic with no log, in a place that must stop. Use it at a boundary (a request, a worker) to log and keep the process up, and always re-raise or report.
- A panic in a goroutine the code starts is not recovered by `net/http`. It ends the whole process. The server recovers panics only in its own handler goroutine.
- `log.Fatal` and `os.Exit` in library code or in a handler: they skip `defer` and kill the process.
- A `defer` inside a loop: it runs when the function ends, not at the end of each turn. Resources pile up.
- `defer tx.Rollback()` after `Begin`: this is safe. A `Rollback` after `Commit` returns `sql.ErrTxDone`. A missing rollback on an early return is the bug.

### Timeouts and cancellation

- `http.Client{}`, `http.DefaultClient`, and `http.Get` have **no timeout**. Set `Client.Timeout`, or use a `context` with a deadline on every request (`http.NewRequestWithContext`).
- `http.Server{}` with no `ReadHeaderTimeout`, `ReadTimeout`, `WriteTimeout`, or `IdleTimeout`: a slow client holds a connection forever. `gosec` reports the header case.
- `net.Dial` with no timeout. Use a `net.Dialer` with `Timeout`, or `DialContext`.
- `db.Query` where `db.QueryContext(ctx, ...)` is needed. Without the context, a cancelled request does not cancel the query.
- `context.Background()` or `context.TODO()` inside a function that already has a request `context`. The work no longer stops when the caller cancels.
- `ctx, cancel := context.WithTimeout(...)` with no `defer cancel()`: a timer and a goroutine stay until the timeout (`lostcancel`).
- A deadline that is longer than the caller's deadline.
- `time.Sleep` for backoff inside a worker that must stop on shutdown. Use a `select` on `ctx.Done()` and `time.After` (or a timer you stop).
- `time.After` in a loop: each call makes a timer. From Go 1.23, an unreferenced timer can be collected at once, but only when `go.mod` says `go 1.23.0` or later. With an older `go` line, each timer lives until it fires.

### Retries and idempotency

- A retry loop with no maximum, no backoff, or no jitter. Use the project's retry helper if there is one.
- A retry on a `POST` or on a call with side effects with no idempotency key.
- A retry on every error. Retry `context.DeadlineExceeded`, 429, and 5xx only when the call is safe to repeat. Do not retry 4xx or `context.Canceled`.
- `http.Request` with a body that is retried: the body is already read. Use `GetBody`, or rebuild the request. `go-retryablehttp` handles this.
- A consumer that acknowledges a message before the work is done (lost work), or after, with no dedupe (duplicates). Pick one order and make the handler safe to repeat.

### Resources

- `resp.Body.Close()` missing, or placed before the `err` check (`resp` is `nil` on error). Check `err` first, then `defer resp.Body.Close()`.
- A body not read to the end before close: the connection cannot be reused. Read it to `io.Discard` when the code ignores the body.
- `rows.Close()` and `rows.Err()` not checked after a `for rows.Next()` loop.
- `os.Create` or `os.OpenFile` for a write, with the `Close` error dropped. Check it, or `Sync`.
- A temp file or directory that is not removed on the error path.
- A `sync.Mutex` locked with no `defer Unlock()` on a path that can return early or panic.

### Concurrency

```go
// Race: two goroutines write the map. This is a fatal error, not a panic you can recover
counts := map[string]int{}
for _, id := range ids {
	go func() { counts[id]++ }()
}

// Safe: one owner. Results come back over a channel or under a mutex
var mu sync.Mutex
counts := map[string]int{}
var wg sync.WaitGroup
for _, id := range ids {
	wg.Add(1)
	go func() {
		defer wg.Done()
		mu.Lock()
		defer mu.Unlock()
		counts[id]++
	}()
}
wg.Wait()
```

- `concurrent map writes` is a fatal error that ends the process. A map that several goroutines touch needs a lock, `sync.Map`, or a single owner.
- Before Go 1.22, the loop variable is shared by every goroutine started in the loop. Check the `go` line in `go.mod`. Since 1.22, each turn has its own variable.
- `wg.Add(1)` inside the goroutine instead of before it: `Wait` can return early.
- A goroutine with no owner: who stops it, and when? A goroutine that sends on an unbuffered channel after the receiver has returned blocks forever (a leak). Give the channel a buffer, or select on `ctx.Done()`.
- A `for { select { ... } }` worker with no `ctx.Done()` case, or one that never exits.
- `errgroup.Group` with no `WithContext`, so a failing goroutine does not cancel the others. Use `SetLimit` to bound the number.
- Closing a channel twice or sending on a closed channel panics. Only the sender closes, and only once. A receive from a `nil` channel blocks forever.
- Check-then-act on a field or map with separate lock and unlock calls: hold the lock across both steps.
- `sync/atomic` for one field and plain access for the same field elsewhere.
- A mutex copied by value (a struct with a `sync.Mutex` passed or returned by value).
- A mutex held while calling `http.Do`, `db.Query`, or a callback: others wait for the whole call, and a callback that takes the same lock deadlocks.
- A `sync.Once` whose function can fail: the failure is remembered and never retried.
- Unbounded `go f()` per item: resource exhaustion under load. Use a worker pool or `errgroup.SetLimit`.
- Fire-and-forget goroutines: track every goroutine the code starts, and wait for it at shutdown (`WaitGroup`, `errgroup`, or a done channel). No goroutines in `init()`.
- A channel with a large buffer: the size hides a blocking or capacity problem. Prefer unbuffered or a buffer of one, and ask for the reason behind a larger one.
- A `sync.Mutex` embedded in an exported struct (its `Lock` and `Unlock` become part of the API), or a struct with a mutex copied by value. Use a named field and pass by pointer.

### Observability

Check the Datadog items in `datadog.md` first, in particular: handled errors marked on the span (`span.Finish(tracer.WithError(err))`), the `ctx` passed to every log call (`slog.ErrorContext`) and to every goroutine, `tracer.Stop()` on shutdown, and bounded metric tags. Then:

- `log.Printf("error: %v", err)` in a service that uses `slog` or a structured logger: no fields, no level, not searchable. Follow the repo's logger.
- A log line with the message only. Add the operation and the IDs as fields: `slog.Error("charge failed", "order_id", id, "err", err)`.
- A log line that includes a secret, a token, or personal data. Note it for `security-analysis`.
- Metric labels with unbounded values (user ID, full URL path, error text). Bound the label set.
- A new outbound call, job, or consumer with no counter, error count, or duration histogram where the repo has them for its peers.
- With OpenTelemetry: a span that is never ended (`defer span.End()`), an error not recorded on the span (`span.RecordError(err)` and `span.SetStatus`), and a new `context` that drops the parent span.
- A `context` that carries the request ID in a handler, but the job or goroutine started from it gets `context.Background()`: the trace stops.
- A health or readiness handler that returns `200` with no check of the database or other dependency the service needs.

## Hand-offs

- A fail-open error path on an authorization or validation check belongs to `security-analysis` (A10).
- A goroutine per item, a missing batch, or a slow call that hurts only speed belongs to `performance-analysis`.
- A missing unique constraint behind a check-then-insert race belongs to `data-and-migration-analysis`.
- Whether the failure paths have tests belongs to `test-analysis`.
- Linters that run on every change belong to `static-analysis`, when the project config enables them.
