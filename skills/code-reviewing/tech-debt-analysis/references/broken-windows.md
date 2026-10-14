# Broken windows (set C)

Use in Step 3 of `tech-debt-analysis`.

## The idea

_The Pragmatic Programmer_, tip 4: **Don't live with broken windows.** A broken window is anything the team knows is wrong and has left unfixed: a bug, a bad design, a wrong decision, poor code. One window left in view tells people that nobody cares, and more decay follows. The authors do not say to fix everything at once. They say: fix it, or **board it up** (mark it so everyone knows it is broken and cannot be trusted), and show that someone is in charge.

An experiment with 29 developers ([arXiv 2209.01549](https://arxiv.org/abs/2209.01549)) found that more debt in a system made developers more likely to re-implement code instead of reusing it, to pick non-descriptive variable names, and to add other code smells. The paper is a preprint with a small sample, and the same idea is contested for crime. So:

- Use the theory to **rank** windows, not to prove a cause.
- Write "the evidence suggests" in the doc, never "this will cause".

## What this set measures

A window must be **visible** (in the code or the pipeline), **known** (a marker, or a tool flags it), and **unfixed**. The set measures four things:

| Measure | Question | How |
|---|---|---|
| Inventory | Which windows exist? | The markers below |
| Age | How long has each been open? | `git blame` on the line |
| Density | Where is decay concentrated? | Windows per 1,000 lines, per directory |
| Spread | Is it growing? | The count now, 6 months ago, and 12 months ago |

## Markers

Use `git grep` (it skips untracked and ignored files and works on old revisions). Scope it to the paths in scope with `-- <paths>`. Add the language patterns from the language reference. A pattern finds candidates. Verify each by reading.

**Portability:** `\b` and `\s` do not work with `git grep -E` on macOS. Use `-w` for whole words and `[[:space:]]` for spaces. `-P` works only when git is built with PCRE.

| ID | Window | Detect | Verify |
|---|---|---|---|
| W1 | Commented-out code | Comment lines that hold code. Count blocks of 3 or more lines | Read the block. Prose and examples are not windows. Git already keeps the old code |
| W2 | Aged TODO, FIXME, HACK, XXX, TEMP, WORKAROUND | Whole-word match | Age by blame. Marked if it has a ticket, an owner, or a date |
| W3 | Skipped, disabled, or pending tests | Language patterns (`skip`, `xit`, `t.Skip`, `pending`) | Is the reason written? Is the test in a hotspot? |
| W4 | Lint and type suppressions, and baseline files | Disable comments, ignore files, a baseline such as `.rubocop_todo.yml` | Count per rule. A baseline file that grows is spreading. Size: `wc -l` |
| W5 | Swallowed errors | Language patterns (empty `rescue`, `rescue nil`, `_ = err`, empty `catch`) | Read the handler. Logging and re-raising are fine. Count only. `reliability-analysis` reviews the behavior |
| W6 | Pipeline windows | `allow_failure`, `continue-on-error: true`, commented or disabled CI jobs, scanner ignore entries with no reason or expiry (`.trivyignore`, `osv-scanner.toml`, `.bundler-audit.yml`) | Does a comment explain it? Reuse the `scan-pipelines` drift list when it exists |
| W7 | Dead code | The language tool (`debride`, `deadcode`), unreferenced files | Search for dynamic use: strings, routes, callbacks, reflection, templates. If any, "Needs human check" |
| W8 | Re-implemented helpers | The same function name or the same rule in 3 or more places; a duplication tool | DRY is about **knowledge**. The same rule in many places is a window. Code that only looks alike and changes for different reasons is not |
| W9 | Vague names | Names like `data`, `tmp`, `res`, `obj`, `foo`, `x1` | Weak signal. Use it only as supporting evidence for a directory that is already dense |
| W10 | Stale docs | Paths, commands, or env names in the README and `CLAUDE.md` that do not exist (`test -e <path>`) | Check each path or command. Report only what you checked |

Starting patterns for W1, W2, and W4 (add more for your language):

```sh
git grep -nwE 'TODO|FIXME|HACK|XXX|TEMP|WORKAROUND' -- <paths>
git grep -nE 'rubocop:disable|nolint|eslint-disable|type: ignore|@ts-ignore|:nocov:' -- <paths>
# W1 is approximate: it finds comment lines that look like code
git grep -nE '^[[:space:]]*(#|//)[[:space:]]*(def |end$|if |return |func |[a-z_.]+ = |[a-z_.]+\(.*\)[[:space:]]*$)' -- <paths>
```

## Age

```sh
git blame -L <line>,<line> --porcelain <file> | awk '/^author-time/{print $2}' | xargs -I{} date -r {} +%F
```

`date -r <epoch>` is macOS. On Linux use `date -d @<epoch>`. For many lines, run `git blame --porcelain <file>` once and read all `author-time` values. Call a window **old** after 6 months, unless the project states another limit.

Blame shows the last change of the line. A reformat resets it. Say so if the file had a mass commit.

## Density

Per directory: the number of windows divided by the thousands of lines of source in it. A **neighbourhood** is a directory with at least 5 windows and a density of at least twice the repository median. Neighbourhoods are the main output of this set: decay concentrates, and the experiment suggests it invites more.

```sh
git ls-files -- <dir> | grep -E '[.](rb|go)$' | xargs wc -l | tail -1
```

## Spread

Count one marker now and at two past points. Compare the same pattern, the same paths.

```sh
for m in 0 6 12; do
  rev=$(git rev-list -1 --before="$m months ago" HEAD)
  [ -n "$rev" ] && printf '%s months ago: %s\n' "$m" "$(git grep -hE 'rubocop:disable|nolint' "$rev" -- . | wc -l | tr -d ' ')"
done
```

If a past point has no commit (the history is shorter), skip it and say so. Count growing at both points means the window is **spreading**. Falling means someone is paying it down: note it as good news. A pattern that is spreading is the strongest evidence in this set.

## Response ladder

For each item, name the response from the book. The skill proposes, it never applies:

| Response | When | Example |
|---|---|---|
| **Fix now** | Small, local, and the file is touched often | Delete 20 lines of commented-out code. Remove a skip that passes |
| **Board up** | It cannot be fixed now. Mark it so nobody trusts it | A comment with a ticket and a date, a failing-visible assertion, a skip with a reason |
| **Tell** | The owner is not clear, or it needs a decision | Raise it to the owner of the directory |

## How windows enter the ranking

A window is a smell, so its pain tier starts at **Medium**. Interest comes from the file or directory that holds it.

- Pain **Low**: the window is boarded up (ticket, date, reason), and not spreading.
- Pain **High**: the window is unmarked and old, or it is in a neighbourhood, or it is spreading.
- A neighbourhood is one item, not one item per marker. Report the directory, the count, the density, the age, the trend, and 3 sample `file:line`.

Do not report single markers one by one. A repository with 200 TODOs gets one line in the backlog: where they cluster, how old they are, and whether the count grows.

## Change mode

Use in Change mode (see `SKILL.md`). Two jobs: do not add a window, and clean the small ones in the code you touch.

### Introduced or inherited

A window is **introduced** when it sits on a line the change adds. Read the added lines of the scope:

Write the scope to `scope.txt`, one path per line, in the scratchpad directory (not in the repository). Do not use an unquoted shell variable for the list: zsh does not split it.

```sh
scope=<path to scope.txt>
{ tr '\n' '\0' < "$scope" | xargs -0 git diff -U0 main...HEAD --
  tr '\n' '\0' < "$scope" | xargs -0 git diff -U0 HEAD --
} | grep -E '^[+][^+]'
```

Run the marker patterns over that output (`grep -nwE 'TODO|FIXME|HACK|XXX'`, and the others). For an untracked file, every line is added. Use `master` if the repository has no `main`. Everything else in the scope files is **inherited**.

Introduced windows are the strongest finding of Change mode: the author can still fix them, and the book's point is that the first window is the one that invites the rest. A new TODO with no ticket or owner, a new skip with no reason, a new suppression, new commented-out code, a new swallowed error, a leftover debug call.

### Small fixes in changed files

A window is **fix now** only when every rule holds:

1. It is in a file in the scope.
2. The fix does not change behavior, and you can say why.
3. The fix touches one file and about 20 lines or fewer.
4. You can check it: the code it removes has no reference (searched, with dynamic use ruled out), or the project's tests and linter cover the file.
5. It needs no decision from a person (no name, no ticket, no design choice).

Items that meet all five, by marker:

| Marker | Fix now | Not fix now |
|---|---|---|
| W1 commented-out code | Delete the block. Git keeps it | Prose, examples, or a block with a reason |
| Leftovers (`binding.pry`, `byebug`, `debugger`, stray `puts`, `fmt.Print`) | Delete the call | A print that is the program's output |
| W7 dead code | Delete an unused private method, import, or variable after a search and the language tool agree | Public API, anything a route, callback, reflection, or template may call. Send it to "Needs human check" |
| W10 stale docs | Fix a path or a command that the repository proves wrong (`test -e`) | A claim about behavior |

Everything else is not "fix now":

| Marker | Response | Next skill |
|---|---|---|
| W2 TODO with no ticket | **Board up**: suggest a marker with a ticket and a date, for the author to fill | none |
| W3 skipped test | **Tell**: un-skipping needs a test run and a decision | `test-analysis` |
| W4 suppression | **Tell**: removing it means fixing the violation | `static-analysis` |
| W5 swallowed error | **Tell**: handling it changes behavior | `reliability-analysis` |
| W8 re-implemented helper | **Tell**: switching to the shared helper can change behavior | `code-simplify` |
| W9 vague names | **Tell**: renames are a style choice | `code-simplify` |

### Keep it separate

Cleanup goes in its own change, apart from the feature. A mixed diff is hard to review and hard to revert. `complete-code-review` applies the fixes as one batch and never commits, so the user can commit them apart.

