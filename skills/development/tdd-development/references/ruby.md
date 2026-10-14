# Ruby / Rails

Use with `tdd-development` when the work is in `*.rb` files or has a `Gemfile`. Project conventions and config win over this page. Commands are starting points: read the project's own first (`CLAUDE.md`, `Makefile`, `docs/pipelines.md`, CI). The Minitest forms below were run on Ruby 4.0 with Minitest 6. The RSpec forms are from the RSpec docs and were not run here.

## Find the framework and the commands

| Signal | Framework | Focused test | Whole area |
|---|---|---|---|
| `spec/`, `.rspec`, `rspec-rails` in the `Gemfile` | RSpec | `bundle exec rspec spec/path/thing_spec.rb:LINE` | `bundle exec rspec spec/path` |
| `test/`, no `rspec` | Minitest | `bin/rails test test/path/thing_test.rb:LINE` (Rails) or `ruby -Itest test/path/thing_test.rb -n test_name` | `bin/rails test test/path` |

Prefer the project's wrapper (`bin/rails`, `bin/rspec`, a `make` target, a Docker command from `docs/pipelines.md`). If the project runs tests in a container, run them there, as the pipelines doc says. Do not install gems.

## What a red looks like

- **Missing unit (a good first red):** `NameError: uninitialized constant Cart` (Minitest reports it as an Error, RSpec as a failure with the same message). A missing file loaded with `require_relative` gives `LoadError: cannot load such file`. This shows the behavior does not exist. It is enough to start, but do not stop there.
- **Assertion red (the one to aim for):** add the empty class or method (`def call(...) = nil`, or a zero value) and run again. Minitest shows `Failure: Expected: 5, Actual: 0`. Show this second red.
- **Not a red:** `SyntaxError`, `NoMethodError` on a typo in the test, `ActiveRecord::StatementInvalid` from a missing table in test setup, a failure in a `before` block.
- **Rails models:** a test for a new column fails with `unknown attribute` or `NoMethodError`. That is the red. The migration and the model change are production code: write them in GREEN, and run the migration on the local test database only. Check `db/schema.rb` or `db/structure.sql` for the change. Never run a migration on a shared database.

## Conventions to follow

Read the neighbouring specs first. If there is no convention, use these (the owner's preferences):

- Let the `describe` / `context` / `it` nesting tell the story. Do not number cases or tag them with labels. `context` starts with "when ...", `it` starts with an active verb ("propagates", "refuses").
- Errors: `expect { call }.to raise_error(SomeError)`. Never a `rescue` modifier or a `begin/rescue` inside the example.
- One assertion per `it` where you can: hoist shared set-up into a `before` block and split the examples. Use `:aggregate_failures` only when splitting would repeat an expensive action. Several `expect`s without the tag is a smell.
- Act first, then assert: call the subject, then check interactions with `have_received`. Use `expect(...).to receive` only when it must be set before the call (a negative expectation together with `raise_error`).
- Never `let(:subject)`: it shadows RSpec's implicit subject. Use a meaningful name (`subject_text`).
- Put helper methods before the first `describe`, so a reader sees the vocabulary before the examples.
- Extract a matcher or a literal that repeats in several examples into a `let`.
- Keep a `let` on one line while it fits. Wrap it only when RuboCop reports `Layout/LineLength`. Never add an inline `# rubocop:disable`: fix the cause (split a method, extract a repeated call).
- Use `described_class`, not the class name, in the spec body.

## Tests and data

- Test through the seam: a request spec for an endpoint, a service's public `call`, a model's public method. Do not test private methods or call `send`.
- Prefer `build` or `build_stubbed` (FactoryBot) when the test does not need a database row. Use `create` when the behavior depends on persistence.
- Time: `travel_to` or `freeze_time` (ActiveSupport time helpers). Never `sleep`.
- HTTP: stub the outside call at the boundary with the tool the project already uses (WebMock, VCR). Do not stub your own classes. Avoid `allow_any_instance_of`.
- Email, jobs, and cache have test adapters in Rails. Use them, and assert on the observable result.

## Freeze list

Add the spec or test files of the slice, and any shared fixture, factory, or `support` file the test relies on and you changed. A change to a shared example or a helper after the red can make a test pass without the code: freeze those too.

## Coverage

SimpleCov is common in Rails projects. If the project uses it, check the lines you changed after the last slice. The owner's bar: every changed line covered, and at least 95% per changed file. The project's own minimum wins.

## Gate

At the end of each slice: the focused test, then RuboCop in check mode on the changed files (`bundle exec rubocop <files>`). If it fails, call `static-analysis`. Do not pass `-a` or `-A` yourself.
