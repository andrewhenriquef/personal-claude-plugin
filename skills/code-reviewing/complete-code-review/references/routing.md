# Routing: which review skills a change needs

Use in Step 1 of `complete-code-review`. Classify the files in scope, check the content signals, and choose the skills. When a signal is unclear, run the skill. A skipped lens finds nothing.

## File classes

Classify every file in scope into one or more classes. Match the path first.

| Class | Go | Ruby / Rails | Other |
|---|---|---|---|
| Dependency manifest | `go.mod`, `go.sum` | `Gemfile`, `Gemfile.lock`, `*.gemspec` | `package.json` and lockfiles, `requirements*.txt`, `pom.xml` (no dependency reference for these yet, see below) |
| Migration or schema | `migrations/**`, `*.sql`, `sqlc.yaml`, `atlas.hcl` | `db/migrate/**`, `db/schema.rb`, `db/structure.sql` | any `*.sql` |
| Test | `*_test.go`, `testdata/**` | `spec/**`, `test/**`, `*_spec.rb`, `*_test.rb` | `__tests__/**`, `*.test.*`, `*.spec.*` |
| Production code | other `*.go` | other `*.rb`, `app/**`, `lib/**`, `config/**` (code, not data) | source files in other languages |
| Build, CI, infra | `Dockerfile`, `.github/workflows/**`, `*.tf`, Kubernetes and Helm files, `Makefile` | same | same |
| Docs and assets | `*.md`, images, `docs/**` | same | same |

Rules:

- A change that is only **docs and assets** gets no review. Say so and stop.
- A file can have several classes (a Rails model is production code and also touches the schema).
- Skip generated code and vendored code (see Step 0 of `SKILL.md`).
- If a language has no reference in the review skills (not Go and not Ruby), still run the skills that work from the process alone, and say that the language references are missing.

## Which skill runs when

| Skill | Group | Run when | Skip when |
|---|---|---|---|
| `security-analysis` | parallel | Any production code, and any build, CI, or infra file | Only tests, docs, or dependency manifests (the dependency skill covers those) |
| `dependency-analysis` | parallel | A dependency manifest or lockfile is in scope. In a full review: always, in Audit mode | No manifest in scope |
| `data-and-migration-analysis` | queue | A migration or schema file is in scope, or the content signal for data access below matches | Neither |
| `reliability-analysis` | queue | The content signal for failure handling below matches, or a job, a consumer, a webhook, or a concurrency primitive is in scope | Pure data structures, pure functions, config only |
| `test-analysis` | queue | A test file is in scope, or production code with behavior changed (the tests that protect it are part of the review) | No test and no production code in scope |
| `performance-analysis` | queue, last | The content signal for hot paths below matches | Config only, one-off scripts, docs |
| `static-analysis` | apply phase | The project has a linter for the language of a code file in scope (`.golangci.yml`, `.rubocop.yml`, or the linter is in the manifest) | No linter configured. Say so, and do not install one |
| `code-simplify` | apply phase, on request | Only when the user asks for simplification or clean-up | Default |

`static-analysis` does not review. It fixes. It runs in the apply phase (Step 6), last, not in Step 2. List it in the plan with its apply-phase position.

`code-simplify` also changes code. Leave it out unless the user asks. If the review finds heavy design smells, mention it in the report as a lead.

### Languages without a dependency reference

`dependency-analysis` has Go and Ruby references. For another ecosystem, run it anyway (its process works from the manifests), and say that the language reference is missing. It then uses the project's own scanners.

## Content signals

Run these over the files in scope that are production code or migrations. Replace `<files>` with the scope list. A match means "run the skill". A miss does not forbid it when the intent says otherwise.

```
# Data access: data-and-migration-analysis
grep -lE 'ActiveRecord|\.where\(|\.find_by|\.update_all|\.insert_all|\.upsert|\.transaction|\.create!?\(|\.destroy|\.delete_all|database/sql|sqlx|pgx|gorm|\.Query(Row)?(Context)?\(|\.Exec(Context)?\(|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b' <files>

# Failure handling and concurrency: reliability-analysis
grep -lE 'http\.(Get|Post|NewRequest|Client)|Faraday|Net::HTTP|HTTParty|RestClient|\bgo func|\bgo [a-zA-Z_.]+\(|sync\.|errgroup|chan |recover\(|\brescue\b|\bretry\b|Thread\.new|Mutex|Concurrent::|perform_async|perform_later|def perform|Sidekiq|ActiveJob|webhook|context\.With(Timeout|Cancel|Deadline)|slog\.|Rails\.logger|Sentry|Datadog|tracer\.' <files>

# Hot paths: performance-analysis
grep -lE '\.each\b|\.map\b|\.where\(|\.includes\(|\.joins\(|\.all\b|find_each|for .* range|for \w+ :=|\.Query|\.Find\(|json\.(Marshal|Unmarshal)|to_json|as_json|CSV|bufio|io\.ReadAll|File\.read|readlines|render|serializer|def (index|show|call)|func .*\(w http\.ResponseWriter' <files>
```

Also use the file path: `app/controllers/**`, `app/jobs/**`, `app/serializers/**`, `cmd/**`, `internal/**/handler*`, and `*_worker.*` point to request, job, and consumer paths.

If the `grep` finds nothing for all three, and the change is production code, the change is probably small and local. Run `security-analysis`, `test-analysis`, and `static-analysis` only, and say so.

## Full review (the user asked for the entire project)

- The scope is the whole codebase. Every skill runs in its full-review path.
- `dependency-analysis` runs in Audit mode.
- Run all the skills that the repository supports, based on what exists in it (a `db/migrate` folder means the data skill runs, a manifest means the dependency skill runs).
- Still use the same groups, order, and apply rules.
- Say in the plan that this spawns one Opus agent per skill, each reading the whole repository, and that it takes a long time.
- In a full review, apply only findings with severity HIGH or MEDIUM, unless the user asks for more. A full review can produce hundreds of LOW items. Report them. Do not apply them.

## Adding a review skill

Add a row to "Which skill runs when", with its group (parallel if it runs no project code, queue if it does), its run and skip rules, and, if it needs one, a content signal. Add its place in the apply order in `merge-and-apply.md`. Then add its name to the list in `SKILL.md` (Step 6).
