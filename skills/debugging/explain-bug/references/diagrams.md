# Diagrams for a bug explanation

Use in Step 2 of `explain-bug` and in `propose-solutions` (the AS IS and TO BE diagrams). Mermaid is the format. The `design-doc-mermaid` skill in this plugin has fuller guides (`references/guides/diagrams/sequence-diagrams.md`, `activity-diagrams.md`) and a validation script.

Sources: [Mermaid sequence diagram](https://mermaid.js.org/syntax/sequenceDiagram.html), [Mermaid flowchart](https://mermaid.js.org/syntax/flowchart.html), [Mermaid state diagram](https://mermaid.js.org/syntax/stateDiagram.html), [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli), and `design-doc-mermaid` in this plugin.

## Rules

1. **Evidence only.** Draw the calls you saw in the code, the trace, or the experiment. Mark an inferred step with `(inferred)` in its label.
2. **Real names.** Use the names of the real components and functions.
3. **Mark the break.** The reader must see the faulty step in two seconds. Use a `Note`, a color, or a `rect`.
4. **Show the wrong value where it first appears.**
5. **One idea per diagram.** If it needs more than about 12 elements, split it.
6. **English labels, short.** Use the glossary terms. A Portuguese caption goes under the diagram.
7. **No sensitive data.** Use `<user-id>`, `<token>`, `<amount>` placeholders.
8. **Valid syntax.** Quote labels that contain parentheses, colons, or slashes. Avoid `end` as a word in a flowchart label. If `mmdc` is installed, render each diagram once to check it.

## 1. Sequence diagram of the failing flow

Use for any bug that crosses components or time.

```mermaid
sequenceDiagram
  autonumber
  participant C as Client
  participant A as API (OrdersController#create)
  participant S as PaymentService
  participant D as Database

  C->>A: POST /orders {amount: 0}
  A->>S: charge(order)
  S->>S: ratio = refund / order.total
  Note over S: BUG: order.total is 0, so the division raises ZeroDivisionError
  S--xA: raises ZeroDivisionError
  A-->>C: 500 Internal Server Error
  Note over D: The order row is already saved (half-finished work)
```

Tips:

- `->>` is a call, `-->>` a return, `--x` a failed message.
- `rect rgb(255, 235, 235)` ... `end` highlights a block. Use sparingly.
- `alt` / `else` shows the branch that differs between the passing and the failing case.
- `par` shows concurrent work for a race. A timeline is often clearer (see below).

## 2. Flowchart of the decision or data path

Use when a condition, a branch, or a data transformation decides the result.

```mermaid
flowchart TD
  A[Request arrives] --> B{order.total > 0?}
  B -- yes --> C[Compute refund ratio]
  B -- no --> D[No check: ratio = refund / 0]
  C --> E[Return 200]
  D --> F[ZeroDivisionError, 500]
  classDef bad fill:#fdd,stroke:#c00,color:#600;
  class D,F bad;
```

Tips:

- Put the failing branch in a `bad` class. Keep the working path in the default style.
- Label the decisions with the real condition from the code.
- A diagram of AS IS (the flow that fails) and TO BE (the flow after the fix) is made in `propose-solutions`, one TO BE per option.

## 3. Timeline for races and ordering

Use a sequence diagram with two actors and a shared resource, and number the steps so the interleaving is visible:

```mermaid
sequenceDiagram
  autonumber
  participant W1 as Worker 1
  participant R as Row (balance=100)
  participant W2 as Worker 2

  W1->>R: read balance (100)
  W2->>R: read balance (100)
  W1->>R: write balance = 100 - 30
  Note over W1,W2: BUG: W2 overwrites W1 with a stale value
  W2->>R: write balance = 100 - 50
```

State changes (expiry, retries, a state machine) read well as a state diagram:

```mermaid
stateDiagram-v2
  [*] --> Pending
  Pending --> Paid: payment ok
  Pending --> Expired: timeout
  Expired --> Paid: late webhook (BUG, allowed)
```

## 4. Captions

Under each diagram, write one line in English and one in Portuguese ("Legenda") that says what to notice. The Portuguese caption names the same step and the same value.

## 5. Checks before you ship a diagram

- Each arrow is in the code, the trace, or an experiment.
- The faulty step is marked.
- Terms match the glossary.
- No secret or personal data.
- It renders.
