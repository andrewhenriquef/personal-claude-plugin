# Go data and migration analysis

Tools, commands, and Go-specific traps for `data-and-migration-analysis`. The project's own conventions and tool config win over everything here. Run only tools the project already uses, or ask first.

## Detect the setup

- Migration tool:
  - goose: files with `-- +goose Up` and `-- +goose Down` annotations, or Go migrations registered with goose.
  - golang-migrate: pairs of files named `<version>_<name>.up.sql` and `<version>_<name>.down.sql`.
  - Atlas: `atlas.hcl` and an `atlas.sum` file next to the migrations.
  - GORM `AutoMigrate`, or `ent` auto-migration, called from application code.
- Queries: `sqlc.yaml` (generated code from SQL), `sqlx`, `database/sql`, `pgx`, GORM, `ent`.
- Engine: driver imports (`github.com/jackc/pgx`, `github.com/lib/pq`, `github.com/go-sql-driver/mysql`), the DSN in config, `docker-compose.yml`, CI service images.
- A `migrate` or `db` target in `Makefile` or `Taskfile` shows how migrations run, and where.

## Commands

### Tools that only read

| Tool | Command |
|---|---|
| Squawk, PostgreSQL SQL files (static) | `squawk <path>/<new migration>.sql` |
| `sqlc` generated code is in sync with the SQL | `sqlc diff` (check with `sqlc --help` on the installed version) |

Squawk reads SQL and does not need a database. Lint only the SQL files in scope. If a project has `.squawk.toml`, the tool reads it. Do not edit it from here.

### Tools that need a database

Run only against a local, disposable database. Never against shared, staging, or production. If you cannot tell which database a command uses, ask first.

| Goal | Command |
|---|---|
| Atlas lint of migrations changed against a branch | `atlas migrate lint --dev-url "<disposable dev database URL>" --git-base <main branch>` |
| Atlas lint of the latest N migrations | `atlas migrate lint --dev-url "<url>" --latest N` |

Atlas uses a dev database to replay the migrations. A `docker://` dev URL starts a throwaway container. Atlas analyzers report destructive changes, data-dependent changes (for example adding a unique index or `NOT NULL` to a column that has rows), backward-incompatible changes (renames and drops), non-concurrent index creation, and out-of-order migrations. Settings live in `atlas.hcl`. Do not add `atlas:nolint` or edit the lint block from here.

## Migration tool traps

### Transactions

Most tools run a whole migration file in one transaction. Some statements cannot run inside one.

- **goose:** the whole file runs in one transaction. `CREATE INDEX CONCURRENTLY` fails inside it. Put `-- +goose NO TRANSACTION` at the top of that file, and keep the file to that one concern.
- **golang-migrate:** to create an index concurrently, put the statement in its own migration file. Check how the project sets up multi-statement mode.

```sql
-- Unsafe: blocks writes on a busy table, and fails inside a transaction if made concurrent
CREATE INDEX idx_orders_user_id ON orders (user_id);

-- Safe on PostgreSQL (goose)
-- +goose NO TRANSACTION
-- +goose Up
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_user_id ON orders (user_id);
-- +goose Down
DROP INDEX CONCURRENTLY IF EXISTS idx_orders_user_id;
```

A failed concurrent build leaves an `INVALID` index. `IF NOT EXISTS` then skips it on retry. Check for invalid indexes after a failure.

### Down migrations

- Does the `down` section or `.down.sql` file exist, and does it undo the `up`?
- A `down` that drops a column or table destroys data. Is that intended?
- A data change with no `down` is fine if it is stated.

### Applied migrations are not edited

- Atlas: editing an applied file changes the hash in `atlas.sum`. A change with no matching `atlas.sum` update is a problem.
- goose and golang-migrate record the version as applied and do not re-run it. An edited migration changes new environments only, and the databases drift.
- Check with git: a migration file that exists on the main branch and is modified here is a finding.

### Version order

- goose supports timestamp and sequential versions. A new version lower than one already applied needs the tool's out-of-order option.
- golang-migrate versions are numbers. A gap or a duplicate number breaks the order.

