# Andrew's Claude Code and Cursor Skills

Personal plugin marketplace for Claude Code and Cursor. Skills for PRD and story planning, idea interviewing, test-first development, code review, tech debt analysis, bug diagnosis, local CI pipelines, and code walkthroughs. The same skills, agents, and MCP servers install in both tools.

## Skills

33 skills in 8 groups. Pick the group by the job, then start at its entry point. Each row below is a summary. The full description, with the words that trigger the skill, is in the frontmatter of its `SKILL.md`.

| Group | Use it to | Entry point |
|---|---|---|
| [Planning](#planning) | Turn an idea into a PRD, user stories, and a technical plan | `feature-planning`, then `implementation-planning` |
| [Development](#development) | Build a change test-first | `tdd-development` |
| [Code reviewing](#code-reviewing) | Review a change or a repository, and fix what is safe | `complete-code-review` |
| [Debugging](#debugging) | Take a bug from a report to a proven cause and fix options | `diagnose-and-reproduce` |
| [Walkthroughs](#walkthroughs) | Understand code: one flow, or what a branch changes | `flow-as-is` or `flow-diff` (independent) |
| [Continuous integration](#continuous-integration) | Run the project's quality checks locally and in GitHub Actions | `run-pipelines` |
| [Productivity](#productivity) | Interview, clarify intent, polish text | None: independent tools |
| [Diagrams](#diagrams) | Mermaid diagrams from text or code | `design-doc-mermaid` |

**Typical flows**

- Feature: `interview` or `understand-the-intent`, then `feature-planning`, `implementation-planning`, `tdd-development`, `complete-code-review`.
- Bug: `diagnose-and-reproduce`, then `tdd-development`, then `complete-code-review`.
- Debt: `tech-debt-analysis` (Repo mode) to rank it, then `tdd-development` or `code-simplify` to pay it.
- Before a PR: `flow-diff` to explain the change, `complete-code-review` to review it, `run-pipelines` to run the checks.

### Planning

From an idea to something a developer can build. Product level first (the PRD and the user stories), then technical level (flows, interfaces, data changes). Output goes to `docs/<TAG>/`.

**Orchestrator:** `feature-planning` runs the sequence: discovery with the `product-designer` agent when the input is light, the PRD (`prd-development`), a review round with the `pm-reviewer`, `tech-lead-reviewer`, and `qa-reviewer` agents, then the stories (`user-story`). `implementation-planning` runs after it and spawns one `senior-dev` agent per story.

| Skill | What it does |
|---|---|
| [feature-planning](skills/planning/feature-planning/SKILL.md) | Turns a feature or task into a written PRD and Mike Cohn / Gherkin user stories, saved under `docs/`. |
| [implementation-planning](skills/planning/implementation-planning/SKILL.md) | Adds a technical plan to each story: flow and sequence diagrams (AS IS and TO BE), classes, API contracts, data changes, rollout, security. Checks the stories against each other. |

### Development

Writing the code. One skill builds a change test-first, one small behavior at a time, and checks that green came from the code and not from editing the test.

**Orchestrator:** `tdd-development` is the only skill. It calls `run-pipelines` and `static-analysis` for its gate, and `interview` for business questions.

| Skill | What it does |
|---|---|
| [tdd-development](skills/development/tdd-development/SKILL.md) | Builds a feature, a behavior change, or a bug fix with Kent Beck's Canon TDD loop: test list and seams, RED with the failure shown, GREEN with the test files frozen by hash, REFACTOR on green. Bounded by limits (10 slices, 3 tries). Has Ruby and Go references. |

### Code reviewing

Review by lens. Each review skill reads one aspect of a change (or of the whole repository) and reports findings with evidence. They are read-only. Two skills change code: `static-analysis` and `code-simplify`. The default scope is the current branch against main plus the uncommitted work.

**Orchestrator:** `complete-code-review` picks the review skills from what changed, runs each in its own `code-reviewer` agent, checks every finding against the real file, merges duplicates and conflicts, and applies the verified fixes in batches through `code-developer` agents. `tech-debt-analysis` runs in Change mode on a change, and in Repo mode (report only) on a whole-project review. Every skill below also works alone.

| Skill | What it does |
|---|---|
| [complete-code-review](skills/code-reviewing/complete-code-review/SKILL.md) | Runs the right review skills on a change, merges their reports, and applies the fixes with a checkpoint for each batch. Say "review only" to stop before any change. |
| [security-analysis](skills/code-reviewing/security-analysis/SKILL.md) | Finds exploitable vulnerabilities, with evidence and few false positives. |
| [dependency-analysis](skills/code-reviewing/dependency-analysis/SKILL.md) | Reviews dependencies for known vulnerabilities, supply-chain risk, maintenance, and license. Review, Audit, and Fix modes. |
| [data-and-migration-analysis](skills/code-reviewing/data-and-migration-analysis/SKILL.md) | Reviews migrations and data-handling code for deploy safety and data integrity. |
| [reliability-analysis](skills/code-reviewing/reliability-analysis/SKILL.md) | Reviews what happens when things go wrong: swallowed errors, missing timeouts, retries, concurrency. |
| [performance-analysis](skills/code-reviewing/performance-analysis/SKILL.md) | Finds performance problems that matter (N+1 queries, unbounded queries, memory), with measurements. |
| [test-analysis](skills/code-reviewing/test-analysis/SKILL.md) | Reviews test quality: changed behavior that no test protects, weak or assertion-free tests. |
| [tech-debt-analysis](skills/code-reviewing/tech-debt-analysis/SKILL.md) | Finds the debt that costs the team now. Repo mode ranks the whole codebase by git churn and complexity and writes `docs/tech-debt.md`. Change mode checks the files of a change for broken windows and lists small "fix now" clean-ups. |
| [harness-code-review](skills/code-reviewing/harness-code-review/SKILL.md) | Runs the tool's own code review (Claude Code `code-review`, Cursor `bugbot`) and reports its findings. |
| [static-analysis](skills/code-reviewing/static-analysis/SKILL.md) | Runs the project's linter and formatter in autocorrect mode, then fixes every remaining violation by hand. No suppressions. |
| [code-simplify](skills/code-reviewing/code-simplify/SKILL.md) | Simplifies code for clarity without changing behavior. Go and Ruby references. |

### Debugging

From a bug report to a proven cause, without fixing it. The skills form a pipeline: guess, reproduce, confirm, explain, propose. Everything is written to `docs/<slug>/diagnosis.md`, and the failing test stays in the working tree.

**Orchestrator:** `diagnose-and-reproduce` runs the five sub-skills in order, keeps the evidence redacted, and stops honestly when the bug cannot be reproduced. It ends by asking which fix to take. The fix itself is for `tdd-development`.

| Skill | What it does |
|---|---|
| [diagnose-and-reproduce](skills/debugging/diagnose-and-reproduce/SKILL.md) | Takes a bug from a report to a confirmed root cause and fix options. Can read Datadog evidence, read-only. |
| [form-hypotheses](skills/debugging/form-hypotheses/SKILL.md) | Turns the symptom into 3 to 5 ranked, falsifiable hypotheses before any experiment. |
| [reproduce-bug](skills/debugging/reproduce-bug/SKILL.md) | Makes the bug fail on demand with one fast command that asserts the exact symptom, then shrinks it. |
| [confirm-root-cause](skills/debugging/confirm-root-cause/SKILL.md) | Proves why the bug happens with one-variable experiments. |
| [explain-bug](skills/debugging/explain-bug/SKILL.md) | Explains the bug in English (ASD-STE100) and Brazilian Portuguese (Linguagem Simples), with diagrams. |
| [propose-solutions](skills/debugging/propose-solutions/SKILL.md) | Offers 2 to 3 fix options with trade-offs, and recommends one. |

### Walkthroughs

Understanding code without changing it. Each skill traces the real code with `file:line`, draws Mermaid sequence diagrams (one per scenario, with no `alt` blocks), and writes a document in your language. No orchestrator: use the one you need. `flow-diff` reuses the tracing rules of `flow-as-is`.

| Skill | What it does |
|---|---|
| [flow-as-is](skills/walkthroughs/flow-as-is/SKILL.md) | Explains how an existing flow works, from the entry point to the last side effect, with an overview diagram and one diagram for each scenario of each part (the main path, each branch, each error path). Writes `docs/<flow-name>-flow.md`. |
| [flow-diff](skills/walkthroughs/flow-diff/SKILL.md) | Explains what a branch or PR changes, flow by flow, with an AS IS and a TO BE diagram for each scenario. Writes `docs/<change-name>-changes.md`. |

### Continuous integration

Running the project's quality checks (lint, tests, security, coverage) the same way locally and in GitHub. The skills are a chain. Each builds on the one before and calls it when its input is missing.

**Entry point:** `run-pipelines`. It runs the checks from the manifest in `docs/pipelines.md`, and calls `document-pipelines` if the doc is missing, which calls `build-pipelines`, which calls `scan-pipelines`. `github-pipelines` also builds on `document-pipelines` and `scan-pipelines`.

| Skill | What it does |
|---|---|
| [scan-pipelines](skills/continuous-integration/scan-pipelines/SKILL.md) | Read-only inventory of the project's quality checks, the drift between CI, hooks, and scripts, and the checks that are missing. |
| [build-pipelines](skills/continuous-integration/build-pipelines/SKILL.md) | Sets up every check to run locally in Docker, one compose service per check. |
| [document-pipelines](skills/continuous-integration/document-pipelines/SKILL.md) | Writes `docs/pipelines.md`, the guide and manifest of the checks. |
| [run-pipelines](skills/continuous-integration/run-pipelines/SKILL.md) | Runs the checks, on the changed files by default, and reports each failure with the skill that fixes it. |
| [github-pipelines](skills/continuous-integration/github-pipelines/SKILL.md) | Adds the checks that run locally but not in CI to a new, hardened GitHub Actions workflow. |

### Productivity

Small tools for thinking and writing. They are independent. `interview` is the building block: `feature-planning`, `implementation-planning`, `product-interrogatory`, and `tdd-development` call it.

| Skill | What it does |
|---|---|
| [interview](skills/productivity/interview/SKILL.md) | Interviews you about a plan or decision until the gaps are closed. |
| [understand-the-intent](skills/productivity/understand-the-intent/SKILL.md) | Interviews you until shared understanding, then writes `docs/<slug>/intent.md`. |
| [product-interrogatory](skills/productivity/product-interrogatory/SKILL.md) | Runs a four-lens discovery interrogation: product manager, designer, QA, technical. |
| [grammar-review](skills/productivity/grammar-review/SKILL.md) | Corrects grammar, spelling, and clarity in any language. |
| [teach-me](skills/productivity/teach-me/SKILL.md) | Turns a topic and its sources (videos, official docs, articles) into one teaching HTML page with animated SVG diagrams, a spectrum-ui dark theme, and a closing quiz, written in plain language (ASD-STE100, Linguagem Simples, and others), in the language of the request. |

### Diagrams

| Skill | What it does |
|---|---|
| [design-doc-mermaid](skills/design-doc-mermaid/SKILL.md) | Creates Mermaid diagrams (flowchart, sequence, class, ER, state, C4) from text or code, with a validation script. Vendored from [SpillwaveSolutions/design-doc-mermaid](https://github.com/SpillwaveSolutions/design-doc-mermaid). Used by `implementation-planning` and the walkthrough skills. |

## Agents

| Agent | Description |
|---|---|
| [pm-reviewer](agents/pm-reviewer.md) | Review a PRD from a product-management lens: problem framing, personas, success metrics, scope. Read-only, findings only. |
| [tech-lead-reviewer](agents/tech-lead-reviewer.md) | Review a PRD from a tech-lead lens: feasibility risk, missing non-functional requirements, integration risk. Read-only, findings only. |
| [qa-reviewer](agents/qa-reviewer.md) | Review a PRD from a left-shift QA lens: testability, missing edge/negative paths, non-functional test coverage. Read-only, findings only. |
| [senior-dev](agents/senior-dev.md) | Spawned by `implementation-planning` (one per story, in parallel, when a tag has multiple stories): explores the codebase, generates diagrams, writes technical details back into one `user_story_<N>.md`. Read/write. |
| [code-reviewer](agents/code-reviewer.md) | Spawned by `complete-code-review`, one per review skill. Runs exactly one code-reviewing skill on the scope it is given and returns that skill's report. Opus, medium effort. Read-only. |
| [code-developer](agents/code-developer.md) | Spawned by `complete-code-review` in its apply phase, one batch at a time. Applies verified findings from one review skill with the smallest change, then runs the focused tests. Never weakens a lint rule or a test. Sonnet, medium effort. |
| [product-designer](agents/product-designer.md) | Runs discovery by interviewing the user about problem framing, flows, and persona, focused on client/API-consumer experience, not frontend UI. Hands off persona/flow/problem-statement artifacts. Read/write. |

## MCP servers

| Server | Description |
|---|---|
| [context7](https://context7.com) | Up-to-date, version-specific documentation and code examples pulled directly from source repos. Hosted remote server, works anonymously; set `CONTEXT7_API_KEY` for higher rate limits. |

## External dependencies

`feature-planning` depends on skills from [deanpeters/Product-Manager-Skills](https://github.com/deanpeters/Product-Manager-Skills) (marketplace: `pm-skills`). `allowCrossMarketplaceDependenciesOn` in `.claude-plugin/marketplace.json` only grants permission to reference that marketplace — it does not install it or its plugins. Each skill in `pm-skills` ships as its own plugin, so the marketplace and each plugin used here must be installed separately:

| Skill | Description |
|---|---|
| [prd-development](https://github.com/deanpeters/Product-Manager-Skills/tree/main/skills/prd-development) | Build a structured PRD connecting problem, users, solution, and success criteria. Drives Step 1 of `feature-planning`. |
| [user-story](https://github.com/deanpeters/Product-Manager-Skills/tree/main/skills/user-story) | Create user stories with Mike Cohn format and Gherkin acceptance criteria. Drives Step 5 of `feature-planning`. |

Install in Claude Code:

```
/plugin marketplace add deanpeters/Product-Manager-Skills
/plugin install prd-development@pm-skills
/plugin install user-story@pm-skills
```

Install in Cursor: Cursor has no cross-plugin dependencies, and `pm-skills` ships no Cursor plugin manifest. From a checkout of this plugin, run:

```
bash scripts/install_cursor_pm_skills.sh
```

The script clones `deanpeters/Product-Manager-Skills` and copies only `prd-development` and `user-story` into `~/.cursor/skills/`. It does not add those skills to this repository.

## Install

### Claude Code

Add marketplace:

```
/plugin marketplace add andrewhenriquef/personal-claude-plugin
```

Install plugin:

```
/plugin install andrew-skills@andrew-plugins
```

### Cursor

1. Open **Customize** in the sidebar, then **From GitHub Repository**.
2. Enter `andrewhenriquef/personal-claude-plugin`.
3. Install the `andrew-skills` plugin.
4. Optional: set `CONTEXT7_API_KEY` in **Plugins → Configure** for higher context7 rate limits. context7 works without it.
5. For `feature-planning`, run `bash scripts/install_cursor_pm_skills.sh` from a checkout of this plugin. That copies `prd-development` and `user-story` into `~/.cursor/skills/`.

#### Update

There is no update command in this repository. What happens depends on how the plugin was installed. Cursor documents this under [Keep plugins up to date](https://cursor.com/docs/plugins).

- A plugin from the official Cursor Marketplace is re-fetched when you open Cursor or focus the window again.
- This plugin, installed from GitHub with the steps above, stays pinned to the commit from the install. **Update** and **Reinstall** put that same snapshot back. That pinning is a known Cursor bug: [Plugin Update & Version Management](https://forum.cursor.com/t/plugin-update-version-management-how-are-installed-plugins-updated/166454).
- Updates that follow the git branch come from a team marketplace imported from this repository. In the dashboard, use **Refresh**, or turn on **Auto Refresh** (the Cursor GitHub App must be installed on the repo; Cursor re-indexes at most once every 10 minutes). Then reopen Cursor or focus the window.

`python3 scripts/sync_cursor.py` is for someone editing this repo. It regenerates `.cursor-plugin/` from the Claude files. It does not update a plugin already installed in Cursor. See [Maintaining](#maintaining).

Generated Cursor agents rewrite Claude Code `Skill` calls into reading that skill's `SKILL.md`. Shared skills name `AskQuestion` and the Task tool where Claude Code uses `AskUserQuestion` and `Agent`. Agents use `model: inherit`. In Cursor, `feature-planning` Step 0 stays in the main thread, because a subagent cannot hold the discovery interview. In Cursor, `complete-code-review` runs `harness-code-review` in the main thread, because a subagent cannot start `bugbot` or `security-review`.

## Maintaining

The Claude Code files are the source of truth: `.claude-plugin/`, `.mcp.json`, and `agents/`. The Cursor files in `.cursor-plugin/` are generated from them. Never edit `.cursor-plugin/` by hand. After you change a Claude file, run:

```
python3 scripts/sync_cursor.py
```

`python3 scripts/sync_cursor.py --check` exits non-zero when the Cursor files are stale, when a skill `description` is longer than 1024 characters, or when a line names `AskUserQuestion` without `AskQuestion` on the same line. The script maps the Claude `model` alias to a Cursor model (`MODEL_MAP`), marks an agent `readonly` when its `tools` list has no `Write`, `Edit`, or `Bash`, rewrites `Skill` tool calls in the generated agents, keeps marketplace entries to the fields the Cursor schema allows, and rewrites `${VAR:-default}` in `.mcp.json` to a Cursor plugin variable.

### Adding a skill

1. Create `skills/<group>/<name>/SKILL.md` (the folder name equals `name` in the frontmatter) and its `references/`.
2. Register it in `.claude-plugin/plugin.json`: add the path to `skills`, add keywords, and bump `version`.
3. Add a row to the Skills table in this README.
4. If the skill came from research, add `docs/research/<topic>-strategies.md`.
5. Run `python3 scripts/sync_cursor.py`, then `python3 scripts/sync_cursor.py --check`.
6. If the skill hands work to or from another skill, update the "When NOT to use" and next-step lines of that skill too.

## License

MIT
