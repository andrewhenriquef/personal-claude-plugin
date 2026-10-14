# Structure and safety-net signals (sets D and E)

Use in Step 3 of `tech-debt-analysis`. A signal is a lead. It becomes an item only when Step 4 shows a cost. Thresholds are defaults. The project's own config (linter limits, ADRs) wins.

## Set D: structure

| Signal | Detect | Cost to show |
|---|---|---|
| God file | Over 500 lines (default) | Churn in the window, and several reasons to change. A long file with one job and no churn is fine |
| God or tangled function | Above the project's complexity limit. With no limit, the top 5 by the proxy | It sits in a hotspot, or bug fixes land in it |
| Duplicated knowledge | The same rule, constant, or format in 3 or more places. A duplication tool, or `git grep` for the literal | A change to the rule needs edits in each place. Check the history for a change that touched them all |
| Inconsistent ways | Several HTTP clients, error styles, loggers, config loaders, or date libraries. Count imports | A new feature must pick one. Name the count and the paths |
| Layering break | A lower layer imports a higher one (the domain imports the web layer). `git grep` the import lines by directory | Coupling in a hotspot. Cite the import `file:line` |
| Cycles | Only when the project has a tool for it (for example Packwerk in Ruby). Go forbids package cycles at build time | The tool's own report |
| Pass-through layers | A class or function that only forwards to another, with the same signature (Ousterhout, shallow modules) | A change in the target needs a change here too. See `code-simplify` references |
| Dead flag or config | A feature flag that is always on or always off in every environment, read from config files | Branches nobody can reach. Verify in every environment file |

Leave out what `static-analysis` owns (formatting, style rules) and what the other review skills own (security, performance). Add one pointer line when you see an obvious case.

## Set E: safety net

| Signal | Detect | Cost to show |
|---|---|---|
| Hotspot with no test | Map the source file to its test (see the language reference). If no match, `git grep -l '<ClassName>' -- <test dirs>` | No test names the class. The hotspot changes without a net |
| Complex code with no test | The most complex functions with no test that calls them | Same as above |
| One owner | 80% or more of commits by one author (see [measuring](measuring.md), section 5) | Knowledge risk. Report as "one owner", never as a person's fault |
| Skipped tests in a hotspot | From set C, W3 | The net has a hole where the team works |
| Runtime past end of life | The version file (`.ruby-version`, `go.mod` `go` line) against the vendor's support dates, which you must look up or send to "Needs human check" | Pointer to `dependency-analysis`. One line, no deep review |
| Outdated dependencies | Pointer only | Run `dependency-analysis` in Audit mode |

Say "no test found" only with the search you ran. A test can name the class in a string, a factory, or a shared example.

## Looks bad but is fine

These go in the doc's "Looks bad but is fine" section. Each entry needs its reason and the evidence.

- Generated code, vendored code, compiled assets, schema dumps.
- Old migrations. They are write-once and run once.
- Fixtures, snapshots, large test data, and long spec files whose examples are independent.
- Config-like files that change by design: routes, locales, factory lists, feature-flag lists (Feathers).
- Adapters and glue code that are long because the outside API is large.
- A TODO with a ticket, an owner, and a date less than 90 days old. It is boarded up, which is what the book asks for.
- Anything cold: no commit in the window. Add it to "Leave alone" with its pain tier, so a later scan can notice a change.
- Code marked as deliberate (a comment, an ADR, a commit message that gives the reason). Quote the source.
- Duplication that only looks alike and changes for different reasons (coincidental duplication).

If this section is empty, the scan was too shallow. Go back to Step 4.

## Origin of an item (optional)

When the code, a comment, or a commit message states the reason, add the origin. This follows Fowler's quadrant.

| Origin | Evidence you can cite |
|---|---|
| Deliberate | A comment or a commit that says "temporary", "for the release", "quick fix", with the date |
| Inadvertent | No such mark. The design simply aged, or was never examined |

Do not guess. With no evidence, leave the field empty. Interest still decides the ranking. Origin only helps the team choose the response.
