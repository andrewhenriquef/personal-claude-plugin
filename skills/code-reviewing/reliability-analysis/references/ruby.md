# Ruby and Rails reliability analysis

Tools, commands, and Rails-specific traps for `reliability-analysis`. The project's own conventions and tool config win over everything here. Run only tools the project already uses, or ask first.

## Detect the setup

Look in the `Gemfile` and `Gemfile.lock` for:

- Cops: `rubocop`, `rubocop-rails`, `rubocop-thread_safety`.
- Job runners: `sidekiq`, `good_job`, `solid_queue`, `resque`, `delayed_job`, `que`, or plain Active Job with the queue adapter set in `config/application.rb` or `config/environments/*.rb`.
- HTTP clients and their retry and timeout settings: `faraday` with `faraday-retry`, `httparty`, `rest-client`, `typhoeus`, `net/http`.
- Resilience gems: `retriable`, `stoplight`, `semian`, `circuitbox`, `rack-timeout`, `rack-attack`.
- Logging: `lograge`, `semantic_logger`, `ougai`, and `config.log_formatter` and `config.log_tags`.
- Error trackers and reporters: `sentry-ruby`, `honeybadger`, `bugsnag`, `rollbar`, `airbrake`, and use of `Rails.error` (the Rails error reporter, Rails 7.0 and later).
- Datadog (the default stack): the `datadog` gem (v2.x; `ddtrace` is the older v1 line), `config/initializers/datadog.rb`, `dogstatsd-ruby` or `statsd-instrument` (DogStatsD), and the `DD_*` variables in deploy config. See `datadog.md` for the full setup checks.
- Other metrics and tracing: `prometheus-client`, `yabeda`, `opentelemetry-sdk`, `newrelic_rpm`, `skylight`.
- Concurrency helpers: `concurrent-ruby`, `connection_pool`, and the app server config for threads (`config/puma.rb`).

Also read the Rails version and the Ruby version. Some advice depends on them.

## Read-only linter run

Cops are candidate generators. Run them without autocorrect and without editing the config. `--only` limits the run to the cops or departments you name.

```
bundle exec rubocop --only Lint/SuppressedException,Lint/RescueException,Lint/ShadowedException,Lint/EnsureReturn,Lint/RescueType,Style/RescueStandardError,Rails/TransactionExitStatement,Rails/SaveBang,Rails/Output,Rails/Exit,ThreadSafety --force-exclusion <files>
```

- `<files>` are the changed Ruby files in scope (see `static-analysis`, section "Scope unit", for a command that builds the list).
- `Lint/SuppressedException`: an empty `rescue`. `Lint/RescueException`: `rescue Exception`. `Lint/ShadowedException`: a broad class rescued before a narrow one. `Lint/EnsureReturn`: a `return` in `ensure` that discards the error.
- `Rails/SaveBang`: `save`, `update`, or `create` whose result is not checked. It needs the `rubocop-rails` plugin, and the cop is off by default.
- `Rails/TransactionExitStatement`: `return`, `break`, or `throw` inside a transaction block, which can roll back or commit in surprising ways.
- `ThreadSafety` runs the department from `rubocop-thread_safety` (class-level mutable state, `Thread.new`, instance variables in middleware).
- If the project config does not load a plugin, the run fails or skips those cops. If the gem is already in the bundle, load it for the run from the command line (check `bundle exec rubocop --help` for `--plugin` or `--require`). If it is not in the bundle, do not install it. Say so, and list the cops under "Linter rules to consider".
- Never pass `-a` or `-A` here. Fixing belongs to `static-analysis`, and only for rules the project enables.

How to read the results: a cop hit is a pattern. Apply the exclusions in `reliability-checks.md` and trace the failure. An empty `rescue` on a best-effort cleanup call, with a comment that says so, is not a finding.

## Prove it

Run tests only in the local test environment, with the test database. Do not run two Rails test runs at the same time: they share the test database.

| Goal | How |
|---|---|
| Force an error | Stub the dependency in a throwaway spec to raise (`allow(client).to receive(:charge).and_raise(Timeout::Error)`), or pass a fake object |
| Force a hang | A local `TCPServer` that accepts and never replies, with a short timeout set in the test |
| Run a job twice | Call `MyJob.perform_now(args)` twice in a throwaway spec, then assert on the records and on the calls the fake received |
| Duplicate delivery | Call the webhook controller or handler twice with the same payload against the test database |
| Thread-safety | Start 20 to 50 threads that call the code together, released by one `Queue` or `Concurrent::CountDownLatch`, repeated. A wrong count or an exception is tier 1. No failure is not proof |
| Order-dependent bug | `bundle exec rspec --order random` (or `bin/rails test`, which already randomizes), repeated |
| What a rescue hides | Raise inside the `begin` block with a stub, and read the log and the return value |

