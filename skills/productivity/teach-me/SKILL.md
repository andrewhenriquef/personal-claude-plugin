---
name: teach-me
description: Create a teaching presentation or explanation as one HTML page, built from videos, official documentation, and articles, with the text written in plain language. Detects the language of the request and applies that language's plain-language standard (ASD-STE100 for English, Linguagem Simples for Brazilian Portuguese, and others). Use when the user asks to study a topic, "explain from the basics", build animated slides, or turn sources (links, videos, summaries) into learning material. The material is written in the language of the request.
---

# Teach Me

> Evidence sources: [ASD-STE100](https://www.asd-ste100.org/), the Brazilian Linguagem Simples rules (Rede Nacional de Linguagem Simples, Decreto 9.191/2017), [ISO 24495-1](https://accessible-eu-centre.ec.europa.eu/content-corner/digital-library/iso-24495-12023-plain-language-part-1-governing-principles-and-guidelines_en) (plain language: governing principles and guidelines), and the [Unicamp Linguagem Simples guide](https://linguagemsimples.unicamp.br/arquivo/uploads/guia-de-linguagem-simples). The language table is shared with `grammar-review` and `explain-bug` in this plugin. Related skills for the page format: [codebase-to-course](https://www.sourcepulse.org/projects/26812814) (interactive HTML course), [explainer-design-system](https://www.skillsdirectory.com/skills/josix-explainer-design-system), and [plain](https://www.skills.sh/shihyuho/skills/plain) (plain-language rewrite).

Turn a topic and a few sources into a teaching HTML page, with animations and diagrams, written so that anyone understands it.

## When to use

- The user wants to learn a subject and asks for a presentation, a guide, or an "explainer".
- The user sends links (videos, articles, documentation) and asks to join them into one material.
- The user asks to rewrite a technical text in plain language.

## When NOT to use

- Formal legal texts, contracts, or documents that need official wording.
- The user wants only a grammar fix of a short text. Use `grammar-review`.
- The user wants to understand the code of the current project. Use `flow-as-is` (one flow) or `flow-diff` (what a branch changes).
- The user wants a diagnosed bug explained. Use `explain-bug`.

## Process

Follow the steps in order. Say in one sentence what you will do before you start.

### Step 1: Understand the request

- Find the topic, the audience, and the format (HTML page, slides, document).
- If the request is clear, start without asking. If something that changes the result is missing, ask one question.
- Assume the audience is smart but new to the subject.

### Step 2: Read the sources the user sent

- Open each link. For videos, try to get the transcript.
- If a site blocks reading, use only what shows (title, channel, description, chapters). **Tell the user as soon as you know.** Never invent the content of a video.
- If the user sends summaries or transcripts made by another tool, use them. Mark in the material that they come from a third party and that you did not check them against the original source.

### Step 3: Research references

- Start with the official documentation. Then use articles, guides, and blog posts.
- For each tool or product you name, read its official page. Never write numbers, limits, or command names from memory.
- Note the date of each lookup. Product information changes fast.
- When two sources disagree, show the difference. Do not choose in silence.

### Step 4: Plan the structure

Use this order, from the simplest to the most advanced:

1. Cover with the promise of the material.
2. A short glossary, at the start. Each technical term has a one-sentence definition.
3. The problem: why the subject matters (answer "why should I care?" before "how does it work?").
4. The basics: the concept, the main commands or steps, with examples.
5. How it works inside (only what helps the reader use it).
6. The subject applied to the reader's context (tools, real cases).
7. Practice: step-by-step flow, good practices, and traps.
8. Sources.

Each slide holds one idea. Group the slides into parts and give each part a real name (for example "Basics", "Tools", "Practice"). Do not number parts only for decoration.

### Step 5: Write in plain language

**Pass 1: detect the language.** Decide from the text itself. Do not ask. If the text is very short or mixes languages, pick the dominant language and record the assumption. The material is written in that language.

**Pass 2: apply the standard of the language.**

| Language | Standard to follow |
|---|---|
| English | ASD-STE100 Simplified Technical English |
| Portuguese (Brazil) | Linguagem Simples / Linguagem Clara (Rede Nacional de Linguagem Simples and the principles of Decreto 9.191/2017) |
| Spanish | Lenguaje Claro (ISO 24495-1) |
| Italian | Linguaggio Chiaro / Semplice |
| Any other language | General plain-language principles (ISO 24495-1) |

**Practical rules (all languages):**

- Write short sentences, up to about 20 words, one idea each.
- Use direct order: who does, what they do, details.
- Prefer the active voice.
- Replace nouns that hide the action with verbs. In Portuguese, "fazer a remoção" becomes "apagar".
- Use everyday words. Avoid foreign words and jargon when a common equivalent exists.
- Explain acronyms and technical terms the first time they appear, and in the glossary.
- Use the same term for the same thing. Do not rotate "folder", "directory", and "pasta".
- Use bullets when there are three or more items. Use a table to compare.
- Put first what the reader needs to know or do.
- Do not trade clarity for vagueness. Keep all facts, numbers, and commands.

**Before and after examples (Brazilian Portuguese):**

| Before | After |
|---|---|
| A realização da limpeza é efetuada automaticamente pelo aplicativo. | O aplicativo faz a limpeza sozinho. |
| É imprescindível a verificação do estado do repositório previamente à execução. | Antes de rodar, confira o estado do repositório. |
| Os arquivos ignorados não são propagados ao novo checkout. | O Git não copia arquivos ignorados para a nova pasta. |

**When you rewrite an existing text**, also deliver a short list of the main corrections. Record the assumptions (for example, the detected language).

### Step 6: Build the page

Deliver one HTML page, with no external files except allowed fonts and libraries.

- **Navigation:** keyboard arrows, buttons, dots, and swipe on mobile. Show the slide number and a progress bar.
- **Animations:** use CSS and SVG, and respect `prefers-reduced-motion`. The page must be complete on load. The animation only shows how the idea works. It never hides the text.
- **Diagrams:** draw in SVG to show the real mechanism (for example, one folder linked to several agents). Give each thing a color with a function. Example: when you explain Git worktrees, each worktree gets its own color, like the lines of a subway map.
- **Interactive terminal:** for commands, use tabs and an output that appears line by line. Mark outputs you wrote from memory.
- **Tables:** use them to compare tools, always with the same criteria in the rows.
- **Themes:** define colors as variables and design both the light and the dark theme.
- **Mobile:** the page must work at about 400 px wide, with no horizontal scroll. Tables and code scroll inside their own box.
- **Images:** do not depend on external images. Draw diagrams in SVG.
- **Typography:** a pair of fonts with personality (headings and text) and a monospace font for code.

### Step 7: Review

Before you deliver, check:

- [ ] Each fact, number, and command matches the source. Nothing comes from memory without a notice.
- [ ] No sentence is longer than about 20 words (outside code and terminal output).
- [ ] Each technical term is explained and always appears with the same name.
- [ ] The examples you made up are marked as "example".
- [ ] Third-party summaries are marked as not verified.
- [ ] The JavaScript syntax is correct.
- [ ] The page works on a small screen and in both themes.
- [ ] The links in the sources section open the right pages.

### Step 8: Deliver

- Say in one or two sentences what is ready.
- List the limits: what you could not read, what you did not check, what you wrote from memory.
- Suggest a next step, if one is clear (for example, a quiz at the end).
- End with the list of sources.

## Honesty rules

- Never invent the content of a video or a page you could not read.
- Never state a product number or limit without a dated source.
- Keep apart what comes from official documentation, from a third-party article, and from a summary made by another tool.
- If the user corrects something, fix the page and say what changed.

## Optional ideas

- **Short quiz** at the end of each part, covering application and not memorization.
- **Glossary tooltip:** the term shows its definition on hover or tap.
- **Side-by-side translation:** show the code or command and, next to it, what it does in one sentence.
- **One analogy per concept,** without repeating the same analogy in different parts.
