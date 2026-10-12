---
name: form-hypotheses
description: Turn a bug's symptom card into 3 to 5 ranked, falsifiable hypotheses before any reproduction attempt. Each hypothesis states where and what is wrong, a prediction ("if this is the cause, then ..."), the cheapest test that would show it, and a confidence level. Draws from seven cause categories (recent change, input or data shape, state and ordering, time, configuration, dependency contract, resource limits) so the list does not anchor on one idea. Writes the table into docs/<slug>/diagnosis.md and shows it to the user. Hypotheses are provisional: the reproduction asserts the user's symptom, and evidence re-ranks the list. Use when the user wants guesses about why something fails, "what could be causing this", or as step 2 of diagnose-and-reproduce. Read-only: reads code, history, and evidence, changes no code.
---

# Form Hypotheses

> Evidence sources: [Zeller, Scientific Debugging](https://www.st.cs.uni-saarland.de/whyprogramsfail/pdf/ScientificMethod.pdf) (observe, hypothesise, predict, experiment, conclude; a hypothesis must predict something that can fail), [mattpocock diagnosing-bugs](https://github.com/mattpocock/skills) (3 to 5 ranked hypotheses, each falsifiable, show the list to the user), [CogniGent](https://arxiv.org/pdf/2601.12522) (an LLM states a root-cause hypothesis with a confidence category, and agents investigate the medium and high ones first), and the [multi-agent root-cause study](https://arxiv.org/pdf/2605.14866) (in a long context the model drops the right hypothesis, so keep a written log). Structure follows `reliability-analysis`.

Write down what could be wrong, and how you would find out. A hypothesis is useful when a cheap test can prove it false.

This skill is read-only. It does not reproduce the bug, add probes, or propose fixes.

## Why this process

1. **The first idea anchors.** One hypothesis feels like an answer. A list of several forces you to look for evidence that tells them apart.
2. **A hypothesis without a prediction is a vibe.** "Maybe a race" cannot be wrong. "If it is a race, running the test 50 times in parallel will fail more often than serially" can.
3. **The test follows from the prediction.** The cheapest discriminating test of the top hypotheses decides what `reproduce-bug` builds first.
4. **The list is provisional.** The reproduction must assert the user's symptom, not the top hypothesis. Evidence changes the ranking, and sometimes empties the list.
5. **Context decays.** Keep the list in `diagnosis.md` and update it, so the right hypothesis is not lost in a long session.

## When to use

- Step 2 of `diagnose-and-reproduce`, with a filled symptom card.
- The user asks "what could cause this" or wants a ranked list of suspects.
- `confirm-root-cause` returns here once, with new evidence, after all hypotheses were rejected.

## When NOT to use

- The symptom card is empty. Go back to intake and ask for the missing facts.
- The cause is already proven by a failing test. Go on to explain and fix.
- The user wants fixes. Hypotheses are about causes, not repairs.

## Process

### Step 0: Read the inputs

0. If `docs/<slug>/diagnosis.md` does not exist (this skill was called alone), pick a slug, ask the user for the missing facts in one `AskUserQuestion` call, and create the file from [the template](../diagnose-and-reproduce/references/diagnosis-template.md).
1. Read the symptom card and the evidence in `docs/<slug>/diagnosis.md`.
2. Read the code at the place the evidence points to: the failing route, job, or function and its direct callers and callees. Do not read the whole repository.
3. Read the history of that place: `git log --oneline -n 20 -- <paths>` and, if the symptom began at a known time, the commits and deploy events just before it.
4. Look for how the repo handles the same case elsewhere. A difference between the failing path and a working sibling is a strong lead.

### Step 1: Generate candidates from all seven categories

Go through each category and write at least one candidate if the evidence allows it. Skip a category only with a reason ("no time logic in this path"). Read [references/cause-categories.md](references/cause-categories.md) for the questions and the signals of each category.

1. **Recent change:** a commit, deploy, flag, or dependency bump just before the first occurrence.
2. **Input or data shape:** a value, size, encoding, null, empty list, or new data the code did not expect.
3. **State and ordering:** shared state, test order, caches, retries, concurrency, partial writes.
4. **Time:** time zones, daylight saving, clock skew, expiry, date boundaries, timeouts.
5. **Configuration and environment:** flags, environment variables, versions, permissions, feature gates.
6. **Dependency contract:** an external service, a library, or a database that changed or behaves differently from what the code assumes.
7. **Resource limits:** memory, connections, file handles, queue depth, rate limits, disk.

Also write one candidate in the form **"the bug is not where the symptom shows"** when evidence allows: the fault is upstream (data written wrong earlier) or in a caller.

### Step 2: Make each candidate falsifiable

For each candidate, fill the row:

| Field | Rule |
|---|---|
| **ID** | `H1`, `H2`, ... Never reuse an ID. |
| **Hypothesis** | One sentence: what is wrong, and where (file, function, component). |
| **Prediction** | `If <X> is the cause, then <changing Y> makes the bug disappear / <changing Z> makes it worse / <looking at W> shows V.` State a result that could be false. |
| **Cheapest test** | The smallest experiment that checks the prediction: a unit test, an input, a log line, a query, a `git bisect`. Name the command or the data. |
| **Evidence for / against** | What already supports or contradicts it. Cite the log line, the trace, the commit. |
| **Confidence** | `high`, `medium`, `low` (see below). |
| **Status** | `open`. Later `supported`, `rejected`, or `confirmed`. |

If you cannot write a prediction, sharpen the hypothesis or drop it.

### Step 3: Rank

1. Score each hypothesis on three things: how well the **evidence fits**, how likely it is **a priori** (recent change and the failing line itself beat distant causes), and how **cheap** the test is.
2. Put high and medium confidence first. Break ties by the cheapest test.
   - `high`: at least one piece of evidence points directly at it, and nothing contradicts it.
   - `medium`: it fits the evidence, with no direct pointer.
   - `low`: possible, no evidence. Keep at most one or two, to avoid anchoring.
3. Keep **3 to 5** hypotheses. With more, merge the ones that predict the same thing. With fewer than 3, you did not look at enough categories. Say so and go through the categories again.
4. Make sure the top three do not all come from the same category.

### Step 4: Write and show

1. Write the table into section 2 of `docs/<slug>/diagnosis.md`. Add the experiment log header.
2. Show the ranked table in the chat, in the user's language, with one line: "These are guesses. The next step is a test that fails on the symptom, and the results will re-rank them."
3. Ask nothing and wait for nothing. Say that the user can reorder the list, add a suspect, or rule one out, because users often know about a deploy or a past incident. If the user answers, update the table.
4. Hand the **cheapest tests** of the top hypotheses to `reproduce-bug`, as ideas for the loop. They are ideas, not the assertion.

## Output

```
## Hypotheses: <slug>

| ID | Hypothesis | Prediction (if true...) | Cheapest test | Confidence | Status |
|---|---|---|---|---|---|
| H1 | ... | ... | ... | high | open |

Ranking basis: <one line: evidence fit, recent change, cost to test>
Categories covered: <list>. Skipped: <category: reason>.
Provisional: the reproduction asserts the symptom, not these guesses.
```

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "It is obviously the null check." | One obvious cause is how you fix the wrong thing. Write at least three. |
| "I will write the prediction later." | A hypothesis with no prediction cannot be tested. Write it now or drop it. |
| "I have five hypotheses in the same file." | Five variants of one idea are one hypothesis. Cover other categories. |
| "Nothing changed recently." | Check the deploy events, the dependencies, the data, and the clock. Something changed. |
| "The user's guess goes first." | Rank by evidence. A user's guess is evidence, not a ranking. Include it and test it. |
| "I will test the top hypothesis by changing the code." | Not in this skill. Name the test. `reproduce-bug` and `confirm-root-cause` run it. |

## Red flags

- Fewer than 3 or more than 5 hypotheses, with no reason given.
- A hypothesis with no prediction, or a prediction that no observation could contradict.
- Every hypothesis in one category.
- A hypothesis that names a fix ("add a lock") instead of a cause.
- A claim of evidence that does not cite a log line, a trace, a commit, or a file.
- Code or tests were changed.
- The user's ranking was ignored, or the hypotheses were presented as findings.

## Verification

- [ ] The symptom card was read and the code at the failing place was read.
- [ ] All seven categories were considered, and skips have a reason.
- [ ] Each hypothesis has a prediction that could be false and a cheapest test.
- [ ] Between 3 and 5 hypotheses are ranked, with a basis for the ranking.
- [ ] The top three are not all from one category.
- [ ] The table is in `diagnosis.md` and was shown to the user, marked provisional.
- [ ] No code, test, or probe was added.
