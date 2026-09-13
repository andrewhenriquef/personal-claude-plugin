# Andrew's Claude Code Skills

Personal Claude Code plugin marketplace. Skills for PRD/story planning and idea interrogation.

## Skills

| Skill | Description |
|---|---|
| [feature-planning](skills/planning/feature-planning/SKILL.md) | Orchestrate PRD development end-to-end into Mike Cohn/Gherkin user stories. Use when turning a feature or task into a written PRD plus development-ready stories, saved under `docs/`. |
| [implementation-planning](skills/planning/implementation-planning/SKILL.md) | Generate flow/sequence diagrams (AS IS/TO BE when changing existing behavior) and extract implementation details — classes/modules, interfaces, API contracts, code samples, data/schema changes, dependencies, non-functional requirements, observability, rollout, security — into one user_story_<N>.md at a time. Use after feature-planning has produced docs/<TAG>/user_story_*.md files. |
| [interrogate](skills/productivity/interrogate/SKILL.md) | Grill the user relentlessly about a plan, decision, or idea. Use when stress-testing thinking. |
| [design-doc-mermaid](skills/design-doc-mermaid/SKILL.md) | Create Mermaid diagrams (flowchart, sequence, class, ER, state, C4, architecture) from text or code. Vendored from [SpillwaveSolutions/design-doc-mermaid](https://github.com/SpillwaveSolutions/design-doc-mermaid). |

## Agents

| Agent | Description |
|---|---|
| [pm-reviewer](agents/pm-reviewer.md) | Review a PRD from a product-management lens: problem framing, personas, success metrics, scope. Read-only, findings only. |
| [tech-lead-reviewer](agents/tech-lead-reviewer.md) | Review a PRD from a tech-lead lens: feasibility risk, missing non-functional requirements, integration risk. Read-only, findings only. |
| [qa-reviewer](agents/qa-reviewer.md) | Review a PRD from a left-shift QA lens: testability, missing edge/negative paths, non-functional test coverage. Read-only, findings only. |
| [senior-dev](agents/senior-dev.md) | Spawned by `implementation-planning` (one per story, in parallel, when a tag has multiple stories): explores the codebase, generates diagrams, writes technical details back into one `user_story_<N>.md`. Read/write. |

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

Install:

```
/plugin marketplace add deanpeters/Product-Manager-Skills
/plugin install prd-development@pm-skills
/plugin install user-story@pm-skills
```

## Install

Add marketplace:

```
/plugin marketplace add andrewhenriquef/personal-claude-plugin
```

Install plugin:

```
/plugin install andrew-skills@andrew-plugins
```

## License

MIT
