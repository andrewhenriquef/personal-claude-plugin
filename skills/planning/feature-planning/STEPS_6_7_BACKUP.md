> Backup of Steps 6-7 removed from `SKILL.md` on 2026-09-12. Kept here in case they're reinstated later.

### Step 6 — Generate implementation plans: `implementation-planning`

Once every story file from Step 5 exists, call `Skill(skill: "implementation-planning", args: <TAG>)`, passing the same ticket tag/slug used for `docs/<TAG>/` in Step 3. It reads every `user_story_<N>.md` under that folder, generates the sequence diagrams per acceptance criterion, and appends an `## Implementation Details` section to each.

### Step 7 — Review and validate

Review the written PRD and user story files (including their Step 6 sequence diagrams and implementation details) against each other: gaps, inconsistencies (naming, scope, persona), missing or contradictory acceptance criteria, stale references. Apply every fix directly to `docs/<TAG>/PRD.md` and the affected `docs/<TAG>/user_story_<N>.md` files — this step updates the files on disk, not just a findings list.

- **Mechanical fixes** (typos, inconsistent terms, broken links) — apply directly to the files.
- **Substantive gaps** (missing decision, ambiguous scope, new open question) — route back to `interrogate`, don't assume. Apply the fix once settled, then re-run this review pass once before considering it done.
- **Unresolved 🔶 Assumption found during review** — leave the tag in place, don't strip it; only remove it if this pass resolves it with the user via `interrogate`.
- **Missing acceptance-criteria scenarios** — for each story, think through edge cases, error paths, and boundary conditions the current criteria don't cover (e.g. empty state, permission denied, concurrent update, invalid input). If a plausible scenario is missing:
  - If it depends on a business rule or priority call only the user can make, route it through `interrogate` before adding it — don't assume.
  - Once settled, add the new acceptance criterion to `user_story_<N>.md`, then re-run Step 6 for that story so its sequence diagram and Implementation Details section cover the new criterion too.
  - Don't invent scenarios beyond what's plausible for the story's stated scope — this fills real gaps, not padding.
- **Conciseness check** — for each story, verify wording is tight: no redundant restatement between the Cohn who/what/why and the acceptance criteria, no filler sentences, no scenario duplicating another almost word-for-word. Tighten in place; if a fix would drop something substantive, treat it as a substantive gap and check with the user via `interrogate` instead of silently deleting it.
- Stop when one pass finds nothing left to fix — don't keep re-reviewing for style.
