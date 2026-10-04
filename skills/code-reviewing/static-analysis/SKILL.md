---
name: static-analysis
description: Run the project's linter and formatter in autocorrect mode on changed code, then fix every remaining violation by hand. Lint rules are never disabled, suppressed, or weakened. Use when the user asks to lint, run the linter, run static analysis, check style, or fix lint errors or warnings, or when a change needs a clean lint run before merge. Default scope is the branch changes against main plus uncommitted files.
---

# Static Analysis

> Strategy sources are in [docs/research/static-analysis-strategies.md](../../../docs/research/static-analysis-strategies.md). Structure follows [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills).

Run the project's own linter and formatter on the code that changed. Let the tool autocorrect what it can. Fix the rest by hand. Finish with a clean run.

**The lint rules are not negotiable.** We never accept code that breaks a rule. We never disable a rule, add a suppression comment, or edit the lint config to make a finding go away. We go to the code and apply the fix the rule requires.

## Why this process

1. **The linter is the source of truth.** The project config says which rules apply. Do not apply your own taste, and do not install or add a tool the project does not use.
2. **Autocorrect first.** The tool fixes most findings with no judgement needed. Hand-fix only what is left.
3. **Agents take shortcuts.** The fastest way to a green run is a disable comment or a weaker config. That hides the problem. This skill forbids both, with no exception.
4. **Not all findings have the same value.** A `Lint/` or `errcheck` finding is often a real bug. A style finding is a preference. Triage so you give bugs the most care.

## When to use

- The user asks to lint, run static analysis, check style, or fix lint output.
- A change needs a clean lint run before merge.
- A linter or CI step fails and the user wants it fixed.

## When NOT to use

- The user wants a design or readability change. Use `code-simplify`.
- The user wants a security review. Use `security-analysis`. Lint security rules (`gosec`, `brakeman`) are only candidates there.
- The project has no linter and the user did not ask to set one up. Ask first. Do not invent a config.

## Rules that never change

- **Autocorrect mode, always.** Run the linter with its autocorrect option on, every time.
- **No suppressions.** Do not add `//nolint`, `# rubocop:disable`, `# rubocop:todo`, `eslint-disable`, `noqa`, or any similar directive.
- **No config edits.** Do not turn off, downgrade, or exclude a rule, a file, or a path in the lint config. Do not generate a todo or baseline file.
- **No "false positive" exits.** If a rule seems wrong for the code, change the code so the rule passes. If you believe the rule is wrong for the project, tell the user in the report. The rule still applies until the user changes the config.
- **Fix the cause.** A fix that only moves the problem (for example `_ =` on an error that matters) is not a fix.

The one exit is **Blocked**: the tool crashes, the config is broken, or two rules conflict so that no code can pass both. Stop and report the exact error. Do not work around it.

## Process

### Step 0: Set scope and language

1. Use the files the user names.
2. If none, use the current change. That is the files not committed yet (`git diff --name-only`, `git diff --staged --name-only`, and new files from `git ls-files --others --exclude-standard`) plus the branch diff against the main branch (`git diff --name-only main...HEAD`; use `master` if the repo has no `main`).
3. Lint the whole codebase or a whole directory only when the user asks for a full run.
4. Skip generated and vendored files. Say that you skipped them.
5. Detect the language from the files and manifests (see Language references). Read the matching reference **before** Step 1. It holds the commands, the autocorrect options, the rule classes, and the user's preferences.

A file in scope is linted as a whole file. Fix every violation in it, including old ones. Files outside the scope are not touched. If the tool works on a wider unit (Go works on packages), the language reference says what the scope unit is.

### Step 1: Find the project's lint setup

Look for how the project lints. Use this order:

1. `CLAUDE.md` and README.
2. `Makefile`, `package.json` scripts, `Rakefile`, `justfile`, `Taskfile`.
3. CI config (`.github/workflows`, `.gitlab-ci.yml`). CI shows the exact command that must pass.
4. Linter config files (listed in the language reference).

Use the project's command, with its autocorrect option added. If the project has no command, use the fallback in the language reference, and say so. If there is no linter config, run the fallback and do not create a config.

Record the tool version. Output differs between major versions.

Find the test command too (`CLAUDE.md`, `Makefile`, CI). You need it in Step 3.

### Step 2: Autocorrect

1. Run the linter with autocorrect on the scoped files only, not the whole repo. Use the command in the language reference.
2. Run the formatter. Formatting is a separate result from lint rules.
3. Read the diff. Autocorrect can change behavior when a fix is marked unsafe. Keep the unsafe fixes you can verify. Revert any fix that changes behavior, then fix that finding by hand in Step 4.
4. Run each tool once per pass. Do not loop on a tool that crashes. Report the crash and the exact error.

If the tool reports a config error or a missing plugin, the run is **Blocked**. Stop and report it.

### Step 3: Run the tests

Run the project's tests that cover the changed files. A green baseline before Step 2 is best. If tests fail after autocorrect, find the fix that broke them, revert that fix, and handle the finding by hand in Step 4.

