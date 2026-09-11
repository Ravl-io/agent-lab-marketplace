---
name: start
description: Start or resume Agent Lab — orientation, curriculum, setup checklist, environment validation and track selection.
disable-model-invocation: true
allowed-tools: Bash, Read, AskUserQuestion
---

Start or resume the Agent Lab training for this participant.

## Output discipline — read this first

This is the participant's first contact with the training. It must read like a short
orientation, not a build log.

- **Never narrate the mechanics.** No "let me check the folder", no "first time through, track
  is null", no "now let me present the orientation". Run the scripts silently and present
  results.
- **Four messages, maximum**, for the whole first-time flow: the introduction, the checklist,
  the environment verdict, the track question. Merging the checklist into the introduction is
  fine and often better.
- **Be brief everywhere except the introduction.** The checklist is a list, not an
  explanation. The track options are one line each — the detail comes after they choose.

The **lab root** is the current working directory. Everything below uses these two scripts —
never hand-edit `.agent-lab/state.json`:

- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py"` — progress and track
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"` — the setup checklist and validation

## Step 0 — sanity check the folder

Run `pwd`. If the lab root is the participant's home directory, or a directory that is
clearly not meant for the lab (their whole Documents folder, a large unrelated repo), STOP.
Tell them to create an empty folder and open VS Code in it, then run `/lab:start` again. A
lab needs its own folder because it becomes a git repository with checkpoint commits.

## Step 1 — initialise or resume

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" init
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" touch-session
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" show --json
```

`init` is idempotent. Read the JSON to decide which path you are on:

- **First time** — `track` is `null`. Run Steps 2 → 6.
- **Returning** — `track` is set. Skip to Step 7 (the resume ritual).

## Step 2 — introduce the training (first time only)

Read `${CLAUDE_PLUGIN_ROOT}/references/orientation.md` and present it close to as written, in
**one** short message. It is deliberately brief — do not expand it.

Two parts only:

1. **What this is** — AI fluency: going from understanding how agents work to building a full
   AI system that does real, complex work. Then the four modules as a compact table.
2. **How we run it** — through this plugin, which is a tutor. One real-world example, built
   on in every module, with Module 4 spent validating and improving it until it is
   production-ready. Then the four things the tutor does: sets up, teaches, guides, validates.

Keep the whole message under 25 lines. Do **not** present the teaching loop, the learning
contract, the checkpoint mechanics, or the module-by-module detail — those belong at the start
of Module 1, from `references/how-the-lab-runs.md`. This is an introduction, not a briefing.
Do not ask a question yet; keep moving.

## Step 3 — show the setup checklist

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" --checklist
```

Present this as a **short list, not an explained list** — names only, grouped on as few
lines as possible, with no per-item justification. Something like: "Required: Python 3.10+,
pip, venv, SQLite 3.35+, Git 2.30+, write access here, 2 GB disk, PyPI access. Recommended
and never blocking: claude CLI, code CLI, Node 18+, chromadb (installed together in Module
2)."

Say once that they do not need to check any of it by hand because you are about to verify it
all automatically. Save the reasons for later: if a check fails, *then* explain why that item
matters.

## Step 4 — validate the environment

Run the checks **once** — they spawn subprocesses and make a network call, so do not run
them twice to read the result a second time. Save, record, then read the saved file:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" --json > .agent-lab/doctor.json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" record-env < .agent-lab/doctor.json
```

Read `.agent-lab/doctor.json` for the detail, then report it:

- **`ready: true`** — confirm in one or two lines. Call out anything interesting rather than
  listing all twelve checks. In particular, if `python_bin` is not plain `python3`, tell them
  which interpreter the lab will use and why (macOS ships Python 3.9 as `python3`; this is
  normal and already handled).
- **`ready: false`** — list only the failed required checks, each with its `install` hint for
  their platform. Then STOP. Do not continue to track selection; an unready machine will fail
  in Module 2, not now. Tell them to fix it and run `/lab:doctor` again, and to raise a hand
  so the facilitator can help. Offer to run the install commands for them if they want.

## Step 5 — the tracks

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" tracks --json
```

A track is the real-world example they build on for all four modules.

Introduce them in **one line each** — name, what it is, and the difficulty note. Do not list
the data, the scenario, the audience or the final deliverable here; that is what
`/lab:track` is for, and they only need it for the one they pick. Four or five lines total
for all three.

Then use **AskUserQuestion** with one option per track, using each track's `tagline` as the
option description — the question UI carries the detail, so your text does not have to.

If the facilitator has already assigned tracks by group, they can just say which one — accept
that without arguing.

## Step 6 — record the track, then introduce the example

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" set-track <id>
```

Now introduce **the example they will build**. This is the last thing `/lab:start` does and
the first part that feels concrete, so give it a little room — but stay under 15 lines. From
their `tracks/<id>/track.json`:

1. **`example_brief`**, close to as written. It names the fictional company, the situation,
   the material they have, and what the finished system does.
2. **`you_will_build`** as a compact four-row table: module → what their system can do once
   that module is finished. This is where they see it grows rather than restarts.
3. One line: they build it, they keep it, it runs on their machine.

Then hand over in **two lines**: their environment is validated and their track is recorded,
and **`/lab:next` opens Module 1** when the facilitator says go.

Do **not** start teaching Module 1, and do not set up the workspace — that is Module 1's
first step, and it belongs to `/lab:next`.

## Step 7 — the resume ritual (returning participant)

Sessions are days apart, so re-entry has to be cheap and honest:

1. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" show` — show them where they are, and
   the scoreboard if it has entries.
2. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" --quick --json` — re-verify the
   machine. Record it with `record-env`. If a required check now fails, deal with that first.
3. Check that the artifacts recorded in `artifacts` still exist on disk. If any are missing,
   say exactly which, and offer `/lab:catchup` to restore the last checkpoint.
4. Recap the previous module's core idea in two or three sentences — not a lecture, a
   reminder.
5. Say what this session covers in a line or two, and that `/lab:next` continues from where
   they stopped. Then wait for the facilitator.

## Rules

- Never invent progress. If a script did not report something, do not claim it.
- Never edit `.agent-lab/state.json` directly; every change goes through `state.py`.
- If `state.py` or `doctor.py` fails to run, show the actual error and stop. A broken tutor
  that pretends to work is worse than one that admits it.
