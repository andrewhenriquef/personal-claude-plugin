# Andrew's Claude Code Skills

Personal Claude Code plugin marketplace. Skills for PRD/story planning and idea interrogation.

## Skills

| Skill | Description |
|---|---|
| [feature-planning](skills/planning/feature-planning/SKILL.md) | Orchestrate PRD development end-to-end into Mike Cohn/Gherkin user stories. Use when turning a feature or task into a written PRD plus development-ready stories, saved under `docs/`. |
| [implementation-planning](skills/planning/implementation-planning/SKILL.md) | Extract implementation details from written user stories — classes/modules, interfaces, code samples, data/schema changes — and append them to each user_story_<N>.md file. Use after feature-planning has produced docs/<TAG>/user_story_*.md files. |
| [interrogate](skills/productivity/interrogate/SKILL.md) | Grill the user relentlessly about a plan, decision, or idea. Use when stress-testing thinking. |
| [design-doc-mermaid](skills/design-doc-mermaid/SKILL.md) | Create Mermaid diagrams (flowchart, sequence, class, ER, state, C4, architecture) from text or code. Vendored from [SpillwaveSolutions/design-doc-mermaid](https://github.com/SpillwaveSolutions/design-doc-mermaid). |

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
