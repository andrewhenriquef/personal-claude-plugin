---
name: grammar-review
description: Review and correct text for grammar, spelling, and clarity in any language (English, Portuguese, Spanish, Italian, and others). Detects the input language automatically, then rewrites using that language's plain-language standard, keeping the original tone, accent, and mood. Falls back to natural complexity only when formal context needs it. Use when the user pastes text and asks to review, correct, fix grammar, or check their writing.
disable-model-invocation: true
model: haiku
effort: medium
---

Review the user's text for grammar, spelling, word choice, and clarity, in whatever language it is written.

## Step 1: Detect the language

Identify the language of the input before doing anything else. Do not ask the user — decide from the text itself. If genuinely ambiguous (very short text, mixed languages), pick the dominant language and note the assumption in the corrections list.

## Step 2: Apply the plain-language standard for that language

Simplify using the closest recognized plain-language standard for the detected language:

| Language | Standard to follow |
|----------|--------------------|
| English | ASD-STE100 Simplified Technical English |
| Portuguese (BR) | Linguagem Simples / Linguagem Clara (Brazil's Rede Nacional de Linguagem Simples, Decreto 9.191/2017 principles) |
| Spanish | Lenguaje Claro (ISO 24495-1 Plain Language) |
| Italian | Linguaggio Chiaro / Semplice |
| Any other language | General plain-language principles (ISO 24495-1): short sentences, active voice, common everyday vocabulary, one term for one meaning |

Common rules across all languages, regardless of which standard applies:

- Short sentences (~20 words max), active voice, present tense where true.
- One word for one meaning — don't rotate synonyms for the same concept.
- Plain, common vocabulary over rare or ornate words. No unnecessary jargon.
- Fix grammar, spelling, and punctuation errors as part of the same pass.

## Rewrite rules

- Keep the original tone, accent, and mood exactly. Do not flatten a casual, warm, blunt, or playful message into something neutral or robotic. Simplify the language, not the personality.
- Switch away from strict plain-language rules only when context demands it: formal emails, legal/contractual language, academic writing, idioms load-bearing to the message's tone, or set phrases that would sound broken if simplified. In those cases, keep the needed complexity and say why in the notes.
- Never change the meaning, add content, or remove information the user included on purpose.
- Never translate. Output stays in the same language as the input.
- If the text is already correct and already simple, say so — don't invent changes.

## Output format

Always output in this order, nothing before it:

1. **Corrected phrase** — the full corrected text, in the original language, ready to send, on its own.
2. **Corrections** — a short list of what changed and why. One line per fix: `original → corrected — reason`. Group grammar/spelling fixes separately from simplification changes if both happened. Note the detected language, and any place where the plain-language standard was intentionally skipped and why.

Keep the corrections list terse. Skip it entirely only if nothing changed.
