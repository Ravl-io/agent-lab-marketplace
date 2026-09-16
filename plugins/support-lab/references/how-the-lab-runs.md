# How the lab runs

The working agreement, for the tutor. The participant hears the short version in the
orientation; this is the long version.

## The loop

Every step is the same four moves:

| | |
|---|---|
| **Frame** | why this step exists, in the participant's terms, in a few lines |
| **Ask** | one thing for them to type, as a quoted prompt they can copy |
| **Execute** | Claude Code does the real work, under the workspace's `CLAUDE.md` |
| **Judge** | on "next": the tutor checks the result against the expected values, says what was right and missing, and either clears the step or gives them the sentence to ask |

## The contract

**They ask. Claude Code executes. They judge.** The tutor never does a step before it is
asked for, never silently fixes a findings sheet, and never changes a customer's
configuration. When something is missing, the tutor gives the participant the words to ask.

## Answer keys live in the step files

Each step file carries the verified expected values (timestamps, counts, verdicts). The tutor
reads one step file at a time, so only the current step's answers are in context. When the
participant types an investigation prompt, the answer must come from running the real
commands — never from the step file.

## State

`.support-lab/state.json`, changed only by `scripts/state.py`. A step is **open** once
presented and **cleared** once judged. The session banner hook prints the position at every
session start, which is how the new-session step (S10) finds its way back.

## Reset

`lab reset` removes findings, the built plugin and the state, and keeps the sandbox. Between
cohorts the facilitator runs it in every participant folder.
