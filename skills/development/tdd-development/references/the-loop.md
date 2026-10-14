# The loop in detail

Use in Steps 0 to 4 of `tdd-development`. The headings match the steps.

## Ledger

Each shell command starts fresh and a long run can be summarized. Keep the state of the run in files outside the working tree, in the git directory, so they do not show in `git status`:

```sh
state="$(git rev-parse --absolute-git-dir)/tdd-development/<slug>"
mkdir -p "$state" && echo "$state"
```

Write the printed path in the first line of `$state/ledger.md`, and start every later command with `state=<that path>`. Read the ledger, not the conversation, to see where the run is. Update it after each phase.

```markdown
# tdd-development run
State dir: <absolute path>
Intent: <one or two lines, and the source>
Commands: test `<...>` | focused `<...>` | lint `<...>`
Limits: slices 10 | phase 0 tests 8 | red tries 3 | green tries 3 | splits 2 | refactor changes 5 | gate tries 2 (or the user's values)
Counters: slices 0 | phase 0 tests 0
Baseline: <result, and the failures that were already there, by name>
Seams: <the public interfaces under test>
Assumptions: <or "none">

## Test list
- [x] 1. <behavior sentence>: slice 1, tracer bullet
- [ ] 2. <behavior sentence>
- [-] 3. <behavior sentence>: dropped, <reason>

## Slices
### Slice 1: <behavior>
- Test: `<file>` "<name>"
- Tries: red 1/3 | green 0/3 | splits 0/2 | refactor changes 0/5 | gate 0/2
- Expected red: <the reason you wrote before running>
- Red: `<command>` -> <decisive failing lines>
- Frozen: $state/slice-1-frozen.txt
- Green: `<command>` -> <passing line>. Freeze check: ok
- Refactor: <what changed, or "none needed: <reason>">
- Gate: <focused tests, lint result>
```

## The test list

From Canon TDD: the list is behavioral analysis, not design. It answers "what must be true when this is done?"

1. Write the main behavior first, as a sentence. Then the variants (different inputs that take the same path), the edges (empty, one, many, the limit), the errors (invalid input, a failing collaborator), and the behavior that must not break.
2. Words from the domain. No class, method, or table names yet. If a sentence needs one, you are designing.
3. One behavior per line. "validates and saves" is two lines.
4. For user stories: each Gherkin `Scenario` gives one or more lines. `Given` is set-up, `When` is the action at the seam, `Then` is the assertion.
5. The list changes while you work. A new idea goes on the list. A line that turns out to be the same as another is dropped, with a note.
6. Do not turn the whole list into tests. One line becomes a test when its turn comes.

**Order.** The first slice is the tracer bullet: the thinnest case that crosses the whole path, even if the code behind it is crude. Then the simple cases, then the variants, then the edges and errors. A later item that breaks the shape of the code is a sign to refactor, not to hack.

## Phase 0: strengthen the existing flow

Use when the change goes into code that already exists (see Step 2 for when). It adds tests and changes no production code. It takes the place of the red-first rule, because the behavior already exists: these tests pass on purpose. They must still be able to fail.

1. Read the code and trace its collaborators. Read the tests that exist. List the gaps (full depth: every gap in the files you will change; minimal depth: only the paths the change touches directly): a branch with no test, a rule no test states, an input not covered.
2. Write one characterization test for one gap. It states what the code does today, through the seam. Name it for the behavior.
3. Run it. It should pass. A failure means you misread the code: fix the test, or you found a bug. A bug is not fixed in Phase 0: list it, and ask the user.
4. **Prove it can fail.** Break the production line it covers on purpose (change an operator, return a constant), with the Edit tool. Run the test: it must fail. Put the line back with the Edit tool, exactly as it was. Check with `git diff -- <file>` that the production file shows only the changes you meant to make. Never use `git restore`, `git checkout`, or `git stash` to undo it.
5. Freeze the new tests like a slice.
6. Stop at the Phase 0 limit (8 tests). Gaps that are left go to the ledger as deferred.
7. The gate must be green before the first RED of Step 3.

Skip a characterization test for a gap that is only a detail of the current implementation. Pin the behavior, not the shape.

**Failures that were already there.** A new test for old code can fail because of a bug or a broken collaborator that is not yours. Do not fix it silently. Check it against the baseline you ran in Step 0. If the code fails without your test too, escalate (see "Escalation") with the options: stub the broken collaborator in this test, fix it as its own task, or defer with a note. Let the user choose.

## RED

**Write one test.** At the agreed seam, in the project's style, named for the behavior. Arrange, act, assert, with the expected value written as a literal ([test quality](test-quality.md)).

**Write the expected failure before you run it.** One line: "fails with `expected 5, got 0`" or "fails with `NameError: uninitialized constant Cart`". This is what stops you from calling any red good.

**Run the focused test and read the output.** Check it against the line you wrote:

| What you see | Meaning | Action |
|---|---|---|
| The failure you expected, at the assertion or at the missing unit | A good red | Go on |
| Syntax error, bad import, wrong path, missing fixture, broken setup | The test is wrong | Fix the test. Run again. Not a red |
| A different assertion failed | The test checks something else | Read it. Fix the test or your expectation |
| The test passes | The behavior exists, or the test cannot fail | Find out which. Drop it, or write a test for the real gap. Never keep it as proof |
| The whole file or the suite fails to load | Something else is broken | Compare with the baseline. Fix only what your test caused |
| Slow, or it hangs | The seam is too far out | Test one level in, at a seam that is still public |

