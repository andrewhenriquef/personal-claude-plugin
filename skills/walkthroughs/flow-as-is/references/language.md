# Language rules

Use in Steps 0, 7, 8, and 9 of `flow-as-is`. The rules come from `grammar-review` in this plugin. `explain-bug/references/language.md` has longer English and Portuguese examples.

Sources: [ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/), the Brazilian Rede Nacional de Linguagem Simples (Decreto 9.191/2017 principles), and [ISO 24495-1 Plain Language](https://www.iso.org/standard/78907.html).

## Do not call `grammar-review`

`grammar-review` corrects text the user wrote, and only the user calls it. Write the doc in the right style from the start.

## Pick the language

Write the doc and the chat report in the language of the user's request. Decide from the text. If it is mixed, use the dominant language and write the choice under "Assumptions". Apply the standard for that language:

| Language | Standard |
|---|---|
| English | ASD-STE100 Simplified Technical English |
| Portuguese (BR) | Linguagem Simples / Linguagem Clara |
| Spanish | Lenguaje Claro (ISO 24495-1) |
| Italian | Linguaggio Chiaro |
| Any other | ISO 24495-1 plain-language principles |

## Rules for every language

- Short sentences, about 20 words or fewer. One idea per sentence.
- Active voice. Present tense: the doc describes what the code does now.
- One word for one meaning. Use the glossary term every time, in the text, the diagrams, and the captions.
- Common words over rare ones. Keep the technical terms engineers use (`transaction`, `callback`, `goroutine`, `job`) and define a term the first time if a new reader may not know it.
- Keep code, paths, class and method names, commands, routes, and error strings exactly as they are in the code. Do not translate them.
- Say what you know and how you know it (`file:line`). Put doubt in one place: "Not verified" and "Assumptions".
- Never invent a fact, a number, or a name.

## English: ASD-STE100

- A verb for an action. No noun clusters of more than three words ("order payment capture retry" becomes "the job retries the payment capture for the order").
- Use "can" for ability and "must" for a requirement.
- No idioms. No phrasal verbs with several meanings when a simple verb fits.

## Portuguese (Brazil): Linguagem Simples

- Ordem direta: sujeito, verbo, complemento.
- Prefira o verbo ao substantivo abstrato ("o serviço grava o pedido", não "é realizada a gravação do pedido").
- Evite gerúndio em excesso e frases com muitas orações.
- Não traduza literalmente do inglês. Escreva como um colega explicaria.
- Mantenha o termo técnico que o time usa (`job`, `endpoint`, `callback`).

## Diagrams

Diagram labels use the doc's language for actions ("valida o pedido") and the code's names for participants and calls (`OrdersController#create`). Each diagram has a one-line caption in the doc's language that says what to notice.

## When to relax the rules

Keep the rules unless an identifier, a quoted error, or a domain term needs a longer phrase. Keep it exact, and say nothing extra around it.
