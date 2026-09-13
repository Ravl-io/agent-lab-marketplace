# Module 4 — The full AI system

**Two hours.** They end with plugin v1.0: a spec, a proposal pipeline, an approval gate that
holds, a full eval suite, a runbook — and a capstone they ran in front of the room.

## What this module is for

By the end they should be able to answer, out loud, to a colleague: *what is my job now?*

Everything before this made the agent more capable. This module is about what a person is
still for, and the answer is specific: intent, boundaries, the evals, and the approval. Not
"oversight" in the abstract — four named jobs they will do on Monday.

## The arc

| Step | Time | What they do | Checkpoint |
|---|---|---|---|
| **1** | 16m | **The spec** — acceptance criteria as scenarios, out of scope, policies, approval | `M4.C1-spec` |
| **2** | 24m | **The proposal pipeline** — the agent does the whole job and applies none of it | `M4.C2-proposal` |
| **3** | 20m | **The approval gate** — a hook that refuses, and an approval that means one thing | `M4.C3-gate` |
| **4** | 14m | **The full suite** — retrieval, graph, proposals, integrity. Then the audit log | `M4.C4-suite` |
| **5** | 24m | **Capstone** — their system, end to end, on a case graded against a key they have not seen | `M4.C5-capstone` |
| **6** | 14m | **The autonomy ladder, and what to do on Monday** | module complete |

**No setup step.** Nothing new to install: the gate is a hook, the spec is markdown, the suite
is the two harnesses they already have plus one new check. Say so — it is the last piece of
evidence for the claim the course has been making since Module 1, that this is all made of
small, ordinary parts.

## The result this module rests on

The central claim here is not a quality metric. It is a **security property**, and it either
holds or it does not. Measured on the reference gate, nine behaviours, all verified — the
table is in `facilitator/module-4-measured.md`. Read it before you teach this.

The three that matter, because they are the three people leave out:

| | |
|---|---|
| an approval covers **one artifact** | edit the proposal afterwards and applying is refused |
| an approval is **single-use** | a replayable one is a standing permission with extra steps |
| the check exists in **more than one layer** | the tool refuses even when the agent is not involved |

## The autonomy ladder — the thing they take to their team

Put this up early in step 1 and leave it up. It is the most useful thing in the module for
anybody who has to explain this work to a manager.

| Level | The agent | The human |
|---|---|---|
| L0 | suggests in chat | everything |
| L1 | drafts a proposal | reads, decides, applies by hand |
| L2 | applies in a sandbox, runs the evals | reviews the results, promotes |
| **L3** | **applies behind an approval gate** | **approves each change — this is where we land today** |
| L4 | applies autonomously, with monitoring and rollback | sets policy, audits, owns outcomes |

Two things to say about it:

**L3 is not a stepping stone to L4.** For most consequential work L3 is the destination, and
saying otherwise is how people end up promising autonomy nobody wanted. Ask the room which of
their own tasks they would ever want at L4; the answers are usually narrower than they expect.

**They have been at L1 since Module 1** without anybody naming it. Today is the step to L3.

---

## Step 1 — The spec (16 minutes)

### 1.1 Install it

```
/lab:next
```

Stage `m4s1-spec` installs `spec/capability.md` and `spec/capability.json`. The JSON is not
paperwork: the gate reads `published_to` from it to know which directory it is guarding.

### 1.2 Why a spec and not a longer prompt

They have written prompts, a skill, an intent and an ontology. So put the question directly:
*what does a spec give you that a very good prompt does not?*

Four answers, and the last is the one that matters here:

| | |
|---|---|
| durable | it outlives the conversation it was written in |
| reviewable | somebody who was not in the room can disagree with it |
| reusable | it applies to every case, not the one in front of you |
| **testable** | each criterion is something you could hand a colleague as pass/fail |

Their `intent.md` from Module 1 is the input. Its **Proposed outcome** section becomes the
acceptance criteria almost word for word — point that out, because it makes the case for
having written intent.md at all.

### 1.3 Scenarios, not adjectives

Acceptance criteria go in as Gherkin, for one reason: a scenario is checkable and an
adjective is not. "Handles missing evidence appropriately" cannot be failed by anybody.

Three scenarios minimum: the normal case, the case where the evidence is not there, and
**approval being required**. The third is the one nobody writes, and it is the control this
module adds.

### 1.4 The section that does the most work

**Explicitly out of scope.** At least three things.

A capability with no stated boundary grows until nobody can review it, and "what does this
NOT do" is the first question a reviewer asks. Make them name the neighbouring jobs somebody
will assume are included.

