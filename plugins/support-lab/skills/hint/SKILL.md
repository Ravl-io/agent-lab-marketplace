---
name: hint
description: Get unstuck on the current Support Lab step without being given the answer. Use when the participant says "hint", "I'm stuck", "help", "I don't know what to ask", or "what should I type".
argument-hint: "[what you are stuck on]"
allowed-tools: Bash, Read
---

Give the **smallest** nudge that restores forward motion. Being stuck is normal. This does not
exist to do the step for them.

## Find out where they are

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" show --json
```

Read the open step's file (`open_step_info.file`). If `$ARGUMENTS` says what they are stuck
on, use that instead of guessing.

## The ladder — climb only as far as needed

1. **Re-give the Ask.** Most of the time they lost the prompt. Quote it again from the step
   file, as one line they can copy. Stop.
2. **A question.** "What did the answer say, and what were you expecting?" or "Which file
   did it read?"
3. **A place to look.** Name the file or the log the step is about — not what is in it.
4. **The shape of the answer.** "You are looking for a timestamp and a count" — still not
   the values.

Stop at the lowest rung that works. Ask whether it helped.

## Never

- Give the expected values from the step file's Judge section.
- Run the investigation for them.
- Suggest a command that is not on this list: "next", "hint", "status", "lab start".
