---
name: find-variants
description: After a vulnerability is confirmed, search the repository for the same flaw elsewhere and ask the user whether the fix should cover the siblings. Defines the pattern in three parts (where untrusted input enters, the control that is missing or wrong, the code shape), runs grep and structural searches (the same helper, copied handlers, sibling routes, the same dependency call), classifies each candidate as Affected (a traced path from entry to the flaw, no guard, file and line), Possibly affected (one named condition), or Not affected (the guard, cited), says how the existing test would adapt, optionally asks security-analysis for a second view, presents the table, and asks which scope to fix: original only, original and all affected, or a chosen set. Read-only: applies no fix. Writes section 6 of docs/security/<slug>/diagnosis.md and the scope into the handoff. Use as step 6 of diagnose-vulnerability, or when the user asks "where else does this happen".
---

# Find Variants

> Evidence sources: variant-analysis practice from [Google Project Zero](https://googleprojectzero.blogspot.com/) root-cause write-ups (after one bug is understood, look for the same mistake in the same code, in copies, and in neighbors, because a patch for one instance is often bypassed by another) and from [CodeQL](https://codeql.github.com/) (a flaw is a query over code shape plus a data path), [CWE](https://cwe.mitre.org/) (the weakness class names the shape), and `security-analysis` in this plugin (its method for tracing a path and its false-positive rules). Structure follows `hypothesize-vulnerability`.

Find the other places where the same mistake lives, show them to the user with evidence, and ask how far the fix goes.

This skill is read-only. It does not fix a sibling and does not write its test. It records the user's decision for the fix step.

## Why this process

1. **A one-instance fix is a hope.** The flaw comes from a pattern. The next route with the same shape has it too.
2. **A search is not a finding.** A grep hit is a candidate. It is **Affected** only when you trace the path and see no guard.
3. **The user owns the scope.** More places mean a bigger change and a bigger review. Show the list and ask.
4. **The shared place may be the fix.** If five routes miss the same check, a middleware or a policy may fix all five. Say so to the next step.

## When to use

- Step 6 of `diagnose-vulnerability`, in Exploited mode, with a confirmed or likely cause.
- The user asks "where else does this happen" for a flaw that is already understood.

## When NOT to use

- The cause is Unconfirmed. Go back to `confirm-vulnerability-cause`. A pattern from a guess finds guesses.
- The verdict is Not exploitable. There is no flaw to look for. (The control may be missing elsewhere. That is a review: use `security-analysis`.)
- The user wants a general security review of the repository. Use `security-analysis`.

## Process

### Step 0: Read

0. If `docs/security/<slug>/diagnosis.md` does not exist (this skill was called alone), pick a slug, run Step 0 of `diagnose-vulnerability`, and create the file from [the template](../diagnose-vulnerability/references/diagnosis-template.md). Ask the user only when a missing fact blocks this skill, once, with `AskUserQuestion` (`AskQuestion` in Cursor). Otherwise go on, and write each guess under **Assumptions**.
1. Read the cause in section 5 (the proximate cause, the contributing factors, the latent conditions), the test, and the hypotheses. Read the code of the confirmed flaw again.

### Step 1: Define the pattern

Write it in `diagnosis.md` in three parts:

- **Entry:** where untrusted input or an untrusted caller comes in (a route with an ID param, a file path param, a job payload).
- **Missing control:** what should stand between the entry and the effect (an ownership check, a parameterized query, an allow-list).
- **Shape:** how the code looks (a `find(params[:id])` with no scope, string interpolation inside a query, a handler that skips the policy call).

Then write 2 to 4 searches that follow from it:

1. The **same call** or helper in other files (`git grep -n`, or a structural search with `ast-grep` or `semgrep` if the project has it).
2. **Copies:** handlers or methods with the same body (the history of the file may show the copy: `git log --follow`).
3. **Siblings:** other routes of the same controller, router, or module, and whether each calls the check.
4. **Callers** of the flawed function: a public entry that reaches it by another path.
5. **Dependency findings:** every call of the vulnerable function of the package, and every other package version in a monorepo or a lockfile.

### Step 2: Search

Run the searches read-only. Show the commands. If a search returns more than about 30 hits, narrow it with the missing-control condition, or use a read-only subagent (`Explore` in Claude Code, a read-only Task in Cursor) and ask for file and line only. Do not paste whole files.

### Step 3: Classify each candidate

Read each candidate's path from the entry to the effect. Classify it:

| Status | Rule |
|---|---|
| **Affected** | You traced the path from the entry to the effect, with file and line, and found no guard. |
| **Possibly affected** | The path exists, and one named condition decides (a role, a setting, a data state). Write the condition. |
| **Not affected** | A guard exists on the path. Cite it with file and line. |

For each Affected or Possibly one, write how the existing test would adapt: "same test, route `X`, same actors" or "needs a different role". Do not write the test.

Optional second view: call `security-analysis` on the Affected files (**Claude Code:** `Skill(skill: "security-analysis")`; **Cursor:** read and follow its `SKILL.md`), limited to the pattern. Treat its findings as candidates and check each one the same way.

### Step 4: Present, and ask

1. Write the table into section 6 of `diagnosis.md`.
2. Show it in the chat: location, status, the evidence in one line, and how the test adapts. Put Affected first. Say how many siblings are Affected, Possibly, and Not affected. Say whether one shared place could fix all of them.
3. If there are **no** Affected or Possibly affected siblings, say so, record "no siblings found" with the searches you ran, and go on. Do not ask.
4. Otherwise ask, with `AskUserQuestion` (`AskQuestion` in Cursor), in one question: **"Should the fix cover the siblings too?"**
   - **Original and all affected siblings** (recommended when any is Affected).
   - **Original only.** The siblings go in the follow-ups of the handoff, with the table.
   - **Let me pick.** The user names the siblings in the answer. List them in the chat first, numbered.
5. Write the decision into section 6 (`User decision`). It goes into the handoff as the **Scope**.

Say to the user in one line what the decision means: nothing is changed now. The fix step, `tdd-development`, writes one red test for each sibling in scope before it changes the code, and the options in the next step take the scope into account.

## Output

```
## Variants: <slug>

Pattern: entry <...>; missing control <...>; shape <...>
Searches: <commands>

| Location | Status | Evidence | Test adapts by |
|---|---|---|---|
| app/.../x.rb:41 | Affected | entry -> ... -> sink, no guard | same test, route /x |
| app/.../y.rb:12 | Not affected | guard at policies/y.rb:8 | - |

Shared fix place: <a middleware, policy, or helper that covers N of them | none>
User decision: <original only | original and all affected | picked: ... | no siblings found>
```

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The grep found 12 hits, so there are 12 bugs." | Hits are candidates. Trace each one. |
| "It is the same code, so it must be vulnerable." | A guard in the caller may protect it. Cite it or call it Affected. |
| "I will fix the siblings now, it is quick." | This skill is read-only. The user decides the scope, and the fix has its own tests. |
| "No other hits, so there are no siblings." | The shape may differ (a copy with another name). Try the history and the callers. |
| "The user will want all of them." | Ask. A bigger change is a bigger review. |

## Red flags

- A candidate marked Affected with no traced path and no file and line.
- A candidate marked Not affected with no cited guard.
- Code was changed, or a sibling test was written.
- The user was not asked, and the scope was assumed.
- Whole files or full search output pasted into the chat.
- The pattern was taken from an Unconfirmed cause.

## Verification

- [ ] The pattern is written as entry, missing control, and shape.
- [ ] The searches that ran are listed, with their commands.
- [ ] Each candidate has a status and evidence with file and line.
- [ ] The table is in `diagnosis.md` and was shown in the chat.
- [ ] The user was asked about the scope, or "no siblings found" is recorded with the searches.
- [ ] The decision is written in section 6, for the handoff.
- [ ] No code or test was changed. Nothing was committed.
