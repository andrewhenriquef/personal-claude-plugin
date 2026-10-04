# Ruby and Rails test analysis

Commands, smells, and mutation tools for `test-analysis`. The project's own test conventions and CI command win over everything here. Run only tools the project already uses, or ask first.

## Detect the setup

- RSpec: a `spec/` directory, `rspec-rails` or `rspec` in the `Gemfile`, `.rspec`, `spec/spec_helper.rb`.
- Minitest: a `test/` directory, `test/test_helper.rb`.
- Helpers in the `Gemfile`: `factory_bot_rails`, `shoulda-matchers`, `capybara`, `vcr` or `webmock`, `simplecov`, `rubocop-rspec`, `mutant-rspec`.
- A `test` or `spec` task in `Rakefile`, a `bin/rails test` or `bin/rspec` binstub, or a test step in `.github/workflows`.

Run through Bundler or the binstub so the pinned versions load.

## Scope unit

The scope is the changed spec or test files, plus the spec or test files that cover the changed production files. Find the covering files by convention (`app/models/order.rb` to `spec/models/order_spec.rb`), then by searching for the class name in `spec/` and `test/`.

## Commands

### RSpec

| Goal | Command |
|---|---|
| Normal run | `bundle exec rspec <paths>` |
| Random order | `bundle exec rspec --order random <paths>` (the seed prints at the end) |
| Replay an order | `bundle exec rspec --order random --seed <N> <paths>` |
| Find the test that causes an order failure | `bundle exec rspec --seed <N> --bisect <paths>` |
| One example | `bundle exec rspec <file>:<line>` |

There is no repeat flag. To repeat, run several random-order runs:

```
for i in 1 2 3; do bundle exec rspec --order random <paths> || break; done
```

### Minitest and Rails

| Goal | Command |
|---|---|
| Normal run | `bin/rails test <paths>` |
| Replay an order | `bin/rails test --seed <N> <paths>` |
| System tests | `bin/rails test:system` (slow and flaky-prone: run them only if the change touches the UI) |

Minitest runs in random order by default. Check `i_suck_and_my_tests_are_order_dependent!` in the test files. It turns that off.

### Coverage

If `simplecov` is configured, a normal run writes `coverage/`. Read `coverage/.last_run.json` or the HTML report for the scoped files. Check `git status` after, and do not leave `coverage/` in the diff.

### Rails and the database

Tests use a shared test database. Do not run the worktree tests (mutation checks) at the same time as the working-tree tests. Untracked files that tests need (`config/database.yml`, `.env.test`) are not in the worktree, so copy them. If the setup is unclear, put the mutants under "Needs human check".

## Smells in Ruby tests

### Weak assertions

```ruby
# Weak: passes for almost any behavior
expect(response).to have_http_status(:ok)
expect(order).to be_truthy
expect { service.call }.not_to raise_error

# Stronger: assert the result and the side effect
expect(response).to have_http_status(:created)
expect(response.parsed_body).to include("status" => "paid")
expect { service.call }.to change { order.reload.status }.from("open").to("paid")
```

A request spec that checks only the status code does not protect the body, the database, or the enqueued job.

### Stubbing the subject

```ruby
# Weak: the method under test is replaced, so the test checks the stub
allow(subject).to receive(:total).and_return(100)
expect(subject.discounted_total).to eq(90)

# Stronger: build real inputs and let the real code run
order = build(:order, items: [build(:item, price: 100)])
expect(order.discounted_total).to eq(90)
```

Also check `allow_any_instance_of` and `expect_any_instance_of`. They hide which object is called.

### Doubles that do not match the real class

A plain `double` accepts any method. If the real method is renamed, the test still passes. Use `instance_double(Klass)`, which fails when the method does not exist.

### Error and deny paths

- Policy and authorization: is there a spec where the check **denies**? With Pundit, check for `forbid` or `not_to permit` cases.
- Validation: is there an invalid case, and does it check the error message or key, not only `valid?` is false?
- Rescue paths: is there a spec where the dependency raises?

