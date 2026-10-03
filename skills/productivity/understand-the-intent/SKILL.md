---
name: understand-the-intent
description: Interview the user relentlessly about a plan, idea, or feature until shared understanding, then write docs/<slug>/intent.md with the original prompt, context, every question and answer, a summary, the structured shared understanding, and the intent of what to build. Use when the user wants the interview result saved as a file.
---

Interview the user relentlessly until you reach a shared understanding, then write it down as `intent.md`. Map the interview as a **design tree**: every decision branches into the decisions that hang off it.

## Language

Use the language of the user's input, for the interview and for `intent.md`:

- **English** — write in ASD-STE100 Simplified Technical English.
- **Brazilian Portuguese** — write in Linguagem Simples (Rede Nacional de Linguagem Simples, Decreto 9.191/2017 principles): short sentences, direct order, active voice, common words.

Keep code, paths, and technical terms verbatim. Each round, give a brief context about what the round covers and why — in that style.

## Record as you go

From the start, keep a running record. You need it for `intent.md`:

- The **original prompt**, verbatim: text after the skill name, plus any pasted context.
- **Context**: facts you found in the environment and background the user gave.
- Every **question** you asked and the user's **answer**. Keep "Other" text and notes verbatim.

## Rounds and frontier

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round, then wait for the user's answers before the next round.

`AskUserQuestion` allows at most 4 questions per call and 4 options per question. If the frontier has more than 4 decisions, split it across multiple `AskUserQuestion` calls issued together in the same round, never trim the frontier to fit the limit. For each question, put your recommended answer as the first option, labeled "(Recommended)", per the tool's own convention, don't just state it in prose.

Every question also carries a last option **"Leave as open assumption"** (in Portuguese: "Deixar como suposição em aberto"). This leaves at most 3 real options per question.

Each round, the user's answers reshape the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch it to the `Explore` agent (or `fork` if it needs your conversation context) via the `Agent` tool; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

## No silent open assumptions

Never mark a question as an open assumption on your own. A question becomes an open assumption **only** when the user picks "Leave as open assumption".

If the user punts in any other way ("not sure", "Other" with no real answer, a vague answer), the question stays open. Reframe it and ask it again in the next round.

## Confirm

The interview is done when the frontier is empty: every branch visited, every question answered or explicitly left open by the user, nothing silently assumed.

Show the settled tree as a short list (decision → answer), plus the open assumptions the user chose. Ask the user to confirm the shared understanding. If the user corrects something, update the tree and ask a new round on the affected branch. Do not write the file until the user confirms.

## Write intent.md

After the user confirms:

1. Derive a short kebab-case `<slug>` from the topic.
2. Write `docs/<slug>/intent.md` with the template below. If the file already exists, ask the user: overwrite, or use a new slug.
3. Tell the user the file path. Do not act on the intent beyond writing the file.

Every answer in the file must trace to something the user said. Do not invent detail to fill a gap. Translate the section headings to the user's language (Portuguese: "Prompt original", "Contexto", "Perguntas e respostas", "Suposições em aberto", "Resumo", "Entendimento compartilhado", "Intenção").

```markdown
# Intent: <topic>

Date: <YYYY-MM-DD>

## Original prompt

<verbatim prompt and pasted context>

## Context

<background: what exists today, constraints, facts found during exploration, why this matters>

## Questions and answers

- **Q:** <question>
  **A:** <user answer, with verbatim notes if any>
- **Q:** ...
  **A:** ...

## Open assumptions

<only the questions the user chose to leave open, or "None">

## Summary

<short resume of the session, 3–6 sentences>

## Shared understanding

<structured design tree: decision → answer, nested by branch>

## Intent

<final description of what was understood: what we want to build, for whom, why, what is in scope and out of scope, and what "done" means>
```
