# Reliability review questions

Use in Step 3 of `reliability-analysis`. Read only the sections that match the slice. Each row is a question about the code, not a pattern to grep for. A row is a finding only when the failure can happen and you have evidence (Step 4). Language traps are in the language references.

## Routine failures to test every external call against

For each call to a network service, database, queue, file, or provider, ask what the code does when:

1. **It hangs.** No answer, for a long time.
2. **It returns an error.** Fast, with a status or an exception.
3. **It answers slowly or partly.** A timeout in the middle, a short read, a page of results that is cut off.
4. **It runs twice.** A retry, a duplicate message, a double click, two workers.
5. **The process stops in the middle.** A deploy sends `SIGTERM`, a pod is evicted, a worker is killed.
6. **It is down for several minutes.** Every caller fails at the same time, and then all retry together.

If the code has no answer for one of these, and the failure is routine, that is a candidate.

## Error handling

| Ask | Why it matters |
|---|---|
| Is an error ignored, assigned to `_`, or caught with an empty handler? Is it safe to ignore here, and does a comment or the repo's practice say why? | The failure vanishes. The code goes on with bad or missing data |
| Does the code turn a failure into a success value (an empty list, `nil`, `false`, `0`, a default) that the caller cannot tell from a real result? | The caller shows "no orders" when the database is down. Data looks lost |
| Is the handler wider than the failure it expects (`rescue Exception`, `rescue => e` around a whole method, `recover()` that swallows every panic)? | It hides programming errors and signals that must stop the process |
| Does the error keep its cause and context (wrapped in Go, `cause` in Ruby, the original class and message)? | The on-call engineer sees "failed" with no operation, ID, or cause |
| Is each error handled once: logged or returned, not both at every layer (the single handling rule)? | Duplicate log lines and duplicate alerts bury the real signal. The layer that handles the error should log it once |
| Does a fallback or default hide a real outage, or return data that is stale or wrong with no signal? Is the fallback path run often enough to be tested? | Users see wrong data. Nobody is alerted. A fallback that runs only during an outage has hidden bugs and can widen the outage |
| Does the caller get the right kind of error: "retry later" versus "your input is wrong" versus "we have a bug"? | Callers retry bad input, or give up on a transient failure |
| Is a failed operation reported as done (job marked complete, `200 OK` returned, record state advanced) before the work finishes? | Lost work with no trace |
| Does an error message or response include internals (SQL, paths, stack traces, tokens)? | A security issue. Note it for `security-analysis` |

## Timeouts, retries, and backoff

| Ask | Why it matters |
|---|---|
| Does every outbound call (HTTP, database, cache, queue, DNS, file on a network mount) have an explicit timeout, for connect and for the whole call? Check the client's default | Many clients wait forever by default. One slow dependency then holds every thread or goroutine |
| Is the timeout set on a request path where a user waits? Is it shorter than the caller's own timeout? | An inner timeout longer than the outer one means work continues after the caller gave up |
| Is the timeout based on the dependency's measured latency (a high percentile), not a round guess? | A timeout below the percentile fails healthy calls and starts retries. A timeout far above it holds the thread for nothing. See `datadog.md` for where to read the percentile |
| Does the call pass the remaining deadline downstream (Go: the same `context`; others: a deadline header or argument), and check it before each stage? | Each layer gets a fresh timeout, so the total can far exceed what the caller waits |
| Can a small share of slow calls use up the pool of threads or connections (for example 5% of calls that wait the full timeout)? | Bimodal latency. A few slow calls hold every worker, and the healthy calls queue behind them |
| Is a retry limited per request (a few attempts) and in total time? Does it use capped exponential backoff with jitter? Is there a service-wide retry budget where the repo has one? | An unbounded or fixed-interval retry turns a short outage into a retry storm. A budget keeps retries to a small share of normal traffic |
| Does the retry cover only transient errors (timeout, 429, 503), not permanent ones (400, 404, validation)? | Retrying a permanent error wastes capacity and never succeeds |
| Is the retried operation idempotent, or does it carry an idempotency key? | A retry after a timeout can repeat a charge, an email, or an insert. The first attempt may have succeeded |
| Are retries stacked in several layers (client, service, job runner, caller)? Does a layer retry an error that a lower layer already gave up on, or an "overloaded, do not retry" answer? | Attempts multiply. Three layers of three attempts make 27 calls to a struggling service. Retry at the layer directly above the one that failed |
| Is there a limit on work that piles up while a dependency is down (queue depth, concurrent calls, a circuit breaker where the repo uses one)? Does the service reject new work early when it is full, instead of queuing it until it times out? | Failure spreads to the callers, then to their callers. Failing early and cheaply is better than failing late |
| Does the service depend on a cache for capacity, not only for speed (the database cannot take the load if the cache is cold)? What happens after a restart or a cache flush? | After a deploy or a cache loss, every request goes to the database at once |
| Does a cancelled request or a closed client connection stop the work behind it (context, deadline, `ensure`)? | The server keeps working for nobody |

