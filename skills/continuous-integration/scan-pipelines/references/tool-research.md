# Tool research

How to choose a tool for a check the project does not have yet. `scan-pipelines` does the research and shows the status. `build-pipelines` asks the user which tool to use. The recommendation always comes from the status found in this run, never from memory.

## When to research

Research every suggestion where the project has **no tool** for the category: no dependency, no config, no image, no CI step. This includes baseline items and the libraries a baseline item needs (a coverage library, a parallel test runner).

Do not research when the project already has a tool for the category (a dependency or config with no command that runs it is Drift: suggest running that tool). The project's choice wins.

## Candidates

Pick 2 to 4 candidates per check:

1. The tools the catalog lists for the category and the project's ecosystem.
2. A search for others, so the list is not only what the catalog knew. Run two queries per check:

```
# tools for the project's language (the language the tool is written in)
gh api -X GET search/repositories \
  -f q='topic:<topic> language:<language> archived:false stars:>200' \
  -f sort=stars -f per_page=10 \
  --jq '.items[] | [.full_name, .stargazers_count, .pushed_at] | @tsv'

# cross-language tools (written in another language: lizard, Semgrep, Gitleaks)
gh api -X GET search/repositories \
  -f q='topic:<topic> archived:false stars:>500' \
  -f sort=stars -f per_page=10 \
  --jq '.items[] | [.full_name, .stargazers_count, .pushed_at] | @tsv'
```

Search by `topic:`, not by phrase. Phrases match only names and descriptions, and miss most tools. Topics by category: `linter`, `static-analysis`, `code-complexity`, `sast`, `security`, `secrets`, `vulnerability-scanner`, `code-coverage`, `parallel-testing`, `testing`. Add a second topic for the framework when there is one (`rails`, `rspec`, `pytest`). Read each result's description: a topic search also returns libraries that are not check tools.

Keep a candidate only if it fits the stack: it supports the project's language, framework, and runtime version, and it can run in Docker (an official image, or an install with the ecosystem's package manager).

## Status of each candidate

Collect, for each candidate, from the GitHub API (`gh api` GET, read-only):

| Field | Command |
|---|---|
| Stars | `gh api repos/<owner>/<repo> --jq .stargazers_count` |
| Archived | `gh api repos/<owner>/<repo> --jq .archived` |
| Last commit on the default branch | `gh api 'repos/<owner>/<repo>/commits?per_page=1' --jq '.[0].commit.committer.date'` |
| Latest stable release and date | `gh api repos/<owner>/<repo>/releases/latest --jq '[.tag_name, .published_at] \| @tsv'` (no releases: use the latest tag, and the registry's latest version from tool-images.md) |
| Commits in the last year | `gh api 'repos/<owner>/<repo>/stats/participation' --jq '.all \| add'` (commits in the last 52 weeks; the API can answer 202 with an empty body the first time, ask again once, then write "n/a") |
| License | `gh api repos/<owner>/<repo> --jq .license.spdx_id` |

If `gh` is missing or not authenticated, read the same endpoints with `curl -fsSL https://api.github.com/<endpoint>` (GET, unauthenticated, 60 requests per hour; search: `curl -fsSL -G https://api.github.com/search/repositories --data-urlencode 'q=<query>' -d sort=stars`). If neither works, say so, show the candidates without status, and still recommend one from the catalog, marked "status not verified".

**Rate limits.** About 6 calls per candidate plus 2 searches per check. Authenticated `gh`: 5,000 calls per hour, 30 searches per minute. Unauthenticated `curl`: 60 calls per hour, 10 searches per minute, which covers about two checks. When a call returns 403 or 429 with a rate-limit message, stop calling, mark the remaining candidates "status not verified", and say when the limit resets (`X-RateLimit-Reset`). Never wait in a loop.

Today's date is the reference for every age. Write ages as days or months, not only dates.

## Fan-out to subagents

With 3 or more checks to research, and an authenticated `gh` (the unauthenticated limit covers only about two checks, so do them yourself), research each check in its own subagent when the tool has them (Claude Code: the `Agent` tool with a general-purpose agent; Cursor: the Task tool). Start them all in one message.

Give each subagent: the check and its category, the stack facts it needs (language, framework, runtime version), this file's sections "Candidates", "Status of each candidate", "Activity status", and "Recommendation", and these rules: read-only, only the commands this file lists, no installs, no file writes. It returns the status table, and for each candidate the raw value and the exact command behind each field.

Check each table before you use it:

1. Run one status call yourself for the recommended candidate (`releases/latest`, or the last commit) and compare the value with the table.
2. Check that the recommendation follows the ranking rules with the numbers in the table, and that no `stale` or `archived` tool is recommended.
3. If a value differs or a rule is broken, research that check yourself. Do not patch the subagent's table.

Subagents share the rate limit. If one reports a 403 or 429, follow the rate-limit rule above for every check still open.

## Activity status

| Status | Rule |
|---|---|
| `active` | Last commit 90 days ago or less, and a release in the last 12 months |
| `slowing` | Last commit in the last 12 months, but older than 90 days, or no release in the last 12 months |
| `stale` | No commit in the last 12 months |
| `archived` | Archived on GitHub |

`stale` and `archived` tools are never recommended. Show them only if the catalog lists them, so the user sees why they were dropped.

**Stars:** under 500 is "low adoption". Show it. Recommend a low-adoption tool only when it is the only one that fits the stack, and say so.

## Recommendation

Always recommend exactly one candidate. Rank them in this order, and stop at the first rule that separates them:

1. Fits the stack (language, framework, runtime version, runs in Docker).
2. Activity status: `active` before `slowing`.
3. Already used elsewhere in the project's ecosystem standard (the catalog's ecosystem default).
4. Stars.
5. Commits in the last year.

The reason names the rule that decided, with the numbers: "RuboCop: active (last commit 3 days ago, release 2 weeks ago), 12.7k stars, ecosystem standard."

## Status table

Show this table for each researched check, recommended candidate first:

```
#### <check>: <category> (<baseline item N | suggestion>)
| | tool | stars | last commit | latest release | commits (1y) | status | license | fits stack |
|---|---|---|---|---|---|---|---|---|
| ★ | <tool> | 12.7k | 3 days | v1.68.0, 2 weeks | 1,140 | active | MIT | yes |
| | <tool> | 3.1k | 5 months | v2.4.1, 14 months | 85 | slowing | Apache-2.0 | yes |
| | <tool> | 900 | 2 years | v0.9.0, 2 years | 0 | stale | MIT | yes, dropped |
Recommended: <tool>. <reason, with the rule that decided>.
```

## Asking the user (build-pipelines)

`build-pipelines` asks, in Step 2, which tool to use for each researched check:

- **Claude Code:** `AskUserQuestion`, one question per check, up to 4 questions per call (more calls if needed). Options: each candidate that is not `stale` or `archived`, recommended first with "(Recommended)" at the end of the label. The description holds its status line: stars, last commit, release, status.
- **Cursor:** ask in chat with the same table, and wait for the answer.
- One candidate only: the options are "Use <tool> (Recommended)" and "Skip this check".
- The user can name a tool that is not on the list. Research its status the same way, and show it before you use it. If it is `stale` or `archived`, say so and ask again.
