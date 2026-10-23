# Portabilidade das skills para o Cursor

Os ajustes das seções 1 a 7 deste documento foram aplicados no código (plugin 1.32.0).

Análise das 33 skills deste plugin, em 22 de outubro de 2026. O objetivo é deixar o mesmo fluxo disponível no Claude Code e no Cursor, com um único `SKILL.md` por skill.

## O que o pacote já faz

Os dois manifests apontam para a mesma pasta `skills/`. Instalar o plugin no Cursor já entrega as 33 skills e os 7 agents. `scripts/sync_cursor.py` gera `.cursor-plugin/` a partir de `.claude-plugin/`, `.mcp.json` e `agents/`. As skills em si não passam por esse script: o texto do `SKILL.md` é compartilhado.

Três diferenças de ferramenta explicam quase todos os buracos:

| No Claude Code | No Cursor | Efeito quando o texto cita só o lado do Claude |
|---|---|---|
| `Skill(skill: "nome")` | Não existe. O agente lê o `SKILL.md` pelo nome | O passo que chama outra skill para, ou o agente reimplementa o fluxo de memória |
| `AskUserQuestion` | `AskQuestion` | A pergunta vira texto solto. Some o limite de opções, a opção recomendada e a resposta "Other" |
| `Agent(subagent_type: ...)` | Task tool, com o mesmo nome de subagent | O fan-out paralelo não dispara |

Agents gerados já reescrevem chamadas `Skill`. O `product-designer` gerado não entrevista: no Cursor a entrevista fica na thread principal (`feature-planning`, Step 0). Isso já está feito.

`model` e `effort` no frontmatter valem no Claude Code. O Cursor ignora esses campos e usa o modelo da conversa. `disable-model-invocation: true` vale nos dois: a skill só entra quando é nomeada.

O spec de skill que o Cursor documenta limita `description` a 1024 caracteres. Duas skills passam desse teto. O restante do texto de disparo fica no fim da frase, que é a parte que some se o loader cortar.

Dependência externa: `feature-planning` chama `prd-development` e `user-story`, do marketplace `pm-skills` (deanpeters/Product-Manager-Skills, licença CC BY-NC-SA 4.0). Elas não entram neste repositório. No Claude Code a instalação é `/plugin install`. No Cursor não há dependência entre plugins, e nesta máquina as duas pastas não estão em `~/.cursor/skills`. Vendorizar os arquivos aqui misturaria essa licença com o MIT deste repo.

Datadog é opcional nos dois. Se as ferramentas de leitura não estão na sessão, o diagnóstico segue e escreve "No Datadog data". `mmdc` (mermaid-cli) também é opcional nos dois: sem ele, a validação do diagrama é manual.

## Como cada skill foi classificada

- **Funciona nos dois.** O fluxo fecha com as ferramentas que o Cursor tem, e onde a ferramenta difere o texto já diz o que fazer.
- **Funciona e ainda precisa de ajuste.** O fluxo roda, e um passo ainda cita só a ferramenta do Claude, estoura o limite da description, ou perde um pedaço quando a skill roda dentro de um subagent.
- **Não fecha no Cursor.** O arquivo está no plugin, e o fluxo para antes do artefato final.

## Funcionam nos dois

Dezenove skills. Nenhuma mudança é necessária para o caminho feliz.

