---
name: feature-planning
description: Orchestrate PRD development end-to-end into Mike Cohn/Gherkin user stories. Use when turning a feature or task into a written PRD plus development-ready stories, saved under docs/.
disable-model-invocation: true
model: opus
effort: high
---

## Purpose

Drive a feature or task from raw idea to written artifacts: a PRD (via `prd-development`, gaps closed via `interview`, reviewed by `pm-reviewer`/`tech-lead-reviewer`/`qa-reviewer`), then user stories extracted from it (via `user-story`), each combining Mike Cohn's use-case format (who/what/why) with Gherkin acceptance criteria (Given/When/Then). Both saved as files under `docs/`.

Not a feature spec — a conversation starter that captures *who* benefits, *what* they're trying to do, *why* it matters, and *how* you'll know it works.

## Input

**Works best with:** the feature or user need the story captures.
**Also useful:** the user role, the outcome they want, and edge cases the acceptance criteria must cover.

Anything supplied with the invocation — text after the skill name, a pasted context dump, an `ARGUMENTS:` line — counts as answers already given. Use it, don't re-ask.

**Arriving empty-handed works too.** Ask who the user is and what they're trying to accomplish before drafting.

## Anti-pattern: no technical questions

Stay at product level: who, what, why, what "done" looks like. Never ask the user — via `interview` or inline — about implementation details: which API endpoint returns an error, HTTP status codes, DB schema/migrations, sync vs async, which service owns a piece of logic, error-handling mechanics. A separate downstream skill extracts technical requirements from the PRD/stories afterward.

When `prd-development` or story drafting surfaces a technical detail:
- Don't stop and ask the user about it.
- Don't guess/assume a technical answer either.
- Restate it as a product-level behavior instead (e.g. "system must show error when X fails" rather than "which endpoint throws it") and tag it 🔧 **Technical detail (deferred)** in the doc.
- 🔧 tags don't block Step 2's completion check or Step 3 — they're left for the downstream technical skill, not resolved here.

## Orchestration

This skill reuses other skills in sequence. Do not reimplement their logic — invoke them with the `Skill` tool.

### Step 1 — Gather requirements: `prd-development`

Call `Skill(skill: "prd-development", args: <task description>)`. Let it drive problem framing, personas, solution overview, and success criteria for the feature/task at hand.

### Step 2 — Fill gaps: `interview`

Whenever `prd-development` (or you) hits a question, ambiguity, or missing data point that only the user can answer — scope boundary, persona detail, edge case, priority call — do not just ask inline. Call `Skill(skill: "interview", args: <the open question(s)>)` to grill the user until that branch is settled. Don't make assumptions, ask the user always. Resume `prd-development` with the answer once settled.

Repeat Steps 1–2 until every PRD section (problem, users, solution, success metrics, scope, dependencies) has no unresolved 🔵 **Open Question** left — 🔶 **Assumption** tags may remain only if the user explicitly punted on that branch (per `interview`'s punt rule), and 🔧 **Technical detail (deferred)** tags may remain always (see anti-pattern above — those aren't this skill's to resolve).

### Step 3 — Write PRD file

Once the PRD is complete (Steps 1–2 done, no open questions outstanding), ask the user for a ticket tag to file this under (Jira tag like PFS-1110, GitHub issue number, or any short slug — if the project has no tracker, ask for a short kebab-case slug instead). Write the PRD to `docs/<TAG>/PRD.md` under the current project's root, creating the folder if it doesn't exist.

### Step 4 — PRD specialist review: `pm-reviewer`, `tech-lead-reviewer`, `qa-reviewer`

Once Step 3's PRD file exists, run all three specialist review agents against it in parallel: `Agent(subagent_type: "pm-reviewer", prompt: <path to docs/<TAG>/PRD.md>)`, `Agent(subagent_type: "tech-lead-reviewer", prompt: <same path>)`, `Agent(subagent_type: "qa-reviewer", prompt: <same path>)`. Each is read-only and returns findings only — none of them edit the PRD.

For each finding returned:
- **Mechanical fix** (typo, inconsistent term, broken reference) — apply directly to `docs/<TAG>/PRD.md`.
- **Suggested tag is 🔵 Open Question or 🔶 Assumption** — route the finding's suggested question through `interview`, same as Step 2. Don't apply the agents' suggested wording as an assumption on their behalf — only the user's actual answer goes in.
- **Suggested tag is 🔧 Technical detail (deferred)** — tag it in place per the anti-pattern rule above; don't resolve it here.

Every finding acted on must end with `docs/<TAG>/PRD.md` updated on disk — mechanical fixes applied directly, and every `interview` answer written back into the relevant PRD section (not just settled in conversation). This step isn't done until the PRD file itself reflects all three agents' resolved findings.

Run one review round only — no re-run after fixes are applied.

### Step 5 — Extract user stories: `user-story`

Once Step 4's review round and fixes are done, call `Skill(skill: "user-story", args: <PRD content or path to docs/<TAG>/PRD.md>)` and extract the user stories from the PRD. If the PRD's epic breakdown yields multiple stories, repeat the call once per story. Write each to `docs/<TAG>/user_story_<N>.md` (e.g. `docs/PFS-1110/user_story_1.md`, `user_story_2.md`, ...), creating the folder if it doesn't exist.

### Step 6 — Log questions & answers

Once Step 5's story files are written, append a `## Questions & Answers` section to the end of `docs/<TAG>/PRD.md`, listing every question routed through `interview` during Steps 2 and 4 — not `prd-development`'s own internal flow, only ones that went through `interview` — in the order asked, each with the answer the user gave:

```
- **Q:** <question as asked>
  **A:** <user's answer>
```

If a question was answered and later revised during the flow, keep only the final answer — don't list stale intermediate ones. Run this once, not after every `interview` call.

### Sequencing rule

Never run Step 5 before Step 4's review round and fixes are done. Never run Step 6 before Step 5's story files are written.


