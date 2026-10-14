# TDD strategies for AI agents

Research behind the `tdd-development` skill. Date of research: 2026-10-13.

## Finding

Public TDD skills agree on the loop: write a failing test, watch it fail, write the smallest code that passes, refactor on green. They differ on what stops an agent from cheating. The strongest ones add an "iron law" and a list of excuses (superpowers). Others split the phases into separate agents so the test writer cannot plan the implementation (Opdahl, jwilger, s-hiraoku). Kent Beck's own account of agents is that they delete failing tests or write tests that confirm the code they just wrote. No source offered a mechanical check. Several sources are blogs, vendor pages, or secondary summaries, so treat the practices as engineering advice, not measured results.

## Strategies and where they come from

| # | Strategy | Source | Where the skill uses it |
|---|---|---|---|
| 1 | Canon TDD: write a test list (behavior only), turn one item into a test, make it and all earlier tests pass, optionally refactor, repeat. New cases found while working go on the list | [Kent Beck, Canon TDD](https://newsletter.kentbeck.com/p/canon-tdd) | Steps 1 and 3, `the-loop.md` "The test list" |
| 2 | Mistakes to avoid: mixing design into the list; turning every list item into a test before any passes; deleting assertions to go green; pasting the actual value into the expected one; refactoring while making it pass; refactoring too far or abstracting too soon. "Duplication is a hint, not a command" | Beck, Canon TDD | Rules, red flags, REFACTOR |
| 3 | No production code without a failing test first. The red must fail for the expected reason. A test that passes at once tests existing behavior. Run the full suite, because a green test is not a green suite | [obra/superpowers test-driven-development](https://skillselion.com/skills/obra/superpowers/test-driven-development) (listed at roughly 110k installs by third-party pages) | Rules, RED checks table, Step 4 |
| 4 | A table of rationalizations and a list of red flags, each with a rebuttal | superpowers | "Common rationalizations", "Red flags" |
| 5 | Discover the stack first: use checked-in wrappers, read CI, never assume `npm test` | [addyosmani/agent-skills TDD](https://skillselion.com/skills/addyosmani/agent-skills/test-driven-development) | Step 0 |
| 6 | Prove-It for bugs: reproduce with a failing test, then fix, then run the suite | addyosmani, and the `tdd` plugin's xfail-first fix flow cited in `bug-diagnosis-strategies.md` | "Bugs: the Prove-It route", reuse of `reproduce-bug` |
| 7 | State over interaction. Real implementation, then fake, stub, mock. One concept per test. Descriptive names. DAMP over DRY | addyosmani | `test-quality.md` |
| 8 | Agree the seams (public interfaces) with the user before any test. Tautological tests: the expected value recomputes the code. Horizontal slicing is an anti-pattern. Vertical slices with a tracer bullet. Mock only at system boundaries | mattpocock `tdd` (installed in the author's environment) | Step 1, `test-quality.md`, slice order |
| 9 | Separate agents for the red, green, and refactor phases. The test writer must run the test and return the failure. The implementer sees only the test. Phase gates. Reason: implementation planning leaks into test design in one context | [Alex Opdahl, custom TDD workflow](https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/); similar rules in s-hiraoku/claude-harnesses `tdd` and jwilger/agent-skills `tdd` (seen as search summaries only) | Not used as agents (see design choices). The idea is kept as "write the expected failure first" and the freeze check |
| 10 | Agents delete failing tests, or write tests that confirm what they built. "The genie doesn't want to do TDD. It wants to write the code and then write tests that pass" | Beck, as quoted by [secondary sources](https://caimito.net/en/blog/2026/04/17/tests-beat-instructions-for-ai-coding-agents.html). Not read in the original | Rules "never weaken a test", the freeze check |
| 11 | Phase 0: strengthen the coverage of the existing flow with no production change. A protocol for failures that were already there. A meaningful red (a missing constant, not a syntax error) | The author's own `tdd-phase-workflow` and `tdd-rspec` skills | Step 2, Phase 0, Ruby conventions |
| 12 | Hard-to-test code is a design problem: inject dependencies, simplify interfaces, extract helpers | superpowers, mattpocock | "When stuck", `test-quality.md` |
| 13 | Refactor principles: keep behavior, follow conventions, clarity, balance, scope | `code-simplify` in this plugin | REFACTOR step |
| 14 | From the author's `rails-tdd-developer`: run the tests of the target files before any edit and stop on a red; escalate after 3 failed tries or when a fix needs files outside the scope, with the tries, the untested hypotheses, and 2 or 3 options; the user picks the depth of Phase 0 (full, minimal, skip); trace every source rule to a plan item and to a test; report exact numbers, never vague words; check coverage of the changed lines; no skipped or pending tests; do not invent APIs or versions; ask the business questions as an interview | The author's own `rails-tdd-developer`, `tdd-phase-workflow`, `tdd-rspec` skills | Baseline rule, "Escalation", Step 1 trace and Phase 0 depth, Step 4 coverage and `run-pipelines`, "Do not guess", "Numbers come from commands", Ruby conventions |
| 15 | Skill anatomy: overview, when to use, process, rationalizations, red flags, verification | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | `SKILL.md` layout |

## Design choices that are not from a source

These come from the owner's requirements and the failure modes of agents. Test them in use.

- **One skill, not an orchestrator with phase agents.** The owner chose a single skill. It keeps the cost low and the maintenance small. The price is that one context writes both the test and the code. Three things replace the isolation: the expected failure is written before the run, the red output is kept as proof, and a hash of the test files is checked after green.
- **The freeze check is new.** After the red, the test files are hashed with `shasum`. After the green, the hash is checked. A changed or deleted file means the green is not valid. No source had a mechanical check: Opdahl's gates are instructions to the model. The check does not stop the agent from editing a test, but it makes the edit visible and stops the run.
- **The ledger lives in the git directory, not in `docs/`.** The loop makes many small notes (proofs, commands). They survive a context summary and do not pollute the repository or `git status`. The final report goes to the chat.
- **Phase 0 breaks and restores a production line with the Edit tool** to prove a characterization test can fail. The plugin bans `git restore`, `checkout`, and `stash`, so the restore is by hand, checked with `git diff`.
- **Refactor stays in the loop**, as in Canon TDD, not moved to review (mattpocock) and not a separate agent (Opdahl). It uses the principles of `code-simplify` and is allowed to be "no refactoring needed".
- **Every loop is bounded.** The skill has a table of limits: 10 slices per run, 8 characterization tests, 3 tries for a good red, 3 for green, 2 splits of one item, 5 refactor changes per slice, 2 gate fixes. The stop after 3 failed tries follows the stop path of `diagnose-and-reproduce` (strategy 5 in `bug-diagnosis-strategies.md`). The other numbers are defaults chosen to keep a run reviewable, not from a study. A limit stops the run and is reported. Only the user can raise it. Added list items do not raise the slice limit.
- **Taken from `rails-tdd-developer`, left out on purpose:** the senior-developer persona; an approval between every phase (kept as an optional "checkpoint pace"); the AS-IS and TO-BE planning documents and the planning review (the planning skills own that); the style gallery and the Tavola Docker functions (project-specific); a fixed 95% coverage floor (only in the Ruby page as the owner's preference; the project's minimum wins).
- **Pace is a user choice.** Continuous is the default so the loop stays fast. Checkpoint pace stops after every slice for the user's OK, for people who want the control of the original skill.
- **Large green means the slice was too big.** The numbers (about 30 lines, more than 2 files) and the stop after 3 tries are defaults, not from a study.
- **The baseline comes first and is compared at the end.** A failure present at the start is "already failing". The plugin forbids `git stash`, so the check is a run before any edit, not the stash-and-rerun protocol of `tdd-phase-workflow`.
- **The gate reuses plugin skills.** `run-pipelines` on the changed files if `docs/pipelines.md` exists, otherwise the project's linter in check mode, then `static-analysis` for violations. Hand-off at the end: `complete-code-review`, and `tech-debt-analysis` in Change mode.

## Tool facts used in the references

Checked on the research date, in a scratch module or project:

- Go 1.26: a test that calls an undefined function prints `undefined: Add` and `FAIL ... [build failed]`. After an empty stub the assertion failure prints `--- FAIL: TestAdd` with the `t.Fatalf` message. `go test ./... -count=1` passes with the real code.
- Ruby 4.0 with Minitest 6: a missing `require_relative` file raises `LoadError`. A missing constant is reported as an Error (`NameError: uninitialized constant`). After a stub, `assert_equal` prints `Failure`, `Expected: 5`, `Actual: 0`. `-n test_name` runs one test.
- `shasum -a 256 -c <file> --quiet` exits with 1 for an edited file and prints a warning for a deleted one. Tested on macOS. The loop that writes the hashes reads paths from a file, because zsh does not split an unquoted variable.

Not verified: the RSpec commands (RSpec is not installed here), `bin/rails test path:LINE`, the Go subtest pattern `-run '^TestName$/^case_name$'`, `golangci-lint run` on a package, and the FactoryBot and ActiveSupport advice. They come from the author's knowledge of the tools. Check them with `--help` on the installed version. Search summaries of the s-hiraoku and jwilger skills and of a 2026 arXiv paper on test-driven code generation (whose date looks unusual) were not read in full. They are not cited as evidence.
