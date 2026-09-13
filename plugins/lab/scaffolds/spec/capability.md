# Specification — {{SYSTEM_NAME}}

The thing you have been building for three modules, written down so somebody else could tell
whether it works.

**Why a spec and not a longer prompt.** A prompt is a request; a spec is a claim about what
must be true. The difference shows up the moment anything changes: a prompt has to be
re-argued, a spec is re-checked. It is durable, reviewable by someone who was not in the
room, reusable across cases, and — the part that matters most here — **testable**. Every
acceptance criterion below should be something you could hand to a colleague as a pass/fail.

Your `intent.md` from Module 1 is the input to this. Its **Proposed outcome** section is
where the acceptance criteria come from, almost word for word.

## The capability

TODO — one paragraph. What this does, for whom, on what input, producing what.

Not "helps with triage". Something a stranger could recognise when they saw it happen.

## Acceptance criteria

Written as scenarios, because a scenario is checkable and an adjective is not. Three or
four is enough — cover the normal case, the case where evidence is missing, and the case
where the answer is "I cannot tell you".

```gherkin
Feature: TODO — the capability, in three words

  Scenario: TODO — the normal case
    Given TODO — the starting state, in terms of real files
    When TODO — the command somebody runs
    Then TODO — what is true afterwards, checkably
    And TODO — every claim carries a source

  Scenario: TODO — the evidence is not there
    Given TODO
    When TODO
    Then the output says what it could not determine
    And no proposal is applied

  Scenario: TODO — approval is required
    Given a proposal has been produced
    When nobody has approved it
    Then applying it is refused
```

Write these before you build anything else in this module. They are what the eval suite
checks and what the capstone is graded against.

## Explicitly out of scope

TODO — at least three things.

This section does more work than the one above it. A capability with no stated boundary
grows until it is unreviewable, and the first question a reviewer asks is "what does this
NOT do". Name the neighbouring jobs somebody will assume are included.

## Policies it must respect

TODO — the rules that hold regardless of what any individual case makes tempting.

Look at your track's policy document; these are mostly already written. Each one should be
something the eval suite can check, not an aspiration.

## Approval

| | |
|---|---|
| What requires approval | TODO — the consequential action, precisely |
| Who may approve | TODO — a role, not a name |
| What they are approving | TODO — the specific artifact, and what it will do |
| What happens if it is edited after approval | the approval no longer holds and applying is refused |

## Rollback

TODO — for each action this capability can take, how it is undone, and by whom.

If an action cannot be undone, say so here explicitly. That is the most important sentence
in this document, because it tells the approver what they are actually deciding.
