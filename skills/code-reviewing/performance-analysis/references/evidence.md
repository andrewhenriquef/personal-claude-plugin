# Gathering performance evidence

Use in Step 3 of `performance-analysis`. A performance claim needs a number or a proof. This file says how to get one safely.

Sources: [Go diagnostics](https://go.dev/doc/diagnostics), [benchstat](https://pkg.go.dev/golang.org/x/perf/cmd/benchstat), and common measure-first practice: define a metric, take a baseline, find the bottleneck by profile, change one thing, and measure again.

## Safety rules

- Measure on **local** data and a **local** database. Never on a shared, staging, or production system. Never run a load test against a shared service.
- Do not change the working tree to measure. Measurements that add no files (query counts, `EXPLAIN`, existing benchmarks) can run in the working tree. Anything that adds a file, and any comparison with the base revision, runs in a separate `git worktree`.
- Write profiles, benchmark output, and temporary files to a temporary directory, not into the repo. Check `git status` after.
- Measure with the tool's normal flags. Do not change application settings to get a better number.
- Run one profile at a time. Profilers can interfere with each other.
- Do not install tools. If a tool is missing, say so, and use the next best evidence.

## Evidence tiers

| Tier | What counts | Notes |
|---|---|---|
| 1. Measured | A benchmark with a baseline, a profile, a query count, or a query plan | Strongest. State the command, the data size, and the numbers |
| 2. Structural | A cost proven by reading the code with `n` stated | Fine for N+1 and nested loops. Write the formula and the size of `n` |
| 3. Suspected | A pattern, a linter hit, or a feeling | Not a finding. Drop it, or put it under "Needs human check" |

## Query count (N+1)

The best evidence for N+1 is the number of queries for a known amount of data.

1. Find the test or entry point that covers the path.
2. Run it with the SQL log on. Count the statements that repeat with only the parameter changed.
3. Compare the count for 1 item and for several items. A count that grows with the items confirms N+1.

If the project has an N+1 detector (Bullet, Prosopite, or similar), run the covering tests with it. Treat its report as a candidate: check the call site yourself. Detectors can miss cases and can flag cases that are fine, such as an association loaded on purpose.

## Query plans

Use `EXPLAIN` for SELECT statements that the change adds or changes.

- `EXPLAIN` shows the plan without running the query. `EXPLAIN ANALYZE` runs it, so use it only for `SELECT` and only on a local database. Never use `ANALYZE` on a statement that writes data.
- **A plan on a tiny local table is misleading.** The planner picks a sequential scan on small tables even when an index exists. Do not conclude "missing index" or "index used" from a small table. Say what table size the plan assumes. If you cannot get realistic data, use "Needs human check" with the exact query to explain on a production-sized copy.
- Look for: sequential scan on a large table, a sort that cannot use an index, a nested loop over many rows, and a large difference between estimated and actual rows.

## Benchmarks

A benchmark compares code, so it needs a baseline.

1. If the project has a benchmark for the path, use it.
2. If not, and the path is small and pure (no network or database), write a short throwaway benchmark file in the temporary worktrees (see below), never in the working tree. Do not add it to the diff unless the user asks.
3. Run the benchmark on the base revision (in a worktree) and on the change. Use the same machine, the same data, and the same flags.
4. Run it several times. A single run is noise. For Go, run at least 10 times and compare with `benchstat` if it is installed. For Ruby, use the project's benchmark tool if it has one, or repeat standard-library timing and compare medians.

Reading results:

- A difference smaller than the run-to-run variation is not a result. Say "no measurable difference".
- With many benchmarks, a few will look significant by chance. Do not rerun until one does.
- Percent alone misleads. A 50% gain on 2 microseconds is nothing. Report the absolute change and how often the code runs.
- Warm up first when the language has a JIT or caches (the first run is slower).
- Do not compare numbers from different machines or different load.

## Profiles

Use a profile to find where time or memory goes, when there is a benchmark or a test that exercises the path.

- Profile the benchmark or the covering test, with realistic data.
- Read the top entries by cumulative cost. Check if the suspect code is in them. If it is not, it is not the bottleneck, and the candidate is dropped or reduced to LOW.
- Do not attach a production profile. If the project has one, ask the user for it.

## Baseline in a separate worktree

Use two worktrees when you compare the base with the change, or when a throwaway benchmark file must go next to the code. `git stash create` prints a commit that holds the tracked changes without touching the working tree. It prints nothing when there are no changes, so fall back to `HEAD`.

```
base=$(mktemp -d); new=$(mktemp -d)
git worktree add --detach "$base" main
rev=$(git stash create); rev=${rev:-HEAD}
git worktree add --detach "$new" "$rev"
# add any throwaway benchmark file to both, run the same command in both, then:
git worktree remove --force "$base"; git worktree remove --force "$new"
```

Use `master` if the repo has no `main`. Remove the worktrees when you finish, even if a step failed. Never commit, push, or change a branch from a worktree. Untracked files are not in the commit: copy the untracked files that the measurement needs (new source files, local config, data files).

## What to write in the report

For each measured finding, state:

- The command and the data size.
- The baseline number and the new number, with the unit.
- How many runs, and whether the difference is outside the noise.
- How often the code runs, so the reader can judge the total effect.

For each structural finding, state the formula and the size of `n`, and how you learned the size (known or assumed).
