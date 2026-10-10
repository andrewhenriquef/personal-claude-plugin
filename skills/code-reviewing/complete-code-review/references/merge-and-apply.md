# Snapshot, validate, merge, and apply

Use in Steps 0, 2, 3, 4, 5, 6, and 7 of `complete-code-review`. Write temporary files to a temporary directory, not into the repository: `tmp=$(mktemp -d)`.

## Tree snapshot

Take it in Step 0. Compare with it after every review agent. A review agent must not change the working tree.

```
tree_state() {
  git status --porcelain=v1 -uall
  git diff | sha256sum
  git diff --staged | sha256sum
  git ls-files --others --exclude-standard -z | xargs -0 -r sha256sum
}
tree_state > "$tmp/tree-before.txt"
# after each review agent:
tree_state > "$tmp/tree-now.txt" && cmp -s "$tmp/tree-before.txt" "$tmp/tree-now.txt" || echo "TREE CHANGED"
```

The snapshot covers tracked changes, staged changes, and the content of untracked files. If it says the tree changed, stop. Tell the user which agent ran and show `diff "$tmp/tree-before.txt" "$tmp/tree-now.txt"`. Do not undo anything yourself. The user's own edits during the run look the same as an agent's edits, so the user decides.

Temporary worktrees that a review agent makes live outside the repository. They do not change the snapshot. After the agents finish, run `git worktree list`. Remove leftover worktrees that agents made (they are in a temporary directory). Leave any other worktree alone.

## Validate

Do this in Step 3, for every finding in every report. Check the real code. Do not re-review it.

| Check | How | If it fails |
|---|---|---|
| File exists | `test -f <file>` | Unverified: "file not found" |
| Line is inside the file | `wc -l < <file>` against the cited line | Unverified: "line outside the file" |
| Code is there | Read 10 lines around the cited line. Does the code the finding quotes or describes appear? | Unverified: "code does not match" |
| In scope | Is the file in the scope list, or does the finding say why it is outside? | Move to "Leads" with the reason |
| Has evidence | Does the finding carry evidence in the skill's own terms (a source and sink, a measurement, a mutant, a failure scenario, an advisory)? | Unverified: "no evidence" |
| Has a fix | Does the finding carry a concrete suggestion? | It can be reported, but it is not in the "Apply" group |

A finding that fails a check is "unverified". It goes to "Needs human check" with the reason. It is not dropped. It is never applied.

A report line that says "Needs human check" stays there. Do not promote it.

## Merge

### De-duplicate

Two findings are the same when they point at the same file within 3 lines and have the same root cause (the same missing control, the same unbounded query, the same swallowed error). Judge the root cause by reading, not by matching words.

- Keep one finding. Keep the strongest evidence and the highest severity.
- Record every skill that reported it: `reported by: security-analysis, reliability-analysis`.
- Agreement from two skills with different lenses raises confidence. Write it down.
- Findings at the same place with different root causes stay separate.

### Find conflicts

A conflict is two findings at the same place whose fixes cannot both apply, or whose goals pull apart. Examples: a cache for speed against fresh reads for correctness, a bulk write for speed against per-row validation, a retry for resilience against a non-idempotent call, removing a log for speed against the observability finding that asks for it.

Resolve with this priority, highest first:

1. `security-analysis`
2. `data-and-migration-analysis`
3. `reliability-analysis`
4. `harness-code-review`
5. `test-analysis`
6. `performance-analysis`
7. `static-analysis` and `code-simplify`

Rules:

- A lower finding never overrides a higher one on the same code. Keep the higher finding. Look for a fix that satisfies both (for example a bulk write that still runs the validation), and offer it as the suggestion.
- Do not choose silently. List every conflict in the report with the two findings and the choice made.
- If no fix satisfies both, move both to "Needs decision" and ask the user.

### Route the notes

Each review report has a "Notes for other reviews" section.

- The note belongs to a skill that ran: find that skill's finding at the same place. If one exists, it is a duplicate. If none exists, add it as a lead for the user, because a note is not a verified finding.
- The note belongs to a skill that did not run: list it under "Leads", and offer to run that skill on the file.

### Rank

Sort by severity (HIGH, MEDIUM, LOW), then by evidence strength (measured or reproduced, then traced or structural), then by the number of skills that agree.

## Merged report format

