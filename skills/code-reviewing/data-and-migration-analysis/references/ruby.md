# Ruby and Rails data and migration analysis

Tools, commands, and Rails-specific traps for `data-and-migration-analysis`. The project's own conventions and tool config win over everything here. Run only tools the project already uses, or ask first.

## Detect the setup

- Migrations: `db/migrate/*.rb`. Schema: `db/schema.rb` or `db/structure.sql`. Multiple databases: `db/<name>_migrate/`.
- Safety gems in the `Gemfile` or `Gemfile.lock`: `strong_migrations`, and gems with the same role such as `online_migrations` or `safe-pg-migrations`.
- Schema check gems: `active_record_doctor`, `database_consistency`.
- Config: `config/initializers/strong_migrations.rb`, `.active_record_doctor.rb`, `.database_consistency.yml`.
- Engine and version: `config/database.yml` (`adapter`), `docker-compose.yml`, CI service images. For PostgreSQL, `StrongMigrations.target_version` states the production version.

## Commands

### Tools that only read

These need a database connection, but they only read the schema. Run them against a local development or test database.

| Tool | Command |
|---|---|
| All `active_record_doctor` detectors | `bundle exec rake active_record_doctor` |
| One detector | `bundle exec rake active_record_doctor:missing_unique_indexes` |
| `database_consistency` | `bundle exec database_consistency` |

They compare models with the schema. Run them on the scope, then keep only the results for the tables and models in the diff.

### Commands that change a database

Run only against a local, disposable database. Never against shared, staging, or production. Check `DATABASE_URL`, `config/database.yml`, and `RAILS_ENV` first. If unsure, ask.

| Goal | Command |
|---|---|
| Run pending migrations. `strong_migrations` raises on unsafe operations | `bin/rails db:migrate` |
| Round trip: roll back and run again | `bin/rails db:migrate:redo` |
| Roll back the last migration | `bin/rails db:rollback STEP=1` |
| Which migrations ran | `bin/rails db:migrate:status` |

After a run, read `git diff db/schema.rb` (or `structure.sql`). It should show only what the migration did. Unrelated lines mean the local database version or earlier state differs. A migration run rewrites the schema file, so tell the user it changed. Do not restore it yourself, because the file may hold the user's own uncommitted changes.

## strong_migrations: what it checks

The gem raises at migrate time on the operations below, and prints the safe steps. Use it as a candidate list when you read a migration, and verify each by hand. Checks, from its documentation:

| Operation | Safe approach |
|---|---|
| `remove_column` | Add the column to `ignored_columns` in the model, deploy, then remove in a later release |
| `change_column`, `rename_column`, `rename_table` | New column or table, dual write, backfill, switch reads, drop the old one |
| `add_index` (PostgreSQL) | `algorithm: :concurrently` with `disable_ddl_transaction!` |
| `add_reference` (PostgreSQL) | Index with `algorithm: :concurrently` |
| `add_foreign_key`, `add_check_constraint` (PostgreSQL) | `validate: false`, then validate in a separate migration |
| `change_column_null` to `false` (PostgreSQL) | Check constraint with `validate: false`, validate, then set `NOT NULL` |
| `add_column` with a volatile default (PostgreSQL) | Add without a default, then `change_column_default`, then backfill |
| `add_column` of `json` (PostgreSQL) | Use `jsonb` |
| `add_unique_constraint` (PostgreSQL) | Unique index concurrently first, then add the constraint on it |
| `create_table` with `force: true` | Remove `force` |
| `execute` (raw SQL) | Review by hand, then mark with `safety_assured` |
| Non-unique index on four or more columns | Limit to three columns |

Backfill guidance from the same documentation: batch, throttle, and run outside a transaction.

### `safety_assured`

`safety_assured { ... }` turns the check off for a block. Treat every new one as a finding to verify:

- Is there a stated reason (a comment, the PR description, an earlier deploy that ignored the column)?
- Is the safe approach from the table above possible and skipped?
- Is the table small, and is that a known fact?

