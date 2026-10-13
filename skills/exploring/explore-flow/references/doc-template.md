# Flow doc template

Use in Steps 0 and 7 of `explore-flow`. Create the file at Step 0 and fill it as you go. Write the headings in the doc's language (the Portuguese headings are in brackets). Remove the bracket text and the instructions in `<>`.

````markdown
# <Flow name> flow [Fluxo de <nome>]

- **Question:** <the one-sentence question from Step 0>
- **Commit:** `<short sha>` <"clean tree" or "with uncommitted changes">
- **Date:** <YYYY-MM-DD>
- **Status:** exploring | done
- **Scope:** starts at <entry point>, ends at <end boundary>. Out of scope: <list>.

## Summary [Resumo]

<3 to 5 sentences: what triggers the flow, what it does, what it changes, where it can fail.>

## Start here [Comece por aqui]

<3 to 6 files a reader opens first, each with one line on why.>

- `path/to/entry.rb:12`: the entry point.

## Glossary [Glossário]

| Term | Meaning | In the code |
|---|---|---|
| <term> | <one line> | `Identifier` |

## Overview [Visão geral]

```mermaid
sequenceDiagram
  ...
```

<Caption: what to notice.>

## Parts [Partes]

### 1. <Verb phrase: "Validate the request">

- **Where:** `file:line` to `file:line`
- **Input → output:** <...>

```mermaid
sequenceDiagram
  ...
```

<Caption.>

**Steps [Passos]**

1. <One hop per line, with `file:line`.>

**Decisions [Decisões]:** <condition from the code, what each branch does, and why if the code, a commit, or an ADR says; else "The code does not say why".>

**Errors [Erros]:** <what fails, where it is handled, what the caller sees.>

**Data changes [Mudanças de dados]:** <tables, columns, caches, events, jobs, external calls.>

**Tests [Testes]:** <`spec/...:line` "it ..." pins <behavior>. Or "No test found (searched: `rg -n ...`)".>

### 2. <...>

## Cross-cutting behavior [Comportamentos transversais]

<Only what the trace shows: auth, transactions, locks, retries, idempotency, feature flags, logging, metrics. Each with `file:line`.>

## Observations [Observações]

<Facts only, no fix: untested branches, swallowed errors, TODOs, side effects inside a transaction, behavior that surprised you. Each with `file:line`.>

## Not verified [Não verificado]

<Each claim you could not confirm, and where you searched. "Nothing" if empty.>

## Assumptions [Suposições]

<Each guess you made instead of asking, and why. "None" if empty.>

## Appendix: hop table [Apêndice: tabela de passos]

| # | From | To | Where | Input → output | Side effect | Decision / error |
|---|---|---|---|---|---|---|
````
