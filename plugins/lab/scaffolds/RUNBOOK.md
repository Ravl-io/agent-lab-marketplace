# RUNBOOK — {{SYSTEM_NAME}}

What somebody else needs in order to run this, and to know when not to trust it. Written for
a colleague who was not in the room, because in six months that includes you.

## What it does

TODO — two sentences. The capability, and the one thing it will not do.

## How to run it

TODO — the actual commands, in order, from a fresh checkout.

Include the setup: the virtualenv, the dependencies, building the vector store and the graph.
Somebody following this on a new machine should not have to guess.

## The approval step

TODO — who approves, what they are looking at, and how.

Be specific about what an approver should check before agreeing. A gate that everybody clicks
through is an audit trail, not a control.

## When not to trust it

TODO — at least three things. This is the most valuable section in the document.

Think about: questions outside the spec; a corpus that has changed since the graph was
extracted; a case unlike anything in the golden set; the difference between low confidence
and high risk.

## How to tell it has gone stale

TODO — the checks, and how often.

The graph is a snapshot. The vector store is a snapshot. Nothing tells you they have drifted
except running something. Say what to run and when.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/eval_all.py"
```

## Rollback

TODO — for each action the system can take, how to undo it and who can.

## Who owns it

| | |
|---|---|
| The capability | TODO — a role |
| The ontology and the spec | TODO — a role |
| Approving its output | TODO — a role |
| The evals | TODO — a role |

Roles, not names. A name survives exactly as long as that person does.
