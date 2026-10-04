# AI code review: strategies that work

Research notes (2026-10-04) behind the `code-reviewing` skills. Each skill in the set should cite the strategies it uses. Update this file when new evidence changes a strategy.

## Strategies, and where they are used

| # | Strategy | Evidence | Used by |
|---|---|---|---|
| 1 | **Split detection and verification.** One pass finds candidates with high recall. A second pass tries to refute each one. | Multi-agent SAST + LLM filter on OWASP Benchmark: precision 0.695 to 0.951, false positives down 88.6%, recall down only 3.1% ([QASecClaw](https://arxiv.org/html/2605.01885v1)). Confirmed by [OpenAnt](https://arxiv.org/html/2606.19149v2) (adversarial verification step). | security-analysis |
| 2 | **Slice the review.** Review one entry point or one risky operation at a time, not the whole diff or repo. | Long context degrades recall, with a bias against the middle of the input ([Needle in the haystack](https://devansh.bearblog.dev/needle-in-the-haystack/)). 41% of surveyed studies use slicing, graphs, or RAG to fit context ([LLMs in Software Security survey](https://arxiv.org/pdf/2502.07049)). | security-analysis |
| 3 | **Give a one-page threat model.** Entry points, trust boundaries, attacker model, high-risk operations. Skip long scaffolding. | Vague "find all vulnerabilities" prompts cause generic pattern matches. Over-scaffolding inflates the haystack ([Needle in the haystack](https://devansh.bearblog.dev/needle-in-the-haystack/)). | security-analysis |
| 4 | **Use adversarial framing.** Ask "how would you break this?" and require a concrete exploit scenario. | Same source: inverted questions and exploit requests beat "is this secure?". Proof requirement cuts hallucinated findings. | security-analysis |
| 5 | **Compare to a secure or existing pattern.** Ask how the code differs from the standard secure version, or from how the repo does it elsewhere. | [Anthropic security review](https://github.com/anthropics/claude-code-security-review/blob/main/.claude/commands/security-review.md) (repo context research, then comparative analysis). | security-analysis |
| 6 | **Structured reasoning.** Summarize what the code does, then list how it could fail, then decide. | Chain-of-thought and multi-level prompts improve precision and recall on vulnerability detection ([prompting vs static analysis](https://arxiv.org/html/2412.12039v3)). | all |
| 7 | **Use static analyzers as candidate generators.** The LLM verifies and explains. It does not replace the tool. | Same syntax can be safe or unsafe depending on context. LLM context review removes most scanner false positives ([QASecClaw](https://arxiv.org/html/2605.01885v1), [industry study](https://arxiv.org/pdf/2601.18844)). | security-analysis |
| 8 | **Set a confidence threshold and hard exclusions.** Report only at 0.8 or higher. Exclude DoS, hardening gaps, theoretical races, and similar. | [Anthropic security review](https://github.com/anthropics/claude-code-security-review) (confidence scale, exclusions, precedents). | security-analysis |
| 9 | **Fail open.** If a check cannot be completed, keep the finding as "needs human check". Never silently drop it. | [QASecClaw](https://arxiv.org/html/2605.01885v1) (fail-open policy). | security-analysis |
| 10 | **Category-specific prompts for policy bugs.** Trust boundaries, tenant isolation, and business-logic authorization need the intended rule, not a pattern. | [QASecClaw](https://arxiv.org/html/2605.01885v1): trust-boundary category underperformed with generic prompts. | security-analysis |
| 11 | **Iterate once with "what else?"** to get past the obvious findings. Stop after one extra pass. | [Needle in the haystack](https://devansh.bearblog.dev/needle-in-the-haystack/). | security-analysis |
| 12 | **Budget the effort.** Under 10% scaffolding, 60-80% slice audits, 20-30% verification. | [Needle in the haystack](https://devansh.bearblog.dev/needle-in-the-haystack/). Single-author recommendation, treat as a heuristic. | all |

## Caveats

- Most benchmark numbers come from synthetic suites (OWASP Benchmark, Java). Real-world precision will differ.
- Several sources are blog posts or preprints. Treat strategy 12 and the adversarial-framing claims as heuristics, and re-check them against our own review results.
- LLM review does not replace SAST, dependency scanning, secret scanning, or a human security review for high-risk changes.

## Planned next skills

Ideas for the rest of the set, not built yet. Pick one at a time.

- Correctness and logic review (edge cases, error paths, concurrency).
- Test review (coverage of the change, brittle tests, missing negative cases).
- Performance review (N+1, hot paths, allocation).
- API and contract review (breaking changes, versioning).
- A review orchestrator that runs the specialist reviews on the same slices and merges findings.
