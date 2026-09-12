---
name: implementation-planning
description: Generate sequence diagrams and extract implementation details from written user stories — classes/modules, interfaces, code samples, data/schema changes — and write them into each user_story_<N>.md file. Use after feature-planning has produced docs/<TAG>/user_story_*.md files and engineering needs a technical plan before coding.
model: sonnet
effort: high
---

## Purpose

Turn product-level user stories into a technical implementation plan, written back into the same story files: a sequence diagram per acceptance criterion, plus concrete engineering decisions — which classes/modules to create or change, their interfaces, code samples where prose alone can't pin the decision down, and any data/schema changes. No interview, no re-derivation of the product decisions already made — this skill synthesizes what the codebase and the story already tell you.

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

### Step 2 — Generate sequence diagrams: `design-doc-mermaid`

For each story file from Step 1, call `Skill(skill: "design-doc-mermaid", args: <one acceptance criterion>)` once per acceptance criterion that doesn't already have a diagram, generating a Mermaid sequence diagram of the actor/system interactions it describes. Skip criteria that already have one from a prior run.

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

### Step 3 — Read story + surrounding context

For each story file, read:
- The Cohn use case (who/what/why) and every acceptance criterion + Step 2 sequence diagram.
- Any 🔧 **Technical detail (deferred)** tags — these are the concrete questions this skill must answer.
- `docs/<TAG>/PRD.md` if present, for shared entities or dependencies across stories.

### Step 4 — Explore the codebase

Before inventing anything, look for what already exists: similar classes/modules, naming conventions, existing services/models the story would extend rather than duplicate, and the layer boundaries the project already uses (services, models, controllers, whatever the project's architecture is). Prefer reusing or extending an existing seam over introducing a new one. If the project has architecture-decision docs or conventions, follow them.

### Step 5 — Draft implementation details per story

Work out, for the story as a whole (not per criterion — a class or schema change is usually shared across several acceptance criteria, so plan it once at story level and note which criteria it serves):

- **Classes/modules** — new ones to create, existing ones to modify, and why.
- **Interfaces/signatures** — key method or function signatures, not full bodies.
- **Code samples** — only where prose can't pin the decision down precisely enough (a tricky algorithm, an interface shape, a data transform). Keep samples short and illustrative, not production-ready implementations.
- **Data/schema changes** — new fields, tables, migrations, API request/response shapes.
- **Error handling** — how failure modes named in the acceptance criteria get surfaced (exceptions, error codes, fallback behavior).

Resolve every 🔧 tag encountered along the way; remove the tag once answered inline in this new content. If resolving one requires a real technical judgment call the codebase can't settle, route it through `interrogate` first (see above) rather than guessing.

Exclude file paths from the writeup itself — name classes/modules by their role, not their location — unless a path materially disambiguates between two same-named things.

### Step 6 — Write back to the story file

Keep the Cohn/Gherkin content and its Step 2 sequence diagrams as they are — don't touch or rewrite them. Write one `## Implementation Details` section per story, appended after the acceptance criteria (not interleaved per criterion — see Step 5):

~~~
## Implementation Details

- Classes/modules: ... (note which criteria each serves, e.g. "supports AC1, AC3")
- Interface: ...
  ```<lang>
  <short signature or illustrative sample>
  ```
- Data/schema: ...
- Error handling: ...
~~~

If the file already has an `## Implementation Details` section from a prior run, overwrite it rather than appending a duplicate or merging piecemeal — regenerate it fresh from the current story content so it never drifts out of sync with the acceptance criteria above it.

### Step 7 — Cross-story consistency check

Once every requested story has its Implementation Details section, re-read them together: same entity named consistently across stories, no two stories independently inventing incompatible shapes for the same class, no contradictory schema changes. Fix directly in the files. Stop once one pass finds nothing left to fix.
