# Session 0 — getting the room running

The single biggest risk to this training is not the content. It is twenty machines that each
break differently in the first fifteen minutes. This document exists to move that pain to
48 hours before the session, where it costs nothing.

---

## Send this 48 hours ahead

> **Before our first Agent Lab session**
>
> Please do these three things now — they take about ten minutes, and doing them in advance
> means we spend the session building rather than installing.
>
> **1. Have these installed:**
> - VS Code, with the Claude Code extension, signed in and working
> - Python 3.10 or newer
> - Git
>
> **2. Make a folder for the lab and open VS Code in it:**
> ```
> mkdir ~/agent-lab && cd ~/agent-lab && code .
> ```
>
> **3. In the Claude Code panel, run these three commands:**
> ```
> /plugin marketplace add <owner>/agent-lab
> /plugin install lab@agent-lab
> /lab:checklist
> ```
>
> `/lab:checklist` will tell you whether anything is missing and exactly how to install it on
> your machine. If it reports a problem you cannot fix, reply to this message and we will sort
> it out before the session rather than during it.
>
> You do not need to do anything else. Do not run `/lab:start` yet — we will do that together.

Two notes for you, not for them:

- **macOS ships Python 3.9 as `python3`.** Many participants will look like they fail the
  Python check. They almost certainly have a newer interpreter under another name — the
  doctor searches for it (`python3.12`, `python3.11`, `python`, and so on), picks the newest
  one that qualifies, and records it. If it reports READY while mentioning a different
  interpreter, that is correct and needs no action.
- **`/lab:checklist` only lists; it checks nothing.** `/lab:doctor` is the one that verifies.
  The pre-flight message deliberately asks for the checklist because it reads as a list of
  instructions rather than a verdict, which gets more people to act on it.

## Opening the session

Walk the room through it out loud, together, one command at a time. Do not let people run
ahead — a participant who is three commands ahead and stuck is harder to help than the whole
room moving in step.

1. **"Open VS Code in your lab folder."** Confirm out loud that nobody is in their home
   directory or a work repo. `/lab:start` refuses to run in either, but it is faster to catch
   it now.
2. **"Run `/lab:start`."** It will orient them, show the curriculum, list the checklist,
   check their machine, and ask for their track. Let it talk; it is written to be read in a
   chat panel.
3. **Assign tracks by group** before they answer the track question, or let them choose. If
   you assign them, tell them the exact id to give: `support-triage`, `vendor-qa`, or
   `docgen`.
4. **Wait for every machine to report READY** before you start teaching. This is the last
   cheap moment to fix an environment. Ask for a show of hands on who is not ready.

Expect this to take twelve to fifteen minutes with a room that did the pre-flight, and
thirty without it.

## The trust dialog

Claude Code ignores a project's `permissions` block until the workspace is trusted. The
first time a participant opens Claude Code in their lab folder they get a trust prompt, and
they must accept it. If they do not, every tool call stops to ask for approval and the
experiments in Module 1 stall.

The symptom is a line like *"Ignoring 2 permissions.allow entries from
.claude/settings.json: this workspace has not been trusted."* Tell the room about it before
it happens; it is thirty seconds to fix and confusing to diagnose mid-exercise.

## When a machine will not cooperate

In priority order:

1. **`/lab:doctor`** and read the actual failure. It names the fix for their platform. Let
   the tutor run the install command for them.
2. **Wrong interpreter.** If Python is genuinely too old with nothing newer available:
   `brew install python@3.12` on macOS, `winget install Python.Python.3.12` on Windows. Then
   `/lab:doctor` again.
3. **Plugin not showing up.** `/reload-plugins`. If the skills still do not appear:
   `rm -rf ~/.claude/plugins/cache`, restart, reinstall.
4. **Marketplace not found.** They typed the owner or repo wrong, or lack read access to a
   private repo. Check their GitHub authentication.
5. **Corporate network blocks PyPI.** The network check will fail. This one you cannot fix in
   the room — pair them with a working machine for the session and follow up afterwards.
6. **Out of time.** Pair them. Two people on one machine learn more than one person watching
   an install bar. Note it and move on; do not hold twenty people for one laptop.

## Assigning tracks deliberately

The three tracks teach the same architecture but each makes a different lesson land hardest.
Assign accordingly:

| Track | Hardest lesson it lands | Give it to |
|---|---|---|
| `support-triage` | Evidence before conclusions, and why an approval gate is not optional | Support, service desk, or any team doing L2/L3 diligence. Documents plus a database |
| `vendor-qa` | Completeness — "which requirements has nobody verified?" is unanswerable by similarity search | A group that will appreciate the coverage/gap argument. Audit, compliance, delivery management |
| `docgen` | Aggregation and change over time — "what moved since the last report?" | Your least experienced group. Gentlest ramp, one document set, one output |

All three land on the same v1.0 architecture, which is the point of the Module 4 comparison.
If a group finishes early, the interesting extension is always the same: point their pipeline
at their own real documents.
