# Static analysis strategies for AI agents

Research behind the `static-analysis` skill. Date of research: 2026-10-04.

## Finding

No single, widely adopted "lint skill" came out of the search. The closest sources are guides on linters as feedback for coding agents, hook recipes that run a linter after each edit, and the official docs of the tools. The skill combines them with the structure of the other skills in this plugin (`code-simplify`, `security-analysis`). Several sources are blog posts, not studies. Treat the practices as engineering advice, not measured results.

## Strategies and where they come from

| # | Strategy | Source | Where the skill uses it |
|---|---|---|---|
| 1 | Linters give an agent fast, exact feedback. Run the linter, give errors back, iterate until it passes | [Factory: Using Linters to Direct Agents](https://factory.com/news/using-linters-to-direct-agents), [Make Claude Code Fix Its Own Lint Errors](https://boehs.com/blog/2026/03/17/claude-code-lint-hooks/) | Process steps 2 to 5 |
| 2 | Autofix where possible, so the agent corrects itself. Treat "lint green" as done | Factory | Step 2 (autocorrect), Step 5 (zero findings) |
| 3 | Run on the path the agent works on, not only in CI. Hook recipes run the linter after every edit | [How to configure Ruff with Claude Code](https://pydevtools.com/handbook/how-to/how-to-configure-ruff-with-claude-code/), boehs.com | Step 1 reads CI config so the local command matches CI |
| 4 | Do not add blanket suppressions. A suppression needs a rule code | pydevtools (no inline `noqa` without a rule code) | "Rules that never change". The skill goes further: no suppressions at all |
| 5 | Linters can encode architecture and security rules. Add rules for patterns that recur in review | Factory | Reference sections "Rules by class" |
| 6 | Separate the formatter from the lint rules | [golangci-lint v2 migration](https://golangci-lint.run/docs/product/migration-guide/), [RuboCop autocorrect](https://docs.rubocop.org/rubocop/latest/usage/autocorrect.html) | Step 2, format class |
| 7 | Distinguish safe autofix from unsafe autofix. Review the diff and run tests after unsafe fixes | RuboCop docs (`-a`, `-A`, `-x`) | Steps 2 and 3, language references |
| 8 | Skill anatomy: overview, when to use, process, rationalizations, red flags, verification | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | `SKILL.md` layout |

## Design choices that are not from a source

These come from the owner's requirements and the failure modes of agents. Test them in use.

- **Default scope for every `code-reviewing` skill:** the files not committed yet plus the branch diff against main. A full review of a file or the codebase happens only when the user asks.
- **Autocorrect always on, and zero tolerance for rule breaks.** The skill never adds a suppression, never edits lint config, and never accepts a "false positive". A rule that seems wrong is reported as feedback and still enforced. The only exit is "Blocked" (tool crash, broken config, conflicting rules).
- **Files in scope are fixed whole, including old violations.** There is no baseline step. This can make a large diff on a legacy file. The user can narrow the scope by naming files.
- **Unsafe autocorrect is allowed with a diff review and a test run.** An unsafe fix that changes behavior is reverted and fixed by hand.
- **Precedence: project config, then user preferences, then reference defaults.** Each language reference has a "My preferences" section for the owner.
- **Hand off, do not overlap.** Design signals are fixed with `code-simplify` principles. Security rules are fixed here and reviewed deeper by `security-analysis`.

## Tool facts used in the references

Checked against the tool documentation on the research date:

- golangci-lint: `run` reports and does not format. `run --fix` applies fixes. `fmt` and `formatters` exist in v2. `--new`, `--new-from-rev`, and `--new-from-patch` limit output to new issues (the skill does not use them). ([CLI](https://golangci-lint.run/docs/configuration/cli/), [false positives](https://golangci-lint.run/docs/linters/false-positives/))
- RuboCop: `-a` is safe autocorrect, `-A` is all autocorrect, `-x` is layout only. `Lint/RedundantCopDisableDirective` flags useless disable comments. `.rubocop_todo.yml` holds generated exceptions. ([autocorrect](https://docs.rubocop.org/rubocop/latest/usage/autocorrect.html), [configuration](https://docs.rubocop.org/rubocop/latest/configuration.html))

Not verified from the docs: the exact RuboCop flags `--lint` and `--force-exclusion`, the shell snippets that build the file lists, and the Go and Ruby code samples. They come from the author's knowledge of the tools. Check them with `--help` on the installed version.

## Planned next steps

- Add references for more languages when needed (JavaScript and TypeScript with ESLint, Python with Ruff).
- Consider a hook recipe (`PostToolUse` on `Write|Edit`) as a companion to the skill. Hooks run on every edit. The skill runs on request.
- Fill the "My preferences" sections.
