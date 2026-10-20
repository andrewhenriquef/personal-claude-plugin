# Diagrams for a flow

Use in Step 6 of `flow-as-is`. Mermaid is the format. For more patterns read `design-doc-mermaid` in this plugin (`references/guides/diagrams/sequence-diagrams.md`, `activity-diagrams.md`, and `references/guides/troubleshooting.md`). The bug-specific version of these rules is in `explain-bug/references/diagrams.md`.

Sources: [Mermaid sequence diagram](https://mermaid.js.org/syntax/sequenceDiagram.html), [Mermaid flowchart](https://mermaid.js.org/syntax/flowchart.html), [Mermaid state diagram](https://mermaid.js.org/syntax/stateDiagram.html), [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli).

## Rules

1. **Evidence only.** Each arrow is a hop in the trace table. Mark an inferred step with `(inferred)` in its label.
2. **Real names.** Participants are real components, with the class or package in the alias: `participant S as PaymentService`.
3. **Order participants by layer**, left to right: caller, entry point, services, data store, external systems, queues and workers.
4. **One idea per diagram.** About 10 participants and 25 messages at most. Split a bigger one by part.
5. **Short labels** in the doc's language for actions, code names for calls: `charge(order)`, `INSERT orders`, `enqueue SendReceiptJob`.
6. **Concrete values** where they explain a branch: `status = "pending"`, `amount > 0`.
7. **No sensitive data.** Use `<user-id>`, `<token>`, `<card>` placeholders.
8. **A caption** under each diagram, one line in the doc's language: what to notice.
9. **No `alt`, `opt`, or `else`.** A diagram is a straight line: one scenario, from its first hop to its last. Each branch and each error path gets its own diagram (section 2).

## 1. Overview sequence diagram

The main path of the whole flow, each part in a numbered `rect`. Use a light fill so text stays readable in light and dark themes. Do not draw branches here. When a part has other scenarios, add a `Note` that names them: `Note over S,P: Other outcomes: card declined, gateway timeout`.

```mermaid
sequenceDiagram
  autonumber
  actor U as Customer
  participant C as OrdersController
  participant S as CheckoutService
  participant D as Database
  participant P as PaymentGateway
  participant Q as Sidekiq

  rect rgb(230, 240, 255)
    Note over U,C: 1. Validate the request
    U->>C: POST /orders
    C->>C: order_params, authorize
  end
  rect rgb(230, 255, 235)
    Note over C,D: 2. Create the order
    C->>S: call(cart)
    S->>D: INSERT orders (status = "pending")
  end
  rect rgb(255, 245, 225)
    Note over S,P: 3. Charge the card
    S->>P: charge(<card>, amount)
    P-->>S: charge_id
    S->>D: UPDATE orders (status = "paid")
  end
  rect rgb(245, 235, 255)
    Note over S,P: Other outcomes: card declined
    Note over S,Q: 4. Notify
    S-)Q: enqueue SendReceiptJob(order_id)
  end
  C-->>U: 201 Created
```

Caption: the charge runs after the order row is saved, so a failed charge leaves a `pending` order.

## 2. Sequence diagrams per part: one per scenario

A part has one **main path** and one **scenario** for each branch or error path in the hop table that changes which components are touched. Draw each scenario as its own straight-line diagram. Never use `alt`, `opt`, or `else`.

- **Title.** Each diagram has a heading with a short description of what happens: "The charge succeeds", "The card is declined". No letters, no numbers, no ids. Start with the main path. The `Note` in the overview uses the same words.
- **Condition.** The first line of the diagram is a `Note` with the real condition from the code and its `file:line`. Do not repeat the main path's hops that come before the split: start at the participant where the paths part, and say so in the caption.
- **One scenario, one diagram.** If the branch touches no other component (a guard that sets a local value), do not draw it. Write it under "Decisions" in the doc.
- **Stages inside a scenario.** When a scenario has stages of its own (each one a verb you can name, with its own hops across components), draw one diagram per stage, in the order they run. The title keeps the scenario and adds what the stage does: "The card is declined: the gateway rejects the charge". Each stage diagram starts with a `Note` that says where the previous stage ended. Draw only the stages a reader needs; a stage of one or two hops goes in the steps list.

Example: part 3, "Charge the card". The declined card is a scenario with two stages, so it has two diagrams.

"The charge succeeds" (the main path):

```mermaid
sequenceDiagram
  autonumber
  participant S as CheckoutService
  participant P as PaymentGateway
  participant D as Database

  Note over S,P: charge succeeds (checkout_service.rb:41)
  S->>P: charge(<card>, amount)
  P-->>S: charge_id
  S->>D: UPDATE orders (status = "paid")
```

Caption: the order becomes `paid` only after the gateway returns a `charge_id`.

"The card is declined: the gateway rejects the charge":

```mermaid
sequenceDiagram
  autonumber
  participant S as CheckoutService
  participant P as PaymentGateway

  Note over S,P: Gateway::DeclinedError (checkout_service.rb:44)
  S->>P: charge(<card>, amount)
  P--xS: raises DeclinedError
  Note over S: rescued in checkout_service.rb:48
```

Caption: this scenario splits from "The charge succeeds" at the `charge` call; the service rescues the error and returns a failure.

"The card is declined: the order is marked declined":

```mermaid
sequenceDiagram
  autonumber
  participant C as OrdersController
  participant S as CheckoutService
  participant D as Database

  Note over C,D: starts after the gateway rejects the charge: the service holds a failure
  S->>D: UPDATE orders (status = "declined")
  S-->>C: failure(:declined)
  C->>C: render 402 Payment Required
```

Caption: the order row keeps the `declined` status, and the caller sees `402`.

Arrows:

- `->>` a call, `-->>` a return, `--x` a failure, `-)` an async message (enqueue, publish).
- `activate` / `deactivate` (or `+` / `-`) only when the lifetime matters.
- `par` for concurrent work. `loop` for batches and retries, with the limit from the code: `loop up to 3 retries`. `loop` repeats the same hops; it is not a branch.
- `Note over` for a transaction: `Note over S,D: inside ActiveRecord transaction`.

## 3. Flowchart for a decision-heavy part

Only when several conditions decide the result. Label each decision with the real condition. It maps the decisions; the sequence diagrams of section 2 show what runs on each path, so name the scenario on each end node.

```mermaid
flowchart TD
  A[Order received] --> B{"cart.empty?"}
  B -- yes --> X[422 Unprocessable]
  B -- no --> C{"coupon.valid?"}
  C -- yes --> D[Apply discount]
  C -- no --> E[Full price]
  D --> F[Charge]
  E --> F
  classDef stop fill:#fde2e2,stroke:#b42318,color:#5c0b0b;
  class X stop;
```

## 4. State diagram for status changes

Only when the flow moves a record through statuses. Each transition cites the method that makes it in the text.

```mermaid
stateDiagram-v2
  [*] --> pending: CheckoutService#call
  pending --> paid: charge succeeds
  pending --> declined: DeclinedError
  paid --> refunded: RefundService#call
```

## 5. Checks before you ship a diagram

Validate with `python3 <design-doc-mermaid skill dir>/scripts/extract_mermaid.py <doc> --validate` when `mmdc` is installed. Otherwise check by hand:

- Each participant or node is declared once and spelled the same everywhere.
- A label with `(`, `)`, `:`, `;`, `#`, `{`, `}`, or quotes in a flowchart node is wrapped in double quotes.
- No sequence diagram has `alt`, `opt`, or `else`. Each branch and error path in the hop table has a diagram, or a line under "Decisions" when it touches no other component.
- Each `rect`, `loop`, `par`, and `critical` block has its `end`.
- No node or participant is named `end`.
- `classDef` styles set `color:` so text stays readable.
- Each arrow is in the trace table. Inferred steps are marked.
