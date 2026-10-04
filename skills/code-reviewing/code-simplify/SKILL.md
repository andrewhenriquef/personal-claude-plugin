---
name: code-simplify
description: Simplify code for clarity without changing behavior. Use when the user asks to simplify, clean up, or refactor for readability, when code works but is harder to read, maintain, or extend than it should be, when a review flags complexity, or when code has accumulated duplication, deep nesting, or unclear names.
---

# Code Simplification

> Adapted from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills/blob/main/skills/code-simplification/SKILL.md). Design references: _A Philosophy of Software Design_ (John Ousterhout), _The Pragmatic Programmer_ (Hunt and Thomas).

Reduce complexity and keep exact behavior. The goal is not fewer lines. The goal is code that is easier to read, change, and debug.

Test for every change: _Would a new team member understand this faster than the original?_

## When to use

- A feature works and tests pass, but the code feels heavier than needed.
- A review flags readability or complexity.
- Code has deep nesting, long functions, or unclear names.
- Code was written under time pressure.
- A merge left duplication or inconsistency.

## When NOT to use

- Code is already clean. Do not simplify for its own sake.
- You do not understand the code yet. Understand first.
- The code is performance-critical and the simpler version is measurably slower.
- The module will be rewritten soon.

## Five principles

### 1. Preserve behavior exactly

Change how code is written, never what it does. Keep inputs, outputs, side effects, error behavior, and edge cases identical. If you are not sure a change preserves behavior, do not make it.

Ask before every change:

- Same output for every input?
- Same errors?
- Same side effects, in the same order?
- Do existing tests pass without edits?

### 2. Follow project conventions

Make the code more consistent with the codebase, not with your taste. Read `CLAUDE.md` and the neighboring code. Match naming, error handling, imports, and layout. A change that breaks consistency is churn, not simplification.

### 3. Prefer clarity over cleverness

Pick explicit code over compact code when the compact form needs a pause to read. Example: replace a nested ternary chain with one early return per condition, and replace a dense boolean expression with a named predicate. Samples are in the language reference.

### 4. Keep balance

Over-simplification is a failure mode too.

- **Over-inlining**: removing a helper that gave a concept a name.
- **Merging unrelated logic**: two simple functions become one complex function.
- **Removing needed abstraction**: some abstractions exist for testing or extension.
- **Optimizing line count**: fewer lines is not the goal.
- **Over-splitting**: many tiny methods with wide interfaces make a module shallower, not simpler. A longer function with one clear job is fine.

### 5. Scope to what changed

Simplify recently changed code by default. Do not refactor unrelated code unless asked. Unscoped changes add noise to the diff and risk regressions.

Work strategically, not only tactically: when you touch code, leave its design a little better than you found it, in small steps. Do not patch around a bad design and do not rewrite it all at once.

## Process

### Step 0: Set scope and a safety net

1. **Scope:** use the files or code the user names. If none, use the current change. That is the files not committed yet (`git diff --name-only`, `git diff --staged --name-only`, and new files from `git ls-files --others --exclude-standard`) plus the branch diff against the main branch (`git diff --name-only main...HEAD`; use `master` if the repo has no `main`). Simplify a whole file or the whole codebase only when the user asks. Do not widen scope without asking.
2. **Tests:** find the test command (`CLAUDE.md`, `Makefile`, CI config, language reference). Run it once to get a green baseline.
3. **No tests, or tests do not cover the code:** write a characterization test that pins current behavior first, or tell the user and ask before you continue. Do not simplify code you cannot verify.

### Step 1: Understand first (Chesterton's Fence)

Do not remove or change a thing before you know why it exists. Answer:

- What is its responsibility?
- What calls it? What does it call?
- What are the edge cases and error paths?
- Which tests define its behavior?
- Why was it written this way? Check `git blame` and the commit message.

If you cannot answer, read more context first.

### Step 2: Find opportunities

Each pattern below is a concrete signal.

**Structure**

| Signal | Fix |
|---|---|
| Nesting 3+ levels deep | Guard clauses or early return |
| Function 50+ lines with several responsibilities | Split by responsibility. A long function with one job is fine |
| Nested ternaries | `if` chain, `switch`/`case`, or lookup map |
| Boolean flag parameters, `run(true, false)` | Options struct / keyword arguments, or separate functions |
| Same condition repeated | Extract a named predicate |

**Naming and comments**

| Signal | Fix |
|---|---|
| Generic names: `data`, `tmp`, `res`, `val` | Name the content: `userProfile`, `validationErrors` |
| Abbreviations: `usr`, `cfg`, `btn` | Full words. Keep universal ones: `id`, `url`, `api` |
| Misleading names: `get` that mutates | Rename to match behavior |
| Comment says _what_: `// increment` above `i++` | Delete it |
| Comment says _why_: `# retry, API is flaky under load` | Keep it |

**Redundancy**

