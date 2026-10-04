# A Philosophy of Software Design (John Ousterhout)

Source of the design lens. Use when the problem is the shape of a module, not its lines. Go and Ruby samples: `go.md`, `ruby.md` (section "Design lens").

## Complexity

Complexity is anything that makes code hard to understand or change. Two causes:

- **Dependencies:** what must you know, or change, to touch this?
- **Obscurity:** what is hidden or unclear?

## Deep modules

A module is **deep** when a small interface hides a lot of work. A module is **shallow** when its interface is about as big as its implementation. Prefer deep modules. Many tiny methods with wide interfaces make a design shallower, not simpler.

## Strategic, not tactical

Tactical work gets the task done and leaves a little mess each time. Strategic work leaves the design a little better each time. Invest in small steps when you touch code. Do not patch around a bad design, and do not rewrite it all at once.

## Signals

| Signal | Why it is complex | Fix |
|---|---|---|
| Shallow module: interface as big as implementation | Caller learns a lot, gets little | Merge into caller or neighbor, or hide more behind a narrower interface |
| Pass-through method: forwards the same arguments | Adds a layer, no behavior | Inline it, or give it a distinct job |
| Information leakage: one decision (format, key name, order) known by several modules | A change in one place breaks others | Move the decision into one module |
| Temporal decomposition: split by order (`read`, `parse`, `write`), not by knowledge | Each step shares the same knowledge | Group by what each part knows |
| General-special mixture: general code with a branch for one caller | General module learns about one use | Move the special case to that caller |
| Conjoined methods: cannot understand one without the other | Hidden dependency | Merge them, or redraw the boundary |
| Config pushed up: callers set options they cannot judge | Complexity leaks to many callers | Pull it down: choose a good default inside the module |
| Hard-to-name thing | Unclear responsibility | Fix the design first, then name it |
| Non-obvious contract, no comment | Obscurity | Add an interface comment: what, not how |

## Define errors out of existence

Change an operation so the error case cannot happen (e.g. deleting a missing key succeeds). This reduces exception handling for every caller.

**It changes the contract.** It is a design change, not a simplification. Flag it, do not apply it unless the user asks.

## Comments

Comments describe what the code cannot say: intent, non-obvious contract, units, why. A comment that repeats the code is noise. A missing interface comment on a non-obvious contract is obscurity.