| Skill | Por que fecha |
|---|---|
| `interview` | Pergunta com `AskUserQuestion` no Claude e `AskQuestion` no Cursor. Fatos vão para um subagent `Explore` via `Agent` ou Task. |
| `understand-the-intent` | Mesma convenção de pergunta e de exploração que `interview`. |
| `grammar-review` | Só reescreve texto. `disable-model-invocation` evita disparo acidental nos dois. No Claude o frontmatter pede Haiku; no Cursor vale o modelo da conversa. |
| `teach-me` | Lê links, escreve um HTML e um quiz. Não cita ferramenta exclusiva. |
| `design-doc-mermaid` | Guias e scripts Python. `mmdc` é opcional nos dois. O `SKILL.md` tem 519 linhas, acima da recomendação de 500 do Cursor. O fluxo de gerar o diagrama não depende disso. |
| `code-simplify` | Edição local, sem outra skill e sem pergunta estruturada. |
| `security-analysis` | Leitura e relatório. Subagent só quando há muitos candidatos, com frase genérica ("quando a ferramenta tiver subagents"). |
| `static-analysis` | Roda o linter do projeto. |
| `test-analysis` | Leitura dos testes do diff. |
| `data-and-migration-analysis` | Leitura de migrations e de código de dados. |
| `dependency-analysis` | Leitura de manifests e de advisories. |
| `performance-analysis` | Medição local. |
| `reliability-analysis` | Leitura. A description tem 1001 caracteres, perto do teto de 1024. |
| `flow-as-is` | Pergunta dual. Regiões grandes vão para `Explore` via Task. |
| `flow-diff` | Igual a `flow-as-is`, sobre o diff. |
| `scan-pipelines` | Inventário só de leitura. Pesquisa de ferramenta via `gh` ou `curl`. Fan-out já cita `Agent` e Task. |
| `document-pipelines` | O passo que chama `build-pipelines` tem ramo explícito Claude e Cursor. |
| `run-pipelines` | O passo que chama `document-pipelines` tem ramo explícito. |
| `github-pipelines` | Os passos que chamam `document-pipelines` e `scan-pipelines` têm ramo explícito. |

## Funcionam e ainda precisam de ajuste

Treze skills. Cada uma roda hoje. O ajuste é para o passo frágil deixar de depender de o agente "adivinhar" o equivalente no Cursor.

### `product-interrogatory`

O preâmbulo manda ler o `SKILL.md` de `interview` no Cursor. Os quatro passos ainda dizem `Call Skill(skill: "interview", ...)`.

**Fazer:** em cada passo, a mesma frase dupla que `document-pipelines` já usa. Claude chama `Skill`. Cursor lê e segue `skills/productivity/interview/SKILL.md`.

### `implementation-planning`

O preâmbulo cobre a ausência do `Skill` tool, e o fan-out do `senior-dev` já cita Task. As chamadas de `interview` e de `design-doc-mermaid` continuam escritas só como `Skill(...)`. `model: opus` e `effort: high` não mudam o modelo no Cursor.

**Fazer:**

- Reescrever cada chamada (`interview` duas vezes, `design-doc-mermaid` duas vezes) no formato duplo, no próprio passo.
- Deixar `model` e `effort` no arquivo. Eles continuam valendo no Claude. Uma linha no passo 0 registra que no Cursor o modelo é o da conversa.

### `tdd-development`

A pergunta bloqueante já cita os dois tools, e o preâmbulo cobre `Skill`. As chamadas de `interview`, `run-pipelines` e `static-analysis` continuam como `Skill(...)`. A description tem 1160 caracteres.

**Fazer:**

- Encurtar a description para menos de 1024 caracteres, com os gatilhos ("TDD", "tests first", "red green refactor", "failing test first") no começo da frase.
- Reescrever as três chamadas no formato duplo.

### `tech-debt-analysis`

O fan-out de repositório grande já cita Task. A description tem 1417 caracteres, a maior do plugin. Os gatilhos de "broken windows" e de modo Repo/Change ficam no fim.

**Fazer:** encurtar a description para menos de 1024 caracteres. Manter no início: debt, hotspot, broken windows, `docs/tech-debt.md`, Repo mode, Change mode.

### `build-pipelines`

A cadeia `scan-pipelines` já tem ramo Cursor. O passo que escolhe as ferramentas pede um `AskUserQuestion` e não cita `AskQuestion`. Com mais de quatro perguntas o texto só descreve o limite do Claude.

**Fazer:** pedir a rodada única com `AskUserQuestion` no Claude e `AskQuestion` no Cursor. Manter a regra de no máximo quatro perguntas por chamada no Claude, e emitir as chamadas extras em sequência, sem outro trabalho no meio. No Cursor, uma chamada pode levar a rodada inteira; se a ferramenta recusar, partir do mesmo jeito.

### Pipeline de debug

