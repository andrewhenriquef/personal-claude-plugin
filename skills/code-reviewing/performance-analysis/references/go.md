# Go performance analysis

Tools, commands, and Go-specific traps for `performance-analysis`. The project's own conventions and tool config win over everything here. Run only tools the project already uses, or ask first.

## Detect the setup

- `go.mod` for the module and Go version.
- Existing benchmarks: `func Benchmark...` in `*_test.go` files.
- Profiling hooks: `net/http/pprof` imports, `runtime/pprof` use, a `/debug/pprof` route.
- `.golangci.yml` and which performance linters it enables.
- `benchstat` available on the machine (`golang.org/x/perf/cmd/benchstat`).
- The query layer: `database/sql`, `sqlx`, `pgx`, GORM, `ent`, `sqlc`.

## Scope unit

Go tools work on packages. The scope is the packages that contain the changed files. Pass each as `./dir/...`. See `static-analysis` (section "Scope unit") for the commands that build the list.

## Read-only linter run

Performance linters are candidate generators. Run them without `--fix` and without editing the config. `--enable-only` limits the run to the named linters, and their settings still come from the project config.

```
golangci-lint run --enable-only=prealloc,perfsprint,bodyclose,makezero ./dir/...
```

- `prealloc`: slice declarations that could be pre-allocated.
- `perfsprint`: `fmt.Sprintf` that a faster call can replace.
- `bodyclose`: an HTTP response body that is not closed. The connection cannot be reused, so this is a real cost.
- `makezero`: slices created with a non-zero length and then appended to.
- `gocritic` has performance checks, but they depend on the checks enabled in the project config. Run it only with the project's settings.
- If a linter is not in your golangci-lint version or config, skip it. Do not edit the config. List it under "Linter rules to consider".

How to read the results: `prealloc` and `perfsprint` are micro-optimizations. Report them only on a hot path with a measurement. `bodyclose` is a resource problem and also a performance problem: report it when the client talks to the same host often.

## Measure

Write outputs to a temporary directory, not into the repo: `tmp=$(mktemp -d)`. Run in the working tree for existing benchmarks. Use the worktree steps in `evidence.md` for the base-versus-change comparison.

| Goal | Command |
|---|---|
| Run a benchmark, with allocations, several times | `go test -run='^$' -bench='<regex>' -benchmem -count=10 ./dir/... > "$tmp/new.txt"` |
| Compare base and change | `benchstat "$tmp/old.txt" "$tmp/new.txt"` (a `~` means no significant difference) |
| CPU and memory profile of a benchmark | `go test -run='^$' -bench='<regex>' -cpuprofile="$tmp/cpu.prof" -memprofile="$tmp/mem.prof" ./dir/...` |
| Read a profile | `go tool pprof -top -cum "$tmp/cpu.prof"` |
| See what escapes to the heap | `go build -gcflags=-m ./dir/... 2>&1 \| grep <function or file>` |
| Execution trace (latency, scheduling) | `go test -run='^$' -bench='<regex>' -trace="$tmp/trace.out" ./dir/...`, then `go tool trace "$tmp/trace.out"` |

Notes:

- `-run='^$'` skips the unit tests, so only benchmarks run.
- Run at least 10 times (`-count=10`) for `benchstat`. Do not rerun until a difference appears.
- Collect one profile at a time. Profiles can interfere with each other.
- If `benchstat` is not installed, do not install it. Compare the medians of the runs by hand, say that the result is less rigorous, and do not claim a small difference.
- If the project has no benchmark for the path, write a short throwaway benchmark in the temporary worktrees only. See `evidence.md`.
- Do not profile a shared or production service.

## Go traps

### Allocation and copying

```go
// Grows and copies the slice several times when the length is known
var out []Item
for _, r := range rows {
	out = append(out, toItem(r))
}

// Allocates once
out := make([]Item, 0, len(rows))
for _, r := range rows {
	out = append(out, toItem(r))
}
```

- String building with `+=` in a loop: use `strings.Builder` with `Grow`.
- `fmt.Sprintf("%d", n)` for a simple conversion in a hot path: `strconv.Itoa`.
- `[]byte` and `string` conversions inside a loop.
- `regexp.MustCompile` inside a function or loop: compile once at package level.
- Passing very large structs by value in a hot path. Report only with a benchmark.
- `sync.Pool` or manual buffer reuse proposed with no measurement. Do not suggest it without a profile that shows allocation cost.

### Data access

- `db.Query` or `QueryRow` inside a loop over rows: N+1. Use one query with `IN` or `ANY($1)` (with `pq.Array` or the driver's array support), or a join.
- A query with no `LIMIT` on a list endpoint.
- `SELECT *` when the code reads a few columns.
- Large result sets read fully into a slice. Stream with `rows.Next` and process in batches.
- One connection pool per request, or `sql.Open` inside a handler. Open once.
- A transaction held open across HTTP calls or other slow work.
- With GORM or `ent`: lazy loading or `Preload` per item inside a loop, and `Find` into a full model slice for a count (`Count`).

### HTTP and I/O

- A new `http.Client` or `http.Transport` per request. Connections are not reused. Share one client.
- A response body not closed, or not read to the end, so the connection cannot be reused (`bodyclose`).
- `io.ReadAll` on a request or response body with no size limit, and on large files. Stream with `io.Copy`, and limit with `http.MaxBytesReader`.
- Independent calls made one after another: run them concurrently with `errgroup`, with a limit.
- A call to another service inside a loop over items: use a batch endpoint if it exists.
- Unbuffered writes to a file or a response in a loop: use `bufio`.

### Concurrency cost

- A goroutine started per item with no limit: use a worker pool or `errgroup.SetLimit`.
- A mutex held while doing I/O. Other callers wait for the whole call.
- A single mutex or channel that every request goes through, in a hot path. Check with a mutex or block profile before you report.
- `time.Sleep` polling in a loop where a channel or a condition would do.

### Serialization

- `encoding/json` on a large payload in a hot path: first measure. A faster library is a large change, so report the measured cost and let the owner decide.
- Marshaling the same value several times in one request.
- Returning more fields than the caller uses.

## Hand-offs

- Goroutine leaks, missing timeouts, retries, and unbounded concurrency as a failure risk belong to `reliability-analysis`. Report them here only for their cost in time or memory.
- Indexes and constraints for a schema change belong to `data-and-migration-analysis`.
- Linters that run on every change belong to `static-analysis`, when the project config enables them.