For a throwaway spec, use the temporary worktree from `evidence.md`. Do not add the spec to the diff unless the user asks.

## Ruby traps

### Error handling

```ruby
# Swallows everything, including programming errors. The caller sees nil
def fetch_rate
  client.rate
rescue
  nil
end

# Rescues the expected failure, keeps the cause, and reports it
def fetch_rate
  client.rate
rescue Faraday::TimeoutError, Faraday::ConnectionFailed => e
  Rails.error.report(e, handled: true, context: { operation: "fetch_rate" })
  raise RateUnavailable, "rate service failed", cause: e
end
```

- `rescue => e` rescues `StandardError`. Check that the class is not wider than the failure the code expects. `rescue Exception` also catches `SignalException`, `SystemExit`, and `NoMemoryError`.
- A rescue modifier (`do_it rescue nil`) hides the cause and the class.
- A rescue that returns `nil`, `false`, `[]`, or `0`: the caller cannot tell the failure from a real answer.
- A new error raised inside a `rescue`: Ruby sets `cause` on its own, so the original is kept. Check that the new error still names the operation and the IDs. A new error raised outside the `rescue` block, or one that copies only `e.message`, loses the cause and the backtrace.
- `retry` in a `rescue` with no counter: an infinite loop.
- `ensure` with a `return`: it discards the error in flight (`Lint/EnsureReturn`).
- A `save`, `update`, or `create` whose result is ignored. These return `false` on a validation failure. Use the bang version, or check the result.
- `update_all`, `delete_all`, and `insert_all` skip validations and callbacks and do not raise on a bad row in some cases. Check the returned count if the code needs the write.
- `rescue_from` in a controller that renders a `200` or an empty body for a real fault.
- `Timeout.timeout` around I/O: it raises in the middle of the code it wraps, at any point, and can leave a connection or a lock in a bad state. Use the client's own timeout settings.
- An exception inside a `Thread.new` is not raised in the main thread unless `report_on_exception` is on or the thread is joined. The failure disappears.
- A `rescue` inside a `transaction` block that swallows the error: the transaction commits with partial writes. Let the error leave the block, or re-raise.

### Timeouts, retries, and idempotency

