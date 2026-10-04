# Ruby and Rails static analysis

Commands, autocorrect options, and cop classes for `static-analysis`. The project's own config and CI command win over everything here. Run only tools the project already uses, or ask first.

## Detect the setup

Look for, in this order:

- `.rubocop.yml` and `.rubocop_todo.yml`. The todo file holds old offenses that the project already excluded. Respect it. Do not add to it.
- Extension gems in the `Gemfile`: `rubocop-rails`, `rubocop-rspec`, `rubocop-performance`, `rubocop-minitest`, `rubocop-thread_safety`. Another config, such as `standard` or `rubocop-rails-omakase`, replaces the usual cop set. Use its own command (`bundle exec standardrb --fix`, `bin/rubocop -a`).
- A `bin/rubocop` binstub, a `lint` task in `Rakefile`, or a RuboCop step in `.github/workflows`.

Always run through Bundler (`bundle exec rubocop`) or the binstub, so the pinned version and plugins load. Check the version with `bundle exec rubocop --version`.

## Scope unit

The scope is the changed files. Build the list from the scope, and keep only Ruby files:

```
{
  git diff --name-only main...HEAD
  git diff --name-only
  git diff --staged --name-only
  git ls-files --others --exclude-standard
} | sort -u | grep -E '\.(rb|rake)$|(^|/)Gemfile$|\.gemspec$' | while read -r f; do [ -f "$f" ] && echo "$f"; done
```

Use `master` if the repo has no `main`. The `[ -f ]` test drops files that were deleted.

## Commands

Always run with autocorrect on. `--force-exclusion` makes RuboCop respect the config `Exclude` list even for files named on the command line.

| Goal | Command |
|---|---|
| Safe autocorrect (always, first) | `bundle exec rubocop -a --force-exclusion <files>` |
| Unsafe autocorrect (second, then review the diff) | `bundle exec rubocop -A --force-exclusion <files>` |
| Layout fixes only | `bundle exec rubocop -x --force-exclusion <files>` |
| Final check with no edits | `bundle exec rubocop --force-exclusion <files>` |
| JSON output | `bundle exec rubocop --format json --force-exclusion <files>` |
| Bug-class cops only | `bundle exec rubocop --lint --force-exclusion <files>` |

Notes:

- `-a` applies only safe corrections. `-A` also applies unsafe ones that can change behavior. RuboCop's own guidance: review the diff and run the tests after autocorrect, most of all after `-A`.
- Run `-a` first, then `-A`, so the diff of the unsafe step is small and easy to read. Revert an unsafe fix that changes behavior and fix that finding by hand.
- Do not run `--auto-gen-config`. It writes `.rubocop_todo.yml` and hides current offenses.
- Do not run `--disable-uncorrectable`. It writes `rubocop:todo` comments into the code. That is a bulk suppression.

### Fallback when the project has no RuboCop config

Say in the report that you used the fallback. Do not add a config.

```
ruby -wc <files>
```

This checks syntax and prints warnings only. Fix the warnings by hand. If `rubocop` is installed but unconfigured, report that and ask before you run it with default cops.

## Cops by class

Department names come from the RuboCop cop name (`Department/CopName`).

| Class | Departments and what they find |
|---|---|
| Likely bug | `Lint/`: `UselessAssignment`, `UnusedMethodArgument`, `ShadowingOuterLocalVariable`, `AmbiguousOperator`, `UnreachableCode`, `DuplicateMethods`, `SuppressedException`. `Rails/` correctness: `HasManyOrHasOneDependent`, `InverseOf`, `SkipsModelValidations`, `FindEach`. `RSpec/NoExpectationExample` (spec with no assertion) |
| Manual fix | `Style/` cops with no autocorrect, `Naming/`, `Rails/` cops marked unsafe, `Performance/` |
| Format | `Layout/` (fixed by `-x` and `-a`), `Style/StringLiterals`, trailing commas, hash syntax |
| Design signal | `Metrics/`: `MethodLength`, `AbcSize`, `CyclomaticComplexity`, `PerceivedComplexity`, `ClassLength`. Refactor until the cop passes. Keep behavior |
| Style | `Style/` in general |
| Security | `Security/`. Fix it, and hand deeper review to `security-analysis` |

Fix the cause, not the symptom:

```ruby
# Lint/SuppressedException: error swallowed
begin
  sync_account(account)
rescue StandardError
end

# Fix: rescue the narrow error and handle it
begin
  sync_account(account)
rescue Faraday::TimeoutError => e
  Rails.logger.warn("sync timed out for #{account.id}: #{e.message}")
end
```

Review unsafe corrections by hand when they depend on the receiver type, or touch a method that metaprogramming calls by name.

## Suppressions

We do not add suppressions. Do not write `# rubocop:disable`, `# rubocop:todo`, or `# rubocop:disable all`. Do not edit `.rubocop.yml` or `.rubocop_todo.yml` to exclude a file or turn off a cop. Fix the code.

Existing directives in the scope stay as they are, unless `Lint/RedundantCopDisableDirective` reports one as useless. Then remove it. Mention existing ones you saw in the report.

## Tests

Run the project's test command after each group of fixes (`bundle exec rspec <paths>`, `bin/rails test <paths>`, or the `Rakefile` task). Run the tests that cover the changed files, then the wider suite if the change is large.

## My preferences

Owner's preferences for Ruby. This section is empty until the owner fills it in. The project config still wins when it disagrees. Suggested topics:

- Which tool to run when the project has no config (`rubocop`, `standard`).
- Preferred string quote style, hash syntax, and line length, for choices the config leaves open.
- Refactor style for `Metrics/` cops (guard clauses, extract method, service object).
- How to fix `Lint/SuppressedException` and similar findings.
- Anything to always flag in the report.