**A missing unit is an acceptable first red** for new code: `NameError`, `undefined: Cart`, `cannot find module`. Do not stop there when the language lets the test run. Add the empty stub (the signature, with a zero value) to get the assertion failure, and show that second red. The language references say how.

**Freeze.** List the slice's test files, one path per line, in `$state/slice-N-tests.txt`. Then:

```sh
state=<state dir>
while IFS= read -r f; do shasum -a 256 -- "$f"; done < "$state/slice-N-tests.txt" > "$state/slice-N-frozen.txt"
```

## GREEN

Write the smallest change that makes the test pass. "Smallest" can be crude: return the constant, handle the one case. The next test will force the general version. Do not write code that no test asks for.

Then, in this order:

1. Run the focused test. It must pass.
2. Run the tests of the area (the folder, the package). Nothing else may break.
3. Check the freeze:

```sh
state=<state dir>
shasum -a 256 -c "$state/slice-N-frozen.txt" --quiet && echo FROZEN_OK
```

A changed file prints `FAILED` and exits with 1. A deleted file prints a warning that it "could not be read". Both mean the green is not valid. Do not look for a way around it. Either the production change was wrong, or the test is wrong and the slice goes back to RED with a stated reason.

**Allowed changes to a test during GREEN:** none. A test that needs a different setup after you saw the code is a test that did not know enough. Go back to RED, say what you learned, write the better test, and show the new red.

**When the green is large.** More than about 30 lines, more than 2 files, or a new concept (a class, a table) is a sign that the test was too big. Undo your production edits by hand, split the item into smaller tests on the list, and start the first one.

## REFACTOR

Only when everything is green. The goal is a design that makes the next change easy (Easier To Change).

What to look at: the code and the test of this slice, and the code next to it that it touches. Not the rest of the repository.

What to do, one change at a time, with the tests run after each:
- Rename to the domain's words.
- Extract a function or a method when a block has a name worth having.
- Remove duplication of **knowledge** (the same rule in two places). Leave code that only looks alike.
- Inline a helper that adds nothing. Flatten nesting with a guard clause.
- Move code to where it belongs when the second slice shows where that is.

The principles of `code-simplify` apply in full. If a change fails a test, undo that change by hand and rethink. If you cannot say what a change is for, leave it.

**Tidy the tests too.** You may rename a test, extract a setup helper, or remove duplicated setup, if the number of examples stays the same, no assertion gets weaker, and the suite stays green. Then freeze the slice again, and say so in the ledger.

**What not to do:** add behavior, make code more general than the tests need, refactor outside the slice, or change a public interface (that is a new slice with its own test).

## Bugs: the Prove-It route

A bug fix is a slice whose RED is the reproduction.

1. If a diagnosis exists (`docs/<slug>/diagnosis.md` from `diagnose-and-reproduce`), take its failing test as the RED. Check that it still fails and that it fails for the reported symptom.
2. If the cause is clear and no test exists, call `Skill(skill: "reproduce-bug")` to get one command that fails on the exact symptom.
3. If the cause is unknown, stop. Call `Skill(skill: "diagnose-and-reproduce")`, then come back.
4. Freeze the reproduction test. GREEN is the smallest fix. Run the area and the full suite.
5. The regression test stays in the suite. Its red is in the ledger. A fix without it is not finished.

## When stuck

| Situation | Action |
|---|---|
| The red is for the wrong reason, again | Fix the test. After 3 tries, read the failure as a question about the seam: is it the right place to test? |
| GREEN does not come after 3 honest tries | Stop. Report the test, the tries, and the output. Ask whether the test is right, the seam is right, or the design needs a decision |
| The test is hard to write | The design is hard to test. Ask what makes it hard: a hidden dependency (inject it), a global (wrap it), a large function (split it). Fix that as its own slice |
| The test needs many mocks | You are testing too deep. Move the seam out, or mock only the system boundary |
| The test is slow | Test one level in, with a fake at the boundary. Keep one slow, end-to-end test for the tracer bullet |
| A new idea or edge case appears | Add it to the list. Do not build it now |
| The suite was red before you started | The baseline. Do not fix it. List it |
| Two tests want opposite things | A requirement conflict. Stop and ask the user |
| You cannot say what the behavior should be | The intent is unclear. Ask, or write the question as an assumption |

The limits table in `SKILL.md` sets how many tries each row gets. A stop is a result. Write what was tried, with the output, and what you need. When the user raises a limit, record the new value and the date in the ledger, and keep counting from the counter you had.

## Escalation

Stop and ask the user, and do not improvise, when:
- a limit in `SKILL.md` is reached;
- the fix needs a file outside the agreed scope;
- a dependency is missing (a gem or module that is not installed, an env var, a service that is down);
- a test in the area fails at the baseline, or a red shows a bug that was already there;
- the change conflicts with a convention in the project's linter or test config;
- two tests want opposite behavior, or the intent is unclear.

Write the escalation in this shape:
1. **Tries.** The number of tries and what each did, with the decisive output.
2. **Not tested yet.** The hypotheses or options you have not tried.
3. **Options.** Two or three concrete ways forward, each with its cost.
4. **Wait.** Make no change until the user chooses.

If more than one open decision depends on another, call `Skill(skill: "interview")` to settle them one branch at a time. Never invent a ticket number for a "defer" option: write "defer, with a note in the report".

## Final check

Run the full command, not only the area. Report each failure by name. Compare with the baseline: a failure that was there at the start is "already failing", and a new one is yours to fix or report. Run the freeze check for every slice once more, in a loop over `$state/slice-*-frozen.txt`.