- `Net::HTTP` has finite but long default timeouts (look up the values for the project's Ruby version). A long default can hold a Puma thread for a minute. Set `open_timeout`, `read_timeout`, and `write_timeout` explicitly.
- Faraday: set `request: { open_timeout:, timeout: }`. `faraday-retry` retries only idempotent methods by default. Check the `methods` option if the code changed it.
- `HTTParty`, `RestClient`, and `Typhoeus` calls with no `timeout`.
- A retry on `POST` or on a call with side effects with no idempotency key (Stripe style `Idempotency-Key` header, or a unique constraint on a client-generated ID).
- Retries stacked: the HTTP client retries, the job runner retries the job, and a `retry_on` retries again.
- Sidekiq retries a failed job by default, up to 25 times over about three weeks, with growing delays. The job must be safe to run again. A job that raises after a partial side effect repeats that effect. Check the repo's `sidekiq_options retry:` and `sidekiq_retries_exhausted`.
- Active Job: `retry_on` and `discard_on` set the policy. `discard_on` drops the job with no trace unless it logs or reports. Check what happens at the final failure.
- A job that takes a model object as an argument instead of an ID: it serializes stale state, and fails if the record is gone (`ActiveJob::DeserializationError`).
- Sidekiq stores job arguments as JSON. Pass strings, numbers, booleans, arrays, and hashes only. Symbols, `Date`, `Time`, and objects do not round-trip. Sidekiq delivers a job at least once, even after it finished, if the acknowledgment is lost. Design every job to run twice.
- Enqueuing a job inside a transaction, before the commit: the worker can run before the row is visible, or run for a row that rolled back. Use `after_commit`, or the Rails option that enqueues after commit (Rails 7.2 and later has `enqueue_after_transaction_commit`; check the version).
- A webhook controller that does slow work inline: the sender times out and sends again. Save the event, answer fast, work in a job, and dedupe on the event ID.
- A job that calls something that can hang, with no timeout on the call: the worker thread is stuck, and the queue backs up behind it.

### Resources and shutdown

- `File.open` without a block, `Tempfile` not closed or unlinked on the error path. Use the block form.
- A connection checked out of a pool by hand, and not returned on the error path. Use `with_connection` or the pool's block form.
- `ActiveRecord::Base.connection` used in a thread the code starts, with no `with_connection` or release: the pool runs dry.
- A lock from `with_lock` or `lock!` held while the code calls an external service. Others wait, and the transaction stays open.
- A long job that ignores shutdown. Sidekiq sends a `TERM` and waits for a limited time. A job that cannot be stopped, and cannot be safely repeated, loses work at every deploy.
- A class that opens a resource at load time (a client, a socket) and fails the whole app boot when the service is down.

### Concurrency

Rails serves requests on several threads (Puma). Class-level state is shared by all of them.

```ruby
# Shared by every thread. Two requests can both miss the check and both write
class RateCache
  @rates = {}
  def self.rate_for(code)
    @rates[code] ||= Client.fetch(code)
  end
end

# One owner, and an atomic helper
class RateCache
  RATES = Concurrent::Map.new
  def self.rate_for(code)
    RATES.compute_if_absent(code) { Client.fetch(code) }
  end
end
```

- Class instance variables, `@@variables`, globals (`$x`), and constants that hold a mutable object (`CACHE = {}`) that code changes at runtime.
- Memoization with `||=` on a class, a singleton, or a shared object: check-then-act with no lock. Memoizing on a per-request or per-job object is fine.
- A read-modify-write on shared state (`@count += 1`, `hash[key] = hash[key] + 1`) with no `Mutex` or atomic object. `Concurrent::AtomicFixnum` and `Concurrent::Map` are the safe forms.
- `Thread.current[:x]` and `Thread.current.thread_variable_set`: state that leaks between requests on the same thread unless it is reset. Prefer `ActiveSupport::CurrentAttributes`, which Rails resets for each request.
- `Mutex#synchronize` held while the code does I/O or calls a callback.
- A `Mutex` locked a second time by the same thread in a call chain: `ThreadError` (deadlock). Use `Monitor` for re-entrant locks.
- `Thread.new` in a request with no `join`, no cleanup, and no error report. In Rails, use a job instead.
- Two jobs or requests that update the same record at once: use `with_lock`, `lock_version` (optimistic locking, rescue `ActiveRecord::StaleObjectError`), or a unique index. If a constraint closes the gap, hand off to `data-and-migration-analysis`.
- `find_or_create_by` and `first_or_create` are not atomic. Two callers both insert. The fix needs a unique index and a rescue of `ActiveRecord::RecordNotUnique` (or `create_or_find_by`, which relies on the index).
- `ENV[...] =` at runtime changes state for the whole process.
- Autoloading and `require` inside request code with threads: load the code at boot (eager load in production).

### Observability

Check the Datadog items in `datadog.md` first, in particular: handled errors marked on the span (`span.set_error(error)`), integrations on for the HTTP client and the job library (`:faraday`, `:http`, `:sidekiq`), log injection on, and bounded metric tags. Then:

- A `rescue` with no log, no `Rails.error.report`, and no tracker call. The failure leaves no trace.
- `Rails.logger.error(e.message)` with no class, no backtrace, and no IDs. Log the exception class, the message, the backtrace, and the IDs the repo uses. Prefer the repo's tracker call (`Sentry.capture_exception`, `Honeybadger.notify`, `Rails.error.report`).
- `puts`, `p`, or `pp` in app code (`Rails/Output`): no level, no tags, lost in production.
- Log lines built with string interpolation of a whole object (`"failed: #{order.inspect}"`): can write secrets and personal data into logs. Check `config.filter_parameters` and note it for `security-analysis`.
- A new job, outbound call, or consumer with no metric or tag where the repo has them for its peers (for example no `Yabeda` counter or `StatsD` call).
- Request ID not passed on: `config.log_tags = [:request_id]` is set for web requests, but a job or an outbound call starts a new context. Check that the job logs the ID that started it.
- An error that the code handles and does not report, on an important path (a payment, an import). The tracker never sees it.
- Handled user errors reported to the tracker as faults, or real faults only logged at `debug`.
- A health check route that returns `200` without a database or cache check, for dependencies the app needs.

## Hand-offs

- A fail-open error path on an authorization or validation check belongs to `security-analysis` (A10).
- A query or a loop that hurts only speed belongs to `performance-analysis`.
- A missing unique index or constraint behind a check-then-insert race belongs to `data-and-migration-analysis`.
- Whether the failure paths have tests belongs to `test-analysis`.
- Linters that run on every change belong to `static-analysis`, when the project config enables them.