### `AutoMigrate` at startup

GORM `AutoMigrate` or `ent` auto-migration run from application code changes the schema when the process starts. Every instance runs it, nothing reviews it, there is no lock timeout, and it never drops a column. Report it when it runs against production. Prefer versioned migrations.

## Go data code traps

### Transactions

```go
// Bug: the second write uses db, not tx. It commits even if the transaction rolls back.
tx, err := db.BeginTx(ctx, nil)
if err != nil {
	return err
}
defer tx.Rollback()
if _, err := tx.ExecContext(ctx, `UPDATE accounts SET balance = balance - $1 WHERE id = $2`, amt, from); err != nil {
	return err
}
if _, err := db.ExecContext(ctx, `UPDATE accounts SET balance = balance + $1 WHERE id = $2`, amt, to); err != nil {
	return err
}
return tx.Commit()
```

Check:

- Every statement inside the transaction uses `tx`, not `db`.
- The commit error is returned. `defer tx.Rollback()` after a successful commit is fine (it returns `sql.ErrTxDone`).
- A repository method that takes `*sql.DB` but is called inside a transaction escapes it. Look for an interface that works with both (`DBTX`).
- No HTTP call, publish, or email inside the transaction, or before the commit succeeds.
- A job or event published after the commit, not before.

### Check-then-insert and read-modify-write

```go
// Race: two requests can both see no row
var exists bool
db.QueryRowContext(ctx, `SELECT EXISTS (SELECT 1 FROM coupons WHERE code = $1)`, code).Scan(&exists)
if !exists {
	db.ExecContext(ctx, `INSERT INTO coupons (code) VALUES ($1)`, code)
}

// Safe: unique index, and treat the violation as a normal result
_, err := db.ExecContext(ctx, `INSERT INTO coupons (code) VALUES ($1)`, code)
var pgErr *pgconn.PgError
if errors.As(err, &pgErr) && pgErr.Code == "23505" { // unique_violation
	return ErrCouponExists
}
```

- Unique violations: PostgreSQL error code `23505`. Check the driver's error type. MySQL uses error number `1062`.
- Read-modify-write: `UPDATE ... SET n = n + 1`, `SELECT ... FOR UPDATE` in a transaction, or a version column.
- Moving a record between states: put the current state in the `WHERE` and check the rows affected.

### Updates that erase data

```go
// Bug: a field the caller did not send is a zero value, and the update writes it
db.ExecContext(ctx, `UPDATE users SET name = $1, age = $2 WHERE id = $3`, in.Name, in.Age, id)

// Clear: build the update from the fields that were present (pointer fields, or a map)
```

Check partial updates built from a struct. A Go zero value (`""`, `0`, `false`) cannot tell "not set" from "set to empty". Use pointer fields, or build the update from the fields that were present. ORMs differ: GORM `Updates` with a struct skips zero values, so a caller cannot set a field to `0` or `false` that way. Check which behavior the code needs.

### NULL handling

- Scanning a `NULL` column into `string`, `int`, or `time.Time` fails at runtime. Check for `sql.NullString`, `sql.Null[T]`, or pointers.
- A nullable column in the migration and a plain type in the struct is a mismatch.

### Types

- Money as `float64`. Use integer minor units or an exact decimal type.
- Time: `timestamptz` in the schema and `time.Time` in code. Store UTC. A `timestamp` without a zone loses the offset.
- IDs: 64-bit integers or UUIDs. `int32` fields for a key that can grow.

### Bulk and raw SQL

- Raw SQL and `sqlc` queries skip any hooks that the ORM would run. Ask what the model relies on.
- A bulk update or delete with a missing or wrong `WHERE` affects the whole table. Check the condition and the rows affected.
- GORM `Delete` on a model with a `DeletedAt` field is a soft delete. Check that queries, unique indexes, and counts handle it.

## Not in this skill

Query speed, N+1, and context timeouts on queries belong to the performance and reliability reviews. Linters such as `rowserrcheck` and `sqlclosecheck` run in `static-analysis`.