Then **rollback**: for every action, how it is undone and by whom. If an action cannot be
undone, that sentence is the most important one in the document, because it tells the
approver what they are actually deciding.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_spec.py"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M4.C1-spec
```

The gate flags unmeasurable words. Read those out — each one is a criterion nobody can fail.

---

## Step 2 — The proposal pipeline (24 minutes)

### 2.1 The frame, and it is not about trust

```
/lab:next
```

Stage `m4s2-propose` installs the `propose` skill, with the procedure left to them.

The skill does the whole job and then **stops**. Be careful how you justify that, because the
obvious justification is wrong. It is not that the agent is unreliable — by now theirs is
quite good, and everyone in the room can see that.

> Deciding and doing are different operations, and the consequential action has an owner.
> Ownership requires a moment where somebody could have said no.

That holds whether the agent is bad at the job or excellent at it. An agent that is right 99
times out of 100 and applies its own conclusions has simply moved the accountability to
nobody.

### 2.2 What a proposal has to carry

Two files: the prose a human reads, and the JSON a machine applies.

| Field | Why an approver needs it |
|---|---|
| `actions` | what will happen, and nothing outside this list |
| `evidence` with `via` | which source, and **which system found it** — retrieval or graph |
| `confidence` | how sure the analysis is |
| `risk` | how bad it is if that is wrong |
| `rollback` | how it is undone, by whom, how fast |
| `unresolved` | what the agent could not determine |

Two of these are worth dwelling on.

**`confidence` and `risk` are not the same axis** and they vary independently. A
high-confidence, high-risk proposal still deserves a careful read. Most people conflate them
and then wonder why their approvers rubber-stamp things.

**`via` looks like bookkeeping and is not.** When a proposal turns out to be wrong, the first
question is which system misled you — and that is unanswerable afterwards unless somebody
wrote it down at the time.

### 2.3 They run it on a real case

Their track's main case, not the capstone one. Then:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_proposal.py" <id>
```

It checks structure, that every cited file exists, that both systems were used, and that
nothing has been applied. Then read one out loud to the room and ask: **would you approve
this?** The answer is usually "not yet", and the reasons are the lesson.

### 2.4 The failure to look for

A proposal with `unresolved: []` on a case that plainly has unknowns. It reads as confidence
and it is the opposite — the agent has smoothed over the gaps rather than naming them. Push
on any group whose proposal declares nothing unresolved.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M4.C2-proposal
```

---

## Step 3 — The approval gate (20 minutes)

### 3.1 Install it

```
/lab:next
```

Stage `m4s3-gate` installs the hook with its two decision functions left to them, plus
`gate/approve.py` and `tools/apply.py` as given plumbing.

They register the hook in `settings.json` on `PreToolUse` — matching `Write|Edit|Bash` this
time, not just the write tools, because applying happens through a command.

### 3.2 What they write, and the three properties

Two functions: hash the proposal, and decide whether an apply may proceed.

**The hash covers the JSON and the prose body.** Hashing only the JSON would let the wording
a human actually read change under an approval that still verified. This is the property that
makes an approval narrower than a permission: it describes one artifact.

**The approval is single-use.** `apply.py` marks it consumed; the gate refuses a consumed one.

**The check lives in two places.** The hook guards the agent's route; the tool re-checks for
everything else — a script, a CI job, somebody's terminal. Demonstrate this: have them run
`python3 tools/apply.py <id>` themselves, outside the agent, on a tampered proposal. It still
refuses. A control that exists in one layer only exists until somebody takes another route.

### 3.3 Walk the whole cycle in front of them

Seven commands, and it is worth doing in this order:

```
python3 gate/approve.py <id> --show      # read it
python3 tools/apply.py <id>              # refused: not approved
python3 gate/approve.py <id>             # a human agrees to THIS
python3 tools/apply.py <id>              # applied, and audited
python3 tools/apply.py <id>              # refused: single-use
python3 gate/approve.py <id>             # approve again
#  ... now edit one line of proposals/<id>.md ...
python3 tools/apply.py <id>              # refused: it changed since approval
```

The last two are the moment. Somebody will say "but I only fixed a typo" — which is exactly
right and exactly the point: the gate cannot tell a typo from a changed amount, so it refuses
both. Approval is of a thing, not of a person's good intentions.

### 3.4 Say what it does not do, before anybody finds it

It does not stop `Bash` from reaching the published directory with `cp`, `mv` or a `>`
redirect. Same incompleteness as Module 1's write boundary, same answer: you cannot enumerate
the ways to write a file.

The layer list from Module 1 is now complete, and this is the slide they should leave with:

| Layer | Where it came from |
|---|---|
| which tools exist at all | Module 1, step 1 |
| which of them may run unprompted | `permissions` in settings.json |
| what a permitted tool may touch | Module 1's write boundary |
| **who approves the consequential action** | this module |

**Any one alone is theatre.** A participant who leaves thinking the gate is sufficient by
itself has been taught the wrong thing.

### 3.5 The sharpest question you will get

*"Can the agent not just write its own approval file?"*

Yes — with a `Write` tool and no other control, it can. Take the question seriously: it is the
best thing anybody asks in this module. The answer is the layer list again. The approvals
directory belongs in the write boundary's protected set, and in a real deployment `/approve`
is a different process with a different identity. The answer is "controls are layered", not
"that cannot happen".

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M4.C3-gate
```

---

## Step 4 — The full suite (14 minutes)

