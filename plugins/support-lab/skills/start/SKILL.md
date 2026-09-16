---
name: start
description: Start or resume the Support Lab. Use when the participant says "lab start", "start the lab", "begin the lab", "resume the lab", "let's start", or asks how to begin the support training.
allowed-tools: Bash, Read
---

Start or resume the Support Lab for this participant. The participant is not technical: no
build logs, no jargon, no narration of what you are about to do. Run the scripts silently and
present results.

The **lab root** is the current working directory. All state goes through
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py"`; never hand-edit `.support-lab/state.json`.

## Step 0 — sanity check the folder

Run `pwd`. If it is the home directory or clearly someone's real project (a large unrelated
repo), STOP: tell them to make an empty folder, open Claude Code there, and say "lab start"
again. One or two lines.

## Step 1 — initialise or resume

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" init
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" touch-session
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" show --json
```

- **First time** (`cleared_steps` is empty and `open_step` is null): Steps 2 → 4 below.
- **Returning**: skip to Step 5.

## Step 2 — set up the workspace

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" setup
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" verify
```

If `setup` refuses (folder not empty, or home directory), show its one-line reason and stop.
If `verify` reports `intact: false`, show what is missing and stop — do not teach on a broken
workspace.

## Step 3 — orientation, once

Read `${CLAUDE_PLUGIN_ROOT}/modules/01/00-orientation.md` and present the "Say this" part
close to as written, in **one** message under 25 lines. Include the one-line description of
what just appeared in the folder. Then record it:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" clear S0
```

## Step 4 — open Step 1 immediately

Do not wait for "next". Read `${CLAUDE_PLUGIN_ROOT}/modules/01/01-meet-the-workspace.md`,
then:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" open S1
```

Present its **Frame** and its **Ask** — the frame in your own words, the ask as a quoted
prompt they can copy. End with one line: *type that, read the answer, then say "next".*
Stop and wait.

## Step 5 — resume (returning participant)

1. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" show` — show where they are, compactly.
2. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" verify` — if not intact, say what
   is missing and offer to run setup again (it never overwrites their findings).
3. One or two sentences recapping what they found so far (from the cleared steps — e.g. "you
   have the docs quote and the settings; next is the timeline").
4. If a step is open: re-present that step's **Ask** from its module file, and say "next"
   when done. If no step is open: say "next" opens the next one. Stop.

## Rules

- Never invent progress; if a script did not report it, do not claim it.
- If a script fails, show the actual error and stop.
- Do not start investigating the ticket yourself. The participant asks; you execute what they
  ask; the tutor judges.