Also check the initializer for changes to `start_after`, `safe_by_default`, or disabled checks. Do not edit it from here.

## Rails traps

### Reversibility

```ruby
# Irreversible: remove_column without a type cannot be reversed
def change
  remove_column :users, :legacy_name
end

# Reversible
def change
  remove_column :users, :legacy_name, :string
end
```

`execute` in `change` is irreversible unless wrapped in `reversible` or split into `up` and `down`. Check that a data-destroying `down` is intended.

### Models inside migrations

```ruby
# Fragile: breaks later when the model changes or is deleted
User.where(plan: nil).update_all(plan: "free")

# Safe: a small class that only knows the table
class MigrationUser < ActiveRecord::Base
  self.table_name = "users"
end
MigrationUser.where(plan: nil).in_batches { |batch| batch.update_all(plan: "free") }
```

### Backfills

```ruby
# Unsafe: one statement over the whole table, in the migration transaction
def up
  User.update_all(status: "active")
end

# Safer: no DDL transaction, batches, a pause between them
disable_ddl_transaction!

def up
  MigrationUser.unscoped.in_batches(of: 10_000) do |batch|
    batch.update_all(status: "active")
    sleep(0.01)
  end
end
```

Even better: a rake task or a job for the data, and a migration only for the schema. The `where(status: nil)` condition makes a re-run safe.

### Dropping and renaming

- `ActiveRecord` caches column names. After a column is dropped, running processes that still know the column can fail on insert and update. `ignored_columns` first.
- `rename_column` and `rename_table` break old code at once. Do not rename in place on a live system.
- `add_column ... null: false` without a default fails on a table with rows.

### Validations and the schema

| Code | Missing in the schema | Tool that finds it |
|---|---|---|
| `validates :email, uniqueness: true` | Unique index | `active_record_doctor:missing_unique_indexes`, `database_consistency` |
| `validates :name, presence: true` | `NOT NULL` | `active_record_doctor:missing_non_null_constraint` |
| `belongs_to :account` | Foreign key | `active_record_doctor:missing_foreign_keys`, `database_consistency` |
| `has_many :items, dependent: :destroy` and the foreign key | Matching `on_delete` | `active_record_doctor:incorrect_dependent_option` |
| A boolean column | `NOT NULL` and a default | `database_consistency` (three-state boolean) |
| `validates :qty, numericality: { greater_than: 0 }` | Check constraint | `database_consistency` |
| A new foreign key column | Index | `active_record_doctor:unindexed_foreign_keys` |
| An integer primary key | 64-bit key | `active_record_doctor:short_primary_key_type` |

### Races

```ruby
# Race: two requests can both pass the check
return if Coupon.exists?(code: code)
Coupon.create!(code: code)

# Safe: unique index in the database, and handle its error
begin
  Coupon.create!(code: code)
rescue ActiveRecord::RecordNotUnique
  # already exists: treat as success or return a clear error
end
```

- `find_or_create_by` with no unique index is the same race. `create_or_find_by` relies on the unique index.
- Read-modify-write: use `with_lock`, `lock!`, an atomic `update_counters` or `increment!`, or optimistic locking (`lock_version`).
- Check the state in the `UPDATE` itself when the code moves a record from one state to another.

### Writes that skip checks

`update_all`, `delete_all`, `update_column`, `update_columns`, `insert_all`, `upsert_all`, and raw `execute` skip validations and callbacks. Ask what the model relies on in callbacks: counter caches, audit rows, derived fields, search index updates.

### Transactions and jobs

- Several writes that must succeed together need `ActiveRecord::Base.transaction`.
- A job enqueued inside a transaction can run before the commit and miss the data. Use `after_commit`, or enqueue after the block.
- `rescue` inside a transaction block that swallows the error prevents the rollback.

### Sensitive data

For a new personal or secret column, check whether the project uses `encrypts` (Active Record encryption) for similar data. Deeper exposure review belongs to `security-analysis`.

