# Option types and how to describe them

Use in Steps 1 and 2 of `propose-solutions`.

Sources: ITIL definitions of workaround and permanent fix, the security split of mitigation and remediation (mitigation lowers the impact now; remediation removes the cause), [Google SRE book, Postmortem Culture](https://sre.google/sre-book/postmortem-culture/) (action items fix contributing factors), [Google SRE book, Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) (stop the bleeding before the cure), [AWS Builders' Library on safe retries and idempotency](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/), [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/) (make illegal states unrepresentable), and `data-and-migration-analysis/references/migration-safety.md` in this plugin.

## 1. Root-cause fix

Change what produces the symptom, at the place where the value or the state first goes wrong (the result of `confirm-root-cause`, not the failing line).

- **Good when:** the cause is Confirmed and the change is local.
- **Check:** does the change sit at the **first** wrong place, or at the symptom? A fix at the symptom is containment.
- **Typical forms:** correct the condition, handle the missing case, fix the data type or the unit, make the write atomic, move the side effect after the commit, use the right time function.
- **Test plan:** the reproduction goes green. Add the cases next to the bug (the boundary, the empty and the null, the second call, the other caller).

## 2. Containment

Stop the damage now. The cause stays.

- **Forms:** a feature flag that turns the path off, a rollback of the commit or the deploy, a guard at the entry that rejects the bad input, a rate limit, a retry that is safe (idempotent), a manual repair of the affected rows, a banner or a support note.
- **State plainly:**
  - what stays broken,
  - who owns it,
  - when it expires (a date or a condition),
  - what will tell us it is no longer needed.
- **Watch for:** a retry on an operation that is not idempotent doubles the side effect. A guard can change what callers see (a new error). A rollback can bring back an older bug or break a data migration that already ran.
- **Test plan:** a test shows the guard or the flag works, and the reproduction still shows the cause (it stays red for the unguarded path), so nobody thinks it is fixed.

## 3. Hardening

Make the class of bug hard or impossible.

- **Forms:** a database constraint (`NOT NULL`, `UNIQUE`, a check, a foreign key), a stricter type or a parsing step at the boundary, an idempotency key, a lock or an optimistic version, an assertion at a boundary, a test for the whole class, a lint rule, a monitor or an alert on the symptom.
- **Good when:** the diagnosis has a latent condition (a design that allows invalid state).
- **Watch for:** a constraint on existing bad data fails the migration. Check and repair the data first (see the data repair field). Add a constraint in a safe order (add it not-valid, repair, then validate) when the engine allows.
- **A monitor or an alert is a suggestion.** Write what to watch (query, threshold, service). The user creates it. The skill never creates one.

## 4. Collect more evidence

Only when the cause is Unconfirmed or Unreproduced.

- **Forms:** a probe or a metric in a non-production environment, a debug log behind a flag with a short life, a trace attribute, a production query the user can run, a customer artifact to ask for.
- **State:** what the evidence will show for each remaining hypothesis, so the result decides.
- **Watch for:** instrumentation in production needs the user's permission and a plan to remove it. Do not log secrets or personal data.

## Combining

Pair types when it helps, and say so:

- **Contain now, fix next:** a flag today, the root-cause fix when the test is ready.
- **Fix and harden:** the fix plus a constraint that stops the same bug from a different path.

## AS IS and TO BE diagrams

- **AS IS:** reuse the sequence diagram or the flowchart from `explain-bug`. Keep the faulty step marked.
- **TO BE:** the same diagram after the option. Show the changed step in a different color, and the new step (the guard, the lock, the constraint) with a note. Keep the same participants and the same order, so the reader compares side by side.
- **One TO BE per option.** If an option does not change the flow (a monitor), say so and skip its diagram.
- **Do not draw a flow the code cannot do.** Check each new step against the code you read in Step 0.
- Rules for diagrams are in [../../explain-bug/references/diagrams.md](../../explain-bug/references/diagrams.md).

## Blast radius checklist

- Callers of the changed function (count them with `grep`).
- Public API shape, error codes, and response bodies.
- Stored data: is any of it wrong now? Will a new rule reject old rows?
- Jobs and messages in flight that carry the old shape.
- Other services and consumers.
- Config, flags, and documentation.
- Performance on the hot path.

## Effort scale

- **S:** hours. One file, one test, no migration.
- **M:** a day or two. Several files, a few tests, a data check.
- **L:** more. A migration, an API change, many callers, or a rollout in steps.

Give the scale and a one-line reason. Do not give hours as a promise.

## Rollout and rollback

- How it ships: normal deploy, a flag, a staged rollout.
- What to watch after: the error rate, the metric the bug moved, the log or trace the bug left.
- How to roll back: revert the commit, turn off the flag, restore the data. Say if a rollback is not possible (a data change).

## Data repair

If rows are wrong now:

1. Write the query that finds them (read-only first).
2. Say how many, and which ones matter.
3. Propose the repair as a reviewed script with a dry run, a backup or a way to restore, and batches. The user runs it.
4. Never run a write on a shared or production database from this skill.