| Skill | O que falta |
|---|---|
| `form-hypotheses` | Pergunta bloqueante só com `AskUserQuestion`. |
| `reproduce-bug` | Idem. O browser headless segue sendo um script do projeto; os dois harnesses rodam esse script no shell. |
| `explain-bug` | Idem. |
| `propose-solutions` | Idem. A escolha da opção fica em `diagnose-and-reproduce`. |
| `confirm-root-cause` | A checagem de contexto fresco já cita `Agent` e Task. A pergunta bloqueante não cita `AskQuestion`. |
| `diagnose-and-reproduce` | O preâmbulo cobre `Skill`. Os cinco passos ainda dizem `Run Skill(skill: "...")`. As duas perguntas (dado que bloqueia, e qual opção de correção) citam só `AskUserQuestion`, inclusive o limite de 4 opções. |

**Fazer:**

- Nos seis arquivos, a pergunta bloqueante cita os dois tools, como `flow-as-is` já faz.
- Em `diagnose-and-reproduce`, cada um dos cinco passos ganha o ramo Cursor: ler e seguir o `SKILL.md` da skill filha (`form-hypotheses`, `reproduce-bug`, `confirm-root-cause`, `explain-bug`, `propose-solutions`).
- A escolha da correção usa `AskQuestion` no Cursor, com uma opção por solução, a recomendada primeiro, e "I need more evidence" quando couber. "Stop here" continua sendo a resposta livre.

### `harness-code-review`

Sozinha, na thread principal, fecha nos dois. No Claude chama `code-review` e, no modo fix, `simplify`. No Cursor sobe `bugbot` e `security-review` juntos e, no modo fix, segue `code-simplify`.

Dentro de `complete-code-review` ela roda no subagent `code-reviewer`. Um subagent do Cursor não sobe outro subagent. O texto já prevê isso e grava "native reviewer unavailable". O resultado é um relatório sem o review nativo, toda vez que a orquestração pede essa lente.

**Fazer:** no Cursor, `complete-code-review` roda `harness-code-review` na thread principal, antes de spawnar os `code-reviewer`. O prompt desse passo repete o escopo e "Do not edit the working tree". As outras lentes continuam cada uma no seu `code-reviewer`. No Claude, `harness-code-review` continua dentro do `code-reviewer`, porque lá o `Skill` tool de `code-review` existe dentro do subagent.

### `complete-code-review`

O spawn de `code-reviewer` e de `code-developer` já cita Task, e os agents gerados leem o `SKILL.md` em vez de chamar `Skill`. Dois furos permanecem.

**Fazer:**

- Aplicar o desvio da lente `harness-code-review` descrito acima. O ledger e a checagem da working tree continuam iguais: a lente nativa também entra no diretório da run e no snapshot.
- Registrar no relatório que, no Cursor, o modelo dos agents é o da conversa (`inherit` no agent gerado). No Claude, review segue Opus e apply segue Sonnet, como os agents de origem pedem. Não trocar o `MODEL_MAP` agora: fixar um id de modelo quebra quando a conta não tem esse id.

## Não fecha no Cursor

### `feature-planning`

O arquivo está no plugin e o Step 0 do Cursor já está escrito: a descoberta roda nesta thread com `interview`, sem spawnar `product-designer`. O Step 4 sobe `pm-reviewer`, `tech-lead-reviewer` e `qa-reviewer` pelo Task tool, e esses agents existem em `.cursor-plugin/agents/`.

O fluxo para nos Steps 1 e 5:

1. Step 1 chama `Skill(skill: "prd-development")`.
2. Step 5 chama `Skill(skill: "user-story")`.

Nenhuma das duas está neste plugin. No Claude Code elas são plugins separados do marketplace `pm-skills`. No Cursor o README manda copiar as pastas para `~/.cursor/skills`, e essa cópia não está feita. Sem os arquivos, o agente não tem o procedimento do PRD nem o das stories, e `docs/<TAG>/PRD.md` e `docs/<TAG>/user_story_<N>.md` não saem.

`model: opus`, `effort: high` e `disable-model-invocation: true` ficam. O último é desejado nos dois: a skill só roda quando nomeada.

**Fazer:**

