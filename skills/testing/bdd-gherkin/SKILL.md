---
name: bdd-gherkin
description: Write business-focused Gherkin/Cucumber BDD feature files using domain-driven ubiquitous language. Use when asked to write BDD scenarios, Gherkin features, acceptance criteria as Given/When/Then, or Cucumber specs. Not for unit/integration test code itself — use the project's test-writing conventions for that.
---

# BDD Gherkin Scenario Writing

Generate feature files with business-focused scenarios describing behavior, not implementation.

## Core principle: domain-driven language

Write scenarios in the language of the business domain, not the database or code.

- Good: `Given a customer with a premium account`
- Bad: `Given the database has user with premium_flag = true`

State business actions and outcomes. Hide technical mechanics unless they add real clarity.

## Workflow

Before generating scenarios, ask clarifying questions about:

- The business capability being described
- Actors/roles involved
- The business value or rule at stake
- Constraints and edge cases
- Common preconditions shared across scenarios (candidate for `Background`)

Do not guess these from a vague request — a wrong assumption here produces scenarios nobody wanted.

## Scenario shape

**One business rule per scenario.** Each scenario verifies exactly one rule, independently of others.

**One `When` per scenario.** Exactly one action or event triggers the behavior under test. Supporting data belongs in `Given`, not spread across multiple `When` steps.

**Data tables for multi-field context.** When a `Given` needs 2+ related fields, or a step is getting long, use a data table instead of cramming values into prose.

```gherkin
Given the following customer:
  | tier    | orders_this_year |
  | premium | 12                |
```

**Scenario Outlines sparingly.** Default to plain `Scenario`. Reach for `Scenario Outline` only when the data variation itself is the point being tested (e.g. a discount table across tiers) — not as a default way to avoid writing two scenarios.

**Journey scenarios only when asked.** Default to single-focused scenarios. Only write a multi-step journey/flow scenario if the user explicitly requests it.

## Anti-patterns to avoid

- Technical implementation detail in Given/When/Then (SQL, HTTP status codes, internal function names)
- `Scenario Outline` used out of habit rather than necessity
- Multiple `When` steps in one scenario — consolidate into the single high-level action
- Journey/flow scenarios when a single-rule scenario was asked for
- Long inline value lists in a `Given` step instead of a data table

## Structure reference

```gherkin
Feature: <capability, in business terms>

  Background:
    Given <precondition shared by every scenario below>

  Rule: <business rule, when scenarios cluster around one>

    Scenario: <one specific case of the rule>
      Given <context>
      When <single action>
      Then <observable business outcome>
```

Keep `Then` steps observable from the business's point of view (what the customer/user sees or receives), not internal state changes.
