# Migration safety

Use in Step 3 of `data-and-migration-analysis`. Each row is a question about the migration, not a pattern to grep for. A row is a finding only when the engine, version, table size, and deploy order make it matter (Step 4).

The PostgreSQL rows follow [strong_migrations](https://github.com/ankane/strong_migrations), [Squawk rules](https://squawkhq.com/docs/rules), and [Atlas analyzers](https://atlasgo.io/lint/analyzers). The lock behavior is general PostgreSQL knowledge. Check it against the docs for the engine version in use.

## Facts to have first

Engine and version, migration tool, table size, write traffic, how migrations run, rolling deploy or not. If you do not have them, see Step 0 in `SKILL.md`.

## Operations on PostgreSQL

| Operation | Risk | Safe approach |
|---|---|---|
| Add a column, nullable, no default | Fast. No risk | None needed |
| Add a column with a constant default | Fast on PostgreSQL 11 and later. A full table rewrite on older versions | Check the version. On old versions add the column, then set the default, then backfill in batches |
| Add a column with a volatile default (for example `gen_random_uuid()`) | Rewrites the table under a lock | Add the column with no default, set the default for new rows, backfill in batches |
| Add a `NOT NULL` column with no default | Fails on a table that has rows | Add nullable, backfill, then add the constraint |
| Set `NOT NULL` on an existing column | Scans the table under an exclusive lock | Add a `CHECK (col IS NOT NULL)` as `NOT VALID`, validate it, then set `NOT NULL`. On PostgreSQL 12 and later, the validated check lets the `SET NOT NULL` skip the scan |
| Change a column type | Usually rewrites the table and blocks reads and writes | Expand and contract: new column, dual write, backfill, switch reads, drop the old one |
| Rename a column or a table | Old code that uses the old name breaks the moment it runs | Expand and contract. Do not rename in place on a live system |
| Drop a column or a table | Old code that still reads it breaks. The data is gone | Stop using it in code first, deploy, then drop in a later release. Take a backup. See "Compatibility" |
| Create an index | Blocks writes for the whole build | `CREATE INDEX CONCURRENTLY`, outside a transaction. A failed concurrent build leaves an `INVALID` index. Check for it and drop it |
| Drop an index | Takes a lock | `DROP INDEX CONCURRENTLY`, outside a transaction |
| Add a foreign key | Validates every row and locks both tables | Add it `NOT VALID`, then `VALIDATE CONSTRAINT` in a separate step |
| Add a check constraint | Same as a foreign key | `NOT VALID`, then validate |
| Add a unique constraint | Builds a unique index under a lock | Build the unique index concurrently first, then attach it as the constraint |
| Add a reference column with an index | The index build blocks writes | Concurrent index in its own step |
| Add or rename an enum value | Renaming breaks old code. Adding a value in a transaction can be restricted on older versions | Add a new value, switch the code, backfill, then retire the old value |
| Use `json` for a new column | `json` has no equality operator, so some queries fail | Use `jsonb` unless the exact text matters |
| Raw SQL in a migration | The tool cannot check it | Read it line by line as if it were a new migration |

**The lock queue.** A migration that waits for a lock blocks every query that arrives after it, even queries that would have been fine. A short statement on a busy table can cause an outage because it waits. Ask: is a `lock_timeout` set, and does the migration retry? (`strong_migrations` can set one: check its config.)

**Long transactions.** One transaction that holds a DDL lock and also runs a data update keeps the lock for the whole update. Keep DDL and data changes in separate migrations.

## Operations on MySQL

Behavior varies by version, storage engine, and the exact operation. Check the Online DDL table in the docs for the version in use. Questions to ask:

- Does this operation run in place without blocking writes, or does it copy the table?
- Is the algorithm and lock level stated (`ALGORITHM=INPLACE, LOCK=NONE`)? Stating them makes an unsafe operation fail instead of silently locking the table.
- Is the table large enough that the project would use an online schema change tool (`gh-ost`, `pt-online-schema-change`)? Does the repo already use one?

## Compatibility: two versions run at once

Deploys are not atomic. Rolling deploys, slow instances, and rollbacks all mean two code versions meet one schema. For every schema change, answer both:

| Case | Question |
|---|---|
| **Old code, new schema** | Does the code that is still running break? Look for dropped or renamed columns and tables, new `NOT NULL` columns the old code does not fill, and type changes. ORMs that cache column lists break on a dropped column |
| **New code, old schema** | Does the new code break if the migration has not run yet, or if the migration is rolled back? Look for reads of a new column |

Find out when migrations run. Before the deploy, the old code meets the new schema. After the deploy, the new code meets the old schema until the migration finishes.

### Expand and contract

A breaking change becomes several deploys, each safe on its own:

1. **Expand:** add the new column, table, or index. Nothing reads it yet.
2. **Migrate:** deploy code that writes to both. Backfill old rows in batches.
3. **Switch:** deploy code that reads the new structure.
4. **Contract:** stop writing the old structure. In a later release, drop it.

A pull request that does all four steps at once is a finding. A pull request that does one step and says which one is correct.

## Backfills

A backfill changes existing rows. It is the usual cause of long locks and slow deploys. Check:

- **Batched.** Updates run in small ranges, not one `UPDATE` over the whole table.
- **Throttled.** There is a pause between batches, so replicas and other queries keep up.
- **Out of the migration transaction.** One transaction over all rows holds locks and bloats the log.
- **Resumable and idempotent.** A restart does not redo or corrupt finished work. The `WHERE` clause skips rows that are done.
- **Separate from the schema change.** A migration file for the schema, a job, task, or script for the data.
- **No application models inside the migration.** A model can change later and break an old migration. Use a small class or SQL inside the migration.
- **Verified.** After the backfill, is there a check that no row is left in the old state, before a `NOT NULL` or a drop?

## Reversibility

- Does `down` (or `rollback`) exist? Does it restore the schema?
- A `down` that drops a column or table destroys data. Is that acceptable, and is it stated?
- Can the code be rolled back after the migration ran? If not, say it.
- Is a migration with raw SQL or data changes marked irreversible on purpose, not by accident?

## Migration hygiene

- **Edited an applied migration.** Compare with the main branch: a migration file that **exists there and changed here** is a finding. Some tools never re-run it, so environments drift. Some tools reject it with a checksum error. The fix is a new migration.
- **Schema file out of sync.** `schema.rb`, `structure.sql`, or generated code changed with no matching migration, or the reverse. Unrelated lines in a schema diff point to a migration run on a different database version.
- **Order.** The new migration's version is older than one already on the main branch. Check how the tool handles that.
- **One concern per migration.** A schema change and a backfill and an index in one file make failure and rollback hard.
- **Name and content match.** `add_index_to_orders` that also drops a column is a finding.

## Tools that work on SQL

Use only if the project already has them. Treat results as candidates.

- **Squawk** (PostgreSQL SQL files, static): `squawk <file>.sql`. Rules include `adding-field-with-default`, `adding-not-nullable-field`, `ban-drop-column`, `changing-column-type`, `require-concurrent-index-creation`, `prefer-timestamptz`, and `renaming-column`. Settings live in `.squawk.toml`. Do not add `-- squawk-ignore` or `excluded_rules` from here.
- **Atlas** (`atlas migrate lint`): needs a dev database URL, and a way to pick migrations (`--latest N` or `--git-base <branch>`). Analyzers include destructive changes (DS101 to DS103), data-dependent changes (MF101 to MF104), backward-incompatible changes (BC101 to BC104), non-concurrent index creation, and non-linear history. It creates changes in a dev database, so it needs a disposable one.

## Exclusions and precedents

Do not report:

- A new table, and indexes or constraints on it, created in the same migration. No traffic and no rows.
- Operations on a table that the owner has said is small or unused, and that is stated in the report as an assumption.
- A migration already merged to the main branch and applied everywhere, unless this change edits it.
- Seeds, fixtures, and local-only scripts.
- A lock risk on a version where the operation is safe (check the version).
- `safety_assured` or an equivalent marker that has a stated reason and a completed safe first step (for example the column was ignored in a prior release).

Precedents:

- An unsafe operation on a table of unknown size is "Needs human check", not a finding and not a drop.
- A missing `down` on a data-destroying migration is a finding only if rollback is part of the deploy plan.
- Style and naming are LOW.
