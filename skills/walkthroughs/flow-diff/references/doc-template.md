# Change doc template

Use in Steps 0 and 7 of `flow-diff`. Create the file at Step 0 and fill it as you go. Write the headings in the doc's language (the Portuguese headings are in brackets). Remove the bracket text and the instructions in `<>`.

````markdown
# <Title: what the change does, imperative, stands alone>

- **Ticket / PR:** <tag, PR number and URL, or "none">
- **Base:** `<main branch>` @ `<base sha>` <add "main has moved past the base in changed files" if true>
- **Head:** `<branch>` @ `<head sha>` <add "plus uncommitted work" if in scope>
- **Date:** <YYYY-MM-DD>
- **Status:** exploring | done
- **Scope:** <N> files in <M> units. Set aside: <generated or vendored files, or "none">.

## General context [Contexto geral]

**The problem [O problema]:** <what was wrong or missing before. "Stated in <source>" or "Inferred from <evidence>".>

**What changed [O que mudou]:** <the approach, 2 to 3 sentences.>

**What the changes indicate [O que as mudanças indicam]:** <impact a reader must know: caller-visible behavior, data and migrations, contracts, dependencies, flags and rollout. Each with `file:line`, or "(inferred)".>

**Divergences [Divergências]:** <where the PR text or a commit says one thing and the code does another. "None found" if empty.>

<Optional change map, when there are 3 or more units.>

## Reading order [Ordem de leitura]

1. <Unit 1 name>: open `path/to/file:line` first.
2. <...>

## 1. <Unit name: verb phrase> — <changed flow | new flow | removed flow>

<Short context, 2 to 4 sentences: what this flow does, what changes, and why.>

**Files [Arquivos]:** `path/a.rb`, `path/b.rb`, `spec/...`

### <Scenario: what happens, e.g. "The refund goes through"> [Cenário]

<Repeat this block for each scenario of the flow: the main path, and each branch and error path. No `alt`, `opt`, or `else`. Title each scenario with a short description of what happens, not with a letter or a number. A scenario with stages of its own gets one pair per stage, each titled with what the stage does. Omit the AS IS of a new scenario and the TO BE of a removed one, and say so in one line.>

#### AS IS (`<main branch>` @ `<base sha>`)

```mermaid
sequenceDiagram
  ...
```

<Caption.>

#### TO BE (this branch)

```mermaid
sequenceDiagram
  ...
```

<Caption.>

**Differences [Diferenças]**

- <Added / removed / changed hop, with `path:line` (TO BE) and `path:line @ <base sha>` (AS IS).>

**Tests [Testes]:** <added, changed, or deleted tests, and the behavior each pins. Or "No test found (searched: `rg -n ...`)".>

## 2. <...>

## Other changes [Outras mudanças]

| File | Change | Why it has no flow section |
|---|---|---|
| `config/x.yml` | <one line> | <config with no behavior effect / rename / dependency bump / docs> |

## Observations [Observações]

<Facts only, no fix: changed behavior with no test, deleted or loosened assertion, removed check, migration without backfill, work moved inside or outside a transaction. Each with `file:line`.>

## Not verified [Não verificado]

<Each claim you could not confirm, and where you searched. "Nothing" if empty.>

## Assumptions [Suposições]

<Each guess you made instead of asking, and why. "None" if empty.>
````
