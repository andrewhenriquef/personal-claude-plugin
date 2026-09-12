---
name: feature-planning
description: Orchestrate PRD development end-to-end into Mike Cohn/Gherkin user stories. Use when turning a feature or task into a written PRD plus development-ready stories, saved under docs/.
disable-model-invocation: true
model: opus
effort: high
---

## Purpose

Drive a feature or task from raw idea to written artifacts: a PRD (via `prd-development`, gaps closed via `interrogate`), then user stories extracted from it (via `user-story`), each combining Mike Cohn's use-case format (who/what/why) with Gherkin acceptance criteria (Given/When/Then), plus a sequence diagram per acceptance criterion (via `design-doc-mermaid`). Both saved as files under `docs/`.

Not a feature spec — a conversation starter that captures *who* benefits, *what* they're trying to do, *why* it matters, and *how* you'll know it works.

## Input

**Works best with:** the feature or user need the story captures.
**Also useful:** the user role, the outcome they want, and edge cases the acceptance criteria must cover.

Anything supplied with the invocation — text after the skill name, a pasted context dump, an `ARGUMENTS:` line — counts as answers already given. Use it, don't re-ask.

**Arriving empty-handed works too.** Ask who the user is and what they're trying to accomplish before drafting.

## Anti-pattern: no technical questions

Stay at product level: who, what, why, what "done" looks like. Never ask the user — via `interrogate` or inline — about implementation details: which API endpoint returns an error, HTTP status codes, DB schema/migrations, sync vs async, which service owns a piece of logic, error-handling mechanics. A separate downstream skill extracts technical requirements from the PRD/stories afterward.

When `prd-development` or story drafting surfaces a technical detail:
- Don't stop and ask the user about it.
- Don't guess/assume a technical answer either.
- Restate it as a product-level behavior instead (e.g. "system must show error when X fails" rather than "which endpoint throws it") and tag it 🔧 **Technical detail (deferred)** in the doc.
- 🔧 tags don't block Step 2's completion check or Step 3 — they're left for the downstream technical skill, not resolved here.

## Orchestration

This skill reuses other skills in sequence. Do not reimplement their logic — invoke them with the `Skill` tool.

### Step 1 — Gather requirements: `prd-development`

Call `Skill(skill: "prd-development", args: <task description>)`. Let it drive problem framing, personas, solution overview, and success criteria for the feature/task at hand.

### Step 2 — Fill gaps: `interrogate`

Whenever `prd-development` (or you) hits a question, ambiguity, or missing data point that only the user can answer — scope boundary, persona detail, edge case, priority call — do not just ask inline. Call `Skill(skill: "interrogate", args: <the open question(s)>)` to grill the user until that branch is settled. Don't make assumptions, ask the user always. Resume `prd-development` with the answer once settled.

