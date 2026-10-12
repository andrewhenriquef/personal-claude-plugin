# Cause categories

Use in Step 1 of `form-hypotheses`. For each category: the question to ask, the signals that point at it, and a prediction pattern. The patterns are templates. Fill them with names from the bug.

Sources: [Zeller, Scientific Debugging](https://www.st.cs.uni-saarland.de/whyprogramsfail/pdf/ScientificMethod.pdf) (every hypothesis predicts an outcome), [superpowers systematic-debugging](https://skillselion.com/skills/obra/superpowers/systematic-debugging) (trace the data flow, compare with a working example), [Google SRE book, Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) (check recent changes first, compare working and broken), and the failure classes in `reliability-analysis/references/reliability-checks.md`.

## 1. Recent change

- **Ask:** What changed just before the first occurrence? Code, dependency, schema, flag, config, data load, traffic.
- **Signals:** The first error matches a deploy or merge time. Error Tracking shows the issue starts at one version. `git log` on the failing file shows a recent edit. A lockfile changed.
- **Prediction pattern:** If commit `<sha>` caused it, then the test passes at its parent and fails at `<sha>` (`git bisect run`).
- **Cheap test:** Bisect between the last known good point and the first bad point.

## 2. Input or data shape

- **Ask:** What input does the failing case have that the passing cases lack? Null, empty, very large, Unicode, a new enum value, a negative number, a duplicate, an unexpected type.
- **Signals:** Only some tenants, routes, or records fail. The error is a type or parse error. The failing records share a field value.
- **Prediction pattern:** If `<field value>` causes it, then the same request with that value changed passes, and any request with that value fails.
- **Cheap test:** Take one failing and one passing input and diff them. Minimise the failing one.

## 3. State and ordering

- **Ask:** Does the result depend on what ran before, in what order, or at the same time? Shared mutable state, caches, retries, partial writes, race conditions, test order.
- **Signals:** The bug is flaky. It passes alone and fails in the suite. It fails more under load. A second run gives a different result.
- **Prediction pattern:** If shared state causes it, then running the test alone passes and running it after `<other test>` fails. If a race causes it, then the failure rate rises with parallelism.
- **Cheap test:** Run the test alone, in the full order, in random order with a fixed seed, and N times in parallel. Compare rates.

## 4. Time

- **Ask:** Does the code read the clock, a time zone, a date boundary, an expiry, or a timeout?
- **Signals:** Failures cluster at midnight, at month end, at a daylight saving change, on certain days. Tokens or caches expire. A timeout is close to the typical latency.
- **Prediction pattern:** If the time zone causes it, then the test fails when the clock is set to `<instant>` and passes at other times.
- **Cheap test:** Freeze or inject the clock (Go: an injected clock; Rails: `travel_to`) and try the boundary values.

## 5. Configuration and environment

- **Ask:** Do the failing and passing environments differ in flags, environment variables, versions, permissions, locale, feature gates, or data?
- **Signals:** Fails in one environment, one region, or one pod only. A flag was flipped. A version differs between hosts.
- **Prediction pattern:** If flag `<F>` causes it, then toggling `<F>` in a local run flips the result.
- **Cheap test:** Run the same input with the production config values (synthetic secrets) and compare.

## 6. Dependency contract

- **Ask:** Did an external service, a library, or the database change or behave differently from what the code assumes? A new response field, a changed error code, a slower response, a rate limit, a major version bump.
- **Signals:** Errors come from a client library or an outbound span. The dependency's status or version changed. The response in the failing trace differs from the fixture.
- **Prediction pattern:** If the dependency now returns `<shape>`, then replaying the captured (redacted) response through the code fails, and the old response passes.
- **Cheap test:** Replay a captured response against the code in isolation.

## 7. Resource limits

- **Ask:** Is something running out: memory, connections, file handles, goroutines or threads, queue depth, disk, a quota?
- **Signals:** Errors rise slowly and then jump. Restarts fix it for a while. Runtime metrics grow (goroutines, threads, heap). "Too many open files", "pool exhausted", out-of-memory kills.
- **Prediction pattern:** If a leak causes it, then the resource count grows with the number of requests and flattens when the leaking path is removed.
- **Cheap test:** Run the path N times and measure the count before and after.

## "The bug is not where the symptom shows"

- **Ask:** Is the failing line a victim? Did an earlier step write wrong data, skip a validation, or leave a wrong state that this line only exposes?
- **Signals:** The stack trace ends in correct-looking code. The wrong value was stored or computed earlier. Different callers pass the same bad value.
- **Prediction pattern:** If the value is wrong before it reaches `<function>`, then logging it at `<earlier boundary>` already shows the wrong value.
- **Cheap test:** Trace the data backwards from the symptom to the first place the value is wrong.

## Mixed signals

When two categories fit, write both as separate hypotheses with different predictions. Do not merge them into "a race with bad data".
