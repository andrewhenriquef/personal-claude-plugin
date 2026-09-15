---
name: interview
description: Interview the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Write in ASD-STE100 Simplified Technical English. Give a brief context about what this round covers and why — in that style.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round, then wait for the user's answers before the next round.

`AskUserQuestion` allows at most 4 questions per call and 4 options per question. If the frontier has more than 4 decisions, split it across multiple `AskUserQuestion` calls issued together in the same round, never trim the frontier to fit the limit. For each question, put your recommended answer as the first option, labeled "(Recommended)", per the tool's own convention, don't just state it in prose.

Each round, the user's answers reshape the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch it to the `Explore` agent (or `fork` if it needs your conversation context) via the `Agent` tool; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

If the user punts on the same branch twice in a row (picks "Other" with no real answer, says "not sure", defers), stop re-asking it: mark it an explicit open assumption, note it in the final summary, and move on — don't loop on one branch forever.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Summarize the settled tree as a short list (decision → answer), plus any open assumptions from punted branches. Do not act on it until the user confirms you have reached a shared understanding.