### Time, randomness, and sleep

```ruby
# Flaky: depends on the clock
expect(token.expired?).to be false

# Stronger
travel_to(Time.zone.parse("2026-01-01 12:00")) do
  expect(token.expired?).to be false
end
```

`Time.now`, `Date.today`, `rand`, and `sleep` in a spec are findings. Use `travel_to` or `freeze_time` (ActiveSupport time helpers), and a fixed seed. In Capybara specs, use matchers that retry (`have_content`, `have_selector`), not `sleep` and not a read of `.text` right after a click.

### Shared state

- `before(:all)` or `before(:context)` that creates records. They are not rolled back by the test transaction.
- Class-level or global state changed in a spec and not restored (`ENV`, `Rails.configuration`, `I18n.locale`, constants).
- `let!` that builds data a spec does not use, or a mystery guest: the data comes from a factory or shared context far from the spec.
- A leaky constant declared in a spec (`class Foo`, `CONST =` inside `describe`).

### Jobs, mail, and callbacks

Check the arguments, not only that something ran: `have_enqueued_job(SyncJob).with(order.id)`, not `have_enqueued_job`. For mail, check the recipient and the key content.

### Skipped, pending, and focused

`skip`, `pending`, `xit`, `xdescribe`, `fit`, `fdescribe`, `focus: true`, `:focus`. A focused example makes the rest of the file silent in a local run. A committed one is HIGH.

### VCR and web mocks

A cassette that recorded an error response, or `record: :all` left in a spec. A cassette that is not checked against the current request shape.

### Minitest

```ruby
# Weak: the mock is never verified, so a missing call passes
mock = Minitest::Mock.new
mock.expect(:call, true, [order.id])
service.run(order)

# Stronger
mock.verify
```

Also: `assert x` where `assert_equal` fits, and `assert_nothing_raised` as the only check.

## Test linters

If `rubocop-rspec` is in the project config, a read-only run gives candidates. It does not edit files without `-a`:

```
bundle exec rubocop --only RSpec <spec files>
```

If the command fails because the RSpec cops are not loaded, skip it. Do not edit config.

Cops that match the smells above: `RSpec/NoExpectationExample`, `RSpec/MultipleExpectations`, `RSpec/ExampleLength`, `RSpec/StubbedMock`, `RSpec/MessageSpies`, `RSpec/ExpectInHook`, `RSpec/AnyInstance`, `RSpec/VerifiedDoubles`, `RSpec/Focus`, `RSpec/Pending`, `RSpec/EmptyExampleGroup`, `RSpec/RepeatedExample`, `RSpec/LeakyConstantDeclaration`. The fixes belong to `static-analysis`.

## Mutation tools

Use a tool only if the project already has it. Otherwise follow `references/mutation-checks.md` with hand-picked mutants.

- `mutant` with `mutant-rspec` ([mbj/mutant](https://github.com/mbj/mutant)): runs only the specs related to the mutated subject. A typical run names the subject: `bundle exec mutant run --use rspec --require ./lib/person 'Person#adult?'`. In Rails it is usually set up in `.mutant.yml`. Diff scoping uses `--since <revision>`: check it with `bundle exec mutant run --help` on the installed version. Check the license terms before you run it on private code.

## Tests

The test command above is the safety net for every mutant. Mutants run in a worktree only.

## My preferences

Owner's preferences for Ruby tests. This section is empty until the owner fills it in. The project conventions still win when they disagree. Suggested topics:

- RSpec or Minitest, and the preferred style (`expect` syntax, `let` versus inline setup).
- Factories versus fixtures, and when to use `build` or `create`.
- Request specs versus controller specs, and what they must assert.
- Policy on `any_instance`, `before(:all)`, and stubbing.
- How many mutants to run, and which operators matter most.
- Anything to always flag in the report.
