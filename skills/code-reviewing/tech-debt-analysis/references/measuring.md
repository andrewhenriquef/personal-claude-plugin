# Measuring: history, size, hotspots, ownership, coupling

Use in Steps 0 and 2 of `tech-debt-analysis`. Set the window once and reuse it:

```sh
SINCE="12 months ago"
```

All commands are read-only. Run them from the repository root. Put each one you use in the appendix of the doc.

## 0. Check that the history is usable

```sh
git rev-parse --is-shallow-repository
git log --since="$SINCE" --no-merges --oneline | wc -l
git log --max-parents=0 --format=%cs | tail -1
# commits that touched more than 100 files (mass commits)
git log --since="$SINCE" --no-merges --format='@%h' --name-only | awk '/^@/{if(n>100)print h,n; h=$0;n=0;next} NF{n++} END{if(n>100)print h,n}'
```

- **Shallow clone** (`true`): churn is partial. Report it under "Needs human check". Deepening needs the network, so ask the user to run `git fetch --unshallow`.
- **Commits in the window** under 50: the ranking is weak. Say so.
- **History start** later than the window start: use all of it, and say so.
- **Mass commits:** the scripts below skip them. List them in the doc.

Squash merges give one commit per pull request. Churn then counts pull requests, not edits. Say it when the history shows it. Bot commits (`[bot]` authors) inflate churn on manifests and lockfiles. Those files are excluded below.

## 1. Churn per file

Commits that touched each file, skipping commits with more than 100 files:

```sh
git log --since="$SINCE" --no-merges --format='@%h' --name-only | awk '
function flush(  i) { if (n > 0 && n <= 100) for (i = 1; i <= n; i++) c[f[i]]++; n = 0 }
/^@/ { flush(); next }
NF   { f[++n] = $0 }
END  { flush(); for (k in c) printf "%d\t%s\n", c[k], k }' | sort -rn
```

Drop what is not code the team maintains. Exclude by pattern, then keep only files that still exist (`[ -f "$f" ]`):

- Lockfiles, `CHANGELOG*`, generated and vendored paths, snapshots, fixtures, compiled assets (see the language reference).
- **Write-once files:** old migrations, schema dumps.
- **Config-like files that change by design** (Feathers): routes, locale files, factory registries, feature-flag lists. Keep them out of the hotspot list, and list them in "Looks bad but is fine" when they rank high.
- **Renames:** `git log` counts a renamed file as a new path. When a high-churn file was renamed in the window, say so. `git log --follow -- <file>` shows the full history of one file.

## 2. Complexity proxy

Use the first option that exists. Name it in the doc.

1. **The project's own tool and thresholds**, when it already runs one (found in Step 1): cyclomatic or cognitive complexity from the linter config or CI. See the language reference for read-only commands.
2. **An installed analysis tool** that only reads (see the language reference).
3. **Lines of code** (`wc -l < file`). CodeScene's own hotspot view uses it as a proxy. It is rough: a long table of constants scores high, and a dense 80-line function scores low.
4. **Deepest or total indentation** per file (from _Your Code as a Crime Scene_): a cheap proxy for nesting that works in any language. Use it to break ties between files with a similar size.

Never mix proxies in one ranking.

## 3. Join churn with size and set the tiers

```sh
# churn.tsv has "count<TAB>path" lines (section 1, filtered)
while IFS="$(printf '\t')" read -r n f; do
  [ -f "$f" ] && printf '%s\t%s\t%s\n' "$n" "$(wc -l < "$f" | tr -d ' ')" "$f"
done < churn.tsv | sort -rn
```

Write `churn.tsv` in the scratchpad directory, not in the repository.

**Interest tier** (how often the team pays), from the churn rank among the files changed in the window:

| Tier | Rule |
|---|---|
| High | Top 5% of changed files, and at least 5 commits |
| Medium | Top 20%, and at least 3 commits |
| Low | Changed at least once |
| Cold | Tracked source file with no commit in the window |

