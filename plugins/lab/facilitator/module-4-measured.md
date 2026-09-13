# Module 4 — what the numbers actually do

**Facilitator reference.** Measured while building the module.

## The gate: nine behaviours, all verified

Unlike Modules 2 and 3, the central claim here is not a quality metric — it is a **security
property**, and it either holds or it does not. Measured end to end on the reference gate:

| # | What was attempted | Result |
|---|---|---|
| 1 | apply with no approval | **denied** |
| 2 | write the published file by hand | **denied** |
| 3 | write a proposal | allowed — proposing has no effect, so nothing gates it |
| 4 | apply after a human approved | allowed |
| 5 | the apply tool runs | published, and recorded who approved |
| 6 | replay the same approval | **denied** — single-use |
| 7 | edit the proposal after approval, then apply | **denied** — digest mismatch |
| 8 | the same tampered apply, run directly rather than by the agent | **denied by the tool itself** |
| 9 | the audit trail | records the apply and both refusals |

Rows 6, 7 and 8 are the ones worth spending time on, because they are the three properties
people leave out when they build one of these in a hurry.

## The three properties that make it an approval rather than a permission

**It is of a specific artifact.** The approval records a SHA-256 of the proposal JSON *and*
the prose body a human actually read. Change either and the approval stops describing what is
about to happen. Without this, "approved" quietly means "this agent is trusted", which is a
different and much larger claim.

**It is single-use.** `tools/apply.py` marks it consumed and the gate refuses a consumed one.
A replayable approval is a standing permission with extra steps.

**It is checked in more than one place.** The hook guards the agent's route to the tool; the
tool re-checks for everything else — a script, a CI job, somebody's terminal. A control that
exists in one layer only exists until somebody takes a different route. Demonstrate row 8 for
exactly this reason: the participant runs the command themselves, outside the agent, and it
still refuses.

## What it deliberately does not do

It does not stop `Bash` from reaching the published directory by other means — `cp`, `mv`, a
`>` redirect. **Say this out loud rather than letting someone find it.** It is the same
incompleteness as Module 1's write boundary and it has the same answer: you cannot enumerate
the ways to write a file.

The honest framing is the layer list from Module 1, now complete:

| Layer | Where it came from |
|---|---|
| which tools exist at all | Module 1, step 1 |
| which of them may run unprompted | `permissions` in settings.json |
| what a permitted tool may touch | Module 1's write boundary |
| **who approves the consequential action** | this module |

Any one alone is theatre. A participant who leaves believing the gate is sufficient on its
own has been taught the wrong thing.

## The question to expect

*"Can the agent not just approve its own proposal by writing the approval file?"*

Yes — with a `Write` tool and no other control, it can. That is not a flaw in the gate, it is
the layer list again: the approval directory belongs in the write boundary's protected set,
and on a real deployment `/approve` is a different process with a different identity. Take
the question seriously when it comes; it is the sharpest thing anybody asks in this module,
and the answer is "controls are layered", not "it cannot happen".
