# Tracing a flow

Use in Steps 2, 3, and 4 of `explore-flow`. Find the real entry point, follow the critical path, and find the tests. Search with `rg` (or `git grep`) first, then open the files.

## Entry points by trigger

| Trigger | Where to look | Also find |
|---|---|---|
| HTTP route | Rails: `config/routes.rb`, then the controller action and its `before_action` filters. Go: the router setup (`http.HandleFunc`, `mux.Handle`, `chi`/`gin`/`echo` route calls), then the handler. | Middleware that runs first: auth, tenant, rate limit. |
| GraphQL / RPC | The schema or `.proto` file, then the resolver or the server method. | Field-level auth and loaders. |
| Background job | Rails: `app/jobs`, `app/workers`, `perform`. Go: the worker loop or the consumer `Handle` method. | Who enqueues it (`perform_later`, `perform_async`, publish calls), the queue, the retry settings. |
| Event or message | The consumer subscription (topic, queue, webhook route). | The producer, the payload shape, idempotency keys. |
| CLI / rake / cron | `lib/tasks`, `bin/`, `cmd/<name>/main.go`, the scheduler config (`config/schedule.rb`, `sidekiq-cron`, Kubernetes `CronJob`). | Flags and env vars that change behavior. |
| UI action | The component handler, then the API call it makes. | The route on the server side; continue there. |
| Model callback | Rails: `before_*`, `after_*`, `after_commit` in the model and its concerns. | Every place that saves the model, since each runs the callback. |

## Following the critical path

- Open each method you cite. Do not cite a method from its name alone.
- Resolve dynamic dispatch: for an interface, a duck-typed call, `send`, a registry, or dependency injection, find the concrete implementation used on this path (the wiring, the factory, the initializer). If several are possible, list them and say which one this flow uses and why, or mark it `(inferred)`.
- Follow data, not only calls: where a value is built, changed, saved, and read again.
- Mark each **async boundary**: an enqueued job, a published event, a goroutine, a `Thread`, a callback after commit. The flow after it runs later, maybe on another process, maybe more than once.
- Mark each **transaction** start and end, and what runs inside it. An external call or an enqueue inside a transaction is a fact the reader needs.
- Note configuration that changes behavior: feature flags, env vars, tenant settings. Cite where they are read.
- Stop at libraries and frameworks. Name the call and its documented effect.

### Ruby / Rails hints

- Concerns, `included do` blocks, and `delegate` hide calls. Search the method name across `app/`.
- `ActiveRecord` callbacks and validations run on `save`. Check the model and its concerns.
- Service objects often have `call` or `perform`. Check `self.call` wrappers.
- Sidekiq or Active Job retries: `sidekiq_options retry:`, `retry_on`, `discard_on`.

### Go hints

- Interfaces: find the struct that implements the method and the place in `main.go` or a constructor where it is wired.
- Errors: follow `return err` up to where it is logged, wrapped, or turned into a response code.
- Goroutines and channels: note who sends, who receives, and who waits (`sync.WaitGroup`, `errgroup`, `context` cancel).

## Find the tests

1. By path convention: Rails `spec/<same path>_spec.rb` or `test/<same path>_test.rb`, request specs under `spec/requests`, system specs under `spec/system`. Go: `<file>_test.go` in the same package.
2. By name: `rg -n "<ClassName>|<method_name>|<route path>" spec test --glob '*_test.go'`.
3. By factory or fixture of the main entity, for integration tests that drive the flow end to end.
4. Shared examples and test helpers that the tests include.

Write the search you ran next to "No test found" when nothing matches.

## Hop table

Keep this table in the doc's appendix while you trace. Each row is one hop.

| # | From | To | Where | Input → output | Side effect | Decision / error |
|---|---|---|---|---|---|---|
| 1 | Client | `OrdersController#create` | `app/controllers/orders_controller.rb:12` | params → `Order` | none | 422 when `order.invalid?` |
