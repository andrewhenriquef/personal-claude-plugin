# Ruby and Rails: reproducing a bug

Use in Steps 0, 2, 4, and 5 of `reproduce-bug` when the code is Ruby (`Gemfile`, `*.rb`). Detect RSpec (`spec/`, `.rspec`) or Minitest (`test/`).

Sources: [RSpec Core command line](https://rspec.info/features/3-13/rspec-core/command-line/), [RSpec `--bisect`](https://rspec.info/features/3-13/rspec-core/command-line/bisect/), [Rails testing guide](https://guides.rubyonrails.org/testing.html), [ActiveSupport TimeHelpers](https://api.rubyonrails.org/classes/ActiveSupport/Testing/TimeHelpers.html), [Sidekiq testing](https://github.com/sidekiq/sidekiq/wiki/Testing), and the conventions in `reliability-analysis/references/ruby.md` of this plugin.

## Run one test

RSpec:

```sh
bundle exec rspec spec/path/to_spec.rb:LINE
bundle exec rspec spec/path/to_spec.rb -e "example name"
```

Minitest and Rails:

```sh
bin/rails test test/models/user_test.rb:LINE
bin/rails test test/models/user_test.rb -n test_name
```

Use the repo's own wrapper if it has one (`bin/rspec`, `make test`, `docker compose run ...`). Read `CLAUDE.md` and the CI config.

## Write the test

- Add a new example or a new file where the repo keeps such tests. Do not edit existing examples.
- Name it for the symptom: `it "rejects a negative amount"`. Keep the example short, with one clear expectation about the symptom.
- Use the repo's factories (`FactoryBot`) or fixtures with synthetic values. Do not read production data.
- Pin time with `travel_to` (Rails `ActiveSupport::Testing::TimeHelpers`) or `Timecop` if the repo uses it. Always return the clock after the test (`travel_back`, or the block form).
- Do not use `skip`, `pending`, or `xit` to hide a failure.
- For a controller or request bug, prefer a **request spec** (or an integration test) over a controller or view test. It reaches routing, params, and middleware.
- For a job, call `perform` directly, or use `Sidekiq::Testing.inline!` / the ActiveJob test adapter, depending on the repo. Check the retry and the idempotency in the same test only if the symptom needs it.
- Stub the **network** (`WebMock`, `VCR` if the repo uses them), not the component the hypothesis suspects.

## Flaky and order-dependent bugs

```sh
# repeat the example
for i in $(seq 1 30); do bundle exec rspec spec/path/to_spec.rb:LINE || echo "FAIL run $i"; done

# fix the order and repeat it
bundle exec rspec --order random --seed 12345
```

- RSpec prints the seed when the order is random. Re-run with `--seed <n>` to repeat the failing order.
- `bundle exec rspec --bisect --seed <n>` reduces a failing suite to the smallest set of examples that still fails. This finds the test that leaks state. It runs the suite many times, so scope it to the failing files first.
- Minitest prints the seed too (`Run options: --seed 1234`). Re-run with `--seed 1234`.
- RSpec can re-run only the last failures if `config.example_status_persistence_file_path` is set: `bundle exec rspec --only-failures`.
- Raise the rate for concurrency bugs: run with several threads (`Thread.new`, a latch), a small `sleep` in the contested window, or `Concurrent::` helpers that the repo already uses. Under test transactions, threads may not see each other's data. Check the repo's `use_transactional_tests` / database cleaner setup.

## Property and fuzz loops

- A loop over many generated inputs inside one example is enough: `1000.times { |i| ... }` with a seeded `Random.new(seed)`. Print the seed and the failing input.
- If the repo uses a property library, follow it.

## Bisect

```sh
#!/bin/sh
bundle check >/dev/null 2>&1 || bundle install >/dev/null 2>&1 || exit 125
bundle exec rspec spec/path/to_spec.rb:LINE
```

`rspec` exits `1` on a failing example. A broken `bundle install` or a load error should exit `125`, not count as bad. See [minimise.md](minimise.md). Copy the new spec to a place the script can restore at each commit, because it does not exist at old commits.

## Other loops

- **Console:** `bin/rails console --sandbox` rolls back database changes on exit. Use it to try the bug path by hand and turn the steps into a test. Never use it on production.
- **SQL:** `ActiveRecord::Base.logger = Logger.new($stdout)` shows the queries a path runs.
- **HTTP:** `bin/rails server` and `curl`, or a request spec.
- **Replay:** build the params from the redacted payload and post them in a request spec.

## Common traps

- A test that passes only because of **leftover data** from another example.
- A time-dependent example that fails only after midnight UTC.
- `let` is lazy: a record is not created until it is referenced. Use `let!` when the bug needs the record to exist.
- Memoised class-level state (`@@var`, constants that hold mutable objects) leaks across examples.
- Transactional fixtures hide bugs that need a commit (`after_commit` callbacks, background jobs).
