# Evidence methods

Use in Step 2 of `confirm-root-cause`. Each method says when it fits, how to run it, and what it can and cannot show.

Sources: [Zeller, Scientific Debugging](https://www.st.cs.uni-saarland.de/whyprogramsfail/pdf/ScientificMethod.pdf), [mattpocock diagnosing-bugs](https://github.com/mattpocock/skills) (debugger first, tagged logs, performance branch), [superpowers systematic-debugging](https://skillselion.com/skills/obra/superpowers/systematic-debugging) (trace data flow, pattern analysis), [Google SRE book, Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) (compare working and broken, check recent changes, bisect the system), [Zeller and Hildebrandt on isolating differences](https://www.st.cs.uni-saarland.de/papers/tse2002/tse2002.pdf).

## Debugger or REPL

- **Fits:** you know the place and need to see the values and the call stack at that moment.
- **How:** set one breakpoint at the boundary the prediction names. Inspect arguments, locals, and the caller chain. Step only as far as needed. Language files list the commands.
- **Shows:** actual values at one moment. Cannot show history over time or behavior under real load.
- **Note:** the debugger needs an interactive terminal. If the environment cannot run one, use a probe.

## Targeted probe

- **Fits:** the debugger is not available, the bug is timing-sensitive, or you need values across many runs.
- **How:** add one log line or one assertion with the run's tag, for example `[DEBUG-a4f2] user_id=<id> amount=<amount>`. Print only the values the prediction needs. Add it at the boundary between two hypotheses.
- **Shows:** values at that boundary, in the order they happen.
- **Cannot show:** values you did not print. Printing may change timing, which matters for races. For a race, count events with an atomic counter and print once at the end.
- **Safety:** no secrets, tokens, or personal data in the output. Remove the line when the run ends.

## Input change

- **Fits:** a hypothesis about the data.
- **How:** take the minimal scenario. Change one field. Run. Record the verdict. Repeat with the next value.
- **Shows:** which input property flips the result.

## Trace backwards

- **Fits:** the failing line looks correct, or the error is far from the cause.
- **How:** write down the wrong value at the symptom. Ask where it came from. Go to that line. Is the value already wrong there? If yes, go up one more level. If no, the cause is between the previous level and this one.
- **Shows:** the first place the value is wrong. That is where the cause sits.
- **Note:** also trace **state**, not only values: a flag set too early, a cache filled with a stale object, a transaction not committed.

## Compare with a working case

- **Fits:** a passing input, a passing code path, an older passing version, or another environment exists.
- **How:** list every difference between the passing and the failing case: input, config, data, version, order, timing. Move the passing case toward the failing one, one difference at a time, until the result flips. Or move the failing case toward the passing one.
- **Shows:** the smallest difference that matters.

## History

- **Fits:** the bug started at a known time, or the suspect code looks odd.
- **How:** `git log --oneline -n 20 -- <path>`, `git log -L <start>,<end>:<path>` for a range, `git blame -w -C <path>` for a line, `git show <sha>` for the change and its message. For a range of commits, `git bisect run` ([minimise.md](../../reproduce-bug/references/minimise.md)).
- **Shows:** when the behavior or the assumption changed, and what the author intended. A message that says "also handle X" explains why a branch exists.
- **Note:** the commit that introduced the bug is a lead. The cause is the condition the commit created, which `confirm-root-cause` must still explain.

## Telemetry (Datadog, read-only)

- **Fits:** the bug appeared in production and a hypothesis predicts a production pattern.
- **How:** use the tools and the order in [datadog.md](../../diagnose-and-reproduce/references/datadog.md). Compare a failing trace with a passing one. Group failures by version, route, tenant, or region.
- **Shows:** that a pattern exists in production, and how common it is.
- **Cannot show:** why. Pair it with an experiment on the reproduction.

## Performance bugs

For a slow path, logs are usually the wrong tool.

1. Measure a baseline with the reproduction: wall time, query count, allocations, CPU profile. Use the project's own benchmark or profiler (language files).
2. Bisect the work: time each stage, find the stage that grew.
3. Change one variable (an index, a batch size, a cache) and measure again.
4. Compare to the baseline, not to a feeling. Run several times and use the median.

## Counterfactual patch

A temporary in-memory or small code change that removes the suspected cause, to see whether the reproduction goes green. Copy each file you will touch to a backup folder first (`backup=$(mktemp -d)`; `cp --parents <file> "$backup"/`) and copy it back afterward. Do not use a `git diff` patch to undo: it would also include the user's own uncommitted changes. Never use `git restore`, `git checkout`, `git stash`, or `git reset`.

## Five whys, with evidence

1. State the symptom.
2. Ask why. Write the answer **and the evidence**.
3. Ask why of that answer. Repeat up to five times.
4. Stop at something you can change, or at "unknown". Do not fill the gap with a guess.
5. A "why" with no evidence is a hypothesis. Add it to the table.
