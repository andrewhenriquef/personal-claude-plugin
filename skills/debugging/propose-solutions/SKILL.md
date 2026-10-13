---
name: propose-solutions
description: Offer 2 to 3 ways to fix a diagnosed bug, written in English (ASD-STE100) and Brazilian Portuguese (Linguagem Simples), each with what changes, why it removes the confirmed root cause, an AS IS and TO BE Mermaid diagram, blast radius, risk, effort, reversibility, test plan (how the reproduction goes green and which cases to add), rollout and rollback, data repair, and a follow-up. Separates the root-cause fix, a containment (workaround, flag, rollback), and hardening (validation, constraint, monitor), compares them in a table, recommends one with reasons, and asks the user which to take. Options match the confidence label: unconfirmed causes get a "collect more evidence" option. Writes section 6 of docs/<slug>/diagnosis.md. Use when a bug has a root cause and the user asks "how can we fix this", "what are the options", or as step 6 of diagnose-and-reproduce. Does not write the fix.
---

# Propose Solutions

> Evidence sources: ITIL and SRE practice on workaround versus permanent fix and mitigation versus remediation (a workaround restores service and leaves the cause; a recurring workaround often costs more than the fix; automate nothing you cannot explain), [Google SRE book, Postmortem Culture](https://sre.google/sre-book/postmortem-culture/) (action items with owners; fix the contributing factors, not only the trigger), [Michael Nygard's architecture decision records](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) (context, options, consequences), the "seam" idea of [mattpocock diagnosing-bugs](https://github.com/mattpocock/skills) (a regression test needs a seam that runs the real bug pattern), [Claude Code best practices](https://code.claude.com/docs/en/best-practices) (a check Claude can run; ask for the user's choice before a large change), and `implementation-planning` in this plugin (AS IS and TO BE diagrams). Structure follows `implementation-planning`.

Give the user real choices with honest trade-offs, then stop and ask.

This skill does not write the fix. It names what would change, and how to prove it.

## Why this process

1. **There is rarely one fix.** A guard at the symptom, a change at the cause, and a constraint that makes the class of bug impossible have different cost, risk, and reach.
2. **Containment and cure are different.** A flag or a rollback stops the pain now. It leaves the cause. Say which an option is, and what it costs to leave it.
3. **The test decides.** An option that cannot be proven by the reproduction is a hope. Each option says how the red goes green.
4. **The user owns the trade-off.** Risk, time, and scope are the user's call. Show them side by side, recommend, and ask.
5. **Match the evidence.** An option for a cause that is only Likely must say so. When the cause is Unconfirmed, the first option is to get more evidence.

## When to use

- Step 6 of `diagnose-and-reproduce`, with a root cause and a reproduction.
- The user has a diagnosed bug and wants the options before choosing.

## When NOT to use

- There is no root cause. Go back to `confirm-root-cause`. If the user wants to go on anyway, offer only the "collect more evidence" option and containment, and label them.
- The user already chose a fix. Write the test and the fix.
- The user wants a design for a feature. Use `implementation-planning`.

## Process

### Step 0: Read

0. If `docs/<slug>/diagnosis.md` does not exist (this skill was called alone), pick a slug and create the file from [the template](../diagnose-and-reproduce/references/diagnosis-template.md). Fill the symptom card from what the user gave. Ask the user only when a missing fact blocks this skill, and then ask once, all questions in one `AskUserQuestion` call. Otherwise go on, and write each guess under **Assumptions**.
1. Read `docs/<slug>/diagnosis.md`: the root cause and its confidence label, the contributing and latent factors, the reproduction, the seam note, the impact.
2. Read the code that would change, and its callers. Read how the repo solves the same kind of problem elsewhere (validation, locking, idempotency, error handling). A fix that follows an existing pattern is cheaper and safer.
3. Check what the fix could break: callers, public APIs, stored data, jobs in flight, other services. Use `grep` for callers and the tests that cover them. Note the numbers (how many callers).

### Step 1: Generate options

Read [references/option-types.md](references/option-types.md). Write **2 to 3** options, so the user can choose with one question. Cover the types that apply. Do not pad. If more types apply, combine them (for example "fix plus constraint").

1. **Root-cause fix:** change the code or the data that produces the symptom. Usually the recommended option.
2. **Containment:** stop the damage without fixing the cause. A feature flag, a rollback, a guard at the entry, a retry, a manual data repair. Say what stays broken and for how long.
3. **Hardening:** remove the class of bug. A validation, a database constraint, a type, a test, a monitor, an idempotency key. Often paired with option 1.
4. **Collect more evidence** (only when the cause is Unconfirmed or Unreproduced): the smallest change that would confirm it, for example a probe or a metric in a non-production environment.

An option can combine types ("fix plus constraint"). Name the main type.

### Step 2: Describe each option

For each option, write:

| Field | Content |
|---|---|
| **Name** | A short label (`Guard the division`, `Make the write atomic`). |
| **Type** | Root-cause fix, containment, hardening, or collect evidence. |
| **What changes** | Files and functions, in a few lines. Real names. |
| **Why it works** | The link to the root cause: which step of the diagnosed flow it changes, and why the symptom then cannot happen. |
| **Diagrams** | AS IS (the failing flow from `explain-bug`, reused) and TO BE (the flow after this option). See [references/option-types.md](references/option-types.md). |
| **Blast radius** | What else it touches: callers, API, data, jobs, services. Numbers where you have them. |
| **Risk** | What could go wrong. Behavior changes, migrations, performance, compatibility. |
| **Effort** | S (hours), M (a day or two), L (more). A range, not a promise. |
| **Reversibility** | How to undo it, and how hard. |
| **Test plan** | The reproduction test goes green. Extra cases: the edge cases around the bug, the neighbors of the changed code. Say where the test sits (the seam). |
| **Rollout and rollback** | How it ships, what to watch, how to roll back. |
| **Data repair** | Whether stored data is wrong now and needs a repair script, and how to run it safely. |
| **Follow-up** | A monitor or alert to add (suggest only), a ticket, an owner. A containment gets an expiry and an owner. |

If the diagnosis says no good seam exists for a regression test, add an option or a step that creates the seam, or say that the regression test will sit at a shallower level and what it cannot catch.

### Step 3: Compare and recommend

1. Write a comparison table: one row per option; columns for type, effort, risk, blast radius, reversibility, fixes the cause (yes, no, partly), and what is left open.
2. Recommend **one** option, or one pairing (for example "contain now with a flag, fix next sprint"). Give two or three reasons that tie to the evidence and the table. State the condition under which you would pick another option.
3. Do not recommend an option that does not remove the confirmed cause, unless it is a clearly labeled containment with an owner and an expiry.
4. If an option is cheap and clearly useful but out of scope (a monitor, a refactor), put it under "Follow-ups", not in the options.

### Step 4: Write both languages

Read the language rules in [../explain-bug/references/language.md](../explain-bug/references/language.md). Write the English version (ASD-STE100) and the Portuguese version (Linguagem Simples) with the same options, in the same order, with the same numbers, the same names (translated sensibly), and the same recommendation. The diagrams are shared: labels in English, a Portuguese caption under each. The comparison table has English headers, and Portuguese headers in the Portuguese version.

### Step 5: Write, show, and ask

1. Write section 6 of `docs/<slug>/diagnosis.md`.
2. Show the options in the chat: the table first, the recommendation, then each option with its diagrams.
3. Return to `diagnose-and-reproduce`, which asks the user to choose with `AskUserQuestion` (one choice per option, the recommended one first, plus "I need more evidence" when there is room) and writes the handoff.
4. Do not start the fix.

## Output

````markdown
## 6. Solutions

### English

**Recommendation:** Option 2, because ...

| Option | Type | Effort | Risk | Blast radius | Reversible | Fixes the cause |
|---|---|---|---|---|---|---|

#### Option 1: <name> (<type>)
**What changes** ...  **Why it works** ...  **Blast radius** ...  **Risk** ...
**Test plan** ...  **Rollout and rollback** ...  **Data repair** ...  **Follow-up** ...

AS IS:
```mermaid
...
```
TO BE:
```mermaid
...
```
Caption (PT): ...

#### Option 2: ...

**Follow-ups outside the options** ...

### Português
(same content in Linguagem Simples)
````

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "There is one obvious fix." | Show it as the recommended option. Also show a containment and the hardening, so the user sees the choice. |
| "A workaround is fine for now." | Say how long, who owns it, and when it expires. A workaround with no owner stays forever. |
| "A guard at the symptom is enough." | It may hide the cause and let the same bug appear elsewhere. Say what stays open. |
| "I will estimate it as 2 hours." | Use S, M, or L with a range. False precision misleads. |
| "Four options look thorough." | Two good options beat four padded ones. The gate offers at most 4 choices. |
| "The test plan is obvious." | Name where the test sits, the edge cases, and what the test cannot catch. |
| "The cause is Likely, but I will write options as if it is certain." | State the label in the options. Offer the evidence option. |
| "I will start the fix, it is quick." | The user chooses first. Stop at the gate. |

## Red flags

- An option that does not remove the confirmed cause and is not labeled as containment.
- A containment with no owner and no expiry.
- An option with no test plan, or a test that the reproduction cannot show going green.
- Blast radius left out, or claimed small without having read the callers.
- Effort given as an exact number of hours.
- The two languages differ in options, numbers, or the recommendation.
- A TO BE diagram that shows a flow the code cannot do.
- A fix was written, applied, or committed.
- The options ignore the confidence label.
- A secret or personal data in a diagram or a script.

## Verification

- [ ] The options match the confirmed (or labeled) root cause, and each says why it works.
- [ ] There are 2 to 3 options. At least one fixes the cause, or the report says why none does.
- [ ] Containment options have an owner and an expiry.
- [ ] Each option has AS IS and TO BE diagrams, blast radius, risk, effort (S, M, or L), reversibility, a test plan, rollout and rollback, data repair, and a follow-up.
- [ ] The comparison table and the recommendation are present, with reasons and a condition for choosing differently.
- [ ] English and Portuguese carry the same options, numbers, and recommendation.
- [ ] Section 6 of `diagnosis.md` is written, and the options were shown in the chat.
- [ ] No fix was written. Nothing was committed.
