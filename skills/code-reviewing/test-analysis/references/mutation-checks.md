# Small mutation checks

Use in Step 4 of `test-analysis`. A mutation check changes production code in one small way and runs the tests. If the tests still pass, no test protects that behavior. This is how the skill gets evidence.

Google runs this at scale during code review. It mutates only changed, covered lines, removes low-value mutants, and caps the number per line and per change ([Practical Mutation Testing at Scale](https://arxiv.org/abs/2102.11378)). The skill copies the same limits at small scale.

## Safety rules

- **Never mutate in the working tree.** The user may have uncommitted work. A failed cleanup would lose it.
- Work in a separate `git worktree` in a temporary directory outside the repo.
- Remove the worktree when you finish, even if a step failed.
- Never push, commit, or change a branch from the worktree.
- Do not run mutants against a shared or live database, a real service, or the network.

### Make the worktree

`git stash create` prints a commit that holds the tracked changes. It does not touch the working tree. It prints nothing when there are no changes, so fall back to `HEAD`.

```
dir=$(mktemp -d)
rev=$(git stash create); rev=${rev:-HEAD}
git worktree add --detach "$dir" "$rev"
```

Untracked files are not in that commit. Copy the untracked files from the scope into the same paths in `$dir`.

Install nothing. If the tests need dependencies that are not in the worktree, use the project's normal setup command only if it is safe and local. Otherwise report "Needs human check".

### Remove it

```
git worktree remove --force "$dir"
```

## Pick the mutants

Cap the work. Per review: at most 10 mutants. Per line: one mutant. Pick behaviors where a bug would hurt most: boundaries, error paths, permission and ownership checks, money and quantity math, and state changes.

Use only changed lines that a test reaches. A mutant on a line no test runs will survive, which only repeats what coverage says.

| Operator | Change | Catches a test that... |
|---|---|---|
| Boundary | `>=` to `>`, `<` to `<=`, `+ 1` to `+ 0` | Never checks the edge value |
| Negate condition | `if x` to `if !x`, `&&` to `||` | Does not cover both branches |
| Remove call | Delete a call to save, send, log-and-return, validate | Does not check the side effect |
| Return value | Return `nil`, `0`, `""`, `true`, or an empty list | Does not check the result |
| Skip check | Remove an authorization or ownership check | Never tests the deny case |
| Swap operand | `a - b` to `a + b`, swap two arguments of the same type | Uses symmetrical test data |
| Drop error | Return success where the code returns an error | Never checks the error path |

Do not mutate: logging, metrics, comments, error message text, constants used only for display, and defensive code that cannot run (for example an unreachable `default`).

## Read the result

| Result | Meaning | Action |
|---|---|---|
| Killed | A test failed | The behavior is protected. Count it |
| Survived | All tests passed | Check for an equivalent mutant (below). If not equivalent, report a weak test |
| Timed out | Tests hung, for example an infinite loop | Count as killed, say so |
| Did not build | The mutant does not compile | Pick another mutant. Do not count it |

**Equivalent mutant:** the change does not alter behavior, so no test can kill it. Example: `i < len` to `i != len` in a loop that always runs to `len`. Before you report a survivor, read the code and answer: can any input make the mutant behave differently from the original? If no, drop it and say "equivalent". If you are not sure, report it as "Needs human check", not as a finding.

## Report a survivor

State exactly:

- The file, line, and the change (`before` to `after`).
- The tests that you ran.
- That they all passed with the mutant.
- The test that should fail, and the case to add (name, input, expected value).

## If the project already has a mutation tool

Use it in diff mode on the scope, and do not hand-write mutants. The language references list the tools and how to scope them. Treat the output like your own mutants: check each survivor for equivalence before you report it.
