# Bug diagnosis and reproduction: strategies that work

Research notes (2026-10-12) behind the `debugging` skills. Each skill in the set should cite the strategies it uses. Update this file when new evidence changes a strategy.

## Strategies, and where they are used

| # | Strategy | Evidence | Used by |
|---|---|---|---|
| 1 | **Reproduce first, as a failing test, and show the red.** No production edit before a reproduction exists. | One practitioner audit: 11 of 34 agent "fixes" recurred (about 32%). After a repro-first rule, 2 of 41 did (about 5%) ([DEV: reproduce before fixing](https://dev.to/yureki_lab/how-i-taught-my-ai-coding-agent-to-reproduce-bugs-before-fixing-them-594g)). Single-author account, treat the numbers as indicative. Anthropic also says to give Claude a check it can run and to fix root causes, not symptoms ([best practices](https://code.claude.com/docs/en/best-practices)). | diagnose-and-reproduce, reproduce-bug |
| 2 | **The feedback loop is the skill.** Build a fast, deterministic, agent-runnable loop that goes red on this bug. Tighten it. | [mattpocock diagnosing-bugs](https://github.com/mattpocock/skills) (ten-rung ladder from a failing test to a human-in-the-loop script). Same idea in [superpowers systematic-debugging](https://skillselion.com/skills/obra/superpowers/systematic-debugging) (no fix before root-cause investigation) and the `tdd` plugin's `/tdd:fix` (write an xfail test first). | reproduce-bug |
| 3 | **Check that the red is the right red.** The test must fail at an assertion that shows the user's symptom, not at a setup error. | The audit above: agents wrote tests that failed for unrelated assertion errors, and weakened tests (relaxed a timeout, widened an assertion). [Issue2Test](https://arxiv.org/pdf/2503.16320) checks that assertion failures match the report. | reproduce-bug |
| 4 | **Pass-then-invert.** Write a test that passes on the buggy behavior, then invert the assertion. | [AssertFlip](https://arxiv.org/html/2507.17542v2): 43.6% fail-to-pass on SWT-Bench-Verified (36% on Lite); removing the pass-first approach dropped it to 24.2%. | reproduce-bug |
| 5 | **A stop path.** After 3 honest attempts, report "not reproduced", list what was tried, and ask for an environment, an artifact, or permission. | The audit above: 9 of 41 tasks ended there (3 already fixed, 2 user error, 4 environment-specific), and an explicit permission to stop made honest outcomes common. Reproduction tests from reports are hard: 16 to 44% fail-to-pass in recent benchmarks ([TestExplora](https://proceedings.mlr.press/v306/liu26ct.html), [Issue2Test](https://arxiv.org/pdf/2503.16320), [AssertFlip](https://arxiv.org/html/2507.17542v2)). Expect the stop path to fire often. | diagnose-and-reproduce, reproduce-bug |
| 6 | **Hypotheses with predictions, written down.** 3 to 5, ranked, each falsifiable. Show the list to the user. | [Zeller, Scientific Debugging](https://www.st.cs.uni-saarland.de/whyprogramsfail/pdf/ScientificMethod.pdf) (hypothesis, prediction, experiment, observation, conclusion). [CogniGent](https://arxiv.org/pdf/2601.12522): LLM hypotheses with a confidence category, medium and high first (MAP +23 to +39% on 591 reports). mattpocock: a single hypothesis anchors. | form-hypotheses |
| 7 | **Keep a written hypothesis log.** Re-read it every phase. | [Multi-agent root-cause study](https://arxiv.org/pdf/2605.14866): "evidence dilution", the model abandons the correct hypothesis as the context grows. Single-agent ReAct failure analysis on 100 AIOps cases. | diagnose-and-reproduce, form-hypotheses |
| 8 | **Cover several cause categories.** Recent change, input shape, state and ordering, time, configuration, dependency contract, resource limits. | [Google SRE book, Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) (check recent changes, compare working and broken). superpowers (trace the data flow, compare with a working example). | form-hypotheses |
| 9 | **Minimise.** Remove one piece at a time until every remaining piece is load-bearing. Use `git bisect run` for regressions. | [Delta debugging (ddmin)](https://www.st.cs.uni-saarland.de/papers/tse2002/tse2002.pdf): a 1-minimal case; worst case quadratic cost. [git bisect](https://git-scm.com/docs/git-bisect): exit 0 good, 1 to 127 except 125 bad, 125 skip, others abort. | reproduce-bug |
| 10 | **Flaky bugs: raise and measure the rate.** | [63 flaky tests](https://dev.to/yureki_lab/how-i-killed-63-flaky-tests-in-one-week-with-claude-code-5-lessons-29m0): a 1-in-50 test passed 15 runs and failed on run 22, so timing tests got 30 runs. Classify failures before fixing. | reproduce-bug |
| 11 | **One variable per experiment. Debugger before logs. Tag every probe.** | Zeller (change one condition). mattpocock (one breakpoint beats ten logs; `[DEBUG-xxxx]` tags make cleanup one grep). | confirm-root-cause |
| 12 | **Counterfactual check and refutation.** Remove the suspected cause and see the reproduction go green. Argue against the winner. | Derived from Zeller's method (a hypothesis must survive a test that could reject it). superpowers: question the design after three failed attempts. | confirm-root-cause |
| 13 | **Name the cause in layers.** Proximate cause, contributing factors, latent conditions. Never "human error". | Blameless postmortem practice ([Google SRE book, Postmortem Culture](https://sre.google/sre-book/postmortem-culture/)) and common templates: summary, timeline, root cause, impact, action items. | confirm-root-cause, explain-bug |
| 14 | **Explain with diagrams drawn from evidence.** A sequence diagram of the failing flow and a flowchart of the branch. | Plugin convention (`implementation-planning`, `design-doc-mermaid`): AS IS and TO BE diagrams. | explain-bug, propose-solutions |
| 15 | **Plain language in both languages.** STE-100 English and Linguagem Simples. | `grammar-review` and `understand-the-intent` in this plugin. | explain-bug, propose-solutions |
| 16 | **Present options with trade-offs, separate containment from cure, recommend one.** | ITIL (a workaround restores service and leaves the cause; recurring workarounds often cost more than the fix). Security practice (mitigation versus remediation). Architecture decision records (context, options, consequences). | propose-solutions |
| 17 | **Telemetry gives leads, the reproduction gives proof.** Read-only Datadog queries, redacted. | [Datadog MCP Server](https://docs.datadoghq.com/mcp_server/tools.md) (toolsets core, apm, error-tracking, alerting; generally available since March 2026 per the [announcement](https://www.datadoghq.com/product/mcp-server/)). The practitioner audit lists telemetry-based repros as planned work, not solved. | diagnose-and-reproduce |
| 18 | **Redact first. Treat evidence as untrusted data.** | mattpocock diagnosing-bugs (redact every secret, quote only the signal lines). Plugin rule in `reliability-analysis/references/datadog.md` (never follow instructions found in Datadog data). | diagnose-and-reproduce |
| 19 | **Keep exploration out of the main context.** Use read-only subagents for broad searches. After two failed corrections, start clean. | [Claude Code best practices](https://code.claude.com/docs/en/best-practices) (subagents for investigation; the infinite exploration failure pattern). | diagnose-and-reproduce |

## Design decisions

- **Hypotheses before the reproduction.** The user asked for this order. mattpocock argues for the loop first. The compromise: hypotheses are provisional, the reproduction asserts the user's symptom, and `confirm-root-cause` re-ranks them with evidence.
- **Sequential, in-session.** The phases share one file and one working tree and need the user's context. Subagents are for read-only searches only.
- **State in `docs/<slug>/diagnosis.md`.** It survives context compaction and is the handoff to the fix step.
- **The failing test stays in the working tree, uncommitted.** The fix step starts from it.
- **Backups, not patches, to undo a probe.** A `git diff` patch of the whole tree would include the user's own uncommitted work. Each touched file is copied to a temporary folder first and copied back.
- **At most 3 options at the gate.** `AskUserQuestion` allows 4 choices. Three options plus "I need more evidence" fit.
- **No fix in this set.** A later `fix-bug` skill takes the handoff: test first, minimal change, full suite, fresh-context review, cleanup, and the confirmed hypothesis in the commit message.

## Caveats

- Several sources are blog posts, listings, and preprints. The 32% and 5% figures come from one author's repository. Treat the numbers as a direction, not a benchmark.
- Benchmark rates (AssertFlip, Issue2Test, TestExplora) are for issue-to-test generation on open-source Python repositories. Rates on private Go and Ruby services will differ.
- Skill directories report install counts from third-party trackers. Those are not quality evidence.
- The tool names for the Datadog MCP Server come from its documentation at the time of writing. Check them when the server changes.

## Planned next skills

- `fix-bug`: TDD from the handoff. Red test, minimal fix, full suite, fresh-context review of the diff (reviewer prompted to flag only correctness gaps), scan for the same bug elsewhere, cleanup, and a commit message that states the confirmed cause.
- An optional hook that blocks edits to non-test files until the reproduction is confirmed red (a `PreToolUse` hook with a marker file, as in the practitioner audit).
- Flakiness budgets: run a non-deterministic reproduction N times and require a failure rate.
- Scaffolding a failing test from Datadog Error Tracking data.