```
## Review: <scope>

Scope: <default | files | full>, <N> files. Dropped: <vendored, generated, deleted>.
Intent: <one line, and the source>
Skills run: <name (agent result)>, ... Not run: <name: why>
Tree check: unchanged after every review agent.

### Findings (<N>)

<id> [<severity>] <skill, or skills that agree> `<file>:<line>`: <the finding in one line>
- Evidence: <short>
- Fix: <short>
- Plan: apply | needs decision | needs human check

### Conflicts
- <finding ids>: <what pulls apart>. Choice: <which and why>.

### Needs human check
- <id or source> `<file>:<line>`: <the exact question, or "unverified: <reason>">

### Leads
- <note> `<file>:<line>`: <skill that would cover it, and whether it ran>

### Summary
Findings: <N> (HIGH <n>, MEDIUM <n>, LOW <n>). Merged duplicates: <n>. Unverified: <n>.
```

## Classify for the apply phase

| Class | Test | What happens |
|---|---|---|
| Apply | Verified, concrete fix, small blast radius, no decision left | Applied without asking |
| Needs decision | The fix changes behavior, a public API, a schema, stored data, or a permission rule. Or it is a major version bump. Or the skill's "Risk of the change" names a trade-off. Or two findings conflict with no fix for both | Ask the user once, with all such items together |
| Needs human check | Unverified, or the reviewer could not confirm | Never applied |
| Lead | A note for a skill that did not run | Offer the skill |

A fix that adds or edits a migration for a table that already shipped is always "needs decision". A fix that edits data (a backfill) is always "needs decision". A security fix that changes who can do what is always "needs decision".

In a full review, apply only HIGH and MEDIUM findings unless the user asks for more.

## Apply

### Order

One batch per review skill, one batch at a time:

1. `dependency-analysis` (moves the lockfile first, so the code fixes build on it)
2. `data-and-migration-analysis`
3. `security-analysis`
4. `reliability-analysis`
5. `harness-code-review`
6. `performance-analysis`
7. `test-analysis` (tests cover the final code)
8. `static-analysis` (runs on the final result)

Skip a batch that has nothing to apply. If a later batch's finding sits on code that an earlier batch changed, the code-developer checks that the finding is still true. It skips the finding if not.

### Checkpoint and undo

Take a checkpoint before each batch. Do not use `git restore`, `git checkout`, `git reset`, `git clean`, or `git stash pop`. They can destroy the user's uncommitted work. Reverse only the batch's own changes.

```
# before the batch
snap=$(git stash create); snap=${snap:-HEAD}       # holds tracked changes without touching the tree
git ls-files --others --exclude-standard | sort > "$tmp/untracked-before.txt"

# ... spawn the code-developer agent for the batch, then run the focused tests ...

# after the batch
git diff "$snap" > "$tmp/batch-N.patch"            # only what this batch changed in tracked files
git ls-files --others --exclude-standard | sort > "$tmp/untracked-after.txt"
comm -13 "$tmp/untracked-before.txt" "$tmp/untracked-after.txt" > "$tmp/newfiles-N.txt"
```

Undo a batch (only right after it, before the next batch starts):

```
git apply -R "$tmp/batch-N.patch"
xargs -d '\n' rm -f -- < "$tmp/newfiles-N.txt"
```

`git stash create` prints nothing when the tracked tree has no changes. The fallback `HEAD` is then the right base. The checkpoint does not include untracked files. That is why the recipe records the list of new files and removes only those.

If `git apply -R` fails, stop. Tell the user which batch and which file. Do not force it.

### Run

1. Spawn one `code-developer` agent per batch (`model` `opus`), with the prompt from `agent-prompts.md`. The `static-analysis` batch and the `dependency-analysis` batch use their own prompts.
2. When the agent returns, run the project's tests for the files it changed.
3. Tests pass: keep the batch. Tests fail: undo the batch, record it as "reverted" with the failing output, and go on.
4. Findings that the code-developer reports as "needs decision" join the question for the user. Ask once at the end of the apply phase if the user has not answered yet. Apply the approved ones as a last batch, with a checkpoint.

### Confirmation questions

Ask the user in one question, with all "needs decision" items listed together, each with the reviewer's own wording of the trade-off. Offer: apply all, apply none, or choose. Do not ask one question per finding. Do not ask for the "Apply" group.

## Final verification

1. Run the project's full test command once, and the project's linter once, on the final tree.
2. If something fails, use the checkpoints to find which batch caused it. Report that batch. Do not undo more than the failing batch, and do not start another review round.
3. Check `git status`. Say which files changed. Nothing is committed.

## Final report format

```
## Review result: <scope>

Applied (<N>):
- <id> `<file>:<line>`: <one line>

Reverted (<N>):
- <id>: <batch, and the failing test output in one line>

Skipped (<N>):
- <id>: <reason>

Needs your decision (<N>):
- <id>: <the question>

Needs human check (<N>):
- <id> `<file>:<line>`: <the question>

Leads (<N>):
- <note>: <skill that would cover it>

Final checks: tests <result>, lint <result>.
Files changed: <list>. Nothing is committed.
```
