---
name: review-orchestrator
description: Run the right code-review skills on a change, each in its own Opus agent at high effort, then merge the reports and apply the fixes. Picks the skills from what changed (security-analysis, dependency-analysis, data-and-migration-analysis, reliability-analysis, test-analysis, performance-analysis, static-analysis), runs them in safe waves, validates and de-duplicates the findings, and applies the verified ones in a safe order with a checkpoint for each batch. Default scope is the current branch against main plus the uncommitted work. Named files narrow it. "Whole project" widens it. Use when the user asks for a full code review, "review my changes", "review this branch", "run all the reviews", or "review the whole project". Say "review only" to stop before any change is made.
---

# Review Orchestrator

> Design draws on the [Claude Code code-review plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-review) (parallel agents, a confidence filter, a check of each finding against the real code), the common multi-agent review pattern (specialist reviewers, a merge that de-duplicates and records which reviewers agree, and a validation pass that drops findings about code that is not there), and the [Claude Code subagent settings](https://code.claude.com/docs/en/sub-agents) (`model` and `effort` in the agent definition, parallel agents, nested depth).

This skill does not review code itself. It decides which review skills a change needs, runs each one in its own agent, checks and merges the results, and applies the fixes.

## Why this process

1. **One reviewer cannot hold every lens.** Security, dependencies, data, reliability, tests, and performance each need their own context. A separate agent per skill keeps each context small and focused.
2. **Reviewers disagree and repeat each other.** Two skills can report the same line, or suggest fixes that conflict. Merge before you change anything.
3. **Review output can be wrong.** A finding can name a line that is not there, or code that changed. Check each finding against the real file before you act on it.
4. **Agents that run code collide.** Test runs share a database. A benchmark that runs next to a test suite is noise. Run the skills that execute code one at a time.
5. **Fixes collide too.** Apply them in a fixed order, one batch at a time, with a checkpoint, so a bad batch can be undone without touching the user's own work.
6. **Fail open.** A finding nobody can verify goes to "Needs human check". It is never dropped, and never applied.

## When to use

- The user asks to review the current work, a branch, a PR, some files, or the whole project, and wants every lens that applies.
- The user wants the findings applied after the review.

## When NOT to use

- The user wants one kind of review (only security, only tests). Call that skill directly.
- The user wants code simplified for readability. Use `code-simplify`.
- The user wants only the linter run. Use `static-analysis`.
- The change is only docs or comments. Say so and stop.

## Process

### Step 0: Set scope and take a snapshot

1. Use the files the user names. Only those files are the scope.
2. If none, and the user did not ask for a full review, use the current change. That is the files not committed yet (`git diff --name-only`, `git diff --staged --name-only`, and new files from `git ls-files --others --exclude-standard`) plus the branch diff against the main branch (`git diff --name-only main...HEAD`; use `master` if the repo has no `main`).
3. If the user asks to review the entire base or project, the scope is the whole codebase. Say that this runs every selected skill over the repository.
4. Drop deleted files, vendored code (`vendor/`, `node_modules/`), and generated code. Say what you dropped.
5. If the scope is empty, say so and stop.
6. Find the intent of the change, without asking if you can avoid it: the user's words, the commit messages on the branch (`git log main..HEAD --format=%B`), the PR description if the `gh` CLI is available (`gh pr view`, read-only), a plan or ticket in the repo. A PRD only if one exists. If you infer the intent, mark it lower confidence. The agents use it.
7. Detect the languages in scope (`go.mod`, `*.go`, `Gemfile`, `*.rb`) and the project's test and lint commands (`CLAUDE.md`, `Makefile`, `Rakefile`, CI config). The agents use these too.
8. Take the **tree snapshot** described in [references/merge-and-apply.md](references/merge-and-apply.md) (section "Tree snapshot"). You compare against it after every review agent.

If the user said "review only", "no changes", or "just report", note that. The process stops after Step 5.

### Step 1: Choose the skills

Read [references/routing.md](references/routing.md). It maps each file class and each content signal to the review skills that should run.

1. Classify every file in scope.
2. Check the content signals with the `grep` commands in the reference. When a signal is unclear, run the skill. A skipped lens finds nothing.
3. Check that each chosen skill is installed (it is in the skills list). If one is missing, say so and carry on without it.
4. Put each chosen skill in a group:
   - **Parallel group:** skills that run no project code. They read files, run read-only scanners, and read packages.
   - **Queue:** skills that run the project's tests, tools, benchmarks, or local database. They run one at a time.
   - **Apply phase:** `static-analysis` (and `code-simplify`, only on request). They change code, so they do not run in Step 2. They run in Step 6.
5. Show the user a short plan, then go on without waiting:

```
Scope: <default | files | full>, <N> files (<languages>)
Intent: <one line, and how you found it>
Plan:
- security-analysis (parallel): <why>
- dependency-analysis (parallel): <why>
- data-and-migration-analysis (queue 1): <why>
- ...
- static-analysis (apply phase, last): <why>
Not run: <skill>: <why>
Apply: <yes | no (review only)>
```

### Step 2: Run the reviews

Read [references/agent-prompts.md](references/agent-prompts.md) for the prompt of each agent.

1. Spawn each review in its own agent: agent type `review-runner`. In Claude Code, set `model` to `opus`; the agent definition also sets effort to high, and the agent type is listed as `andrew-skills:review-runner` when the plugin is installed. In Cursor, spawn the `review-runner` subagent through the Task tool; its model comes from the Cursor agent definition. Give each agent: its skill, the scope as an explicit file list (or "full"), the intent, the languages, and the project's commands.
2. Start the whole parallel group in **one message**, so the agents run at the same time. You may start the first queued agent in the same message.
3. Start each next queued agent when the previous queued agent returns. Run `performance-analysis` last, after every other agent has returned, so nothing else loads the machine during its measurements.
4. If the user says "run them all in parallel", do it, and say that shared test databases and benchmark noise may affect the results of the skills in the queue.
5. After **each** agent returns, compare the tree with the snapshot. If the working tree changed, stop. Tell the user which agent and which files. Do not continue and do not undo anything yourself.
6. Do not edit any file in this step.

If an agent fails or returns no report, retry it once. If it fails again, record "<skill>: failed, not reviewed" and carry on.

### Step 3: Validate each finding

Read the "Validate" section of [references/merge-and-apply.md](references/merge-and-apply.md). For every finding in every report, you check the real code:

- The file exists, and the line is inside it.
- The code the finding quotes or describes is at that line now.
- The file is in the scope, or the finding says why it is outside.

A finding that fails the check is marked "unverified". It goes under "Needs human check" with the reason. It is not dropped and not applied. Do not re-review the code yourself. You check that the finding points at real code.

### Step 4: Merge

Read the "Merge" section of [references/merge-and-apply.md](references/merge-and-apply.md).

1. **De-duplicate.** Two findings at the same place with the same root cause become one. Keep the strongest evidence and the highest severity. Record every skill that reported it. Agreement of two skills raises your confidence.
2. **Find conflicts.** Two findings whose fixes cannot both apply (a cache for speed and fresh reads for safety, a batch for speed and per-item error handling). Do not pick silently. Use the priority order in the reference. Record the conflict and the choice.
3. **Route notes.** Each report has "Notes for other reviews". If the note belongs to a skill that already ran, match it with that skill's findings. If it belongs to a skill that did not run, list it as a lead and offer to run that skill.
4. **Rank.** Sort by severity, then by evidence tier, then by the number of skills that agree.

### Step 5: Report and plan the fixes

Present the merged report (format in the reference). Then classify every finding:

- **Apply:** a verified finding with a concrete suggestion, a small blast radius, and no decision left.
- **Needs decision:** the fix changes behavior, a public API, a schema, or data, or it is a major version bump, or the skill says the change carries a trade-off.
- **Needs human check:** unverified, or the reviewer could not confirm it.
- **Lead:** a note for a skill that did not run.

If the user asked for review only, stop here.

### Step 6: Apply the fixes

Read the "Apply" section of [references/merge-and-apply.md](references/merge-and-apply.md).

1. Apply only the "Apply" group. Ask the user once, with all "Needs decision" items together, and apply those the user approves.
2. Apply in batches, one review skill per batch, one batch at a time, in this order: `dependency-analysis`, `data-and-migration-analysis`, `security-analysis`, `reliability-analysis`, `performance-analysis`, `test-analysis`, and last `static-analysis`. A dependency change moves the lockfile. Code fixes then build on it. Tests cover the final code. The linter runs on the final result.
3. Before each batch, take a checkpoint. Spawn a `review-fixer` agent (in Claude Code, `model` `opus`) with the batch. After it returns, run the project's tests for the files it changed. If the tests fail, undo that batch with its reverse patch (never with `git restore`, `git checkout`, `git stash pop`, or `git reset`), record the batch as "reverted", and carry on with the next one.
4. Never apply anything in the "Needs human check" group.
5. Never commit.

### Step 7: Verify and report

1. Run the project's full test command and its linter once on the final tree.
2. If a check fails, find which batch caused it from the checkpoints. Report it. Do not start another review loop.
3. Give the final report: what each skill found, what was applied, reverted, and skipped, what needs the user, and what the final checks showed.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "I will run every skill every time." | Each agent costs an Opus session at high effort. Run the skills that the change needs, and say why you skipped the rest. |
| "The agents are read-only, so I do not need to check the tree." | A skill can have a bug. The snapshot check is cheap and it catches a reviewer that edited code. |
| "Run all the agents at once, it is faster." | Test runs share a database. Benchmarks next to a test suite are noise. Queue the skills that run code. |
| "The finding looks right, so apply it." | Read the cited line first. Review output can name code that is not there. |
| "Two skills disagree, so I will choose the one I like." | Use the priority order, write down the conflict, and show it to the user. |
| "A fix failed the tests, so I will restore the files." | A restore can destroy the user's uncommitted work. Reverse only your own batch patch. |
| "I will fix the 'Needs human check' items to be helpful." | They are unverified. A fix on a guess is a new bug. |
| "I will run another review round to be safe." | One round, then the final checks. More rounds hide the first round's problems. |

## Red flags

- A skill ran on a scope that the orchestrator did not give it.
- A review agent changed the working tree and the run went on.
- A finding was applied without a check against the real file.
- An unverified finding was applied.
- A batch was undone with `git restore`, `git checkout`, `git reset`, or `git stash pop`.
- Two agents that run code ran at the same time, without the user asking for that.
- `performance-analysis` ran while another agent was running.
- A fixer disabled a lint rule, skipped a test, or added a scanner ignore entry.
- A fix for a major version bump, a schema change, or a data change was applied without the user's approval.
- The report hides a conflict between two skills.
- Anything was committed.

## Verification

- [ ] The scope, the files dropped, and the intent are stated.
- [ ] The plan names every skill that ran, why, and every skill that did not run, and why.
- [ ] Every review ran in its own `review-runner` agent on `opus`, with the scope given as a file list.
- [ ] The parallel group started in one message. The queue ran one agent at a time. `performance-analysis` ran last.
- [ ] The tree was compared with the snapshot after each review agent.
- [ ] Every finding was checked against the real file before it was merged or applied.
- [ ] De-duplicated findings list every skill that reported them. Conflicts are listed with the choice made.
- [ ] Only verified, no-decision findings were applied without asking. "Needs decision" items were asked once.
- [ ] Each batch had a checkpoint, and the tests ran after it.
- [ ] The batches ran in the fixed order, with `static-analysis` last.
- [ ] The final tests and linter ran on the final tree.
- [ ] Nothing was committed.