Repeat Steps 1–2 until every PRD section (problem, users, solution, success metrics, scope, dependencies) has no unresolved 🔵 **Open Question** left — 🔶 **Assumption** tags may remain only if the user explicitly punted on that branch (per `interrogate`'s punt rule), and 🔧 **Technical detail (deferred)** tags may remain always (see anti-pattern above — those aren't this skill's to resolve).

### Step 3 — Write PRD file

Once the PRD is complete (Steps 1–2 done, no open questions outstanding), ask the user for a ticket tag to file this under (Jira tag like PFS-1110, GitHub issue number, or any short slug — if the project has no tracker, ask for a short kebab-case slug instead). Write the PRD to `docs/<TAG>/PRD.md` under the current project's root, creating the folder if it doesn't exist.

### Step 4 — PRD specialist review: `pm-reviewer`, `tech-lead-reviewer`, `qa-reviewer`

Once Step 3's PRD file exists, run all three specialist review agents against it in parallel: `Agent(subagent_type: "pm-reviewer", prompt: <path to docs/<TAG>/PRD.md>)`, `Agent(subagent_type: "tech-lead-reviewer", prompt: <same path>)`, `Agent(subagent_type: "qa-reviewer", prompt: <same path>)`. Each is read-only and returns findings only — none of them edit the PRD.

For each finding returned:
- **Mechanical fix** (typo, inconsistent term, broken reference) — apply directly to `docs/<TAG>/PRD.md`.
- **Suggested tag is 🔵 Open Question or 🔶 Assumption** — route the finding's suggested question through `interrogate`, same as Step 2. Don't apply the agents' suggested wording as an assumption on their behalf — only the user's actual answer goes in.
- **Suggested tag is 🔧 Technical detail (deferred)** — tag it in place per the anti-pattern rule above; don't resolve it here.

Run one review round only — no re-run after fixes are applied.

### Step 5 — Extract user stories: `user-story`

Once Step 4's review round and fixes are done, call `Skill(skill: "user-story", args: <PRD content or path to docs/<TAG>/PRD.md>)` and extract the user stories from the PRD. If the PRD's epic breakdown yields multiple stories, repeat the call once per story. Write each to `docs/<TAG>/user_story_<N>.md` (e.g. `docs/PFS-1110/user_story_1.md`, `user_story_2.md`, ...), creating the folder if it doesn't exist.

### Step 6 — Generate sequence diagrams: `design-doc-mermaid`

Once every story file from Step 5 exists, call `Skill(skill: "design-doc-mermaid", args: <one acceptance criterion>)` once per acceptance criterion, generating a Mermaid sequence diagram of the actor/system interactions it describes.

Interleave each diagram directly beneath the acceptance criterion it belongs to — never batch all criteria first and all diagrams after:

~~~
Acceptance Criteria:

1. <criterion 1>

  ```mermaid
  sequenceDiagram
    ... diagram for criterion 1 ...
  ```

2. <criterion 2>

  ```mermaid
  sequenceDiagram
    ... diagram for criterion 2 ...
  ```
~~~

Edit the `docs/<TAG>/user_story_<N>.md` file in place to insert each diagram right after its criterion — don't append all diagrams at the end of the file.

### Step 7 — Generate implementation plans: `implementation-planning`

Once every story file from Step 5 has its Step 6 diagrams, call `Skill(skill: "implementation-planning", args: <TAG>)`, passing the same ticket tag/slug used for `docs/<TAG>/` in Step 3. It reads every `user_story_<N>.md` under that folder and appends an `## Implementation Details` section to each.

### Step 8 — Review and validate

Review the written PRD and user story files (including their sequence diagrams and Step 7 implementation details) against each other: gaps, inconsistencies (naming, scope, persona), missing or contradictory acceptance criteria, stale references. Apply every fix directly to `docs/<TAG>/PRD.md` and the affected `docs/<TAG>/user_story_<N>.md` files — this step updates the files on disk, not just a findings list.

- **Mechanical fixes** (typos, inconsistent terms, broken links) — apply directly to the files.
- **Substantive gaps** (missing decision, ambiguous scope, new open question) — route back to `interrogate`, don't assume. Apply the fix once settled, then re-run this review pass once before considering it done.
- **Unresolved 🔶 Assumption found during review** — leave the tag in place, don't strip it; only remove it if this pass resolves it with the user via `interrogate`.
- **Missing acceptance-criteria scenarios** — for each story, think through edge cases, error paths, and boundary conditions the current criteria don't cover (e.g. empty state, permission denied, concurrent update, invalid input). If a plausible scenario is missing:
  - If it depends on a business rule or priority call only the user can make, route it through `interrogate` before adding it — don't assume.
  - Once settled, add the new acceptance criterion to `user_story_<N>.md`, then run Step 6 for it so it gets its own sequence diagram, interleaved in place like the rest, and re-run Step 7 for that story so its Implementation Details section covers the new criterion too.
  - Don't invent scenarios beyond what's plausible for the story's stated scope — this fills real gaps, not padding.
- **Conciseness check** — for each story, verify wording is tight: no redundant restatement between the Cohn who/what/why and the acceptance criteria, no filler sentences, no scenario duplicating another almost word-for-word. Tighten in place; if a fix would drop something substantive, treat it as a substantive gap and check with the user via `interrogate` instead of silently deleting it.
- Stop when one pass finds nothing left to fix — don't keep re-reviewing for style.

### Step 9 — Log questions & answers

Once Step 8's review pass finds nothing left to fix, append a `## Questions & Answers` section to the end of `docs/<TAG>/PRD.md`, listing every question routed through `interrogate` during Steps 2, 4, and 8 — not `prd-development`'s own internal flow, only ones that went through `interrogate` — in the order asked, each with the answer the user gave:

```
- **Q:** <question as asked>
  **A:** <user's answer>
```

If a question was answered and later revised during the flow, keep only the final answer — don't list stale intermediate ones. Run this once, after Step 8 is fully done, not after every `interrogate` call.

### Sequencing rule

Never run Step 5 before Step 4's review round and fixes are done. Never run Step 6 before every story file from Step 5 exists — with multiple stories, wait for all of them, not just the first. Never run Step 7 before every story has its Step 6 sequence diagrams appended. Never run Step 8 before every story has its Step 7 Implementation Details section. Never run Step 9 before Step 8's review pass is finished.


