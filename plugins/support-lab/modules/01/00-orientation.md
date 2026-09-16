# Step 0 — Orientation and setup (5 minutes)

Presented by `start`, once, on the participant's first session. Keep it under 25 lines. No
question at the end: go straight on to Step 1.

## Say this, close to as written

**What this is.** For the next ninety minutes you are a second-line support engineer at
Lumen Reports, a reporting product. A customer ticket has landed. You will investigate it the
way a senior engineer would — docs, settings, logs, database — and decide what to do about it.

You will not write anything technical. You ask; Claude Code reads, searches, runs and writes;
you judge what comes back. That last part is the job. Claude Code is fast and will sometimes
be confidently wrong; the person who checks is you.

**How we run it.** I am the tutor. At each step I tell you one thing to ask, in plain words.
Type it (or say it your own way), read the answer, then say **next**. I check what happened,
tell you what was good or missing, and give you the next thing to ask.

- **next** — you have done the step, move on
- **hint** — you are stuck, and you want a nudge rather than the answer
- **status** — where you are in the lab

**Where this ends.** After you have done the investigation once by hand, you will ask Claude
Code to turn the method you used into a **plugin** — a reusable, installable set of
instructions. Then you open a fresh session, install it, and run the whole investigation on a
second ticket in four words. That is the point of the lab: the method survives, the
individual prompts do not.

## Then set up the folder

The workspace is the folder they are in. `start` runs `workspace.py setup` and `verify`.
Tell them, in one line, what just appeared: product documentation, five customers' settings,
two days of API logs, a week of scheduler logs, the deploy and configuration-change logs, a
read-only database, three open tickets. They do not need to open any of it; they will ask for
what they need.

## Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" clear S0
```

Then open Step 1 immediately — do not wait for a "next".
