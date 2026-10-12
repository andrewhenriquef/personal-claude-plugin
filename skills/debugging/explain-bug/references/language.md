# Language rules: English and Portuguese

Use in Steps 1, 3, and 4 of `explain-bug` and `propose-solutions`. The rules come from `grammar-review` and `understand-the-intent` in this plugin.

Sources: [ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/), the Brazilian Rede Nacional de Linguagem Simples (Decreto 9.191/2017 principles), and ISO 24495-1 Plain Language.

## Do not call `grammar-review`

`grammar-review` is a tool for correcting text the user wrote. It is called only by name, by the user. Apply its rules here by writing the text in the right style from the start.

## Rules for both languages

- Short sentences, about 20 words or fewer. One idea per sentence.
- Active voice. Present tense where the statement is true now.
- One word for one meaning. Pick a glossary term and keep it. Do not rotate synonyms ("request", then "call", then "hit" for the same thing).
- Common words over rare ones. No jargon where a plain word works. Keep technical terms that engineers use (`race condition`, `nil`, `timeout`) and define a term the first time if the reader may not know it.
- Instructions, if any, in the imperative.
- Keep code, paths, commands, error strings, and identifiers exactly as they are.
- Say what you know and how you know it. Do not hedge every sentence. Put doubt in one place: the confidence label and the "Not verified" list.
- Never invent facts, numbers, or names.

## English: ASD-STE100

- Use approved meanings of words where you can. Use a verb for an action. Avoid noun clusters of more than three words ("user session token refresh failure" becomes "the token refresh for the user session fails").
- Use "the" and "a" (articles stay in English).
- Write one instruction or one fact per sentence. Do not join facts with a semicolon.
- Avoid phrasal verbs with several meanings (`bring up`, `set up`) when a simple verb fits (`start`, `configure`).
- Use "can" for ability and "must" for a requirement. Avoid "should" when you mean "must".
- Do not use idioms or figures of speech.
- Write numbers as digits.

Example:

> The service returns `500` for a refund of `0.00`. The code divides the refund by the order total. The order total is `0` in this case. The division raises `ZeroDivisionError`.

## Portuguese (Brazil): Linguagem Simples

- Ordem direta: sujeito, verbo, complemento.
- Frases curtas, voz ativa, palavras comuns.
- Prefira o verbo ao substantivo abstrato ("o serviço falha", não "ocorre a falha do serviço").
- Evite gerúndio em excesso e frases com muitas orações.
- Use o termo técnico que o time usa e o mantenha. Em código, mantenha o identificador como está.
- Use "você" ou a forma impessoal. Não use "o usuário" se o texto fala de um sistema.
- Use linguagem inclusiva só quando natural e simples ("a pessoa usuária"), sem deixar o texto pesado. Mantenha a mesma escolha no texto todo.
- Não traduza literalmente do inglês. Diga a mesma coisa do jeito que um colega diria.
- Escreva números com algarismos. Use vírgula decimal em texto corrido (`0,5 s`), e ponto no código.

Exemplo:

> O serviço devolve `500` quando o reembolso é `0,00`. O código divide o reembolso pelo total do pedido. O total do pedido é `0` nesse caso. A divisão gera `ZeroDivisionError`.

## When to relax the rules

Keep the rules unless a technical term, a quoted error, or a name needs a longer phrase. Keep it exact and say nothing extra around it.

## Glossary

Before you write, make a short table:

| Concept | English term | Termo em português | In the code |
|---|---|---|---|
| ... | ... | ... | `Identifier` |

Use the table in the text, in the diagram labels, and in the captions. Where the Portuguese keeps the English word (`timeout`, `cache`, `endpoint`), keep it in both.