1. Não copiar `prd-development` nem `user-story` para este repositório. A licença delas é CC BY-NC-SA 4.0.
2. Acrescentar `scripts/install_cursor_pm_skills.sh`. O script clona `deanpeters/Product-Manager-Skills` em um diretório temporário e copia só `skills/prd-development` e `skills/user-story` para `~/.cursor/skills/`. Idempotente. O README troca o bloco manual de três linhas por este comando, e mantém os três comandos `/plugin` do Claude Code.
3. Nos Steps 1, 2 e 5, escrever o ramo no próprio passo. Claude: `Skill(skill: "prd-development")` e `Skill(skill: "user-story")`, e `Skill(skill: "interview")` nos gaps. Cursor: ler `~/.cursor/skills/prd-development/SKILL.md`, `~/.cursor/skills/user-story/SKILL.md` e `skills/productivity/interview/SKILL.md`.
4. Se o `SKILL.md` externo não existir, parar nesse passo e mostrar o comando de instalação do harness atual. Não redigir o PRD nem as stories de memória.
5. O Step 0 e o Step 4 ficam como estão.

As duas skills externas são markdown de workflow. Elas não chamam `Skill`, `AskUserQuestion` nem `Agent`. Uma vez copiadas, o Cursor consegue seguí-las. O frontmatter extra delas (`intent`, `type`, `theme`, `best_for`, `scenarios`, `estimated_time`, `argument-hint`) pode permanecer: o loader usa `name` e `description`.

## Plano de ações

Ordem pensada para cada fase deixar o plugin instalável nos dois lados antes da fase seguinte. Skills e agents continuam com uma fonte só. Nada em `.cursor-plugin/` é editado à mão.

### Fase 1. Perguntas estruturadas

Arquivos:

- `skills/debugging/form-hypotheses/SKILL.md`
- `skills/debugging/reproduce-bug/SKILL.md`
- `skills/debugging/confirm-root-cause/SKILL.md`
- `skills/debugging/explain-bug/SKILL.md`
- `skills/debugging/propose-solutions/SKILL.md`
- `skills/debugging/diagnose-and-reproduce/SKILL.md`
- `skills/continuous-integration/build-pipelines/SKILL.md`

Em cada pergunta bloqueante, usar a frase já estável de `flow-as-is`: uma chamada, todas as perguntas juntas, `AskUserQuestion` no Claude Code e `AskQuestion` no Cursor, candidatos como opções, a recomendada primeiro com o rótulo "(Recommended)".

Critério de pronto: nenhum desses sete arquivos contém `AskUserQuestion` sem `AskQuestion` na mesma frase.

### Fase 2. Descriptions dentro do teto

Arquivos:

- `skills/development/tdd-development/SKILL.md` (1160 caracteres)
- `skills/code-reviewing/tech-debt-analysis/SKILL.md` (1417 caracteres)

Manter o que a skill faz e as frases que disparam ela. Cortar o miolo do processo; esse miolo já está no corpo. Conferir também `reliability-analysis` (1001): só mexer se a edição da description passar de 1024.

Critério de pronto: `description` de toda skill do plugin com no máximo 1024 caracteres, medido na linha do frontmatter.

### Fase 3. Chamadas de skill no próprio passo

Trocar o preâmbulo genérico ("as chamadas abaixo são `Skill(...)`; no Cursor leia o arquivo") por uma frase dupla em cada chamada. O preâmbulo pode ficar como lembrete, e o passo não depende dele.

Arquivos e chamadas:

| Arquivo | Chamadas |
|---|---|
| `skills/productivity/product-interrogatory/SKILL.md` | `interview` nos quatro passos |
| `skills/planning/implementation-planning/SKILL.md` | `interview` (2), `design-doc-mermaid` (2) |
| `skills/development/tdd-development/SKILL.md` | `interview`, `run-pipelines` (2), `static-analysis` |
| `skills/debugging/diagnose-and-reproduce/SKILL.md` | as cinco skills filhas |

Modelo da frase, já usado em `document-pipelines`:

> **Claude Code:** call `Skill(skill: "<nome>")`. **Cursor:** read and follow the `<nome>` skill's `SKILL.md` in full.

Critério de pronto: um agente que leia só o passo, sem o preâmbulo, sabe o que fazer nos dois harnesses.

### Fase 4. `feature-planning` de ponta a ponta

