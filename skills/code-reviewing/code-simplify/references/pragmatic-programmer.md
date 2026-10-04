# The Pragmatic Programmer (Hunt and Thomas)

Use when the problem is duplication, coupling, or hidden errors.

## Easier To Change (ETC)

Good design is design that is easier to change. For every simplification ask: is the next likely change easier or harder after this? If harder, revert.

## DRY: Don't Repeat Yourself

Every piece of **knowledge** has one authoritative place. DRY is about knowledge (a rule, a format, a constant, a schema), not about similar-looking text.

| Case | Action |
|---|---|
| Same business rule in several places | Move to one place |
| A constant or format repeated | Name it once |
| Comment that restates the code | Delete it |
| Two blocks look alike but change for different reasons (coincidental duplication) | Leave them. Merging couples unrelated things |

## Orthogonality

Unrelated things do not affect each other. Signal: one small requirement change touches many modules, or a helper changes hidden global state. Fix: narrow the interface, remove shared mutable state, split things that change for different reasons.

## Law of Demeter, tell don't ask

A call chain like `order.customer.address.city` couples the caller to the whole structure. Ask the nearest object to do the job (`order.shipping_city`).

Do not apply it to plain data access or to collection pipelines (`list.select(...).map(...)`). Those are fine.

## Fail early

The book says "crash early": a dead program does less harm than a wrong one. Do not swallow or hide errors to make code look cleaner. Removing error handling is not simplification. Fail with a clear error at the point of the problem.

"Fail" follows the language and project convention. In Go, return the error, do not `panic`. In Ruby, raise a specific error.

## Do not program by coincidence

Code that works but you cannot say why is risky. Before you simplify, know why it works (see Chesterton's Fence in `SKILL.md`). If you cannot explain it, add a test first.

## Broken windows

Small decay invites more decay. Fix small mess when you touch the code, in small, separate, reviewable changes. Stay in scope.

## Good enough

Stop when the code is clear and easy to change. Over-polishing is also waste. Do not gold-plate.
