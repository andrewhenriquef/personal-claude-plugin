# AS IS and TO BE diagrams

Use in Step 6 of `explain-changes`. The base rules (evidence only, real names, layer order, size limits, captions, no sensitive data, hand checks) are in [the explore-flow diagram rules](../../explore-flow/references/diagrams.md). This file adds the rules for comparing two versions of one flow.

## Rules for a pair

1. **Same frame.** The AS IS and the TO BE start at the same entry point and end at the same boundary. Declare the same participants in the same order. Declare a participant that exists only in one version in both diagrams, in the same position, so the columns line up.
2. **Same words.** Use the same glossary term for the same thing in both diagrams and both captions.
3. **AS IS from the base.** Each arrow is a hop on the merge base. The caption says `Base: <base-sha>`.
4. **Mark the change in TO BE.**
   - Added or changed steps: inside `rect rgb(220, 245, 225)` with a `Note` that starts with `NEW:` or `CHANGED:`.
   - Removed steps: a `Note` that starts with `REMOVED:` at the place where the step was.
   - Unchanged steps: no mark.
5. **Context, not the whole world.** Show the entry point, the hop before and after each change, and the changed hops. Collapse long unchanged stretches into one self-call with a short label (`C->>C: validate params (unchanged)`).
6. **A caption for each.** AS IS: what the flow did. TO BE: what is different and what to notice.

## Example: a changed flow

AS IS (base `a1b2c3d`):

```mermaid
sequenceDiagram
  autonumber
  actor U as Customer
  participant C as RefundsController
  participant S as RefundService
  participant G as PaymentGateway
  participant D as Database

  U->>C: POST /orders/:id/refund
  C->>S: call(order)
  S->>G: refund(charge_id, order.total)
  G-->>S: refund_id
  S->>D: UPDATE orders (status = "refunded")
  C-->>U: 200 OK
```

Caption: the service always refunds the full order total.

TO BE:

```mermaid
sequenceDiagram
  autonumber
  actor U as Customer
  participant C as RefundsController
  participant S as RefundService
  participant G as PaymentGateway
  participant D as Database

  U->>C: POST /orders/:id/refund {amount}
  C->>S: call(order, amount)
  rect rgb(220, 245, 225)
    Note over S: CHANGED: amount must be > 0 and <= order.refundable_amount
    alt amount is valid
      S->>G: refund(charge_id, amount)
      G-->>S: refund_id
      S->>D: INSERT refunds (order_id, amount)
      Note over S,D: NEW: status = "partially_refunded" while refundable_amount > 0
      S->>D: UPDATE orders (status)
      C-->>U: 200 OK
    else amount is not valid
      S--xC: raises InvalidRefundAmount
      C-->>U: 422 Unprocessable
    end
  end
```

Caption: the request now takes an amount; the service checks it, records each refund in `refunds`, and sets a partial status. Invalid amounts return `422`.

## New and removed flows

- **New flow:** one TO BE diagram. No marks, since every step is new. The caption says "New flow".
- **Removed flow:** one AS IS diagram from the base. The caption says what replaces it, or "No replacement".

## Change map (optional)

When there are 3 or more units, one small flowchart in the general context. One node per unit, arrows only for real dependencies, the class of each unit in the label.

```mermaid
flowchart LR
  U1["1. Add refunds table (new data)"]
  U2["2. Partial refund (changed flow)"]
  U3["3. Refund webhook (new flow)"]
  U1 --> U2
  U2 --> U3
```
