# Tech debt doc template

Use in Step 6 of `tech-debt-analysis`. Create `docs/tech-debt.md` and fill every section. Write the headings in the user's language. Remove the instructions in `<>`. Keep item ids (`TD-01`) stable across refreshes: never reuse an id.

````markdown
# Tech debt: <repository or directory>

- **Commit:** `<short sha>` <"clean tree" or "with uncommitted changes">
- **Date:** <YYYY-MM-DD>
- **Scope:** <paths>. Skipped: <vendored, generated>.
- **Window:** <e.g. 12 months, from YYYY-MM-DD>. Commits in the window: <N>.
- **Complexity proxy:** <tool and threshold, or lines of code, or indentation>.
- **History notes:** <shallow clone, mass commits, squash merges, bots, short history; or "none">.

## Summary

<4 to 6 sentences: where the cost is, the top 3 items by id, how many quick wins, and the trend if this is a refresh.>

## Top 5

| # | Id | What | Where | Why it costs | Priority | Effort |
|---|---|---|---|---|---|---|

## Quick wins

<P1 or P2 items with effort S, as a checklist: `- [ ] TD-04 <what>`.>

## Backlog (max 15)

| Id | Set | What | Where | Evidence | Interest / pain | Priority | Effort | Origin | Next skill | Status |
|---|---|---|---|---|---|---|---|---|---|---|

- **Set:** A hotspot, B coupling, C broken window, D structure, E safety net.
- **Evidence:** the numbers (commits, share of fixes, co-changes, age, density, trend) with `file:line`.
- **Status:** NEW, PERSISTING, WORSE, RESOLVED. On the first scan, all are NEW.

Items not shown: <count per set>.

## Hotspots (set A)

| File | Commits | Lines or proxy | Fix share | Owner share | Coupling partners |
|---|---|---|---|---|---|

<Top 15. One line under the table for each hotspot in the backlog: what makes it hard to change, from reading the code, with `file:line`.>

## Change coupling (set B)

| File A | File B | Co-changes | Share | Shared knowledge |
|---|---|---|---|---|

<Only pairs that cross a boundary. Name the shared knowledge from reading both files.>

## Broken windows (set C)

| Directory | Windows | Per 1,000 lines | Oldest | Median age | Trend (now / 6 mo / 12 mo) | Response |
|---|---|---|---|---|---|---|

- **Neighbourhoods:** <directories at 2x the median density or more, with 3 sample `file:line` each.>
- **Spreading:** <patterns whose count grew at both past points.>
- **Paying down:** <patterns whose count fell.>
- **Markers by kind:** <W1 to W10 counts. List only kinds with a count above 0.>

<One sentence: "The evidence for the broken windows theory is small. This section ranks where decay is concentrated. It does not prove that it causes more decay.">

## Structure and safety net (sets D and E)

<Short list per signal that made the backlog or fell just below it. Each with `file:line` and the cost.>

## Leave alone (cold code)

| File or directory | Pain | Last change | Note |
|---|---|---|---|

## Looks bad but is fine

<Each entry: what, why it is fine, the evidence. Never empty.>

## Needs human check

<Each unverified candidate with the exact question and where you looked. "Nothing" if empty.>

## Changes since the last scan (refresh only)

<Last scan: commit and date. NEW: ids. RESOLVED: ids with how you know (the marker is gone, the file is gone). WORSE: ids with the old and new numbers.>

## Not covered

<Areas out of scope, tools that were not installed, what the proxies cannot see.>

## Appendix: commands

<Each command used for a number in this doc, with the date it ran. Copy it exactly.>
````

## Change mode report (chat, no file)

Use in Change mode. Keep it to 10 items. Write in the user's language.

````markdown
## Tech debt in the change: <scope>

Scope: <default | files>, <N> files. Window: <12 months>. Proxy: <name>. History notes: <or "none">.

### Introduced by this change (<N>)
- <id> [MEDIUM] `<file>:<line>`: <window, kind W1 to W10>. Added line: `<the line>`. Response: fix now | board up | tell. Fix: <one line>.

### Small windows in the touched files (<N>)
- <id> [LOW] `<file>:<line>`: <window>. Age: <date>. Interest of the file: <tier, commits>. Response: fix now | board up | tell. Fix or next skill: <one line>.

### Leads
- `<file>` usually changes with `<partner>` (<N> co-changes, <P>%). The partner is not in this change.
- `<file>` is a hotspot (<commits>, <proxy>) and the change adds no test.

### Leave alone
- `<file>`: <window>, cold or generated. Reason.

### Needs human check
- `<file>:<line>`: <the exact question>. Looked in: <files, commands>.

Summary: <N> introduced, <N> inherited, <N> fix now. Not covered: <spread and density over the repository>.
````

Each "fix now" item must meet every rule in [broken windows](broken-windows.md), "Small fixes in changed files".

