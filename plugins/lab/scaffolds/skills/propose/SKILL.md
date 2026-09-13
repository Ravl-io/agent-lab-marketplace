---
name: propose
description: TODO — say what this proposes and WHEN. It must be clear that this skill never acts, only proposes.
---

# Produce a proposal. Change nothing.

This skill does the whole job and then **stops**. It writes a proposal describing what should
happen, with the evidence for it, and applies none of it.

That separation is the entire point of this module: **deciding and doing are different
operations, and a human belongs between them.** Not because the agent is unreliable — by
now yours is quite good — but because the consequential action has an owner, and ownership
requires a moment where somebody could have said no.

## What you produce

Two files, and both matter:

`proposals/<id>.md` — the human-readable proposal. This is what a person actually reads
before approving. Write it for a colleague who has not seen the case.

`proposals/<id>.json` — the machine-readable half:

```json
{
  "id": "<id>",
  "capability": "<from spec/capability.json>",
  "body": "proposals/<id>.md",
  "confidence": "high | medium | low",
  "risk": "low | medium | high",
  "actions": [{"type": "write", "path": "{{OUTPUT_DIR}}/<id>.md", "from": "proposals/<id>.md"}],
  "evidence": [{"via": "retrieval | graph", "source": "data/...", "supports": "<the claim>"}],
  "rollback": "<how this is undone, and by whom>",
  "unresolved": ["<what you could not determine>"]
}
```

## Procedure

### 1. Read the spec first

TODO — write this step.

`spec/capability.md` says what this capability is for, what it must not do, and which
policies hold. A proposal that violates the spec is not a judgement call; it is out of scope,
and saying so is a valid outcome.

### 2. Do the work, using both systems

TODO — write this step.

You have retrieval and a graph, and Module 3 taught which is for what: **graph for the set,
retrieval for the sentence.** A proposal resting only on retrieved passages will be missing
whatever completeness question the case turns on.

### 3. Evidence, per claim

TODO — write this step.

Every claim in the proposal names its source, and records whether it came from retrieval or
the graph. The `via` field is not bookkeeping: when a proposal turns out to be wrong, the
first question is which system misled you, and that is unanswerable afterwards if nobody
wrote it down.

### 4. Confidence and risk, and they are not the same thing

TODO — write this step.

**Confidence** is how sure you are that the analysis is right. **Risk** is how bad it is if
you are wrong. They vary independently, and the pair is what an approver actually needs: a
high-confidence, high-risk proposal still deserves a careful read.

Say what would change your confidence. "Low confidence" with no reason is not information.

### 5. The rollback plan

TODO — write this step.

For every action: how it is undone, by whom, and how quickly. **If an action cannot be
undone, say so in the proposal itself**, not just in the spec. An approver deciding about an
irreversible action should have to read the word "irreversible".

### 6. What you could not resolve

TODO — write this step.

List it, in `unresolved`. A gap you declare is a gap the approver can weigh; a gap you smooth
over becomes their problem after they have signed.

## Constraints

- **Never apply anything.** Not a write into the published location, not a command that
  publishes. The gate will refuse you, but do not make it do the work of your own discipline.
- Never propose an action the spec puts out of scope.
- Never claim something no source supports. If it is judgement, label it as judgement.
- Never leave `unresolved` empty because it looked better that way.

## How you will be judged

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_proposal.py" <id>
```

It checks the structure, that evidence cites real files, that both systems were used, and
that nothing has been applied. Then a human reads it — which is the check that counts.
