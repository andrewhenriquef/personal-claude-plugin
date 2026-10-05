---
name: performance-analysis
description: Review code changes for performance problems that matter, with evidence. Finds N+1 queries, unbounded queries and memory use, work that grows with data size, sequential I/O that could be batched, and costly work on hot paths. Uses the project's own performance libraries and linters (rubocop-performance, Bullet, Prosopite, golangci-lint performance linters, benchmarks, profilers) as candidate generators, and requires a measurement or a stated data size for every finding. Use when the user asks for a performance review, asks "is this slow", "will this scale", or asks to check N+1, query count, memory, or benchmarks. Read-only, reports findings, does not optimize.
---

# Performance Analysis

> Evidence sources: [Go diagnostics](https://go.dev/doc/diagnostics), [benchstat](https://pkg.go.dev/golang.org/x/perf/cmd/benchstat), [Bullet](https://github.com/flyerhzm/bullet), [Prosopite](https://github.com/charkost/prosopite), [RuboCop Performance](https://docs.rubocop.org/rubocop-performance/latest/cops_performance.html), [golangci-lint linters](https://golangci-lint.run/docs/linters/), and [SWE-fficiency](https://arxiv.org/abs/2511.06090). Structure follows [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills).

Find code that is slow or wasteful where it matters, and prove it. A pattern that looks slow is not a finding. A finding says how often the code runs, how much data it handles, and what it costs.

This skill is read-only. Report findings. Do not change code unless the user asks for a fix after the report.

## Why this process

1. **Agents are weak at performance work.** In the SWE-fficiency benchmark, agents reached under a quarter of expert speedups. They failed to find the real bottleneck, to reason across functions, and to keep the code correct. So: measure first, and do not guess.
2. **Most slow-looking code is not on a hot path.** A micro-optimization in code that runs once a day is noise. Every finding needs a scale statement.
3. **Structure beats micro-tuning.** Query count that grows with the data, unbounded loads, and nested loops over collections cost far more than a faster string method.
4. **Existing tools know the patterns.** Run them as candidate generators. Then check each result against real scale and real measurements.

## When to use

- A diff touches request handlers, jobs, queries, loops over collections, parsing, or serialization.
- The user asks "is this slow", "will this scale", or asks about N+1, query count, memory, or benchmarks.
- A change adds a list endpoint, an export, an import, a batch job, or a report.

## When NOT to use

- The user wants code made faster. Review first, then optimize as a separate step, with a benchmark.
- The user wants the schema change checked for lock risk, backfills, or constraints. Use `data-and-migration-analysis`. This skill checks query shape and cost. Indexes that a schema change needs belong there.
- The user wants timeouts, retries, leaks, or race conditions checked. That is a reliability review.
- The user wants style cleanup. Use `static-analysis`. If the project already enables a performance cop, it runs there.

## Process

### Step 0: Set scope and learn what is hot

1. Use the files the user names.
2. If none, use the current change. That is the files not committed yet (`git diff --name-only`, `git diff --staged --name-only`, and new files from `git ls-files --others --exclude-standard`) plus the branch diff against the main branch (`git diff --name-only main...HEAD`; use `master` if the repo has no `main`).
3. Review the whole codebase only when the user asks for a full review.
4. Skip tests, docs, generated code, and one-off scripts. Say what you skipped.
5. Detect the language and framework (see Language references). Read the matching reference now.
6. Learn what is hot and how big the data is. Look in `CLAUDE.md`, README, docs, existing benchmarks, and load or performance tests. If you cannot find it, ask the user once for: the largest table or collection sizes, the request rate of the changed paths, and any latency target. If the user does not know, say which sizes you assumed.

A path is **hot** when it runs on a user request, in a loop over data, in a frequent job, or at startup of every process. A path is **cold** when it runs once, by hand, or on a tiny input.

### Step 1: Find and run the project's performance tools

Find the performance libraries the project already uses. Do not rely only on the tools named in this skill or in the references. Look in:

- Dependency manifests and lockfiles: `Gemfile.lock`, `go.mod`, `package.json`, `requirements.txt`, and similar.
- `CLAUDE.md`, `Makefile`, `Taskfile`, `Rakefile`, CI config.
- Tool config files at the repo root.
- Existing benchmark files and profiling hooks.

Sort what you find into groups:

| Group | Examples of what it does | What to do |
|---|---|---|
| Linters and cops for performance | Flag slow idioms and database misuse | Run as a candidate generator, read-only (see below) |
| Query and N+1 detectors | Count and group queries by call site | Use with the covering tests |
| Benchmark tools | Time code and compare runs | Use for evidence (Step 3) |
| Profilers | Show where time and memory go | Use for evidence (Step 3) |

For a library the references do not name, read its README or `--help`, find how to run it, and use it the same way.

Rules for running tools:

- Do not install anything. Treat all output as unverified candidates.
- Linters run **read-only** and **from the command line**. Run the project's performance rules even when its config does not enable them. Do not edit the config. Do not use autocorrect. The language references give the commands.
- If a linter cannot run because its plugin is not loaded in the config, say so and skip it. Suggest enabling it in the report. The user decides.
- Never run a benchmark, a load test, or a profile against a shared, staging, or production system.

If the project has no such tool, say so. Continue with Step 2.

### Step 2: Detect candidates, one hot path at a time

A **slice** is one entry point (a route, a job, a command) and everything it reaches. Do not review the whole diff as one block.

For each slice:

1. **Trace the work.** Start at the entry point. Follow the code to every query, loop, and external call. Read the callee code. Do not guess what a helper does.
2. **State the scale.** For each loop and query, write what `n` is (rows, items, requests) and how large it gets.
3. **Check the categories** in [references/performance-checks.md](references/performance-checks.md). Read only the sections that match the slice. The list is a source of questions, not a pattern list.
4. **Compare with the repo.** How does the repo load related data, paginate, and cache elsewhere? A new path that skips an established practice is a strong signal.
5. **Add the linter candidates** from Step 1 that fall on this slice.

Write each candidate as one line: `file:line, category, what grows with what, suspected cost`. Be generous. Steps 3 and 4 remove the noise. After the last slice, do one more pass: "What in this change gets slow when the data is 100 times larger?" Stop after one extra pass.

### Step 3: Gather evidence

Read [references/evidence.md](references/evidence.md) first. For each candidate, get the strongest evidence you can, in this order:

| Tier | Evidence | Example |
|---|---|---|
| 1. Measured | A benchmark, profile, query count, or query plan from a safe run | "The list endpoint runs 101 queries for 100 rows" |
| 2. Structural | A cost you can prove by reading the code, with `n` stated | "Nested loop over orders and items. O(orders x items). Orders can reach 50,000" |
| 3. Suspected | A pattern with no measurement and no stated scale | "Looks like it allocates in a loop" |

Tier 3 is never a finding. Move it to "Needs human check" if it might matter, or drop it.

Run only safe measurements: local data, no shared systems, no changes to the working tree. For a before and after comparison, use a separate `git worktree` of the base revision. The reference has the steps.

If you cannot measure (no benchmark exists, the data is too small to show the problem, a service is not available), do not guess. Use tier 2 if you can state `n`. Otherwise use "Needs human check".

### Step 4: Verify each candidate (try to refute it)

Treat each candidate as a claim to disprove. Answer all five:

| Check | Question |
|---|---|
| Hot | Is this path hot? How often does it run, with how much data? |
| Cost | Is the cost large in absolute terms, not only in percent? Does the measurement show it? |
| Control | Does something already limit it: a cache, eager loading in a caller, a batch, a limit, a database index? Search for it. |
| Trade | Does the fix keep the behavior, and is the code still clear? A small gain that makes the code hard to read is not worth it. |
| Impact | What does the user see: slow pages, timeouts, memory growth, a large cloud bill, a failed job? |

Then apply the exclusions in [references/performance-checks.md](references/performance-checks.md).

Decide per candidate:

- **Report:** the path is hot, you have tier 1 or tier 2 evidence, and the cost is meaningful.
- **Needs human check:** you cannot tell from the repo (data size, traffic, a plan that depends on production statistics). Report it with the exact question. **Fail open: never drop a candidate only because you could not measure it.**
- **Drop:** a check fails with evidence (for example the path is cold, or a caller already eager loads). Keep a one-line reason for the count.

### Step 5: Report

Sort by severity, then by how strong the evidence is.

```
## Performance review: <scope>

Scope: <files / range>. Skipped: <tests / docs / generated / scripts>.
Scale: <data sizes and request rates, each marked "known" or "assumed">.

### Findings

Perf 1: <Category>: `<file>:<line>`
- Severity: HIGH | MEDIUM | LOW
- Evidence: <Measured | Structural>: <numbers, command, or the reasoning with n stated>
- Scale: <how often it runs, how much data>
- Cost: <what the user sees: latency, memory, queries, bill>
- Suggestion: <specific change, and its expected effect>
- Risk of the change: <behavior or clarity trade-off>
- Confirm with: <the command that shows the improvement>

### Needs human check
- `<file>:<line>`: <what you could not verify and the exact question, for example "rows in orders?">

### Linter rules to consider
- <rule or tool the project could enable, and where it would have helped>. The user decides.

### Summary
Candidates: <N>. Reported: <N>. Needs check: <N>. Dropped: <N> (<top reasons>).
Tools run: <name and result, or "none available">.
Not covered: <production load, infra, caching layers, frontend, areas out of scope>.
```

If there are no findings, say so plainly, with what you checked. Do not invent findings.

**Severity**

- **HIGH:** cost grows with user data or is unbounded, on a request path or a frequent job. Examples: N+1 over a list, no limit on a query, a nested loop over large collections, loading a whole file or table into memory.
- **MEDIUM:** a clear constant-factor cost on a hot path, with measurement. Example: sequential calls that could run in one batch.
- **LOW:** minor waste. Report LOW only when the user asked for it.

## Language references

Detect the project language and framework from the files in scope and manifests (`go.mod`, `Gemfile`). Read **only** the matching reference before Step 1. If the scope spans several languages, read each one:

| Language | Detect | Reference |
|---|---|---|
| Go | `go.mod`, `*.go` | [references/go.md](references/go.md) |
| Ruby / Rails | `Gemfile`, `*.rb` | [references/ruby.md](references/ruby.md) |

Each reference holds the common performance tools with read-only commands, how to measure, and traps that are specific to the language. It is a starting point, not a complete list. Libraries the project uses that are not listed there are handled in Step 1.

**Precedence when rules conflict:**

1. The project's own conventions, tool config, and `CLAUDE.md`.
2. The defaults in the references.

If the language has no reference, apply the process above with the shared references and follow the repo's own patterns.

To add a language: create `references/<language>.md` with the same sections and add a row to this table.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "This looks slow, so I will report it." | A look is an opinion. Measure it, or state `n` and prove the cost by reading. |
| "The linter flagged it." | A linter finds idioms. It does not know if the path is hot. Check the scale. |
| "It is faster, so it is better." | Not if the code is harder to read and the gain is not measurable. |
| "It is fast on my laptop with 10 rows." | Small data hides N+1 and bad plans. State the real size. |
| "We should cache it." | A cache adds stale data and invalidation. Show the cost first. |
| "I cannot measure it, so I will skip it." | Use structural evidence, or put it under "Needs human check". |
| "I will rewrite it to be faster." | This skill reports. A rewrite needs a benchmark and a separate step. |

## Red flags

- A finding has no scale statement and no measurement.
- A finding is a pattern from a linter on a path that is cold.
- The report states a speedup that nobody measured.
- A benchmark ran against a shared or live system.
- The working tree was modified during the review.
- The report suggests a rewrite that changes behavior.
- A finding repeats a security or reliability issue with no performance cost.
- Query-plan conclusions came from a tiny local table.

## Verification

- [ ] Scope and skipped files are stated.
- [ ] Data sizes and request rates are stated, each as known or assumed.
- [ ] Review ran per slice, not on the whole diff at once.
- [ ] Every reported finding has tier 1 or tier 2 evidence and a scale statement.
- [ ] Tier 3 candidates were dropped or are under "Needs human check".
- [ ] Linters ran read-only, with no config edit and no autocorrect.
- [ ] Libraries from the manifests were checked, not only the tools named in this skill.
- [ ] No measurement ran against a shared or live system.
- [ ] No code in the working tree was modified.
- [ ] Report says what was not covered.
