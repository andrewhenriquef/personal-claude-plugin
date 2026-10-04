# Test smells and review questions

Use in Step 2 of `test-analysis`. Read only the sections that match the tests in scope. Each row is a question to ask about a test, not a pattern to grep for. A smell is a finding only when it hides a bug that could ship. Language and framework smells are in the language references.

Sources: the xUnit test smell catalog ([Meszaros](https://dl.acm.org/doi/10.5555/1076526)), [tsDetect](https://testsmells.org/assets/publications/FSE2020_TechnicalPaper.pdf), and studies of LLM-written tests.

## Does the test protect the behavior?

| Smell | Ask | Example |
|---|---|---|
| No assertion | Does the test check anything? Does it only call the code and finish without an error? | A test that calls `process(order)` and has no `expect` |
| Weak assertion | Does the assertion hold for almost any output? | `not nil`, `status 200` only, `be_truthy`, `len > 0` |
| Wrong thing asserted | Does it check the mock it just set up, or a value computed with the same logic as the code? | `expect(mock).to receive(:x)` then call `x` yourself. Expected value built with the production formula |
| Boundary blindness | Are the inputs far from the edges? | Tests `age = 5` and `age = 50`, never `17`, `18`, `0` |
| Happy path only | Is there a test for the error, empty, nil, duplicate, and not-allowed case? | Only `valid credentials` for a login change |
| Tautology | Can the test fail at all? | `assert x == x`, an `if` in the test that skips the assertion |
| Catch-all | Does the test pass when the code raises or returns an error? | `rescue` or `recover` around the assertion, `expect { }.not_to raise_error` as the only check |

## Does the test check behavior, not structure?

| Smell | Ask | Example |
|---|---|---|
| Over-mocking | Is the unit under test mocked? Are internal collaborators mocked so that nothing real runs? | The test stubs the method it claims to test |
| Implementation coupling | Would a correct refactor break the test? | Asserts the exact order of private calls, or the SQL text |
| Mystery guest | Does the test depend on data in a fixture file or a shared setup that the reader cannot see? | The expected value is in a distant factory or JSON file |
| Logic in the test | Does the test have loops, conditionals, or computation that can itself be wrong? | `for` loop that builds the expected list |

## Is the test reliable?

| Smell | Ask | Example |
|---|---|---|
| Sleep or fixed wait | Does it wait a fixed time for something async? | `sleep 2`, `time.Sleep(time.Second)` |
| Real time or randomness | Does it depend on the clock, the time zone, or random values with no control? | `Time.now`, `time.Now()` without a fake clock, no fixed seed |
| Shared state | Does it leave data, globals, env vars, or files that another test sees? | Global config changed, rows not cleaned up, `before(:all)` data |
| Order dependence | Does it pass only after another test ran? | Fails with random order or when run alone |
| External call | Does it call the network, a real service, or the real filesystem path? | Real HTTP call to a third-party API |
| Concurrency in the test | Does it start goroutines or threads and not wait for them? | Test ends before the goroutine asserts |

## Is the test honest?

| Smell | Ask | Example |
|---|---|---|
| Name lies | Does the test name match what it asserts? | `rejects expired token`, but asserts only that a token exists |
| Skipped or focused | Is a test skipped, pending, or focused in a way that hides others? | `t.Skip`, `xit`, `skip`, `pending`, `fit`, `focus: true`, `.only` |
| Blind snapshot | Was a snapshot or golden file regenerated and accepted without reading the diff? | `-update` flag run, snapshot diff in the same change as the code |
| Assertion roulette | Does a test with many assertions and no messages hide which one failed? | 12 `expect` lines in one example with no context |
| Duplicate test | Do two tests check the same thing and nothing else? | Copy-paste with a new name |

## Does the change have the tests it needs?

For each changed behavior, ask:

- Is there a test that fails if this branch is removed or inverted?
- Is the error path tested, and does the test check the error value, not only that an error happened?
- Is the boundary tested on both sides?
- If a permission or ownership check was added, is there a test where the check **denies**?
- If a bug fix: is there a test that failed before the fix? Search the history or run the test against the old code in a worktree.
- If a new input field or option: is a test case present for it and for its absence?
- If an external call: is the failure and timeout case tested?

## Weakened in the same change

Check the diff of test files next to the diff of production files:

- Assertions removed or commented out.
- A strict assertion replaced by a loose one.
- Expected values edited to match new output, with no matching change in the intended behavior (plan, description, story, or commit message).
- Tests deleted when the code they tested is still present.
- New skip, pending, focus, or retry annotations.
- Snapshot or golden files updated.

Each one needs a reason. If you cannot find it, report it under "Needs human check", or as HIGH when the production behavior also changed.

## Exclusions

Do not report:

- Missing tests for trivial code: getters, simple constructors, generated code, and one-line delegation.
- Style of test names, formatting, and line length. That is `static-analysis`.
- A smell that has no path to a shipped bug and that the repo uses everywhere. Mention it once as LOW only if the user asked for LOW.
- "Not enough tests" with no named behavior. Every finding names a behavior.
