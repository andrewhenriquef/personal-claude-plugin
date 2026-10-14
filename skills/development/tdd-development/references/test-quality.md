# Test quality

Use in the RED phase of `tdd-development`, before you write each test. Project conventions come first: if the neighbouring tests do something differently, follow them.

## A good test

A good test reads like a specification and goes through a public interface. The code behind the interface can change completely, and the test stays.

- **Behavior, not implementation.** It states what the caller can see: a return value, a response, a visible state change. It does not state which method is called inside.
- **Through a seam.** The seam is a public boundary that you agreed on in Step 1: a function, an endpoint, a command, a class method that callers use. A test at any other place needs a reason.
- **One behavior.** One reason to fail. If the name needs "and", it is two tests.
- **Named as a sentence.** `refuses checkout when the cart is empty`, not `test_checkout_2`. Use the domain's words. Do not number cases.
- **Arrange, act, assert.** Three clear parts. Set-up that matters is visible in the test, not hidden in a helper far away (DAMP over DRY: a test is allowed some repetition to stay readable).
- **Independent.** Each test builds its own state and cleans up. No order dependence. No shared mutable state.
- **Deterministic.** No real clock, random numbers, network, or sleep. Inject or fake them.

## The expected value

The expected value must come from outside the code: a literal, a worked example, the spec. Never from the same formula the code uses.

```
# bad: the test repeats the code, so it passes by construction
expected = items.sum { |i| i.price }
expect(total(items)).to eq(expected)

# good: an independent known value
expect(total([item(10), item(5)])).to eq(15)
```

Never paste the actual value from a failing run into the expected one. Work it out first, from the requirement.

## Where to mock

Prefer, in this order: the real thing, a fake (a working in-memory version), a stub (a canned answer), a mock (an assertion on calls). Go down the list only when you must.

Mock or fake at **system boundaries** only:
- External services (payment, email, HTTP APIs).
- The clock and randomness.
- The file system and the network, when a real one is slow or unsafe.
- The database: prefer a real test database. Fake it only if the project does.

Do not mock your own classes, your own collaborators, or the class under test. A test that asserts a mock was called checks the mock.

To make a boundary easy to fake, pass it in (dependency injection) and give each external operation its own function, not one generic fetcher with conditions inside the fake.

## Anti-patterns

| Anti-pattern | The tell | Fix |
|---|---|---|
| Implementation-coupled | Breaks on a refactor with no behavior change. Asserts call counts, order, or private methods | Assert the outcome at the seam |
| Tautological | The expected value is computed like the code computes it | Use a literal from an independent source |
| Verified through a side channel | Reads the database or a private field to check what the interface should show | Check through the public interface (create, then read it back) |
| Horizontal slicing | All tests written before any code | One test, one change, repeat |
| Assertion-free | No `expect`, or only "does not raise" for logic with a result | Assert the result |
| Over-mocking | More set-up lines than assertions. The mocks mirror the code | Move the seam out. Use a fake |
| Flaky | Passes and fails with no code change. Sleeps, order, real time | Make it deterministic. Do not retry |
| Snapshot abuse | A big snapshot updated without reading | Assert the fields that matter |
| Testing the framework | Checks that the library works | Test your own code |
| Shared state | One test relies on another | Build state per test |
| Giant test | Many acts and asserts, one failure message for all | Split by behavior |
| Skipped or commented out | `skip`, `xit`, `t.Skip`, a commented block | Fix it or delete it with a reason. Never leave it as a hole |

## Size

Match the test to the risk. Most tests should be small and fast.

| Size | What it touches | Use for |
|---|---|---|
| Small | One process, no I/O. Milliseconds | Pure logic, rules, calculations. Most tests |
| Medium | One machine: a test database, localhost | Boundaries: persistence, the HTTP layer, jobs |
| Large | Several systems. Minutes | A few critical end-to-end paths. Keep few |

The tracer bullet can be medium. The rest of the slices should usually be small.

## Before you move on

Ask of the test you just wrote:
1. Did I see it fail for the right reason?
2. Would it fail if the behavior were removed? (If the code is simple, break one line in your head: the test must notice.)
3. Would it survive a harmless refactor?
4. Does the name read as a requirement?
5. Does the expected value come from outside the code?
6. Would a new team member understand the behavior from the test alone?

If the test is hard to write, treat that as a design signal, not a test problem: a hidden dependency, a global, or a function that does too much. Fix the design in its own slice.
