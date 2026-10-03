---
name: product-interrogatory
description: Run a four-lens discovery interrogation — product manager, product designer, QA, technical — each round driven by `interview`, each building on what the last one settled. Produces raw settled answers for a PRD, not the PRD itself. Use when the input has no clear persona/flow/problem framing/feasibility view yet, or before designing an endpoint/integration surface with nothing settled.
---

You are running discovery as four sequential interrogation rounds, each from a different point of view, each in this session — no subagents, nothing in parallel. Every round calls `Skill(skill: "interview", ...)` to actually grill the user; you don't ask ad hoc.

This skill only interrogates and records settled answers. It does not write a problem statement, persona doc, or diagram — that's the PRD skill's job downstream, working from this skill's output.

## Shared rules across all four steps

- Every round uses `interview` for its questions — don't shortcut to the next step before that round's frontier of open decisions is empty.
- Between rounds, **re-evaluate**: read back what the previous round settled, and let it shape the next round's questions. Don't ask a question the last round already answered; don't repeat a lens's concerns in a later round.
- If the user punts on the same branch twice (per `interview`'s own rule), mark it an open assumption and move on — carry it forward, don't silently resolve it.
- Every recorded answer must trace to something the user actually said. Don't invent detail to fill a gap — leave it as an open assumption.
- Keep one running list of settled Q&A across all four steps — each step appends to it, none of them starts over.

## Step 1 — Product manager: framing

Focus: the problem, who benefits, why it matters, success criteria, scope boundaries.

Call `Skill(skill: "interview", ...)` with the PM lens: what problem, whose workflow, what's broken today, what "done" looks like, what's explicitly out of scope, how success gets measured.

## Step 2 — Product designer: persona and flow

Focus: the persona as a consumer of the system — API caller, CLI operator, webhook integrator, another service, not a screen-user — and the flow as a sequence of calls/events/decisions, not screens.

Re-evaluate Step 1's output first: does the PM framing already name who benefits? If so, sharpen it into a concrete persona (goals, constraints, what a bad experience looks like) rather than re-asking who they are from scratch.

Call `Skill(skill: "interview", ...)` with the design lens: persona detail, the flow step by step, decision points, what triggers each step.

## Step 3 — QA: left-shift testability

Focus: whether Steps 1–2's answers are actually testable, before any of this becomes a PRD.

Re-evaluate the running Q&A against:
1. **Falsifiability** — can each stated outcome or "done" signal actually be checked?
2. **Missing negative/error paths** — for each flow step, what's the implied failure mode (invalid input, permission denied, empty state, timeout, conflict, misuse)?
3. **Boundary/edge conditions** — zero, one, many; first-time vs. repeat; concurrent access; partial completion.
4. **Non-functional dimensions** — auth/authz, data exposure, performance under load, concurrency.
5. **Ambiguous acceptance signal** — anywhere two people could disagree on pass/fail later.

Turn whatever this checklist surfaces into real questions and call `Skill(skill: "interview", ...)` with them — don't just list gaps, close them with the user. Don't invent scenarios beyond what's plausible for the stated scope.

## Step 4 — Technical: feasibility and constraints

Focus: integration risk, feasibility, dependencies, constraints — not the solution design itself, just what the user already knows that bounds it.

Re-evaluate the running Q&A first: what does the flow imply needs to exist (another service, an external API, a data store, an auth mechanism)? Turn the real unknowns into questions.

Call `Skill(skill: "interview", ...)` with the technical lens: what systems/services this touches or depends on, any known constraints (latency, scale, compliance, existing contracts it must not break), anything already ruled out and why. Stay at the level of constraints and dependencies the user actually knows — don't design the solution here, and don't ask the user to invent technical answers they don't have; if they don't know, that's an open assumption, not a punt to solve now.

## Output

```
## Discovery Q&A: <topic>

### Step 1 — PM
- **Q:** <question> **A:** <answer>

### Step 2 — Design
- **Q:** <question> **A:** <answer>

### Step 3 — QA
- **Q:** <question> **A:** <answer>

### Step 4 — Technical
- **Q:** <question> **A:** <answer>

### Open assumptions
<anything punted across any step — flag, don't hide>

### Handoff
Raw settled answers, ready for `prd-development` (or `feature-planning`) to draft the PRD from. Nothing here is a finished artifact.
```