## Idempotency and delivery

| Ask | Why it matters |
|---|---|
| Can this handler or job run twice with the same input (queue at-least-once delivery, webhook resend, user double submit, retry after timeout)? | Most queues and webhook senders deliver at least once. Duplicates are normal |
| What stops the second run from repeating the side effect: a unique constraint, an idempotency key, a state check inside a transaction, or a dedupe table? | Without it: double charges, double emails, double inserts |
| If the code accepts an idempotency key: does it store the request parameters with the key, reject the same key with different parameters, and return an equivalent answer to a repeat (even if the resource changed since)? Is the key recorded in the same transaction as the change? | A key stored apart from the change leaves two bad cases: key saved and change lost, or change saved and key lost. A repeat with other parameters must not run |
| Is the side effect (email, charge, external API call) done before the database commit, so a rollback leaves the effect behind? Or after, so a crash between the two loses it? | Dual write problem. Pick an order and make the other side safe to repeat |
| Does a job enqueue happen inside a transaction, before the commit? | The job can run before the row exists, or run for a row that was rolled back |
| Does a job take full objects as arguments, or only IDs? Does it re-read the state when it runs? | A stale object overwrites newer data, and objects may not serialize |
| Does a job have a retry and discard policy? What happens on the final failure: dead set, alert, or silence? | A failed job that nobody sees is lost work |
| Does a webhook handler answer fast and do the slow work in a job? Does it verify it has not processed this event ID before? | The sender times out and resends. Duplicates follow |

## Resource lifecycle and partial failure

| Ask | Why it matters |
|---|---|
| Is every opened resource closed on every path, including error paths (file, response body, rows, connection, lock, temp file, transaction)? | Leaks grow with traffic until the process fails |
| Is a lock or a transaction released when an error or an early return happens (`defer`, `ensure`, a block form)? | A held lock or an open transaction blocks everyone else |
| Does a multi-step operation leave a half-finished state when a step fails: some rows written, some not; file moved, record not updated? | Data that is inconsistent and hard to repair |
| Is there a transaction around steps that must succeed together? Does an inner `rescue` or `recover` swallow the error and let the transaction commit? | Partial writes that look like success |
| Is there a compensation or a clean-up for steps that cannot join the transaction (external calls)? Can an operator tell which step failed? | Manual repair with no map |
| Does the code check the result of a write that can fail quietly (a `save` that returns `false`, an `update_all` count, an affected-rows count)? | The code believes the write happened |
| Does the process shut down cleanly: stop taking work, finish or hand back in-flight work, close pools (graceful shutdown, `SIGTERM`)? | Every deploy drops requests and half-finishes jobs |
| Does startup fail fast and loudly on missing config, and not limp on with defaults? | A silent bad default is found in production |

## Observability

Report an observability gap only with a scenario: "when X fails, the on-call engineer cannot answer Y." Do not ask for logs and metrics on every function. The default stack is Datadog: read [datadog.md](datadog.md) for the setup checks (unified service tagging, spans that carry handled errors, log and trace correlation, monitors, metric tags). The questions below apply to any stack.

| Ask | Why it matters |
|---|---|
| When this new path fails, is there a log line or a tracked error, with the operation, the IDs, and the cause? Does it follow the repo's logger and error tracker? | A failure with no trace cannot be debugged |
| Is a request ID or trace ID carried to this log line, to the job it enqueues, and to the outbound call? | One request cannot be followed across services and jobs |
| Does a new external call, job, or consumer have the repo's usual metrics: count, errors, and duration? | Nobody sees it slow down or fail |
| Could someone be alerted when this breaks? Is a failure only a debug-level line, or swallowed after a retry? | A silent failure on an important path runs for days |
| Are expected, handled outcomes (a user typed a bad value) logged at a level that pages or alerts, or real faults logged at debug? | Noise hides faults. Faults at debug hide from everyone |
| Are secrets, tokens, or personal data in the log line or the error context? | A security issue. Note it for `security-analysis` |
| Do metric labels or log fields have unbounded values (user ID, URL with an ID, error text)? | Cost grows and the metrics backend can fail |
| Is a retry logged once per attempt with the attempt number, and the final failure logged clearly? | A retried failure that succeeds late leaves no sign of the trouble |
| Do health or readiness checks reflect the dependencies the new code needs? | The orchestrator sends traffic to an instance that cannot work |
| Does a tracing span wrap the new external call, and does it record the error? | A slow request has no breakdown |

