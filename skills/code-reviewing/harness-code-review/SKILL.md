---
name: harness-code-review
description: Run the current harness's own code review and simplify tools on a change, and report the findings. In Claude Code, it calls the built-in `code-review` skill, then the built-in `simplify` skill. In Cursor, it runs the native `bugbot` and `security-review` subagents (the same reviewers as `/review`), then this plugin's `code-simplify`. Report only by default. Applies fixes only when the user says "fix" or "apply". Default scope is the current branch against main plus the uncommitted work. Named files narrow it. Also runs inside a `code-reviewer` agent for `complete-code-review`, as one review lens. Use when the user asks for a "harness review", a "native review", a "quick review", or a review "with the built-in tools". For every lens, use `complete-code-review`.
---

# Harness Code Review

> Native tools: Claude Code ships the `code-review` and `simplify` skills. Cursor 3.7+ ships `/review`, `/review-bugbot`, and `/review-security` ([changelog](https://cursor.com/changelog/bugbot-updates-june-2026)). Each Cursor command launches one subagent: `bugbot` (correctness and logic bugs) or `security-review` (security issues). Cursor has no native simplify command.

This skill does not review code itself. It finds out which harness it runs in, calls that harness's own review and simplify tools, and reports what they found in one place.

## Why this process

1. **Each harness has a reviewer built in.** It is tuned for its own models and tools. Use it, do not copy it.
2. **Review first, then simplify.** Fix correctness first. Simplify the final code.
3. **Simplify changes code.** The Claude Code `simplify` skill always edits files. In report mode it does not run.
4. **One format for the orchestrator.** When `complete-code-review` runs this skill, it merges the findings with the other skills. The findings must use the shared format.
5. **Fail open.** A native tool that is missing or fails is reported. It is never replaced in silence by another skill.

## When to use

- The user wants a fast review with the harness's own tools.
- `complete-code-review` runs it in a `code-reviewer` agent, as one lens.

## When NOT to use

- The user wants every lens (security, data, reliability, tests, performance). Use `complete-code-review`.
- The user wants only the linter. Use `static-analysis`.
- The user wants only simplification. Use `simplify` in Claude Code, or `code-simplify`.
- The change is only docs or comments. Say so and stop.

## Process

### Step 0: Find the harness and the mode

**Harness.** Look at the tools you have:

- The `Skill` tool is available: **Claude Code**.
- No `Skill` tool, but the Task tool and `AskQuestion` are available: **Cursor**.
- Neither: the harness is not supported yet. Say so and stop. Do not guess a command.

**Mode.**

- **Orchestrated:** the prompt gives a scope (a file list, or "full") and says "Do not edit the working tree". A `code-reviewer` agent started this skill for `complete-code-review`.
- **Standalone fix:** the user said "fix", "apply", or "review and fix".
- **Standalone report:** everything else. This is the default.

### Step 1: Set the scope

1. **Orchestrated:** use the scope from the prompt. Do not compute a new one.
2. **Standalone:** use the files the user names, or the PR the user names. If none, use the current change: the files not committed yet (`git diff --name-only`, `git diff --staged --name-only`, and new files from `git ls-files --others --exclude-standard`) plus the branch diff against the main branch (`git diff --name-only main...HEAD`; use `master` if the repo has no `main`).
3. Drop deleted files, vendored code (`vendor/`, `node_modules/`), and generated code. Say what you dropped.
4. If the scope is empty, say so and stop.

### Step 2: Run the native review

**Claude Code.** Call `Skill(skill: "code-review", args: "<target>")`.

- `<target>`: the PR number or branch the user named, or the file paths in scope. For the default scope, pass no target (the skill reviews the current diff).
- Add the effort level (`low`, `medium`, `high`, `xhigh`, `max`) only if the user gave one. Without one, the skill reuses the last level.
- Add `--fix` only in standalone fix mode. Never add `--fix`, `--comment`, or `ultra` in orchestrated mode.
- Its recipe also reports reuse, simplification, and efficiency cleanups. Keep them. In report mode they stand in for `simplify`.

**Cursor.** Spawn the `bugbot` and `security-review` subagents through the Task tool, **in one message**, so they run at the same time. This is the same as choosing both reviewers in `/review`. Give each one:

```
Repository: <absolute repository path>
Diff: <branch changes | uncommitted changes>
Base Branch: <main, or master>
Custom Instructions: Report only findings in these files: <file list>. Do not edit files.
```

- Use `branch changes` when the branch has commits against the base. Use `uncommitted changes` when it has none. The subagent computes the diff. Do not compute it for it.
- After it returns, drop the rows for files outside the scope.
- In standalone fix mode, apply the findings yourself after both return: verified findings only, the smallest change, then the focused tests.

**Failures.** Retry a failed call once with the same input. If it fails again, record "<tool>: failed, not reviewed" and carry on. If the `bugbot` or `security-review` subagent type does not exist (Cursor older than 3.7, or a subagent that cannot start another subagent), record "native reviewer unavailable" under "Needs human check" and tell the user to run `/review` in the main chat. Do not run another plugin skill in its place without asking.

### Step 3: Simplify

| Mode | Claude Code | Cursor |
|---|---|---|
| Orchestrated | Do not run. Put cleanup findings under "Notes for other reviews" for `code-simplify` | Same |
| Standalone report | Do not run `simplify`, because it edits code. Report the cleanups from `code-review`. Say: "Say fix to run `simplify`" | Read and follow the `code-simplify` skill's `SKILL.md`, Steps 0 to 2 only (scope, understand, find opportunities). Report the opportunities. Edit nothing |
| Standalone fix | After the review fixes are in, call `Skill(skill: "simplify")` | After the review fixes are in, read and follow the `code-simplify` skill's `SKILL.md` in full |

### Step 4: Report

Do not re-review the code and do not re-rank the native output. Two tools that report the same `file:line` with the same root cause become one finding that lists both tools.

Map the native severity to HIGH, MEDIUM, or LOW (critical and high to HIGH, medium to MEDIUM, low, nit, and info to LOW). Use this format:

```
## Harness review: <scope>

Harness: <Claude Code | Cursor>. Mode: <orchestrated | report | fix>.
Scope: <N files, or "full">. Dropped: <vendored, generated, deleted, or "none">.
Tools run: <code-review (<level>) | bugbot, security-review>, <simplify | code-simplify (report only) | none>

### Findings

<id> [<severity>] <tool, or tools that agree> `<file>:<line>`: <the finding in one line>
- Evidence: <what the tool saw>
- Fix: <the tool's suggestion, or "none given">

### Simplification
- `<file>:<line>`: <the opportunity, or what simplify changed>

### Applied (fix mode only)
- <id>: <what changed>, tests: <pass | fail>

### Needs human check
- `<file>:<line>`: <the question, or "native reviewer unavailable">

### Notes for other reviews
- <skill> `<file>:<line>`: <note>

### Summary
Findings: <N> (HIGH <n>, MEDIUM <n>, LOW <n>). Failed tools: <names, or "none">.
```

- Orchestrated mode: leave out "Simplification" and "Applied". Cleanup findings go under "Notes for other reviews" as notes for `code-simplify`.
- A tool that found nothing is a valid result. Say so, with what it checked.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The native reviewer is missing, so I will run `complete-code-review` instead." | That is a different review at a different cost. Report the gap and offer it. |
| "`simplify` makes small changes, so it is fine in report mode." | Report mode edits nothing. Say how to run it. |
| "I will add `--fix` in orchestrated mode, it saves a step." | `complete-code-review` validates, merges, and applies the fixes itself. A reviewer that edits breaks its tree check. |
| "I will add my own findings to the native ones." | This skill reports what the harness found. Your own review belongs in another skill. |

## Red flags

- A file changed in report mode or in orchestrated mode.
- `--fix`, `--comment`, or `ultra` passed in orchestrated mode.
- A command that the harness does not have was invented, or run in the shell.
- A missing or failed native tool was replaced without telling the user.
- `simplify` or `code-simplify` ran before the review fixes were in.
- A change was undone with `git restore`, `git checkout`, `git reset`, or `git stash pop`.
- Anything was committed.

## Verification

- [ ] The harness and the mode are stated.
- [ ] The scope came from the prompt (orchestrated) or from the default rule, and dropped files are stated.
- [ ] Claude Code: `code-review` ran, with `--fix` only in standalone fix mode.
- [ ] Cursor: `bugbot` and `security-review` started in one message, with the scope in the custom instructions.
- [ ] Simplify ran only as the Step 3 table says.
- [ ] The report uses the format above, with HIGH, MEDIUM, and LOW.
- [ ] Failed or missing tools are listed.
- [ ] Nothing was committed.