**Pain tier** (how much each payment hurts), from the proxy, ranked among all tracked source files: High is the top 10%, Medium the next 20%, Low the rest. Evidence from reading can move a file one tier (a short but tangled file, or a long but flat one). Say why when you do.

A **hotspot** is a file with interest High or Medium and pain High or Medium. List the top 15 by churn times proxy.

Relative churn (lines added and deleted divided by file size) is a better signal when a few people commit in very different styles. Use `git log --numstat` for it, and say you did.

## 4. Bug-fix share

A weak proxy: commits whose subject mentions a fix.

```sh
git log --since="$SINCE" --no-merges -i -E --grep='fix|bug|hotfix|regress' \
  --format= --name-only | grep -v '^$' | sort | uniq -c | sort -rn
```

Share = fix commits on the file divided by all commits on the file. Use it only with at least 4 commits. If the project does not name fixes in its commits, say the proxy does not apply. It supports an item. It never makes one.

## 5. Owners

`git shortlog` with no revision waits on standard input. Always pass `HEAD`:

```sh
git shortlog -sn --no-merges --since="$SINCE" HEAD -- <file>
```

If one author has 80% or more of the commits and the file has at least 5 commits, flag "one owner". Check the method: squash merges, pair work, and bot accounts make this misleading. State the limit when you report it.

## 6. Change coupling

Files that change in the same commit again and again, with no import between them:

```sh
git log --since="$SINCE" --no-merges --format='@%h' --name-only | awk '
function flush(  i, j, a, b, t) {
  if (n > 0 && n <= 30)
    for (i = 1; i <= n; i++) { c[f[i]]++
      for (j = i + 1; j <= n; j++) { a = f[i]; b = f[j]; if (a > b) { t = a; a = b; b = t }; p[a "\t" b]++ } }
  n = 0 }
/^@/ { flush(); next }
NF   { f[++n] = $0 }
END  { flush()
  for (k in p) { split(k, x, "\t"); m = (c[x[1]] < c[x[2]]) ? c[x[1]] : c[x[2]]
    if (p[k] >= 5) printf "%d\t%d%%\t%s\t%s\n", p[k], 100 * p[k] / m, x[1], x[2] } }' | sort -rn | head -30
```

Columns: co-changes, share of the less-changed file's commits, file A, file B. Commits with more than 30 files are skipped.

Read the pairs:

| Pair | Meaning |
|---|---|
| A file and its test | Healthy. Ignore |
| Manifest, lockfile, README, changelog, schema dump | Housekeeping. Ignore |
| Two files in the same module | Normal cohesion. Note it only if the module is a hotspot |
| Two files in **different modules** with no import | A hidden dependency. This is a candidate for set B. Read both to name the shared knowledge |
| One file coupled to 3 or more others | A coordination point. Raises the priority (Step 5, modifier) |

## 7. Change mode lookups

Use the same commands with the scope as a filter. Run section 1 and 6 once for the repository (the tiers need the whole ranking), then look up the files in scope.

```sh
scope=<path to scope.txt>   # one path per line, in the scratchpad directory
tr '\n' '\0' < "$scope" | xargs -0 git log --since="$SINCE" --no-merges --format= --name-only -- | grep -v '^$' | sort | uniq -c | sort -rn
git shortlog -sn --no-merges --since="$SINCE" HEAD -- <file>
```

Do not put the list in an unquoted shell variable: zsh does not split it, so every path becomes one argument.

**Missing partners.** From the coupling output (section 6), keep the pairs where exactly one file is in the scope. The other file is a partner that usually changes with it and is not in this change. Report it as a lead with the co-change count and share: "`A` changed in 9 of 10 commits that changed `B`; `B` is not in this change." Read both files before you say what knowledge they share.

**New files** have no history. Say "no history" and rank them by the markers only.

## Limits to state in the doc

- Churn and size are proxies for effort and complexity. They rank, they do not prove.
- The ranking looks back. A new hot area has little history.
- Commit style, squash merges, and bots bend the numbers. Say which applied.
- Correlation with defects is documented in research, but it is not a guarantee for this repository.