### 4.1 Run everything

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/eval_all.py"
```

Four sections: retrieval, graph, proposals, **integrity**.

### 4.2 Integrity is the one to read first

The other three are questions about usefulness. Integrity asks whether the controls held, and
it is the only part with a wrong answer nobody can argue with: a file in the published
directory that no approval accounts for.

Demonstrate it. Write a file into the published directory by hand and re-run:

> `triage/CASE-4999.md` is published but no audit entry accounts for it. Something wrote it
> directly — the gate was bypassed, or it predates the gate.

That is the check that would catch a real incident, and it is four lines of code.

### 4.3 Evals are the new tests, and say why precisely

They have three kinds of measurement now, and they are not interchangeable:

| | Answers | Fails when |
|---|---|---|
| retrieval score | is the right passage coming back, affordably | wording, chunking, embedding |
| graph score | are the sets complete and the dates right | extraction gaps, modelling errors |
| integrity | did anything escape the gate | a control is missing or bypassed |

A system can score well on the first two and be unsafe. Naming that is the point of running
them together.

### 4.4 Read the audit log

```
cat audit.jsonl
```

Every apply and every refusal, with who approved and when. Ask the room the question this
exists to answer: *six weeks from now, somebody asks why this went out. What do you show them?*

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M4.C4-suite
```

---

## Step 5 — Capstone (24 minutes)

The full instructions and the answer keys are in `facilitator/module-4-capstone.md`. Read it
beforehand; it is the only part of this course you cannot run cold.

### 5.1 Set it up honestly

One case, their system, end to end: propose → a human reads it → approve → apply → suite →
audit. Fifteen minutes to run, then demos.

Tell them the answer key exists and that it is in the plugin on their own machine. Ask them
not to look. It is the last exercise of eight hours and the room is invested; in practice
nobody looks.

### 5.2 Grade four things, out loud, no points total

1. **Did the gate hold?** `eval_all.py`. Pass or fail.
2. **Is every claim cited?** Pick two at random and ask for the source.
3. **Did it catch the planted thing?** Their track's table in the capstone notes.
4. **Does `unresolved` say something real?** An empty one on a case this hard is a tell.

### 5.3 Then put the three tracks side by side — do not skip this

Five minutes. A triage note, a findings pack, a monthly report, next to each other.

Three unrelated domains, three different corpora, **one architecture**: skill, tool, hook,
retrieval, graph, proposal, gate. That is the transferable claim of the whole course and it
only lands if they see the other two tracks. Somebody who spent eight hours on support
tickets should leave knowing they built a pattern, not a triage tool.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M4.C5-capstone
```

---

## Step 6 — What your job is now (14 minutes)

### 6.1 Package v1.0

```
/lab:next
```

Stage `m4s4-runbook` installs `RUNBOOK.md`. Its most valuable section is **"when not to trust
it"** — at least three things, and they should be specific to what they built.

Then the last packaging move: the `propose` skill goes into the plugin, they add an `approve`
skill so a human has a command to run, and the version becomes `1.0.0`.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_plugin.py"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/eval_all.py"
```

The gate and the apply tool stay in the project, for the reason they have now met twice:
they depend on `proposals/`, `approvals/` and `audit.jsonl`, which are situation, not
capability.

### 6.2 Where the review moved

The thing they should notice about the last two hours: **they stopped reviewing output and
started reviewing specs and evals.**

That is the change in the job. Reviewing every output does not scale and never did. Reviewing
the spec, the evals and the boundary does — and then approving the consequential action,
which is the one thing that cannot be delegated because it is where accountability lives.

### 6.3 The four jobs that are still a person's

Not "oversight". Four named things, and it is worth going round the room on which of these
they are weakest at:

| | |
|---|---|
| **Intent** | deciding what is worth building, and what "good" means. `intent.md` |
| **Boundaries** | what it must never do. The spec's out-of-scope, the hooks, the permissions |
| **Evals** | deciding what counts as right. Nobody else can author your golden set |
| **Approval** | owning the consequential action |

Then the sentence to end the course on:

> Every one of those is a judgement, and none of them is the part anybody was worried about
> being automated.

### 6.4 Monday

Concretely, in their own work. Three things, and hold them to picking one:

1. **Point it at your real documents.** Same architecture, their corpus. The golden set is
   the only real work, and it is a couple of hours.
2. **Write the intent and the spec first**, before any prompt. That habit is the single
   biggest difference between this and what they were doing on Friday.
3. **Do not skip the gate.** The first system anybody builds that acts without one is the
   last one their organisation lets them build.

### 6.5 Close

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" complete-module 04
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" show
```

Show them the scoreboard, all of it: the retrieval arc from Module 2, the graph scores from
Module 3, and a plugin at v1.0. Eight hours ago the model could not open a file.

---

## If the clock has beaten you

| Keep at all costs | Step 3.3 (the seven-command cycle) and step 6.3 (the four jobs). The module's two moments |
|---|---|
| Cut to a demo | Step 5 — you run the capstone on one track, the room grades it. It survives being watched |
| Shorten | Step 2 to 15 minutes by having them propose on a case they already triaged in Module 1 |
| Never cut | Step 3.4, the layer list. A room that leaves believing a gate is sufficient on its own is worse off than one that never saw it |

If you are badly over, cut step 4 to running `eval_all.py` once and reading the integrity
line. The suite is the artifact; the walkthrough of it is not.
