# The loop ladder

Use in Step 1 of `reproduce-bug`. Take the first rung that can reach the bug's code path and assert the user's exact symptom. Go down only when a rung cannot.

Sources: [mattpocock diagnosing-bugs](https://github.com/mattpocock/skills) (the ladder, and "tighten the loop"), [Claude Code best practices](https://code.claude.com/docs/en/best-practices) (a check Claude can run; a script that diffs output against a fixture), [AssertFlip](https://arxiv.org/html/2507.17542v2) (pass first, then invert), [Agentless](https://www.alphaxiv.org/abs/2407.01489) (a reproduction test picked per issue).

| # | Loop | Use when | Watch for |
|---|---|---|---|
| 1 | **Failing test at the right seam** (unit, integration, or end to end) | The repo has tests and a seam reaches the bug. Best option: it becomes the regression test. | The seam must run the real bug pattern. A unit test that skips the caller chain that triggers the bug gives false confidence. |
| 2 | **HTTP or `curl` script** against a local server | The bug is in a request path and the app boots locally. | Seed the data with synthetic values. Assert on status and body, not on "no crash". |
| 3 | **CLI run with a fixture**, diff stdout against a known-good snapshot | The bug is in a command, a job runner, or a data transform. | Pin time and random seeds so the diff is stable. |
| 4 | **Headless browser script** (Playwright or similar) | The bug shows in the UI, the DOM, the console, or the network. | Wait on conditions, not on sleeps. Assert on DOM or network facts. |
| 5 | **Replay a captured trace or payload** | You have a real request, event, or message (redacted). Replay it through the code in isolation. | Redact first. Keep the shape, replace the values, and check the bug still reproduces. |
| 6 | **Throwaway harness** | The bug needs one service with its dependencies stubbed, or a single function call with a crafted input. | Do not stub the component the hypothesis suspects. Put the harness under `docs/<slug>/repro/`. |
| 7 | **Property or fuzz loop** | The bug is "sometimes wrong output". Run many random inputs and check the invariant. | Print the failing seed and input. Shrink the input afterward (see [minimise.md](minimise.md)). |
| 8 | **Bisection harness** | The bug appeared between two known states (commit, version, data set). Wrap the check in a script that returns the right exit code, and run `git bisect run`. | Use exit code 125 for states that cannot be tested (a build break). See [minimise.md](minimise.md). |
| 9 | **Differential run** | You have a working and a failing version or config. Run the same input through both and diff the outputs. | The diff shows where behavior splits. Keep everything else identical. |
| 10 | **Human-in-the-loop script** | Last resort. A person must click, or must run something on a machine you cannot reach. | A script prompts the person for each step and captures the output, so the loop stays structured. |

## Choose with the hypotheses

Read the "cheapest test" column of the top hypotheses. If two of them can be separated by one loop, build that loop. It then tells you more than reproducing alone.

## Tighten the loop

Once a loop exists, make it better:

- **Faster:** cache setup, skip unrelated initialization, narrow the test scope. A 2-second loop is a debugging tool. A 5-minute loop is not.
- **Sharper:** assert the specific symptom, not "does not crash".
- **More deterministic:** pin time, seed random numbers, isolate the file system, freeze the network, fix the data.

## Performance and other measured symptoms

A slow path, a memory growth, or a query count has no wrong value to assert. Assert a **measurement with a margin**.

1. Measure the baseline first: several runs, take the median. Record the number and the machine.
2. Prefer a count that does not change between machines (queries, allocations, calls, rows read, retries) over wall time. A test on "more than 5 queries" is stable. A test on "slower than 200 ms" is flaky.
3. If only time shows the bug, set the limit well between the good and the bad medians, and run several times.
4. The test fails when the measure is above the limit. State the limit in the assertion and in the comment.
5. For memory or goroutine growth, run the path N times and assert that the count after is not above the count before plus a small margin.
6. Use the project's own benchmark or profiler, and its language file.

## Pass-then-invert (when the red keeps failing for the wrong reason)

1. Write a test that exercises the bug path and asserts the **current, buggy** behavior. It passes.
2. Check that it passes for the reason you think: the buggy value is what the code returns.
3. Invert the assertion to the **expected** behavior. It now fails at the assertion, and the failure shows the symptom.

This filters out setup errors: a test that passes first has a working setup. The method comes from AssertFlip. Its authors note that an LLM validation of "right reason" is imperfect, so still read the failure yourself.

## When no loop is possible

Stop. Say so, list what you tried, and ask the user for: an environment that shows the bug, a redacted artifact (log dump, HAR file, core dump, recording with timestamps), or permission to add temporary instrumentation to a non-production environment. Do not go on to hypothesise without a loop.
