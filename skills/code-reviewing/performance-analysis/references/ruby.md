# Ruby and Rails performance analysis

Tools, commands, and Rails-specific traps for `performance-analysis`. The project's own conventions and tool config win over everything here. Run only tools the project already uses, or ask first.

## Detect the setup

Look in the `Gemfile` and `Gemfile.lock` for:

- Cops: `rubocop-performance`, `rubocop-rails`.
- N+1 detectors: `bullet`, `prosopite` (it needs `pg_query` on PostgreSQL).
- Profilers and benchmark tools: `benchmark-ips`, `stackprof`, `memory_profiler`, `rack-mini-profiler`, `rails-pg-extras`.
- Performance helpers: `oj`, `ar_lazy_preload`, caching gems, and the cache store set in `config/environments/*.rb`.

Also read the Rails version and the database adapter. Some advice depends on the version.

## Read-only linter run

Performance cops are candidate generators. Run them without autocorrect and without editing the config. `--only` limits the run to the cops or departments you name.

```
bundle exec rubocop --only Performance,Rails/FindEach,Rails/Pluck,Rails/PluckInWhere,Rails/WhereExists,Rails/RedundantActiveRecordAllMethod --force-exclusion <files>
```

- `<files>` are the changed Ruby files in scope (see `static-analysis`, section "Scope unit", for a command that builds the list).
- If the project config does not load `rubocop-performance` or `rubocop-rails`, the run fails or skips those cops. If the gem is already in the bundle, load it for the run from the command line (check `bundle exec rubocop --help` for `--plugin` or `--require`). If it is not in the bundle, do not install it. Say so, and list the cops under "Linter rules to consider".
- Never pass `-a` or `-A` here. Fixing belongs to `static-analysis`, and only for rules the project enables.

### How to read the cops

Most `Performance/` cops are micro-optimizations with the same complexity (`RegexpMatch`, `Size`, `StartWith`, `StringInclude`, `Sum`, `FlatMap`, `MapCompact`, and similar). Report them only when the code is on a hot path and a measurement shows a cost. Otherwise drop them.

| Cops | What they can mean |
|---|---|
| `Rails/FindEach` | `all.each` loads every record at once. Memory grows with the table. A real finding when the table is large |
| `Rails/Pluck`, `Rails/PluckInWhere` | Loading models to read one column, or a subquery written as two queries. Check the size |
| `Rails/WhereExists`, `Rails/RedundantActiveRecordAllMethod` | Query shape. Usually small, check the path |
| `Performance/IoReadlines` | `readlines` reads the whole file into memory. Real for large files |
| `Performance/CollectionLiteralInLoop`, `Performance/ConstantRegexp`, `Performance/ChainArrayAllocation` | Allocation inside a loop. Real only on a hot loop with a measurement |
| `Performance/Count`, `Performance/Detect`, `Performance/Size`, `Performance/Sum` and other cops marked unsafe by RuboCop | They can be wrong on ActiveRecord relations, because the receiver may be a relation, not an array. Read the receiver before you report |

## N+1 and query count

Use these when the project has the gem. Do not install them.

- **Bullet** reports N+1 queries, unused eager loading, and missing counter caches. In tests it can raise on a finding (`Bullet.raise = true`) with `Bullet.start_request` and `Bullet.end_request` around each example. It can give false positives. It is meant for development and test, not production.
- **Prosopite** flags queries that share a call stack and a query fingerprint, so it catches N+1 that Bullet misses, such as lookups in a loop with `find`, and repeated `first`, `last`, or `pluck` on associations. Wrap each example in `Prosopite.scan` and `Prosopite.finish`.

Without these gems: run the covering spec with the test log on, and count the statements that repeat with only the parameter changed (see `evidence.md`). Confirm with one item and with several items.

Treat detector output as candidates. Open the call site and check that the code runs on a hot path.

## Rails traps

### N+1 and loading

```ruby
# N+1: one query for orders, one per order for the customer
Order.all.each { |o| puts o.customer.name }

# One extra query for all customers
Order.includes(:customer).each { |o| puts o.customer.name }
```

- `includes` and `preload` run a second query. `eager_load` uses a join. Use `eager_load` when the code filters or orders on the association.
- Serializers, Jbuilder views, GraphQL resolvers, and `as_json` that read an association per item hide N+1. Check them.
- `.count` runs a `COUNT` query each time, `.size` uses the loaded records when present, `.exists?` stops at one row. Check which one a loop uses.
- `where(...).map(&:id)` loads models to read ids. Use `ids` or `pluck(:id)`.
- Loading models to count or check existence (`.to_a.size`, `.all.any?` on a large table).
- Callbacks that run a query per record on a bulk path.

### Large data

- `Model.all.each` or `.where(...).each` on a large table: use `find_each` or `in_batches`.
- `.to_a`, `.load`, or `.map` over a whole large relation.
- `File.read` and `readlines` on large files: use `File.foreach` or `each_line`.
- `CSV.read` of a large upload: use `CSV.foreach`.
- Building a large string with `+=` in a loop: use `<<` or `Array#join`.
- Exports and reports that build the whole document in memory: stream the response.

### Writes in a loop

- `update`, `save`, or `create` per item: one round trip per row. `update_all`, `insert_all`, and `upsert_all` are faster but skip validations and callbacks. Check what the model relies on.
- Enqueuing a job per item in a loop: Rails 7.1 and later has `ActiveJob.perform_all_later` for bulk enqueue. Check the Rails version.

### Pagination and ordering

- `offset` with a large page number scans and skips all earlier rows. Keyset pagination (`where("id > ?", last_id).order(:id).limit(n)`) stays fast.
- `order` and `where` on columns with no index, on a large table. Check `EXPLAIN` on realistic data. Adding the index is a schema change: see `data-and-migration-analysis`.
- `distinct`, `group`, and `count` over a large unfiltered table on a request path.
- `default_scope` that adds a join or order to every query.

### Views and caching

- `render partial: ..., collection:` renders faster than a loop that renders a partial per item.
- Fragment and Russian-doll caching with a wrong or missing key serves wrong data. Check the cache key includes what changes the output.
- `Rails.cache.fetch` without `expires_in` on data that grows or changes. Check the cache store limit.
- Memoization with `||=` repeats work when the value is `nil` or `false`.

### Ruby-level cost

Only on hot loops, and only with a measurement:

- `Regexp.new` or a regex literal with interpolation inside a loop: build it once.
- `sort`, `select`, or `include?` on a large array inside a loop: build a `Hash` or `Set` once.
- `map.flatten`, `select.map`, and chained enumerators that allocate intermediate arrays: `flat_map`, `filter_map`, or `lazy` for large input.
- `OpenStruct` in a hot path (slow to create and to access).

## Measure

| Goal | Tool |
|---|---|
| Time two versions of a small pure method | `benchmark-ips` if the project has it. Otherwise `Benchmark.realtime` or `Benchmark.bm` from the standard library, repeated, comparing medians |
| Where time goes | `stackprof`, if the project has it |
| Where memory goes | `memory_profiler`, if the project has it |
| Query plan | `relation.explain` or `EXPLAIN` on a local database. See the table-size caveat in `evidence.md` |
| Query count | The test log, or `ActiveSupport::Notifications` for `sql.active_record` in a covering test, ignoring schema and cached queries |

Run measurements on local data only, in the test or development environment. For the base-versus-change comparison, use the worktree steps in `evidence.md`. Rails tests use a shared test database, so do not run two test runs at the same time.
