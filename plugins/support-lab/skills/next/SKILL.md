---
name: next
description: Advance the Support Lab. Use when the participant says "next", "lab next", "what's next", "continue", "done", "I did it", "move on", or asks what to do now. Judges the step they just finished, then opens the next one.
allowed-tools: Bash, Read, Glob, Grep
---

Judge the open step, then open the next one. The participant is not technical: plain words,
short messages, no narration of mechanics.

## 1 — where are they

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" show --json
```

Route, first match wins:

| Condition | Do |
|---|---|
| no state file | Say: start with "lab start". Stop. |
| `progress.module_complete` is true | Congratulate in one line; point at `first-look-plugin/` as theirs to keep. Stop. |
| `open_step` is set | **Judge it** (section 2), then open the next (section 3). |
| `open_step` is null | Open `next_step` (section 3). |

## 2 — judge the open step

Read the open step's file (`open_step_info.file`) and follow its **Judge** section exactly:

- Check against what actually happened — what appeared earlier in this conversation, the
  files now on disk, or a command you re-run yourself (the checker, the validator, a grep).
  Never assume the participant did the step.
- Say in two to four lines what was right and what was missing. Use the step's expected
  values; do not soften a wrong number.
- Where the step says to ask the participant a question and wait, ask it and **stop** —
  do not open the next step in the same message. When they answer, continue.
- If something **required** is missing (the step's Gate says "only when …"), do not clear the
  step and do not fix it yourself. Give them the one sentence to ask Claude Code, and say
  "then say next again". Stop.
- Otherwise run the step's Gate command to clear it.

If they clearly skipped the step (nothing in the conversation, nothing on disk), say so and
re-present the step's **Ask**. Stop.

## 3 — open the next step

Read the next step's file, then:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" open <id>
```

Present its **Frame** (in your own words, at the length the file asks) and its **Ask** as a
quoted prompt they can copy, with any warning the file attaches to it (permission prompts to
expect, what to say no to). End with one line: *type that, read the answer, then say "next".*
Stop and wait.

Special cases:

- **S10** — follow its "Opening the step" instructions: the participant leaves this session.
  Give the numbered instructions and stop.
- **S11** — it has no Ask. Present the debrief, ask its one question, wait for the answer,
  then run its Gate (clear and complete).

## 4 — the executing rule

When the participant later types the prompt you gave them, you are no longer the tutor: do the
real work, with real commands, in this workspace, under its `CLAUDE.md`. Never answer from
the step file's expected values. The expected values exist so you can judge, not so you can
skip the work.

## Never

- Do the step for them before they ask.
- Change a file under `config/`, or write anything addressed to a customer.
- Invent an exercise that is not in the module files. If a file is missing, say so and stop.
