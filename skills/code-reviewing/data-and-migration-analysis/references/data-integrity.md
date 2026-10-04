# Data integrity review questions

Use in Step 3 of `data-and-migration-analysis`. Each row is a question about the data model or the write path, not a pattern to grep for. A row is a finding only when you can name the bad data or the failure that results. Tools that check some of these automatically (`database_consistency`, `active_record_doctor`) are listed in the language references.

## Constraints: does the database guarantee it?

| Ask | Why |
|---|---|
| Is every required value `NOT NULL` in the database, not only validated in code? | Code paths that skip validation (scripts, bulk writes, other services) insert nulls |
| Is every uniqueness rule backed by a unique index? Does the index cover the same columns and scope as the validation? | A uniqueness check in code races. Two requests at once insert duplicates |
| Is every reference a foreign key? Is the delete behavior stated (restrict, cascade, set null)? | Without it, rows point at nothing. The wrong cascade deletes data silently |
| Are value rules (range, positive, allowed set) a check constraint or an enum, not only code? | Same reason as `NOT NULL` |
| Are boolean columns `NOT NULL` with a default? | A nullable boolean has three states, and the code handles two |
| Does a new default value make sense for old rows and for new rows? | A default changes what an unset value means |

## Types

| Ask | Why |
|---|---|
| Is money stored as an exact type (decimal, or integer minor units), never a float? | Floats round |
| Are timestamps time-zone aware (`timestamptz` or stored in UTC)? | A local time without a zone is ambiguous and breaks across daylight saving changes |
| Are identifiers wide enough (64-bit) for the expected growth? Do key and foreign key types match? | An integer key can run out. A mismatch blocks joins or hurts index use |
| Is a text column's length limited, or intentionally unlimited? Does a limit match the validation? | A mismatch truncates or rejects data at the database |
| Does an enum map to the same values in code and in the database? | Different values cause bad reads |
| Is `json` or `jsonb` used for data that has a fixed shape and gets queried or constrained? | A column per field gives constraints and indexes |

## Races: what happens with two requests at once?

| Ask | Example |
|---|---|
| Check-then-insert: does the code look for a row, then create it? | `find`, then `create`, with no unique index. Two requests create two rows |
| Read-modify-write: does the code read a value, change it in memory, and write it back? | A balance, a counter, or a stock count. Two requests lose one update |
| Is there a lock (`SELECT ... FOR UPDATE`), an atomic update (`SET n = n + 1`), or a version column for optimistic locking? | Without one, the later write wins |
| Does a unique violation get handled as a normal outcome, not as a crash or a swallowed error? | The unique index is the guard. The code must handle its error |
| Does a state change check the current state in the same statement (`WHERE status = 'open'`)? | Check and update in one statement cannot be interleaved |

## Transactions: all or nothing

| Ask | Why |
|---|---|
| Do several writes that must succeed together run in one transaction? | A failure between them leaves half the data |
| Are all the writes using the transaction handle, not the general connection? | A write outside it commits even when the transaction rolls back |
| Is the commit error checked? Does an error path roll back? | An unchecked commit loses data silently |
| Does an external call (HTTP, queue publish, email) happen inside a transaction, or before it commits? | A rollback cannot undo the call. A job can run before the data is visible |
| Is a job or message queued only after the commit? | The consumer can read data that does not exist yet |

## Writes that skip checks

| Ask | Why |
|---|---|
| Does bulk code (`update_all`, `delete_all`, `insert_all`, raw SQL, batch upserts) skip validations, callbacks, or hooks that the model relies on? | Counters, audit rows, derived fields, and cache keys go stale |
| Does an update of a struct or hash overwrite fields with zero values or `NULL` when the caller meant "leave unchanged"? | A partial update erases data |
| Does a script or task write data without the model's rules? | The same bad data the constraints should stop |

## Deleting and keeping data

| Ask | Why |
|---|---|
| Is delete a hard delete or a soft delete? Do queries, unique indexes, and counts handle soft-deleted rows? | A unique index that ignores `deleted_at` blocks re-creation. A query that ignores it shows deleted data |
| Does deleting a parent leave children, or delete more than intended? | Check the cascade rule |
| Is there a retention rule for new personal or sensitive data? Is the column encrypted if the project encrypts such data? | Data kept forever is a liability. Deeper exposure review is `security-analysis` |
| Does the change keep a copy (backup, audit row) before a destructive step? | Dropped data does not return |

## Indexes for the schema change

Only the indexes that the schema change itself needs. Query speed in general is a performance review.

- A foreign key column with no index (joins and cascades scan the child table).
- A uniqueness rule with no unique index.
- A new column that the same change adds to `WHERE` or `ORDER BY` in a hot path, with no index.
- A new index that duplicates or is a prefix of an existing one.
- A partial or composite index whose column order does not match the lookup.

## Data code review for backfills, imports, and exports

- Is the transformation correct for null, empty, and unexpected values? Does it log or count rows it skipped?
- Does a re-run give the same result (idempotent)?
- Is there a count or checksum check before and after?
- Does an export include only the fields it should, for only the rows the caller may see?

## Exclusions

Do not report:

- A missing constraint on a table or column that is created in this change and only written by code that is in this change and already enforces it atomically.
- A missing foreign key where the project documents a deliberate choice (for example sharded or cross-service data).
- A "race" with no way for two writers to reach the code (a single-writer job with a lock you verified).
- Style of column names or the order of columns.
