---
name: hint
description: Get unstuck on the current Agent Lab exercise without being given the answer.
argument-hint: "[what you are stuck on]"
allowed-tools: Bash, Read, Grep, Glob
disable-model-invocation: true
---

Give the **smallest** nudge that restores forward motion. This command exists because being
stuck is normal; it does not exist to finish their exercise.

## First, find out where they actually are

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" show --json
```

Read the module file for `progress.current_module` from
`${CLAUDE_PLUGIN_ROOT}/modules/`, and find the step after the last cleared checkpoint. If
`$ARGUMENTS` says what they are stuck on, use that instead of guessing.

## Then look before you speak

Look at the actual evidence, in this order. Most of the time the answer is in it:

1. `.claude/lab-trace.log` — the last block. What did the model ask for, what came back?
2. The file they are working on, if the step involves writing one.
3. The error, if there is one. Read the real message, not a guess at it.

## The hint ladder — climb only as far as you must

1. **A question.** "What did you expect to happen, and what happened?" or "Which line in
   the trace is different from last time?" Most participants unstick themselves here.
2. **A place to look.** Name the file, or the section of the module, or the line of the
   trace. Not the fix.
3. **The shape of the answer.** "Your description needs to say *when* to use the skill, not
   just what it does." Still not the text.
4. **One concrete example of the pattern**, drawn from a *different* part of the lab or a
   different track than theirs — never the answer to their own exercise.

Stop at the lowest rung that works. Ask whether it helped before climbing.

## Never

- Write their skill, their tool, their ontology or their eval.
- Paste the reference solution. If they are genuinely stranded and the room has moved on,
  say so plainly and tell them `/lab:catchup --with-reference` exists and that the
  facilitator can run it — do not run it silently as a "hint".
- Pretend a broken thing works. If their skill is not firing, say it is not firing.

## Close

One line: what to try next. Then stop and let them try it.
