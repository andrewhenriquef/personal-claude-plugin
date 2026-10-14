# Ruby / Rails

Use with `tech-debt-analysis` when the scope has a `Gemfile` or `*.rb` files. The commands are starting points. Check flags with `--help` on the installed version. Run a tool only if it is already installed. Never pass an autocorrect flag (`-a`, `-A`, `-x`).

## Skip these paths

`vendor/`, `node_modules/`, `tmp/`, `log/`, `coverage/`, `public/assets/`, `public/packs/`, `db/schema.rb`, `db/structure.sql`, generated protobuf files (`*_pb.rb`).

**Write-once:** `db/migrate/` (never a hotspot).

**Config-like, change by design:** `config/routes.rb`, `config/locales/**`, `spec/factories/**`. Keep them out of the hotspot list. Mention them under "Looks bad but is fine" if they rank high.

## Complexity proxy

1. Check `.rubocop.yml` and `.rubocop_todo.yml` for the `Metrics/` cops (`CyclomaticComplexity`, `PerceivedComplexity`, `AbcSize`, `MethodLength`, `ClassLength`). The limits there are the project's thresholds. A cop disabled in the todo file is also a window (W4).
2. Read the offenses without fixing them:

```sh
bundle exec rubocop --only Metrics/CyclomaticComplexity,Metrics/PerceivedComplexity,Metrics/AbcSize,Metrics/MethodLength,Metrics/ClassLength --format json <files>
```

3. `flog <paths>` scores methods by ABC-like complexity, if installed.
4. Fall back to lines of code.

## Dead code and duplication

- `debride --rails --whitelist <file> app lib` lists methods that look unused. It is static, so expect false positives. In Rails, a method can be called by a route, a callback, `send`, `constantize`, a view, a job name in a string, or a gem. For each hit, `git grep` the method name as a string, symbol, and in `config/routes.rb` and `app/views`. If a dynamic path is possible, send it to "Needs human check".
- `flay app lib` finds structural duplication (same shape, different names). Read both blocks before you call it duplicated knowledge.

## Window patterns (set C)

Use `git grep -nwE` for words and `[[:space:]]` for spaces (see the portability note in [broken windows](broken-windows.md)).

- **W2:** `TODO|FIXME|HACK|XXX` (whole word).
- **W3:** `xit|xdescribe|xcontext|skip|pending` in `spec/` and `test/` (whole word), and `skip:` or `pending:` options.
- **W4:** `rubocop:disable`, `:nocov:`, the size and `Exclude:` lists of `.rubocop_todo.yml`, entries in `config/brakeman.ignore`.
- **W5:** `rescue nil`; a bare `rescue` or `rescue => e` followed by `end` or `nil`; a handler with no `raise`, `Rails.logger`, or error reporter. Use `git grep -n -A2 'rescue'` and read each hit.
- **W6:** CI `allow_failure`, `continue-on-error`, commented jobs; ignore entries in `.bundler-audit.yml`.
- **Leftovers:** `binding.pry`, `byebug`, `debugger`, `binding.irb`, and stray `puts`/`pp` in `app/` and `lib/` are windows in committed code.

## Map a source file to its test

| Source | Test |
|---|---|
| `app/<path>/<name>.rb` | `spec/<path>/<name>_spec.rb` (or `test/<path>/<name>_test.rb`) |
| `lib/<path>/<name>.rb` | `spec/lib/<path>/<name>_spec.rb` |

If there is no file, search for the class name in `spec/` and `test/` (including request, feature, and shared-example specs) before you say "no test found".

## Traps

- Rails autoloading and callbacks hide callers. A "dead" method can be live.
- `default_scope`, concerns, and `method_missing` hide coupling. Change coupling can show it when imports cannot.
- A fat model with many concerns can have low per-file churn and high real cost. Check the concerns it includes.
- Large `spec/` files are often long by nature (set E, "looks bad but is fine"), unless examples repeat the same setup.
