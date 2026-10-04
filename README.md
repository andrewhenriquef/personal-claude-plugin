# Andrew's Claude Code Skills

Personal Claude Code plugin marketplace. Skills for PRD/story planning, idea interviewing, and code simplification.

## Skills

| Skill | Description |
|---|---|
| [feature-planning](skills/planning/feature-planning/SKILL.md) | Orchestrate PRD development end-to-end into Mike Cohn/Gherkin user stories, with optional `product-designer` discovery when input arrives light on context. Use when turning a feature or task into a written PRD plus development-ready stories, saved under `docs/`. |
| [implementation-planning](skills/planning/implementation-planning/SKILL.md) | Generate flow/sequence diagrams (AS IS/TO BE when changing existing behavior) and extract implementation details — classes/modules, interfaces, API contracts, code samples, data/schema changes, dependencies, non-functional requirements, observability, rollout, security — into one user_story_<N>.md at a time. Use after feature-planning has produced docs/<TAG>/user_story_*.md files. |
| [interview](skills/productivity/interview/SKILL.md) | Interview the user relentlessly about a plan, decision, or idea. Use when stress-testing thinking. |
| [understand-the-intent](skills/productivity/understand-the-intent/SKILL.md) | Interview the user until shared understanding, then write `docs/<slug>/intent.md`: original prompt, context, questions and answers, summary, structured shared understanding, and intent. Open assumptions only when the user chooses them. Writes in STE100 English or Linguagem Simples (pt-BR), per the user's language. |
| [grammar-review](skills/productivity/grammar-review/SKILL.md) | Review and correct text for grammar, spelling, and clarity in any language (English, Portuguese, Spanish, Italian, and others). Detects the language automatically and rewrites using that language's plain-language standard, keeping original tone and mood. Explicit call only (`/grammar-review`). |
| [product-interrogatory](skills/productivity/product-interrogatory/SKILL.md) | Product discovery (persona, flow, problem statement) via direct interview in this session, plus a QA left-shift testability pass on the synthesis. Sequential, no subagent — same result as `product-designer` + `qa-reviewer` without the parallel overhead. |
| [code-simplify](skills/code-reviewing/code-simplify/SKILL.md) | Simplify code for clarity without changing behavior. Process: set scope and a test baseline, understand first (Chesterton's Fence), find opportunities, apply one change at a time, verify, report. References loaded on demand: design ([A Philosophy of Software Design](skills/code-reviewing/code-simplify/references/philosophy-of-software-design.md), [The Pragmatic Programmer](skills/code-reviewing/code-simplify/references/pragmatic-programmer.md)) and language samples ([Go](skills/code-reviewing/code-simplify/references/go.md), [Ruby](skills/code-reviewing/code-simplify/references/ruby.md)), picked by project language. Adapted from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills). Use when code works but is hard to read or maintain. |
| [security-analysis](skills/code-reviewing/security-analysis/SKILL.md) | Read-only security review of a diff, branch, or files. Process: one-page threat model, learn the repo's security patterns, detect candidates per attack-surface slice, then verify each candidate in a separate pass that tries to refute it. Reports only findings with source, sink, missing control, exploit scenario, and confidence of 0.8 or higher. Unverifiable items go to "Needs human check" (fail open). References loaded on demand: [OWASP Top 10:2025 questions](skills/code-reviewing/security-analysis/references/owasp-2025.md), [false-positive rules](skills/code-reviewing/security-analysis/references/false-positive-rules.md), and language sinks and samples ([Go](skills/code-reviewing/security-analysis/references/go.md), [Ruby](skills/code-reviewing/security-analysis/references/ruby.md)), picked by project language. Strategy evidence in [docs/research](docs/research/ai-code-review-strategies.md). Use when asking for a security review or "is this safe". |
| [design-doc-mermaid](skills/design-doc-mermaid/SKILL.md) | Create Mermaid diagrams (flowchart, sequence, class, ER, state, C4, architecture) from text or code. Vendored from [SpillwaveSolutions/design-doc-mermaid](https://github.com/SpillwaveSolutions/design-doc-mermaid). |

## Agents

| Agent | Description |
|---|---|
| [pm-reviewer](agents/pm-reviewer.md) | Review a PRD from a product-management lens: problem framing, personas, success metrics, scope. Read-only, findings only. |
| [tech-lead-reviewer](agents/tech-lead-reviewer.md) | Review a PRD from a tech-lead lens: feasibility risk, missing non-functional requirements, integration risk. Read-only, findings only. |
| [qa-reviewer](agents/qa-reviewer.md) | Review a PRD from a left-shift QA lens: testability, missing edge/negative paths, non-functional test coverage. Read-only, findings only. |
| [senior-dev](agents/senior-dev.md) | Spawned by `implementation-planning` (one per story, in parallel, when a tag has multiple stories): explores the codebase, generates diagrams, writes technical details back into one `user_story_<N>.md`. Read/write. |
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
