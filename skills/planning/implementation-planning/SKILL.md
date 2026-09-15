---
name: implementation-planning
description: Generate flow/sequence diagrams (with AS IS/TO BE when changing existing behavior) and extract implementation details from written user stories — classes/modules, interfaces, API contracts, code samples, data/schema changes, dependencies, non-functional requirements, observability, rollout, security — and write them into each user_story_<N>.md file. Given a story ID, runs that one story; given just the tag with multiple stories, fans out one senior-dev agent per story in parallel then checks cross-story consistency. Use after feature-planning has produced docs/<TAG>/user_story_*.md files and engineering needs a technical plan before coding.
model: opus
effort: high
---

## Purpose

Turn product-level user stories into a technical implementation plan, written back into the same story files: a story-level flow diagram, a sequence diagram per acceptance criterion — each as AS IS/TO BE pair when changing an existing flow, single diagram when introducing a new one — plus concrete engineering decisions: which classes/modules to create or change, their interfaces and API contracts, code samples for every planned change, data/schema changes, and (where relevant) dependencies, non-functional requirements, observability, rollout/backward compatibility, and security/permissions. No interview, no re-derivation of the product decisions already made — this skill synthesizes what the codebase and the story already tell you.

Not a spec-writing skill and not a coding skill. It plans *how* the story gets built; it does not write production code, open a PR, or re-litigate *what* the story is.

## Input

**Required:** `<TAG>` — the ticket tag/slug identifying `docs/<TAG>/`, the folder `feature-planning` / `user-story` wrote the story files into. Without it, the correct folder can't be resolved — ask for it before doing anything else.

**Optional:** `<STORY_ID>` — the `N` in `user_story_<N>.md`, to scope the run to that one story. Omit it with a `<TAG>` that has more than one story file to fan out instead: one `senior-dev` agent is launched per story, in parallel, each doing the technical work for its own story directly (see Step 1). If only one story file exists under `<TAG>`, that one is unambiguous and runs directly, no fan-out needed. Multiple explicit `<STORY_ID>`s (or explicit filenames) may be given to scope a direct run to more than one story without fanning out.

**Also useful:** the PRD at `docs/<TAG>/PRD.md`, if present, for cross-story context (shared entities, dependencies between stories).

Anything supplied with the invocation — the tag, the story ID(s), explicit story filenames — counts as scope already given. Use it, don't re-ask.

## Anti-pattern: no re-litigating the product decision

The who/what/why and acceptance criteria are settled. Never second-guess scope, persona, or business rules here — if a story is ambiguous at the *product* level, that's a bug in the story, not something to silently resolve. Flag it back to the user instead of guessing.

This skill exists to resolve exactly the things `feature-planning` deliberately deferred: any 🔧 **Technical detail (deferred)** tag left in a story is this skill's to resolve now.

## Interrogate for technical decisions only

Codebase exploration settles most technical decisions. When one doesn't — a real fork with no clear winner from convention or context (e.g. sync vs async, which existing service owns this, new table vs new column) — call `Skill(skill: "interview", args: <the open technical question(s)>)` to grill the user until settled. Don't guess on a decision that would be expensive to reverse later. Never route product-level questions (scope, persona, business rules) through this — those go back to the user directly, flagged, per the anti-pattern above.

## Process

### Step 1 — Locate story file(s), or fan out one senior-dev per story

Require `<TAG>` before proceeding — if missing, ask for it, don't guess or search for a folder to infer it from. Once known, glob `docs/<TAG>/user_story_*.md` and branch:

