# diagnosis.md template

Copy this into `docs/<slug>/diagnosis.md` in Step 0. Each sub-skill fills its own section and nothing else. Sections that were not reached say `Not reached: <why>`.

Write the file in English. The English and Portuguese sections of the explanation and the options are written by `explain-bug` and `propose-solutions`.

````markdown
# Diagnosis: <short title>

- **Slug:** <slug>
- **Date:** <YYYY-MM-DD>
- **Commit:** <git rev-parse --short HEAD>
- **Status:** Intake | Hypotheses | Reproduced | Not reproduced | Root cause <Confirmed|Likely|Unconfirmed|Unreproduced> | Options ready | Option chosen
- **Needs from you:** <the open question for the user, or "nothing">
- **Run state:** `<git dir>/diagnose/<slug>/` (tree snapshot, backups of files edited during experiments)

## 1. Symptom card

- **Symptom:**
- **Expected:**
- **Actual:**
- **Trigger:**
- **Environment:**
- **Timeline:** first seen / last seen / frequency / last known good
- **Scope:**
- **Evidence:** (redacted; tool, query, time window)
- **Unknowns:**
- **Assumptions:**

## 2. Hypotheses

(written by `form-hypotheses`; updated by `reproduce-bug` and `confirm-root-cause`)

| ID | Hypothesis | Prediction (if true...) | Cheapest test | Confidence | Status |
|---|---|---|---|---|---|

### Experiment log

(one entry per experiment: hypothesis, change (one variable), predicted result, observed result, conclusion)

## 3. Reproduction

(written by `reproduce-bug`)

- **Command:** `<one command>`
- **Kind:** failing test | script | HTTP call | headless run | replay | harness | bisect
- **Files:** (test or script paths; left in the working tree, not committed)
- **Result:** red, matches the symptom: <the shortest decisive output lines>
- **Failure rate:** <k of N runs>
- **Minimal scenario:** <what is load-bearing>
- **Attempts:** (what was tried, in order)

## 4. Root cause

(written by `confirm-root-cause`)

- **Confidence:** Confirmed | Likely | Unconfirmed | Unreproduced
- **Proximate cause:**
- **Contributing factors:**
- **Latent conditions:**
- **Supporting experiment:**
- **Counter-checks:** (what could have disproved it, and did not)
- **Rejected hypotheses:** (ID and the observation that rejected it)
- **Probe tag:** `[DEBUG-xxxx]` (the tag used in this run)
- **Probes removed:** yes (the search for the tag outside `docs/<slug>/` shows none)
- **Fresh-context check:** <no point held | points that held, and how they changed the label | not available>

## 5. Explanation

(written by `explain-bug`: English, then Português)

## 6. Solutions

(written by `propose-solutions`: English, then Português)

## 7. Decision and handoff

(written at the gate)

- **Chosen option:**
- **Reproduction command:** `<command>` (must be red before the fix, green after)
- **Failing test location:** <path>, uncommitted
- **Root cause (one sentence):**
- **Seam note:** (does the test sit where the real bug pattern occurs? If no good seam exists, say so: it is a finding)
- **Test plan for the fix:** (the regression test, the extra cases)
- **Do not forget:** (cleanup, data backfill, monitor to add, follow-up ticket)
- **Next step:** write the fix, test first. Run the full suite after.
````