## Concurrency

Run these only when the slice has a concurrency trigger (see Step 3 in `SKILL.md`).

| Ask | Why it matters |
|---|---|
| What shared mutable state does the code touch (a map, a slice, a struct field, a class variable, a cache, a counter)? Who writes it, who reads it, and what protects it? | A race corrupts data, or in Go can crash the process |
| Is there a check-then-act on shared state (`if !exists { create }`, read-modify-write, memoize with `\|\|=`) with no lock or atomic operation across both steps? | Two callers pass the check, and both act |
| Does the code use the library's atomic helper where one exists (`LoadOrStore`, `compute_if_absent`, `atomic.Add`, `UPDATE ... SET n = n + 1`)? | Atomic helpers close the gap. Treat their use as safe |
| Is a lock held while the code calls out to I/O, a callback, or code it does not control? | Deadlock risk, and every other caller waits |
| Are locks taken in the same order everywhere? Is a lock taken again in a call chain that already holds it? | Deadlock |
| Is the lock always released, including on error and panic paths (`defer Unlock`, `ensure`, block form)? | A lock that stays held stops the system |
| Who owns each goroutine, thread, or worker: who starts it, and what makes it stop? Can it block forever on a send, a receive, or a lock after the caller has gone? | A leak per request, until memory or the thread limit runs out |
| Does a worker, goroutine, or thread die silently when it raises or panics? Does a panic in it stop the whole process? | Lost work, or a process crash |
| Does each background unit of work get a cancel signal or deadline from its caller (`context`, a stop flag)? | Work runs on after the request is gone |
| Is the number of concurrent workers bounded? | Resource exhaustion under load |
| Is a value shared with another thread through a closure or a loop variable that changes? | Every worker sees the last value (check the language version) |
| Do two jobs or requests that run at the same time on the same record have a lock, a version check, or a unique constraint? | Lost updates. If a constraint on the row closes it, hand off to `data-and-migration-analysis` |
| Is a channel or a queue closed or finished once, by its owner? | A double close panics. A send after close panics. A receiver that never sees the end blocks forever |

## Exclusions

Do not report:

- An ignored error where the code does not need the result and the repo's practice agrees: `Close` on a file open for reading, `Flush` of a log line, a best-effort metric or analytics call that is logged on failure.
- A fail-fast crash or raise at startup on bad config. That is correct.
- `os.Exit`, `panic`, or `raise` in a command, a script, a migration, or a test where the process should stop.
- A missing retry on a call that is not idempotent and has no key. Adding one is the bug.
- A missing circuit breaker, bulkhead, or fallback with no failure scenario that needs it.
- A timeout that the framework or a shared client already sets. Name where you saw it.
- A race on state that one goroutine or thread owns, on immutable or frozen values, or on state created per request.
- Code that uses the library's atomic helper correctly.
- A panic in a net/http handler goroutine that the server already recovers per request. (A panic in a goroutine the handler starts is not recovered.)
- Log wording, log level taste, or double logging with no effect on alerts or cost.
- A missing metric or log on a function that is not an external call, a job, a consumer, or an important decision.
- Gaps in alert rules, runbooks, or dashboards. Say these are "Not covered".
- A finding that needs a failure the system can never produce (a state its own code prevents).

Precedents:

- A call with no timeout on a request path is MEDIUM at least. It is HIGH when it also holds a database transaction, a lock, or a pooled connection.
- A retry on a non-idempotent operation with no key is HIGH when the effect is visible outside the system (money, email, a call to a partner).
- A swallowed error that makes the caller report success is a finding. A swallowed error on a best-effort side effect is not.
- A leak per request is HIGH. A leak per process start is LOW.
- A data race that the race detector reports is a finding, whatever the code looks like.
- An observability gap is a finding only with a named question the on-call engineer cannot answer.
- Unknown delivery guarantee, unknown infra timeout, or unknown alert setup is "Needs human check". It is not a finding and not a drop.
- A security issue or a performance cost with no reliability effect goes under "Notes for other reviews".