- **`<STORY_ID>`(s) or explicit filename(s) given** — resolve directly to `docs/<TAG>/user_story_<N>.md` for each and run Steps 2 through 7 yourself, including the cross-story consistency check.
- **Nothing given, exactly one `user_story_*.md` exists** — unambiguous. Run Steps 2 through 7 yourself (Step 7 will no-op per its own single-file skip rule).
- **Nothing given, more than one `user_story_*.md` exists** — fan out instead of asking which one or processing any of them yourself. For each story file, launch one agent in parallel: `Agent(subagent_type: "senior-dev", prompt: "<TAG> <STORY_ID>")`, one `Agent` call per story, all issued in the same message so they run concurrently — same pattern as `feature-planning`'s parallel review step. Each `senior-dev` does the equivalent of Steps 2-6 for its own story only, directly (it does not call back into this skill, and never runs `interview` itself — a background agent can't hold a live back-and-forth with the user). Once every spawned agent has finished, skip Steps 2-6 yourself and:
  1. Relay each agent's report to the user (story, changed-flow vs new-feature, 🔧 tags resolved).
  2. For anything an agent reported as **Blocked** (a product-level ambiguity, or a real technical fork it couldn't settle), call `Skill(skill: "interview", args: <the blocked question(s)>)` yourself — you're in the main thread and can. Once answered, patch that resolved detail directly into the affected story's `## Implementation Details` (and remove its 🔧 tag) — you don't need to re-spawn the agent for a one-field fix.
  3. Run Step 7 once, yourself, against every story with an `## Implementation Details` section — a story an agent couldn't finish at all just has none yet, and Step 7 already skips those.

This skill is the only thing that spawns `senior-dev` agents — it never calls itself back, and `senior-dev` never calls this skill. Fan-out happens exactly once, at Step 1, only when `<STORY_ID>` is absent and multiple stories exist.

### Step 2 — Read story + surrounding context

For each story file, read:
- The Cohn use case (who/what/why) and every acceptance criterion.
- Any 🔧 **Technical detail (deferred)** tags — these are the concrete questions this skill must answer.
- `docs/<TAG>/PRD.md` if present, for shared entities or dependencies across stories.

### Step 3 — Explore the codebase

Before inventing anything, look for what already exists: similar classes/modules, naming conventions, existing services/models the story would extend rather than duplicate, and the layer boundaries the project already uses (services, models, controllers, whatever the project's architecture is). Prefer reusing or extending an existing seam over introducing a new one. If the project has architecture-decision docs or conventions, follow them.

Trace the existing code flow and sequence relevant to the story — which classes/modules/services already handle this area, and how they call each other. Identify whether the story is a **change to that existing flow** or a **complete new feature** with no current equivalent; this determines whether Step 4's story flow diagram, Step 5's AC diagrams, and Step 6's plan extend existing structure or introduce new structure.

### Step 4 — Generate story-level flow diagram: `design-doc-mermaid`

Call `Skill(skill: "design-doc-mermaid", args: <the story as a whole, as a flowchart>)` once per story, to produce one **flowchart** (`flowchart TD`) covering the story end-to-end — not a sequence diagram; this is the high-level shape of the story, not an actor/message trace (that's Step 5). Skip a story that already has its flow diagram(s) from a prior run. Base it on Step 3's finding, same logic as Step 5's AC diagrams:

- **Existing flow being changed** — generate two diagrams: **AS IS** (current story-level flow) and **TO BE** (flow after the story's change).
- **Complete new feature** — generate one diagram: the new story-level flow. No AS IS diagram.

Place it after the Cohn use case (who/what/why) and before the acceptance criteria, e.g.:

~~~
## Story Flow

**AS IS**
```mermaid
flowchart TD
  ... current end-to-end flow ...
```

**TO BE**
```mermaid
flowchart TD
  ... changed end-to-end flow ...
```
~~~

(New-feature stories get a single `## Story Flow` diagram, no AS IS/TO BE split.)

### Step 5 — Generate per-AC sequence diagrams: `design-doc-mermaid`

For each story file, call `Skill(skill: "design-doc-mermaid", args: <one acceptance criterion>)` once per acceptance criterion that doesn't already have a diagram(s). Skip criteria that already have their diagram(s) from a prior run. Base it on Step 3's finding:

- **Existing flow being changed** — generate two diagrams: **AS IS** (current flow, unchanged) and **TO BE** (flow after the story's change). Both cover the same acceptance criterion.
- **Complete new feature** — generate one diagram: the new flow the criterion describes. No AS IS diagram — there's no prior flow to show.

Interleave each criterion's diagram(s) directly beneath it — never batch all criteria first and all diagrams after. New-feature case:

~~~
Acceptance Criteria:

1. <criterion 1>

  ```mermaid
  sequenceDiagram
    ... diagram for criterion 1 ...
  ```
~~~

Changed-flow case:

~~~
Acceptance Criteria:

1. <criterion 1>

  **AS IS**
  ```mermaid
  sequenceDiagram
    ... current flow for criterion 1 ...
  ```

  **TO BE**
  ```mermaid
  sequenceDiagram
    ... changed flow for criterion 1 ...
  ```
~~~

**Never use `alt`/`opt` (or `loop`/`par`) in an AC sequence diagram.** Each acceptance criterion already describes one Given/When/Then path — draw exactly that path, start to finish, with no branching inside the diagram. If a scenario's flow genuinely forks into more than one path worth showing, that's a sign it should be more than one diagram (or more than one AC) — draw each path as its own separate, self-contained sequence diagram rather than one diagram with `alt`/`else` branches. This also sidesteps a real Mermaid failure mode: activating a participant with `->>+X` before a branch and only deactivating it (`-->>-X`) in one arm leaves the activation stack unbalanced and the diagram fails to render (or renders broken activation bars) — isolated linear diagrams can't hit this at all.

Edit the `docs/<TAG>/user_story_<N>.md` file in place to insert each criterion's diagram(s) right after it — don't append all diagrams at the end of the file.

### Step 6 — Draft implementation details and write back to the story file

Work out, for the story as a whole (not per criterion — a class or schema change is usually shared across several acceptance criteria, so plan it once at story level and note which criteria it serves):

- **Classes/modules** — new ones to create, existing ones to modify, and why.
- **Interfaces/signatures** — key method or function signatures, not full bodies.
- **API/interface contracts** — request/response shapes, status codes, error payloads, for any endpoint or external-facing interface the story touches.
- **Code samples** — for every planned code change (new function/method, modified logic, new class), not just tricky ones: show the planned change itself, illustrative not production-ready. Keep short — signature plus the key lines that carry the decision, not a full body.
- **Data/schema changes** — new fields, tables, migrations, API request/response shapes.
- **Error handling** — how failure modes named in the acceptance criteria get surfaced (exceptions, error codes, fallback behavior).
- **Dependencies/integration points** — other services, other stories, or feature flags this story depends on or blocks. Only if any exist.
- **Non-functional requirements** — perf, security, concurrency, data-volume constraints the PRD/AC imply but don't state outright. Only if the story's AC or PRD implies one.
- **Observability** — logging, metrics, or alerts needed to confirm the new/changed flow works in production. Only if the flow is user-facing or failure-prone enough to warrant it.
- **Rollout/backward compatibility** — migration strategy, feature flag, whether the AS IS and TO BE flows must coexist during rollout. Only for changed-flow stories (see Step 3/4) where old and new behavior might overlap in production.
- **Security/permissions** — auth/authz checks the flow touches or changes. Only if the story crosses a permission boundary.

Include the last five bullets only when relevant to the story — skip silently for a story with none of these concerns, don't pad with "N/A".

Resolve every 🔧 tag encountered along the way; remove the tag once answered inline in this new content. If resolving one requires a real technical judgment call the codebase can't settle, route it through `interview` first (see above) rather than guessing.

Exclude file paths from the writeup itself — name classes/modules by their role, not their location — unless a path materially disambiguates between two same-named things.

Keep the Cohn/Gherkin content, the Step 4 story flow diagram, and the Step 5 per-AC sequence diagrams as they are — don't touch or rewrite them. Write one `## Implementation Details` section per story, appended after the acceptance criteria (not interleaved per criterion):

~~~
## Implementation Details

- Classes/modules: ... (note which criteria each serves, e.g. "supports AC1, AC3")
- Interface: ...
  ```<lang>
  <key method/function signature>
  ```
- API contract: ... (request/response shape, status codes, error payloads — omit if no external-facing interface)
- Code samples:
  ```<lang>
  <planned change, illustrative — repeat per class/module changed>
  ```
- Data/schema: ...
- Error handling: ...
- Dependencies/integration points: ... (omit if none)
- Non-functional requirements: ... (omit if none implied)
- Observability: ... (omit if not warranted)
- Rollout/backward compatibility: ... (omit for new-feature stories with no coexistence concern)
- Security/permissions: ... (omit if no permission boundary touched)
~~~

If the file already has an `## Implementation Details` section from a prior run, overwrite it rather than appending a duplicate or merging piecemeal — regenerate it fresh from the current story content so it never drifts out of sync with the acceptance criteria above it.

### Step 7 — Cross-story consistency check

Once every requested story has its Step 4-6 content, check it against every other `user_story_*.md` under `docs/<TAG>/` — not just the one(s) processed this run, since this skill usually runs one story at a time. If a sibling story has no `## Implementation Details` section yet (not yet run through this skill), skip it — there's nothing technical to compare yet. If `docs/<TAG>/` has only one story file total, skip this step. Otherwise re-read the processed story alongside every sibling that does have implementation details, and check:

- **Naming** — same entity, class, module, field named consistently across every story that touches it.
- **Shapes** — no two stories independently inventing incompatible shapes for the same class, interface, or code sample.
- **Data/schema** — no contradictory schema changes (two stories altering the same table/field differently).
- **API contracts** — no two stories defining conflicting request/response shapes or status codes for the same endpoint.
- **Diagrams** — each story's Step 4 flow diagram agrees with its own Step 5 per-AC diagrams (same actors, same sequence); AS IS diagrams across stories agree on the current flow where they overlap.
- **Dependencies** — every dependency one story declares on another is real (that story exists, does what's expected) and reciprocal where relevant (if story A depends on story B, story B's plan doesn't contradict that).
- **Non-functional requirements** — no two stories assuming conflicting perf/concurrency/data-volume constraints for a shared component.
- **Observability** — shared flows aren't logged/measured redundantly or inconsistently by different stories (same event, different metric name).
- **Rollout/backward compatibility** — no two stories assuming incompatible rollout orders or coexistence states for a shared flow.
- **Security/permissions** — no two stories applying different auth/authz rules to the same resource.

Fix directly in the files. If a fix touches a diagram, regenerate it via `design-doc-mermaid` rather than hand-editing the Mermaid source. If a fix requires a real technical judgment call, route it through `interview` (see above) rather than guessing. Stop once one pass finds nothing left to fix.
