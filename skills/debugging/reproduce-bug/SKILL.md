---
name: reproduce-bug
description: Make a bug fail on demand with one fast command that asserts the user's exact symptom, then shrink it to the smallest scenario that still fails. Builds the feedback loop in a fixed order (failing test at the right seam, HTTP or CLI script, headless browser, replay of a captured payload, throwaway harness, property or fuzz loop, git bisect, differential run, human-in-the-loop script), checks that the test fails for the right reason (an assertion that shows the symptom, not a setup error), measures the failure rate for flaky bugs, minimises by removing one piece at a time, and stops with a clear report when the bug does not reproduce. Writes tests and scripts only, never touches production code, leaves the failing test uncommitted in the working tree. Use when the user says "reproduce this bug", "write a failing test for this", "can you make it fail", or as step 3 of diagnose-and-reproduce. Go and Ruby references included.
---

# Reproduce Bug

> Evidence sources: [mattpocock diagnosing-bugs](https://github.com/mattpocock/skills) (build a tight, red-capable, deterministic, fast, agent-runnable loop; minimise until every part is load-bearing), [a repro-first practitioner audit](https://dev.to/yureki_lab/how-i-taught-my-ai-coding-agent-to-reproduce-bugs-before-fixing-them-594g) (show the failing output, stop after 3 attempts, fail-required checks, agents weaken tests to get green), [AssertFlip](https://arxiv.org/html/2507.17542v2) (write a test that passes on the bug, then invert the assertion, so setup errors do not count as a reproduction; 43.6% fail-to-pass on SWT-Bench-Verified), [Issue2Test](https://arxiv.org/pdf/2503.16320) (check that the failure matches the report), [Zeller, Simplifying and Isolating Failure-Inducing Input](https://www.st.cs.uni-saarland.de/papers/tse2002/tse2002.pdf) (ddmin), [git bisect](https://git-scm.com/docs/git-bisect) (exit-code rules), and [how 63 flaky tests were fixed](https://dev.to/yureki_lab/how-i-killed-63-flaky-tests-in-one-week-with-claude-code-5-lessons-29m0) (measure the rate first; 30 runs for timing bugs). Structure follows `test-analysis`.

Find the one command that goes red on this bug. Everything else depends on it.

This skill writes tests, scripts, and files under `docs/<slug>/`. It does not change production code and does not commit.

## Why this process

1. **A tight loop finds the cause.** A signal that goes red on this bug, in seconds, lets every later step consume it. Without it, you read code and guess.
2. **A red is not a reproduction.** A test that fails on an import error, a missing fixture, or a timeout proves nothing. The failure must show the user's symptom.
3. **Models take the cheap way to green or red.** They relax a timeout, widen an assertion, or write a test that fails for an unrelated reason. Check the failure message and never edit the existing tests.
4. **A smaller scenario is a better scenario.** Every piece you remove is one fewer suspect, and the minimal case becomes the regression test.
5. **Flaky is a rate.** A bug that fails 1 time in 50 needs many runs before "it passes" means anything.
6. **Some bugs do not reproduce.** Say so, show what you tried, and ask. Do not invent a reproduction.

## When to use

- Step 3 of `diagnose-and-reproduce`, with a symptom card and ranked hypotheses.
- The user asks to reproduce a bug, to write a failing test for it, or to make a flaky test fail reliably.

## When NOT to use

- The symptom card is empty. Go back to intake.
- The user wants the fix. Reproduce first, then fix as a separate step.
- The failing check already exists and fails for the right reason. Record it and go on.
- The "bug" is a request for new behavior. That is a feature. Use `feature-planning`.

## Process

### Step 0: Read, and know the green baseline

0. If `docs/<slug>/diagnosis.md` does not exist (this skill was called alone), pick a slug and create the file from [the template](../diagnose-and-reproduce/references/diagnosis-template.md). Fill the symptom card from what the user gave. Ask the user only when a missing fact blocks this skill, and then ask once, all questions in one `AskUserQuestion` call (`AskQuestion` in Cursor). Otherwise go on, and write each guess under **Assumptions**.
1. Read `docs/<slug>/diagnosis.md`: symptom card, hypotheses and their cheapest tests, project commands.
2. Read the test conventions of the area: where tests live, helpers, factories, fixtures, naming, the focused-test command. Read the language file now: [references/go.md](references/go.md) or [references/ruby.md](references/ruby.md).
3. Run the existing tests of the area once. Record green or red. A suite that is red before you start changes what "fails" means. If it is red, find which tests, and do not count those.

### Step 1: Choose a loop

Read [references/loop-ladder.md](references/loop-ladder.md). Take the first loop that can reach the bug's code path and assert the user's symptom. Use hypothesis tests as ideas for the seam.

Order: failing test at the right seam, HTTP script against a local server, CLI run with a fixture, headless browser script, replay of a captured payload, throwaway harness, property or fuzz loop, bisection, differential run, human-in-the-loop script.

A loop must be:

- **Red-capable:** it runs the real bug path and asserts the exact symptom. "Runs without error" does not count.
- **Deterministic:** the same verdict every run, or a measured failure rate for a flaky bug.
- **Fast:** seconds, not minutes.
- **Agent-runnable:** you can run it unattended. A human only through the human-in-the-loop script.

### Step 2: Write the loop

1. **Test:** put it where the repo puts such tests, in a new test file or as a new case in an existing file. Adding a case is fine. Changing, skipping, or deleting an existing case is not. Name it for the symptom (`test_returns_422_when_...`, `TestParseDuration_rejects_negative`). Add a comment with the slug and the expected-versus-actual behavior.
2. **Script:** put it under `docs/<slug>/repro/`. It starts with a header: slug, expected, observed, environment, and the exact command. It exits non-zero when the bug is present.
3. **Fixtures:** use synthetic values with the real shape ([redaction rules](../diagnose-and-reproduce/references/redaction.md)). Pin time, seed random numbers, and isolate files and the network.
4. **Assert the symptom.** Assert the wrong value, the error message, the status code, or the timing, as the user saw it. State the expected behavior in the assertion.
5. **If the red keeps failing for setup reasons** (a missing fixture, an import error), use the pass-then-invert method: first write a test that **passes** by asserting the buggy behavior as it is. Then invert the assertion to the expected behavior. The test now fails because of the assertion, not because of the setup.

### Step 3: Run it and check the red

Run the one command. Show the command and the shortest decisive output (redacted).

Check, in this order:

- [ ] It **fails**. A pass is not a reproduction: go to Step 4 (flaky) or Step 6 (stop path).
- [ ] It fails at the **assertion**, not at a compile error, an import, a missing fixture, a nil in the setup, a timeout in the harness, or a different bug.
- [ ] The message **matches the symptom** in the symptom card (same error, same wrong value, same status).
- [ ] The cause of the failure is in the **code under test**, not in the test.
- [ ] It fails on **repeat**: run it three times.

If a check fails, fix the test (not the production code) and run again. Count each rewrite as an attempt.

### Step 4: Measure flaky bugs

If it does not fail every time, the goal is a higher failure rate, not a clean red.

1. Run it N times with the cache off. N is 15 for a logic bug and 30 or more for a timing bug. Record `k of N`.
2. Raise the rate: loop in parallel, add load, narrow the timing window with a short sleep or a barrier, shrink the data, fix the seed that failed. Language tips are in the language files.
3. Stop raising when the rate is high enough to debug: 1 in 2 is good, 1 in 10 is workable, 1 in 50 or worse is not yet. Write the rate in the report.
4. Do not call it reproduced on one failure. Do not call it fixed later on fewer runs than you used here.

### Step 5: Minimise

Read [references/minimise.md](references/minimise.md).

1. Cut one thing at a time: an input field, a record, a caller, a config value, a setup step, a test line. Run the loop after each cut.
2. Keep the cut if it still fails the same way. Put it back if it passes or fails differently.
3. Stop when every remaining piece is load-bearing: removing any one makes it pass.
4. If the bug appeared between two known states (a commit, a version, a data set), automate `git bisect run` ([references/minimise.md](references/minimise.md)) to find the first bad commit.
5. Write the minimal scenario into `diagnosis.md`. Update the hypotheses: mark which ones the repro supports, contradicts, or leaves open.

### Step 6: Stop path

Stop and report **"not reproduced"** if you made 3 honest attempts and the symptom did not fail. An attempt is a different loop or a materially different test, not a re-run.

1. Write the attempts in `diagnosis.md`: what you tried, the command, the output.
2. Say why it may not reproduce: already fixed on the main branch, a changed expectation, an environment or data difference, a race that needs more load, a version mismatch.
3. Return to `diagnose-and-reproduce`. It asks the user for an environment, a redacted artifact, or permission for temporary instrumentation. Do not continue to hypothesise forward and do not propose a fix.

## Output

```
## Reproduction: <slug>

Command: `<one command>`
Kind: <failing test | script | HTTP | headless | replay | harness | bisect>
Files: <paths> (uncommitted)
Result: RED, matches the symptom
  <shortest decisive output lines, redacted>
Rate: <k of N>
Minimal scenario: <what is load-bearing>
Hypotheses: H1 supported, H2 contradicted, H3 open
Attempts: <n>, <what each was>
```

or

```
## Reproduction: not reproduced
Need from the user: <environment | redacted artifact | permission>
Attempts: <1..3 with commands and outputs>
Likely reasons: <list>
```

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The test fails, so I am done." | Read the message. A `NameError` in the setup is not the symptom. |
| "I will make the repro pass by raising the timeout." | The repro goes green only when the bug is fixed. Never loosen it. |
| "I will edit the existing test to cover the bug." | Add a new test. Existing tests are evidence of what worked. |
| "It failed once, so it reproduces." | One failure of a flaky bug is a hint. Measure the rate. |
| "I could not make it fail, so I will fix the likely cause." | A fix without a red is a guess. Use the stop path. |
| "Minimising is a waste of time." | The minimal case shrinks the suspects and becomes the regression test. |
| "I need the real production data." | You need its shape. Use synthetic values, and check the bug still reproduces. |
| "I will mock the database to make the test fast." | A mock can remove the bug. Keep the real component the hypothesis points at. |

## Red flags

- Production code, an existing test, or a lint or CI config was changed.
- The failing output was not shown, or it was paraphrased.
- The red comes from a setup error, an import error, or a different bug.
- The assertion was widened, a timeout raised, a retry added, or a test skipped to make the result look right.
- A flaky bug was called reproduced after one failure.
- A mock replaced the component the hypothesis suspects, and the red depends on the mock.
- The loop takes minutes, or needs a human, and no faster loop was tried.
- The repro hits a live system, or writes to a shared database.
- Real secrets or personal data are in a fixture or a script.
- A test or script was committed.

## Verification

- [ ] The green baseline of the area is stated.
- [ ] One command exists. It was run, and its output is shown.
- [ ] The failure is an assertion that shows the user's symptom, and it matches the symptom card.
- [ ] It is repeatable: 3 of 3 runs, or a stated rate over N runs (N is 15 or more, 30 or more for timing).
- [ ] The scenario is minimal: each remaining piece is load-bearing.
- [ ] No existing test, config, or production file changed. The new files are tests, scripts, and `docs/<slug>/`.
- [ ] Fixtures hold no secrets or personal data.
- [ ] The hypotheses table is updated.
- [ ] The stop path ran when 3 attempts failed.
- [ ] Nothing was committed.
