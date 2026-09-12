# Andrew's Claude Code Skills

Personal Claude Code plugin marketplace. Skills for PRD/story planning and idea interrogation.

## Skills

| Skill | Description |
|---|---|
| [feature-planning](skills/planning/feature-planning/SKILL.md) | Orchestrate PRD development end-to-end into Mike Cohn/Gherkin user stories. Use when turning a feature or task into a written PRD plus development-ready stories, saved under `docs/`. |
| [implementation-planning](skills/planning/implementation-planning/SKILL.md) | Generate sequence diagrams and extract implementation details from written user stories — classes/modules, interfaces, code samples, data/schema changes — and write them into each user_story_<N>.md file. Use after feature-planning has produced docs/<TAG>/user_story_*.md files. |
| [interrogate](skills/productivity/interrogate/SKILL.md) | Grill the user relentlessly about a plan, decision, or idea. Use when stress-testing thinking. |
| [design-doc-mermaid](skills/design-doc-mermaid/SKILL.md) | Create Mermaid diagrams (flowchart, sequence, class, ER, state, C4, architecture) from text or code. Vendored from [SpillwaveSolutions/design-doc-mermaid](https://github.com/SpillwaveSolutions/design-doc-mermaid). |

## Agents

| Agent | Description |
|---|---|
| [pm-reviewer](agents/pm-reviewer.md) | Review a PRD from a product-management lens: problem framing, personas, success metrics, scope. Read-only, findings only. |
| [tech-lead-reviewer](agents/tech-lead-reviewer.md) | Review a PRD from a tech-lead lens: feasibility risk, missing non-functional requirements, integration risk. Read-only, findings only. |
| [qa-reviewer](agents/qa-reviewer.md) | Review a PRD from a left-shift QA lens: testability, missing edge/negative paths, non-functional test coverage. Read-only, findings only. |

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
