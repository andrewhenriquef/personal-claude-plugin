---
name: test-analysis
description: Review the quality of tests for a code change. Finds changed behavior that no test protects, weak or assertion-free tests, over-mocking, missing negative and edge cases, flaky patterns, and tests weakened in the same change. Proves weak tests with a small diff-scoped mutation check. Use when the user asks to review tests, check test quality, find missing or weak tests, check for flaky tests, or asks "are these tests good". Read-only, reports findings, does not write tests unless asked.
---

# Test Analysis

> Evidence sources: [Practical Mutation Testing at Scale (Google)](https://arxiv.org/abs/2102.11378), [Mutation Testing for AI-Generated Code](https://www.augmentcode.com/guides/mutation-testing-ai-generated-code), and the xUnit test smell catalog ([Meszaros, xUnit Test Patterns](https://dl.acm.org/doi/10.5555/1076526); [tsDetect](https://testsmells.org/assets/publications/FSE2020_TechnicalPaper.pdf)). Structure follows [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills).

A test is good when it **fails if the behavior breaks**. Passing tests and high coverage do not show that. This skill checks whether the tests for a change would catch a bug, and proves it with evidence.

This skill is read-only. Report findings. Do not edit code or tests unless the user asks for a fix after the report.

## Why this process

1. **Coverage is not protection.** A line can run in a test and still have no assertion about it. Coverage is a candidate generator, not a verdict.
2. **Generated tests are the usual weak spot.** Studies of LLM-written tests find weak assertions, boundary blindness, and assertions copied from what the code does, not from what it should do. Review tests written by an agent with extra care.
3. **Proof beats opinion.** "This test looks weak" is an opinion. "I changed `>=` to `>` on line 42 and every test still passed" is evidence.
4. **A test that was edited to pass is a warning.** If a change alters production code and also loosens a test, ask why.

## When to use

- A diff, branch, or PR changes behavior and needs a check that the tests protect it.
- The user asks if tests are good, missing, weak, or flaky.
- Tests were written or edited by an agent.

## When NOT to use

- The user wants tests written. Review first, then write as a separate step.
- The user wants test style or formatting checked. Use `static-analysis`. Test linters (`rubocop-rspec`, `testifylint`) run there.
- The user wants the code checked against its intended behavior (a story, PRD, plan, ticket, or a plain description). That is a correctness review. This skill checks the tests, not the code.

## Process

### Step 0: Set scope

1. Use the files the user names.
2. If none, use the current change. That is the files not committed yet (`git diff --name-only`, `git diff --staged --name-only`, and new files from `git ls-files --others --exclude-standard`) plus the branch diff against the main branch (`git diff --name-only main...HEAD`; use `master` if the repo has no `main`).
3. Review a whole test suite only when the user asks for a full review.
4. Split the scope into **production files** and **test files**. Skip generated code and fixtures. Say what you skipped.
5. Detect the language from the files and manifests (see Language references). Read the matching reference now. It holds the test command, the flags, the framework smells, and the user's preferences.
6. Find the test command (`CLAUDE.md`, `Makefile`, CI config).
7. Find the **intended behavior** of the change, in this order: what the user told you, then the PR description, commit messages, plan, or ticket, then any story or PRD the user points to. A PRD is not required. If you find no statement of intent, infer it from the commit messages and the code, and say so. Checks that compare an expected value to the intent then have lower confidence. Put those under "Needs human check", not under findings.

### Step 1: Map changed behavior to tests

For each production file in scope, list the **behaviors** that changed or were added. A behavior is one of: a branch or condition, an error path, a boundary, a new input case, a side effect, or a new public function.

For each behavior, find the tests that exercise it (search by function name, file name, and the test directory conventions). Fill this table in your notes:

| Behavior | Test that exercises it | Assertion that would fail if it broke |
|---|---|---|

An empty cell is a candidate. Also note **test files changed with no production change**. Those are refactors of tests, and Step 3 applies.

If the project already has coverage tooling configured, run it on the scope and use the uncovered lines as extra candidates. Do not install a tool.

### Step 2: Detect candidates, one test at a time

Read each test in scope, and each test found in Step 1. Check it against [references/test-smells.md](references/test-smells.md). Read only the sections that match.

Also read the diff of the test files, and look for **weakening in the same change**:

- Assertions removed.
- A strict matcher replaced by a loose one (`eq` to `be_truthy`, `Equal` to `NotNil`).
- An expected value changed to match new output, with no change in the intended behavior (plan, description, commit message, or story).
- A test that is newly skipped, focused, or marked pending.
- A snapshot or golden file regenerated in the same change.

Write each candidate as one line: `file:line, smell, evidence`. Be generous. Step 4 removes the noise.

### Step 3: Run the tests

Run only the tests for the scope, using the command and flags in the language reference. Run them with random order and more than once, so order dependence and flakiness show up:

1. Run once with the project's normal command. If it fails, report the failure first. A failing suite stops the review of other findings, because evidence from a red suite is not reliable.
2. Run again with random order and a fixed seed or shuffle (flags in the language reference). Run 3 times for tests added or changed in this scope.

A test that passes in one order and fails in another is a finding. Record the seed.

### Step 4: Prove weak tests with a small mutation check

Read [references/mutation-checks.md](references/mutation-checks.md) first. It has the safety rules. The short form:

1. Pick up to 10 behaviors from Step 1 that matter most: boundaries, error paths, permission checks, money, and state changes.
2. For each, make **one small change** to the production code that breaks its behavior (flip `>=` to `>`, negate a condition, delete a call, return a constant).
3. Do this in a **separate git worktree**, never in the working tree.
4. Run the tests that should cover it. A mutant that is **killed** (a test fails) shows the test works. A mutant that **survives** (all tests pass) is a weak test, unless the mutant is equivalent.
5. If the project already has a mutation tool configured, use its diff mode on the scope instead.

If the tests need a service you cannot run (a database, a queue, the network), do not guess. Put the behavior under "Needs human check".

### Step 5: Verify each candidate

Treat each candidate as a claim to disprove. Check:

| Check | Question |
|---|---|
| Real | Is the weakness in this test, or does another test already cover it? Search before you report. |
| Evidence | Do you have a surviving mutant, a run result, or a diff line? |
| Risk | If this behavior broke in production, would the user notice only by luck? |
| Fit | Does the fix follow the repo's test style and helpers? |

Decide per candidate:

- **Report:** the weakness is real and you have evidence.
- **Needs human check:** you cannot tell (for example the test needs a service you cannot run). Fail open: do not drop a candidate only because you could not verify it.
- **Drop:** another test covers it, the mutant is equivalent, or the repo's convention makes it correct. Keep a one-line reason for the count.

Do not demand 100% coverage. Do not flag trivial getters, generated code, or code with no behavior. Follow the repo's conventions over general advice.

### Step 6: Report

Sort by severity, then by how much evidence you have.

```
## Test analysis: <scope>

Scope: <files / range>. Skipped: <generated / fixtures>.
Test command: <command>. Runs: <normal / random seed N / count>.

### Change map
| Behavior | Tests | Verdict (protected / weak / none) |

### Findings

Test 1: <Smell>: `<file>:<line>`
- Severity: HIGH | MEDIUM | LOW
- Evidence: <surviving mutant with the exact change / run result and seed / diff line>
- Why it matters: <what bug would pass unnoticed>
- Fix: <the test to add or change: case name, input, expected value>

### Needs human check
- `<file>:<line>`: <what you could not verify and the exact question>

### Summary
Behaviors checked: <N>. Mutants run: <N>, killed: <N>, survived: <N>. Findings: <N>. Needs check: <N>. Dropped: <N> (<top reasons>).
Not covered: <areas out of scope: integration, load, UI, services you could not run>.
```

If the tests are good, say so plainly, with what you checked. Do not invent findings.

**Severity**

- **HIGH:** changed behavior that no test protects (no test, or a mutant survived). A test weakened in the same change as the code. A committed skip or focus that hides a test.
- **MEDIUM:** weak assertions, a missing negative or boundary case, order dependence or flakiness shown by a run, over-mocking that hides the behavior.
- **LOW:** readability smells with no risk. Report LOW only when the user asked for it.

## Language references

Detect the project language from the files in scope and manifests (`go.mod`, `Gemfile`, `*.go`, `*.rb`). Read **only** the matching reference before Step 1. If the scope spans several languages, read each one:

| Language | Detect | Reference |
|---|---|---|
| Go | `go.mod`, `*.go` | [references/go.md](references/go.md) |
| Ruby / Rails | `Gemfile`, `*.rb` | [references/ruby.md](references/ruby.md) |

Each reference holds the test commands and flags (random order, repeat, coverage), the framework's smells with vulnerable and safe samples, the mutation tools, and a **My preferences** section.

**Precedence when rules conflict:**

1. The project's own test conventions, `CLAUDE.md`, and CI.
2. The preferences in the language reference.
3. The defaults in the references.

If the language has no reference, apply the process above with the project's own test command.

To add a language: create `references/<language>.md` with the same sections and add a row to this table.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Coverage is 95%, so the tests are good." | Coverage shows lines that ran. It does not show lines that are checked. |
| "The test passes, so it works." | A test with no assertion passes forever. Run a mutant. |
| "It looks weak, so I will report it." | Without evidence it is an opinion. Run the mutant or find the diff line. |
| "The agent wrote the test and it is green." | Agents assert what the code does, not what it should do. Check the expected values against the intended behavior. |
| "The test needed an update after my change." | Maybe. Check that the new expected value matches the intended behavior, not just the new output. |
| "I could not run it, so I will skip it." | Put it under "Needs human check". Do not drop it. |
| "Every function needs its own test." | Test behavior, not functions. Do not flag code with no behavior. |

## Red flags

- A finding has no evidence (no mutant, no run, no diff line).
- A mutant was applied in the working tree.
- The report counts coverage as protection.
- A test was weakened in the same change and the report does not say so.
- A finding repeats what the linter already reports.
- You asked for 100% coverage or tests for trivial code.
- You wrote or edited tests during a review.
- You ran the suite once and called it stable.

## Verification

- [ ] Scope, skipped files, and test command are stated.
- [ ] Every changed behavior is in the change map.
- [ ] Tests ran in random order and more than once, or the report says why not.
- [ ] Mutants ran only in a separate worktree, and the worktree was removed.
- [ ] Every reported finding has evidence.
- [ ] Weakening in the test diff was checked.
- [ ] Unverifiable candidates are under "Needs human check", not dropped.
- [ ] No code or test file in the working tree was modified.
- [ ] Report says what was not covered.
