---
name: implementation-planning
description: Generate sequence diagrams and extract implementation details from written user stories — classes/modules, interfaces, code samples, data/schema changes — and write them into each user_story_<N>.md file. Use after feature-planning has produced docs/<TAG>/user_story_*.md files and engineering needs a technical plan before coding.
model: opus
effort: high
---

## Purpose

Turn product-level user stories into a technical implementation plan, written back into the same story files: a story-level flow diagram, a sequence diagram per acceptance criterion, plus concrete engineering decisions — which classes/modules to create or change, their interfaces, code samples where prose alone can't pin the decision down, and any data/schema changes. No interview, no re-derivation of the product decisions already made — this skill synthesizes what the codebase and the story already tell you.

Not a spec-writing skill and not a coding skill. It plans *how* the story gets built; it does not write production code, open a PR, or re-litigate *what* the story is.

## Input

**Required:** `<TAG>` — the ticket tag/slug identifying `docs/<TAG>/`, the folder `feature-planning` / `user-story` wrote the story files into. Without it, the correct folder can't be resolved — ask for it before doing anything else.

**Optional:** specific `user_story_<N>.md` filenames within that folder, to scope the run to a subset instead of every story under `docs/<TAG>/`.

**Also useful:** the PRD at `docs/<TAG>/PRD.md`, if present, for cross-story context (shared entities, dependencies between stories).

Anything supplied with the invocation — the tag, explicit story filenames — counts as scope already given. Use it, don't re-ask.

## Anti-pattern: no re-litigating the product decision

The who/what/why and acceptance criteria are settled. Never second-guess scope, persona, or business rules here — if a story is ambiguous at the *product* level, that's a bug in the story, not something to silently resolve. Flag it back to the user instead of guessing.

This skill exists to resolve exactly the things `feature-planning` deliberately deferred: any 🔧 **Technical detail (deferred)** tag left in a story is this skill's to resolve now.

## Interrogate for technical decisions only

Codebase exploration settles most technical decisions. When one doesn't — a real fork with no clear winner from convention or context (e.g. sync vs async, which existing service owns this, new table vs new column) — call `Skill(skill: "interrogate", args: <the open technical question(s)>)` to grill the user until settled. Don't guess on a decision that would be expensive to reverse later. Never route product-level questions (scope, persona, business rules) through this — those go back to the user directly, flagged, per the anti-pattern above.

## Process

### Step 1 — Locate story files

Require `<TAG>` before proceeding — if missing, ask for it, don't guess or search for a folder to infer it from. Once known, resolve to a concrete list of files: specific filenames if given, otherwise glob `docs/<TAG>/user_story_*.md`.

### Step 2 — Read story + surrounding context

For each story file, read:
- The Cohn use case (who/what/why) and every acceptance criterion.
- Any 🔧 **Technical detail (deferred)** tags — these are the concrete questions this skill must answer.
- `docs/<TAG>/PRD.md` if present, for shared entities or dependencies across stories.

### Step 3 — Explore the codebase

Before inventing anything, look for what already exists: similar classes/modules, naming conventions, existing services/models the story would extend rather than duplicate, and the layer boundaries the project already uses (services, models, controllers, whatever the project's architecture is). Prefer reusing or extending an existing seam over introducing a new one. If the project has architecture-decision docs or conventions, follow them.

Trace the existing code flow and sequence relevant to the story — which classes/modules/services already handle this area, and how they call each other. Identify whether the story is a **change to that existing flow** or a **complete new feature** with no current equivalent; this determines whether Step 4's story flow diagram, Step 5's AC diagrams, and Step 6's plan extend existing structure or introduce new structure.

### Step 4 — Generate story-level flow diagram: `design-doc-mermaid`

Call `Skill(skill: "design-doc-mermaid", args: <the story as a whole>)` once per story, to produce one flow diagram covering the story end-to-end (not per acceptance criterion — that's Step 5). Skip a story that already has its flow diagram(s) from a prior run. Base it on Step 3's finding, same logic as Step 5's AC diagrams:

- **Existing flow being changed** — generate two diagrams: **AS IS** (current story-level flow) and **TO BE** (flow after the story's change).
- **Complete new feature** — generate one diagram: the new story-level flow. No AS IS diagram.

Place it near the top of the story file, before the acceptance criteria, e.g.:

~~~
## Story Flow

**AS IS**
```mermaid
sequenceDiagram
  ... current end-to-end flow ...
```

**TO BE**
```mermaid
sequenceDiagram
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

Resolve every 🔧 tag encountered along the way; remove the tag once answered inline in this new content. If resolving one requires a real technical judgment call the codebase can't settle, route it through `interrogate` first (see above) rather than guessing.

Exclude file paths from the writeup itself — name classes/modules by their role, not their location — unless a path materially disambiguates between two same-named things.

Keep the Cohn/Gherkin content, the Step 4 story flow diagram, and the Step 5 per-AC sequence diagrams as they are — don't touch or rewrite them. Write one `## Implementation Details` section per story, appended after the acceptance criteria (not interleaved per criterion):

~~~
## Implementation Details

- Classes/modules: ... (note which criteria each serves, e.g. "supports AC1, AC3")
- Interface: ...
  ```<lang>
  <short signature or illustrative sample>
  ```
- API contract: ... (request/response shape, status codes, error payloads — omit if no external-facing interface)
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

Once every requested story has its Step 4-6 content, re-read all stories together and check:

- **Naming** — same entity, class, module, field named consistently across every story that touches it.
- **Shapes** — no two stories independently inventing incompatible shapes for the same class, interface, or code sample.
- **Data/schema** — no contradictory schema changes (two stories altering the same table/field differently).
- **API contracts** — no two stories defining conflicting request/response shapes or status codes for the same endpoint.
- **Diagrams** — each story's Step 4 flow diagram agrees with its own Step 5 per-AC diagrams (same actors, same sequence); AS IS diagrams across stories agree on the current flow where they overlap.
- **Dependencies** — every dependency one story declares on another is real (that story exists, does what's expected) and reciprocal where relevant (if story A depends on story B, story B's plan doesn't contradict that).
- **Rollout/backward compatibility** — no two stories assuming incompatible rollout orders or coexistence states for a shared flow.
- **Security/permissions** — no two stories applying different auth/authz rules to the same resource.

Fix directly in the files. If a fix touches a diagram, regenerate it via `design-doc-mermaid` rather than hand-editing the Mermaid source. If a fix requires a real technical judgment call, route it through `interrogate` (see above) rather than guessing. Stop once one pass finds nothing left to fix.