1. Criar `scripts/install_cursor_pm_skills.sh` com o clone raso e a cópia das duas pastas para `~/.cursor/skills/`.
2. Atualizar a seção "External dependencies" do `README.md` para apontar o script no Cursor e manter os comandos `/plugin` no Claude Code.
3. Ajustar os Steps 1, 2 e 5 de `skills/planning/feature-planning/SKILL.md` como na seção "Não fecha no Cursor".
4. Se o arquivo externo não estiver no disco, o passo para e imprime o comando. Não há fallback que invente o PRD.

Critério de pronto: com o script rodado, um pedido de feature no Cursor percorre descoberta, PRD, review dos três agents e stories em `docs/<TAG>/`. Sem o script, o Cursor para no Step 1 com o comando na tela. No Claude Code os mesmos passos continuam usando `Skill`.

### Fase 5. Review nativo dentro da orquestração

Arquivos:

- `skills/code-reviewing/complete-code-review/SKILL.md`
- `skills/code-reviewing/complete-code-review/references/agent-prompts.md`
- `skills/code-reviewing/harness-code-review/SKILL.md`

No Cursor, a lente `harness-code-review` sai da lista de spawns do `code-reviewer` e roda na thread principal, em modo orquestrado (sem editar a árvore). O relatório dela entra no ledger como as outras. No Claude Code ela continua no `code-reviewer`.

`harness-code-review` ganha uma linha: se quem a invocou já é um subagent no Cursor, devolver "native reviewer unavailable" e não tentar Task de `bugbot`. Quem decide o desvio é `complete-code-review`, na thread principal.

Critério de pronto: uma "review my changes" no Cursor produz findings de `bugbot` e de `security-review` no relatório merged. Uma review no Claude Code continua chamando `code-review` dentro do agent.

### Fase 6. Conferência

1. `python3 scripts/sync_cursor.py` e `python3 scripts/sync_cursor.py --check`. As fases 1–5 não editam agents; o check confirma que `.cursor-plugin/` segue igual ao gerado.
2. Script curto, ou um teste no `sync_cursor.py --check`, que falha se alguma `description` passar de 1024 caracteres ou se um `SKILL.md` do plugin citar `AskUserQuestion` sem `AskQuestion` na mesma linha. A lista de exceções começa vazia.
3. Atualizar a tabela de skills do `README.md` só se alguma descrição de uma linha deixar de bater com o frontmatter novo.
4. Smoke manual, um fluxo por grupo, nos dois harnesses:

| Fluxo | Skills | Pronto quando |
|---|---|---|
| Entrevista | `interview` | As duas rodadas saem de `AskQuestion` no Cursor e de `AskUserQuestion` no Claude |
| Texto | `grammar-review` | O texto volta corrigido, sem pergunta de idioma |
| Diagrama | `design-doc-mermaid` | Um flowchart válido, com checagem manual se não houver `mmdc` |
| Feature | `feature-planning` depois `implementation-planning` | `PRD.md`, `user_story_*.md` e a seção de implementação, com `senior-dev` em paralelo quando há mais de uma story |
| TDD | `tdd-development` | Um slice RED/GREEN num repo pequeno, ledger fora da árvore |
| Review | `complete-code-review` em "review only" | Um relatório por lente, incluindo a lente nativa do harness |
| Bug | `diagnose-and-reproduce` | `docs/<slug>/diagnosis.md` até a escolha da opção, sem editar código de produção |
| CI | `scan-pipelines` | Relatório no chat, nenhum arquivo escrito |
| Walkthrough | `flow-as-is` | `docs/<flow>-flow.md` com `file:line` |

## Fora deste plano

- Trocar `MODEL_MAP` de `inherit` para um id fixo de modelo. O id certo depende da conta, e `inherit` já deixa review e apply no modelo que a pessoa escolheu no Cursor.
- Embutir o servidor MCP do Datadog neste plugin. Quem quiser evidência de produção instala o plugin do Datadog no harness que estiver usando. O diagnóstico já segue sem ele.
- Reescrever `design-doc-mermaid` para caber em 500 linhas. É conteúdo vendorado de guias. O estouro é de recomendação, e o script de validação já existe.
- Vendorizar `pm-skills` dentro deste repo.
