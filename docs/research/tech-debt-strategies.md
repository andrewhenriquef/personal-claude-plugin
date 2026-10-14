# Tech debt analysis strategies for AI agents

Research behind the `tech-debt-analysis` skill. Date of research: 2026-10-13.

## Finding

Several public skills audit tech debt (listed below). They agree on the shape: orient first, sweep named dimensions, cite `file:line`, rank, and write one document. Most rank by severity and effort alone. The research on code quality points to a better first key: **how often the code changes** (interest), crossed with **how hard it is** (pain). The Pragmatic Programmer's broken windows idea adds a lens for small, visible decay. No source gave a ready skill for broken windows, so that set is built from the book and one experiment. Several sources are vendor material or preprints. Treat the thresholds as defaults to tune in use, not as measured results.

## Strategies and where they come from

| # | Strategy | Source | Where the skill uses it |
|---|---|---|---|
| 1 | A hotspot is complicated code that is also changed often. Churn and complexity alone predict little. The combination is the signal | [CodeScene hotspots](https://docs.enterprise.codescene.io/versions/2.4.2/guides/technical/hotspots.html), [Tornhill on prioritizing debt](https://www.infoq.com/news/2017/04/tornhill-prioritise-tech-debt), [Feathers: Getting Empirical about Refactoring](https://www.stickyminds.com/article/getting-empirical-about-refactoring) | Set A, Step 2, `measuring.md` |
| 2 | Lines of code is the proxy for complexity, change count the proxy for effort. Relative churn corrects for commit-style bias. The ranking is a probability, not a proof | CodeScene hotspots doc | Complexity proxy ladder, "Limits to state in the doc" |
| 3 | Files that change together without a visible dependency are a hidden coupling (change coupling) | InfoQ summary of Tornhill, CodeScene | Set B, coupling script |
| 4 | Some high-churn files are config-like (factories, settings). Do not read churn alone | Feathers | Exclusions, "Looks bad but is fine" |
| 5 | Interest decides. Debt in code that is rarely touched may be left alone. Reckless debt carries high interest | [Fowler: Technical Debt Quadrant](https://martinfowler.com/bliki/TechnicalDebtQuadrant.html) | Priority matrix, "Leave alone", optional Origin field |
| 6 | Broken windows: anything known to be wrong and left unfixed invites more. Fix it, or board it up so everyone knows, and show that someone is in charge | [Hunt and Thomas via Artima](https://www.artima.com/articles/dont-live-with-broken-windows), [Laws of Software Engineering](https://lawsofsoftwareengineering.com/laws/broken-windows-theory/) | Set C, response ladder (fix now, board up, tell) |
| 7 | Experiment, 29 developers: higher debt density led to more re-implementation, non-descriptive names, and code smells | [arXiv 2209.01549](https://arxiv.org/abs/2209.01549) | Density and spread measures, W8 and W9 |
| 8 | The broken windows analogy is contested, and the evidence is thin | [techdebtpolicy.com](https://techdebtpolicy.com/broken-windows-theory), the paper's own limits | Wording rule: "the evidence suggests", never "will cause" |
| 9 | Unhealthy code has more defects and slower, less predictable fixes (the "Code Red" study of 39 proprietary codebases, 15 times more defects reported by secondary sources) | [Code Red, TechDebt 2022](https://dl.acm.org/doi/10.1145/3524843.3528091), [CodeScene whitepaper](https://codescene.com/hubfs/web_docs/Business-impact-of-code-quality.pdf) | Why bug-fix share raises priority |
| 10 | Orient before judging. Cite `file:line` on every finding. Require a "looks bad but is fine" section. Use "open questions" instead of asserting. Do not pad empty categories. Fan out one subagent per module on big repos. Tag findings RESOLVED or NEW on repeat runs | [ksimback/tech-debt-skill](https://github.com/ksimback/tech-debt-skill) | Steps 1, 4, 6, "Needs human check", refresh statuses |
| 11 | Other public skills: [tech-debt-analyzer](https://claudemarketplaces.com/skills/ailabs-393/ai-labs-claude-skills/tech-debt-analyzer) (scripts, debt register), [tech-debt-tracker](https://claudeskills.info/ja/skills/borghei/Claude-Skills/tech-debt-tracker/) (trend over time), [team-tech-debt](https://openskillindex.com/skills/catlog22-claude-code-workflow-team-tech-debt-f11f36) (scan, assess, plan, fix, validate), [techdebt](https://tessl.io/registry/skills/github/NeverSight/skills_feed/techdebt/review) (session-end scan with parallel subagents) | Not read in full. Used to confirm the common shape. The trend idea shaped the refresh statuses and the spread measure |
| 12 | Fix small mess when you touch the code, in small, separate, reviewable changes, and do not add the first window | Hunt and Thomas (Artima), `code-simplify` reference `pragmatic-programmer.md` | Change mode: introduced versus inherited windows, "fix now" rules, cleanup kept apart from the feature |
| 13 | Files that usually change together are a review signal: a change to one without the other is suspect | Tornhill, change coupling (CodeScene) | Change mode: missing partners as leads |
| 14 | Skill anatomy: overview, when to use, process, rationalizations, red flags, verification | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | `SKILL.md` layout |

## Design choices that are not from a source

These come from the owner's requirements and the failure modes of agents. Test them in use.

- **Two modes.** Repo mode ranks the whole repository (debt shows in history). Change mode takes the default scope of the other `code-reviewing` skills, because every changed file has its own history and the book says to clean what you touch. `complete-code-review` runs Change mode on a change and Repo mode (report only) on a whole-project review.
- **"Fix now" is strict.** One file, about 20 lines, no behavior change, verifiable, no decision. Only deletions of commented-out code, debug leftovers, verified dead code, and stale paths qualify. Skips, suppressions, swallowed errors, duplicates, and names go to the skill that owns them. These limits are defaults from the failure modes of agents, not from a source.
- **Introduced windows rank above inherited ones.** The author can still fix a window the change adds. Severity MEDIUM against LOW. Not from a source.
- **Interest first, severity second.** The priority matrix, the tiers (top 5% and top 20% by churn, top 10% and 20% by the proxy), the 5 and 3 commit floors, and the "one modifier, one level" rule are defaults. They are not from a study.
- **Broken windows are reported as neighbourhoods, not markers.** One line per cluster, with density, age, and trend. This keeps 200 TODOs from filling the backlog.
- **Boarded-up windows rank lower.** A TODO with a ticket, an owner, and a date follows the book's advice, so it is Pain Low.
- **Cold code is never in the backlog.** It goes in "Leave alone" with its tier, so a later scan can see a change.
- **The backlog is capped at 15.** The rest are counted per set.
- **Output is one committed document, `docs/tech-debt.md`.** Stable ids and statuses make two scans diffable. It is the only file the skill writes.
- **The skill never edits.** Repo mode names a next skill for each item. Change mode lists "fix now" edits for the caller to apply. Other fixes belong to `code-simplify`, `static-analysis`, `test-analysis`, and others.
- **Read-only, and no test run.** The skill uses git history, text search, and tools the project already has.

## Tool facts used in the references

Checked on the research date:

- `git shortlog` with no revision reads standard input when it is not a terminal and waits. The skill always passes `HEAD`. Tested in this repository: without it the command hung.
- The churn and coupling `awk` scripts and the `git grep` trend loop ran on this repository (macOS `awk`). A repository with no commit older than the trend point returns an empty revision. The skill skips that point.
- `deadcode` (golang.org/x/tools/cmd/deadcode): `deadcode .`, `-test`, `-filter`, `-whylive`. It starts from `main`, is conservative with reflection, and may miss some dead code. ([Go blog](https://go.dev/blog/deadcode))
- `debride`: `debride <dir>`, `--rails`, `--whitelist`, `--exclude`. Static analysis of a dynamic language gives false positives. ([seattlerb/debride](https://github.com/seattlerb/debride))

Not verified from the docs: the exact flags of `gocyclo`, `gocognit`, `dupl`, `flog`, `flay`, and the `rubocop --only Metrics/...` form. The RuboCop and golangci-lint config key names, the `date -r` form on macOS, and indentation as a complexity proxy come from the author's knowledge. The "15 times more defects" figure comes from secondary summaries, not from the paper. Check each with `--help` on the installed version.
