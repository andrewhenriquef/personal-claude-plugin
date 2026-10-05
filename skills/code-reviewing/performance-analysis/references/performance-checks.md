# Performance review questions

Use in Step 2 of `performance-analysis`. Read only the sections that match the slice. Each row is a question about the code, not a pattern to grep for. A row is a finding only when the path is hot and you have evidence (Step 3). Language traps are in the language references.

## Data access

| Ask | Why it matters |
|---|---|
| Does the number of queries grow with the number of rows or items? A query inside a loop, or a lazy association read per item | N+1. 1 query for the list plus 1 per row. The classic cause of slow list pages |
| Is every query on a list or an export limited and paginated? What stops the result from growing without bound? | A table that grows turns a fast query into an outage |
| Does the code load full records when it needs one field, a count, or an existence check? | Memory and transfer cost, and the database cannot use an index-only read |
| Does the query have a `WHERE` and `ORDER BY` that an index supports, on a table that is large? | A missing index on a large table scans every row. Index creation itself belongs to `data-and-migration-analysis` |
| Is deep pagination done with `OFFSET`? | The database reads and skips every earlier row. Keyset pagination stays fast |
| Does the same query run several times in one request? | Repeated reads of the same data |
| Does a loop update or insert one row at a time? | One round trip per row. A bulk statement is far faster, but check what it skips (see `data-integrity.md` in `data-and-migration-analysis`) |
| Does a transaction stay open while the code does slow work (HTTP, files, sleeps)? | Holds locks and a connection |
| Does a counter, total, or aggregate run on every request over a large table? | A stored counter or a cache may fit |

## Algorithms and structure

| Ask | Why it matters |
|---|---|
| Is there a loop inside a loop over collections that can both be large? | O(n x m) work. Check `n` and `m` |
| Is a list searched linearly inside a loop (`include?`, `find`, `contains`)? | Turns O(n) into O(n x m). A set or map lookup is constant time |
| Is something sorted, filtered, or compiled (a regex, a template, a parser) inside a loop when it can be done once? | Repeated work with the same result |
| Is the same expensive value computed several times in one path? | Compute once and reuse |
| Is work done for items that are discarded later? | Filter first, then transform |
| Does the code recurse or retry with no bound? | Cost grows without limit. The failure side belongs to `reliability-analysis` |

## Memory

| Ask | Why it matters |
|---|---|
| Is a whole file, response body, or result set read into memory when it could be streamed or processed in batches? | Memory grows with input. Large inputs crash the process |
| Does a collection grow for the lifetime of the process (a cache, a map, a slice) with no limit or expiry? | A slow leak that ends in an out-of-memory kill |
| Are large strings or slices built by repeated concatenation or copying in a loop? | Quadratic copying |
| Does a batch job process everything in one pass instead of chunks? | Peak memory and long transactions |
| Does a payload include more data than the caller needs? | Memory, serialization, and network cost |

## I/O and network

| Ask | Why it matters |
|---|---|
| Are independent calls (HTTP, database, file) made one after another when they could run together or in one batch? | Latency adds up. Total time becomes the sum, not the longest call |
| Is a network or database call made inside a loop? | One round trip per item. Batch endpoints and `IN` queries avoid it |
| Is a connection, client, or session created per request or per item? | Setup cost on every call, and no connection reuse |
| Is a slow call on the user's request path when a background job would do? | The user waits for work they do not need |
| Is a large response compressed, paginated, or filtered by the server? | Transfer cost |

## Caching and reuse

| Ask | Why it matters |
|---|---|
| Does the code recompute or refetch data that rarely changes, on a hot path? | A cache may remove most of the cost |
| Is a new cache added? Does it say how it expires and how it is invalidated? | Stale data and unbounded growth are the usual bugs |
| Does the cache key include everything that changes the result (user, locale, parameters)? | A wrong key serves data to the wrong caller. Report as a bug as well |
| Is memoization used on a value that can be `nil` or `false`? | The check misses and the work repeats |

## Concurrency and contention

| Ask | Why it matters |
|---|---|
| Is a lock held during I/O or slow work? | Other callers wait for the whole duration |
| Is work serialized that has no dependency, in a path with spare cores or connections? | Idle capacity |
| Is the number of goroutines, threads, or jobs started per item unbounded? | Resource exhaustion. A bounded pool is the usual fix |
| Is there one shared resource (a single row, a single key, a single queue) that every request updates? | A hot spot limits throughput |

## Serialization and output

| Ask | Why it matters |
|---|---|
| Does serialization load an association or call a service per item? | N+1 hidden in a serializer or template |
| Is logging in a hot loop building large strings that are discarded at the current log level? | Wasted work |
| Is a large structure converted back and forth between formats? | Repeated parsing and allocation |

## Startup and background work

| Ask | Why it matters |
|---|---|
| Does the change add work that runs at every process start (loading data, warming caches, large imports)? | Slower deploys, restarts, and autoscaling |
| Does a scheduled job do work that grows with total data, not with new data? | The job gets slower every week |

## Exclusions

Do not report:

- Micro-optimizations on cold paths: startup that runs once, migrations, admin tools, one-off scripts, and tests.
- A cost on a collection that is small and bounded by design (for example a fixed list of 12 months).
- A linter finding on a path that is not hot, or where the gain is not measurable.
- Idioms with identical complexity (`map.flatten` versus `flat_map` on a short list).
- A fix that makes the code harder to read for a gain that no measurement shows.
- A cache or a rewrite proposal with no cost shown first.
- Speed differences from a measurement that is inside the noise (see `evidence.md`).

Precedents:

- An N+1 on an endpoint with a bounded, small page size is MEDIUM at most. Say what the bound is.
- Unknown data size is "Needs human check". It is not a finding and not a drop.
- A security or reliability issue with no performance cost goes in the report as a note for that review, not as a performance finding.
