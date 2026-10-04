---
name: data-and-migration-analysis
description: Review database migrations and data-handling code in a change for deploy safety and data integrity. Finds lock and rewrite risk, unsafe backfills, changes that break old or new code during a deploy, irreversible steps, missing constraints and indexes, validation without a database guarantee, race conditions, and writes that skip integrity checks. Uses the project's existing tools (strong_migrations, squawk, Atlas, active_record_doctor, database_consistency) as candidate generators. Use when the user asks to review a migration, schema change, backfill, index, constraint, or data model, or asks "is this migration safe". Read-only, reports findings, does not fix.
---

# Data and Migration Analysis

> Evidence sources: [strong_migrations](https://github.com/ankane/strong_migrations), [Squawk rules](https://squawkhq.com/docs/rules), [Atlas migration analyzers](https://atlasgo.io/lint/analyzers), [database_consistency](https://github.com/djezzzl/database_consistency), [active_record_doctor](https://github.com/gregnavis/active_record_doctor), and the expand-and-contract pattern ([Xata](https://xata.io/blog/zero-downtime-schema-migrations-postgresql)). Structure follows [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills).

A migration runs once, on real data, often on a live system, and is hard to undo. Data bugs stay in the database after the code is fixed. Review both with more care than ordinary code.

This skill covers two things:

- **Migration safety:** will this change deploy without an outage, data loss, or a broken old version?
- **Data integrity:** does the database itself guarantee what the code assumes?

This skill is read-only. Report findings. Do not edit code unless the user asks for a fix after the report.

## Why this process

1. **Risk depends on facts that are not in the diff.** The same `ALTER TABLE` is harmless on a table of 200 rows and an outage on a table of 200 million. Find the engine, its version, the table size, the traffic, and the deploy order before you rate a finding.
2. **A deploy has two versions running.** During a rolling deploy or a rollback, old code runs against the new schema, or new code against the old one. Check both.
3. **Validations in code are not guarantees.** Two requests at once defeat a uniqueness check in code. A constraint in the database does not fail.
4. **Existing tools already know the unsafe operations.** Run them as candidate generators, then verify each result yourself.

## When to use

- A diff adds or changes a migration, a schema file, or a backfill.
- A change adds a table, column, index, constraint, or relation, or changes a data model.
- Code does multi-step writes, read-then-write logic, or bulk updates and deletes.
- The user asks "is this migration safe" or "will this lock the table".

## When NOT to use

- The user wants query speed checked: N+1, query plans, indexes for a slow query. That is a performance review. This skill checks indexes only where a schema change needs one (foreign keys, uniqueness, a new lookup column).
- The user wants a security review of data exposure or injection. Use `security-analysis`.
- The user wants fixes applied. Review first, then fix as a separate step.

## Process

### Step 0: Set scope and facts

1. Use the files the user names.
2. If none, use the current change. That is the files not committed yet (`git diff --name-only`, `git diff --staged --name-only`, and new files from `git ls-files --others --exclude-standard`) plus the branch diff against the main branch (`git diff --name-only main...HEAD`; use `master` if the repo has no `main`).
3. Review the whole schema or all migrations only when the user asks for a full review.
4. Pick the relevant files: migration files, schema files (`schema.rb`, `structure.sql`, `*.sql`), models and entities, repositories and queries that write data, backfill scripts, rake tasks, jobs, and seeds. If none are in scope, tell the user there is nothing for this skill to review.
5. Detect the language and framework (see Language references). Read the matching reference now.
6. Find the facts below. Look in `CLAUDE.md`, README, `docker-compose.yml`, CI config, `Gemfile.lock` or `go.mod`, and the existing migrations. If a fact is missing, ask the user once for the whole list. If the user does not know, rate the finding as "depends on size" and say what you assumed.

| Fact | Why it matters |
|---|---|
| Engine and version (PostgreSQL, MySQL, SQLite, version number) | Safe operations differ by engine and version |
| Migration tool | Transaction behavior and checksums differ |
| Table size and write traffic for the tables in the diff | Decides if a lock or rewrite is an outage |
| How migrations run: before the deploy, after it, or by hand | Decides which code version meets the new schema |
| Rolling deploy or downtime allowed | Decides if old code must keep working |

### Step 1: Find and run the project's existing tools

Find the data and migration libraries the project already uses. Do not rely only on the tools named in this skill or in the references. Look in:

- Dependency manifests and lockfiles: `Gemfile.lock`, `go.mod`, `package.json`, `requirements.txt`, `pom.xml`, and similar.
- `CLAUDE.md`, `Makefile`, `Taskfile`, `Rakefile`, CI config, and pre-commit config.
- Tool config files at the repo root.

Sort what you find into groups:

| Group | Examples of what it does | What to do |
|---|---|---|
| Migration safety or lint | Flags unsafe operations in migrations or SQL | Run it as a candidate generator |
| Schema and model checks | Compares models or queries with the schema | Run it as a candidate generator |
| Migration runner | Applies migrations, checksums, locks | Learn its transaction and ordering behavior |
| ORM, query builder, and extension libraries that change data behavior | Soft delete, auditing, partitioning, schema views, multi-tenancy, encryption, bulk insert helpers | Read how they change writes and deletes before you judge the data code |

For a library the references do not name: read its README or `--help`, find how to run it, and use it the same way. Check its config for settings that weaken it (disabled checks, an old `start_after` date, ignore lists), and report them. Do not change them.

Rules for running tools:

- Do not install anything. Treat all output as unverified candidates.
- Tools that only read the schema or SQL files are safe to run (for example `squawk`, `active_record_doctor`, `database_consistency`). The language references list commands.
- Tools that **execute migrations** (`rails db:migrate` with `strong_migrations`, `atlas migrate lint` with a dev database): run them only against a local, disposable database. Never run them against a shared, staging, or production database.
- If you cannot tell whether a command changes the database or only reads it, treat it as one that changes it. If you cannot tell which database it uses, ask first.

If the project has no such tool, say so. Continue with Step 2.

### Step 2: Learn the repo's patterns

Before you judge the change, read how the repo handled similar changes:

- Past migrations: how it adds indexes, backfills, removes columns, and renames.
- Helpers and conventions: batching helpers, `safety_assured` use, concurrent index habits, expand-and-contract in the history.
- Tool config: `strong_migrations` settings (`start_after`, `target_version`, lock timeouts), `.squawk.toml`, `atlas.hcl`, and the config of any other library from Step 1.

A new migration that skips a pattern the repo always follows is a strong signal. Also check git for the status of the migration files: an **existing** migration that was **modified** (not added) is a finding by itself. See [references/migration-safety.md](references/migration-safety.md), section "Migration hygiene".

### Step 3: Detect candidates, one change at a time

A **slice** is one migration file, or one data model change, or one write path. Do not review the whole diff as one block.

For each migration slice, go through [references/migration-safety.md](references/migration-safety.md):

1. Each operation: lock, rewrite, or scan risk on the engine and version.
2. Compatibility: old code against the new schema, new code against the old schema.
3. Backfill: batching, throttling, transaction scope, resumability.
4. Reversibility: does `down` exist and work, and can the code roll back?
5. Hygiene: edited applied migration, schema file in sync, order, one concern per migration.

For each data slice, go through [references/data-integrity.md](references/data-integrity.md):

1. Constraints: NOT NULL, unique, foreign key, check, and defaults.
2. Types: money, time, identifiers, enums, text length.
3. Races: check-then-insert, read-modify-write, counters.
4. Transactions: multi-step writes that must succeed or fail together.
5. Bypasses: bulk writes that skip validations and callbacks.
6. Deletion and sensitive data.

Write each candidate as one line: `file:line, category, operation, suspected risk`. Be generous. Step 4 removes the noise. After the last slice, do one more pass: "What would break on deploy day, or in a month, that I have not listed?"

### Step 4: Verify each candidate (try to refute it)

Treat each candidate as a claim to disprove. Answer all five:

| Check | Question |
|---|---|
| Engine | Is this operation really unsafe on this engine and version? Read the version, not a general rule. |
| Size | Does the table size and traffic make it matter? A new empty table is fine. |
| Compatibility | Can you name the code version and the query that breaks? |
| Control | Does the project already handle it: a tool setting, a lock timeout, an earlier migration that did the safe first step? Search for it. |
| Impact | What happens: an outage, data loss, wrong data, a failed deploy, or a slow migration? |

Then apply the exclusions in [references/migration-safety.md](references/migration-safety.md) and [references/data-integrity.md](references/data-integrity.md).

Decide per candidate:

- **Report:** all checks hold and you can state the failure.
- **Needs human check:** you cannot tell from the repo (table size, version, deploy order, a setting outside the repo). Report it with the exact question. **Fail open: never drop a candidate only because you could not verify it.**
- **Drop:** a check fails with evidence (for example the table is created in the same migration). Keep a one-line reason for the count.

When it is cheap and safe, verify with a run on a disposable local database: migrate, then roll back, then migrate again. Never run a migration or a backfill against a shared or live database.

### Step 5: Report

Sort by severity, then confidence.

```
## Data and migration review: <scope>

Scope: <files / range>. Skipped: <seeds / fixtures / docs>.
Facts: <engine and version, tool, table sizes, deploy order. Mark each "known" or "assumed">.

### Findings

Finding 1: <Category>: `<file>:<line>`
- Severity: HIGH | MEDIUM | LOW
- Operation: <the migration step or data operation>
- Failure scenario: <what happens, to which code version, on which data or table size>
- Evidence: <tool output, schema fact, or the exact query that breaks>
- Safe approach: <the specific steps, for example expand-and-contract in two deploys>

### Needs human check
- `<file>:<line>`: <what you could not verify and the exact question, for example "row count of orders?">

### Summary
Candidates: <N>. Reported: <N>. Needs check: <N>. Dropped: <N> (<top reasons>).
Tools run: <name and result, or "none available">.
Not covered: <production data volume, replica lag, ORM-generated SQL you did not read, infra>.
```

If there are no findings, say so plainly, with what you checked. Do not invent findings.

**Severity**

- **HIGH:** data loss or corruption. A change that breaks the running version during deploy or rollback. A lock or table rewrite on a large, busy table. A migration that cannot be undone and has no backup step. A missing constraint that allows duplicate or invalid data in a real race.
- **MEDIUM:** a backfill without batching. A missing foreign key, unique index, or NOT NULL that the code relies on. A migration with no working `down`. Wrong type for money or time.
- **LOW:** hygiene and naming. Report LOW only when the user asked for it.

## Language references

Detect the project language and framework from the files in scope and manifests (`go.mod`, `Gemfile`, `db/migrate/`, `migrations/`). Read **only** the matching reference before Step 1. If the scope spans several languages, read each one:

| Language | Detect | Reference |
|---|---|---|
| Go | `go.mod`, `migrations/`, goose, golang-migrate, Atlas, GORM | [references/go.md](references/go.md) |
| Ruby / Rails | `Gemfile`, `db/migrate/`, `db/schema.rb` | [references/ruby.md](references/ruby.md) |

Each reference holds the common migration tools and their transaction behavior, safety tools with commands, and framework-specific traps. It is a starting point, not a complete list. Libraries the project uses that are not listed there are handled in Step 1.

**Precedence when rules conflict:**

1. The project's own conventions, tool config, and `CLAUDE.md`.
2. The defaults in the references.

If the language has no reference, apply the process above with the shared references and follow the repo's own patterns.

To add a language: create `references/<language>.md` with the same sections and add a row to this table.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The table is small." | Check. Tables grow. Ask the owner, or mark "depends on size". |
| "It runs in a few seconds in dev." | Dev has no traffic and little data. The lock is the problem, not the speed. |
| "The model validates it." | Two requests at once pass the same validation. Only a database constraint is a guarantee. |
| "We will deploy the code and the migration together." | A deploy is never atomic. Old code runs for a while. Check both orders. |
| "Rollback is easy, we have `down`." | Does `down` restore the data? Dropped columns do not come back. |
| "The tool did not complain, so it is safe." | Tools cover known patterns only. Read the migration. |
| "`safety_assured` is fine here." | Find the reason. Without one, it hides the finding. |

## Red flags

- A finding does not state the engine, the version, or the table size, or mark them as assumed.
- A finding names no code version or query that breaks.
- A migration or backfill ran against a shared database.
- A finding repeats tool output with no verification.
- You reported a new empty table as a lock risk.
- You dropped a candidate because you could not check the table size.
- You rated a performance or query-shape issue as a migration issue.
- You edited code during the review.

## Verification

- [ ] Scope and skipped files are stated.
- [ ] Engine, version, tool, table sizes, and deploy order are stated, each as known or assumed.
- [ ] Review ran per slice, not on the whole diff at once.
- [ ] Both code-and-schema orders were checked for every schema change.
- [ ] Every reported finding has an operation, a failure scenario, evidence, and a safe approach.
- [ ] Unverifiable candidates are under "Needs human check", not dropped.
- [ ] No migration or backfill ran against a shared database.
- [ ] Libraries from the manifests were checked, not only the tools named in this skill.
- [ ] Tool output was verified, not pasted.
- [ ] No code was modified.
- [ ] Report says what was not covered.