If there are no tests for the code, tell the user. Review the autocorrect diff more carefully instead.

### Step 4: Fix the rest by hand

Run the linter again. Group the remaining findings by rule and classify them:

| Class | Meaning | Action |
|---|---|---|
| Likely bug | Correctness rules: ignored errors, shadowed variables, unreachable code, wrong types | Fix first. Flag to the user as a possible bug |
| Manual fix | The rule is correct and needs a code change | Fix the cause |
| Design signal | Complexity, length, or nesting rules | Refactor the code so it passes. Keep behavior. Use the `code-simplify` principles: small steps, tests green. Do not split code mechanically |
| Autocorrect refused | The tool cannot fix it, or its fix changed behavior | Fix by hand |

Order of work: likely bugs, then manual fixes, then design signals.

For each finding:

1. Read the rule. Understand what it protects.
2. Change the code so it complies. Prefer the smallest change that satisfies the rule and keeps behavior.
3. Run the linter on the file. Run the tests after each group of fixes.
4. If a fix needs a test change, you probably changed behavior. Revert it and find another fix. If no other fix exists, report it under **Blocked**.

Repeat until the linter reports zero findings on the scope. Do not stop at "mostly clean".

Commit only if the user asked.

### Step 5: Verify and report

Run in this order: linter (no autocorrect), formatter in check mode, tests. All must pass.

```
## Static analysis: <scope>

Scope: <files / range>. Skipped: <generated / vendored files>.
Tools: <name, version, command used>.

### Result
Findings before: <N>. Autocorrected: <N>. Fixed by hand: <N>. Remaining: <N>.

### Fixed by hand
- `<file>:<line>` <rule>: <what changed and why it satisfies the rule>.

### Possible bugs found
- `<file>:<line>` <rule>: <what the rule found>.

### Blocked (only if any)
- <exact error or conflict, what you tried>.

### Rule feedback (optional)
- <rule the user may want to change in config, and why>. Still enforced.

### Verified
Lint: <result>. Formatter: <result>. Tests: <result or "not run, no tests">.
Not covered: <tools not available, files skipped>.
```

If the first run is already clean, say so plainly and name the tool and scope. Do not invent findings.

## Language references

Detect the project language from the files in scope and manifests (`go.mod`, `Gemfile`, `*.go`, `*.rb`). Read **only** the matching reference before Step 1. If the scope spans several languages, read each one and run each tool:

| Language | Detect | Reference |
|---|---|---|
| Go | `go.mod`, `*.go` | [references/go.md](references/go.md) |
| Ruby / Rails | `Gemfile`, `*.rb` | [references/ruby.md](references/ruby.md) |

Each reference holds the config files to look for, the commands (lint, format, autocorrect), common rules by class, and a **My preferences** section.

**Precedence when rules conflict:**

1. The project's own config, `CLAUDE.md`, and CI. The project always wins.
2. The preferences in the language reference. They guide the choices the config leaves open: which tool to run when several exist, and how to fix a finding.
3. The defaults in the language reference.

Preferences never change the project config. If a preference and the project config disagree, follow the project and tell the user.

If the language has no reference, apply the process above with the project's own commands and its autocorrect option.

To add a language: create `references/<language>.md` with the same sections and add a row to this table.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "I will add a disable comment so CI passes." | Never. Fix the cause. |
| "This rule is noisy, so I will turn it off in the config." | Never. Report the rule in "Rule feedback". It still applies. |
| "It is a false positive." | Change the code so the rule passes. The user decides if the rule changes. |
| "The violation was there before my change." | The file is in scope. Fix it. |
| "A complexity rule fired, so I will split the function." | A mechanical split makes the code worse. Refactor with `code-simplify` principles until the rule passes. |
| "Unsafe autocorrect is fine, the tests will catch it." | Only if the tests cover that code. Read the diff. |
| "Zero warnings means the code is good." | Lint finds a class of problems only. It does not replace review or tests. |

## Red flags

- A new `nolint`, `rubocop:disable`, `rubocop:todo`, or similar comment in the diff.
- A change to `.golangci.yml`, `.rubocop.yml`, or `.rubocop_todo.yml` in the diff.
- The linter ran without its autocorrect option.
- The linter was run with a different version or config than CI.
- The report says "clean" and does not name the tool or the scope.
- Findings remain and the report says "done".
- A fix needed test edits.
- Autocorrect ran on files outside the scope.

## Verification

- [ ] Scope, tool, version, and command are stated.
- [ ] The project's own command and config were used, or the fallback is named.
- [ ] The linter ran with autocorrect on.
- [ ] The linter reports zero findings on the scope, or each remaining finding is under **Blocked** with the exact error.
- [ ] No suppression comment and no config change in the diff.
- [ ] Formatter passes in check mode.
- [ ] Tests pass, or the report says why they did not run.
- [ ] No file outside the scope was changed.
- [ ] Report says what was not covered.