| Signal | Fix |
|---|---|
| Same knowledge (rule, format, constant) in many places | Keep one source. See `pragmatic-programmer.md` (DRY) |
| Same-looking code that changes for different reasons | Leave it. Merging it couples things that are not related |
| Dead code: unreachable branches, unused variables, commented-out blocks | Remove, after you confirm it is dead |
| Wrapper that adds nothing | Inline it |
| Factory of a factory, strategy with one strategy | Use the direct approach |

If the problem is the shape of a module (layers, interfaces, coupling), not its lines, see Design references below.

### Step 3: Apply changes one at a time

One simplification per change. Run tests after each.

1. Make the change.
2. Run the tests.
3. Pass: continue to the next change. Fail: revert and rethink.

Commit only if the user asked you to.

Keep refactors separate from features and bug fixes. A PR that does both is two PRs.

**Rule of 500:** if a refactor touches more than 500 lines, use automation (codemod, AST script, or the autocorrect tool in the language reference) instead of manual edits.

### Step 4: Verify the result

Compare before and after:

- Is it really easier to understand?
- Did you add a pattern the codebase does not use?
- Is the diff clean and reviewable?
- Would a teammate approve it?

If the result is harder to read or review, revert. Not every attempt succeeds.

### Step 5: Report

Tell the user, briefly:

- **Applied:** each simplification and why.
- **Flagged, not applied:** changes that alter behavior or contract, changes outside scope, and design issues that need a decision.
- **Skipped:** things you left alone on purpose (Chesterton's Fence, coincidental duplication).
- **Verified:** which tests and linters you ran, and the result.

## Design references

When the problem is the shape of a module, not its lines, read the matching reference. Read only what you need. Project conventions (principle 2) win over any advice in these references.

| Reference | Read when |
|---|---|
| [references/philosophy-of-software-design.md](references/philosophy-of-software-design.md) | Interfaces, layers, or modules feel heavy: shallow modules, pass-through methods, information leakage, config pushed to callers. |
| [references/pragmatic-programmer.md](references/pragmatic-programmer.md) | Duplication, coupling, or hidden errors: DRY, orthogonality, Law of Demeter, fail early. |

Core ideas, always apply:

- **Easier To Change (ETC):** the test for any design change. After it, is the next likely change easier or harder? If harder, do not make it.
- **Complexity** is dependencies plus obscurity. Reduce what a reader must know to change a piece of code.
- **DRY is about knowledge, not text.** Merge duplicated rules. Do not merge code that only looks alike.
- **Do not hide errors to look simpler.** Fail early with a clear error. Do not swallow errors or add a silent fallback.
- **Good enough:** stop when the code is clear. Do not gold-plate.

**Do not apply a design change when it changes behavior.** Example: "define errors out of existence" (make `delete` of a missing key succeed) changes the contract. That is a design change, not a simplification. Flag it to the user, do not apply it.

## Language references

Detect the project language from the files you are changing and manifests (`go.mod`, `Gemfile`, `*.rb`, `*.go`). Read **only** the matching reference before you simplify. If the change spans several languages, read each one:

| Language | Detect | Reference |
|---|---|---|
| Go | `go.mod`, `*.go` | [references/go.md](references/go.md) |
| Ruby | `Gemfile`, `*.rb` | [references/ruby.md](references/ruby.md) |

Each reference holds before/after samples, plus the language's test, lint, and autocorrect commands. If the language has no reference, apply the principles and process above, and follow the neighboring code.

To add a language: create `references/<language>.md` and add a row to this table.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "It works, do not touch it." | Hard-to-read code is hard to fix when it breaks. |
| "Fewer lines is always simpler." | A one-line nested ternary is not simpler than five lines of `if`. Simple means fast to understand. |
| "I will simplify this unrelated code too." | Unscoped changes make noisy diffs and risk regressions. |
| "This abstraction may be useful later." | Do not keep speculative abstractions. Add them back when needed. |
| "The original author had a reason." | Maybe. Check `git blame`. Often it is leftover from iteration under pressure. |
| "I will refactor while I add this feature." | Mixed changes are hard to review and revert. Split them. |

## Red flags

- A simplification needs test edits to pass. You probably changed behavior.
- The "simpler" code is longer and harder to follow.
- You rename things to your taste, not the project's convention.
- You remove error handling "to be cleaner".
- You simplify code you do not fully understand.
- You batch many simplifications in one large commit.
- You refactor outside the task scope without being asked.

## Verification

- [ ] Existing tests pass without modification.
- [ ] Build passes with no new warnings.
- [ ] Linter and formatter pass (see the language reference).
- [ ] Each simplification is a small, reviewable change.
- [ ] Diff has no unrelated changes.
- [ ] Code follows project conventions.
- [ ] No error handling was removed or weakened.
- [ ] Interfaces are not wider, and modules are not shallower, than before.
- [ ] No dead code left behind (unused imports, unreachable branches).
