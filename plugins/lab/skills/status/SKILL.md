---
name: status
description: Show where you are in the Agent Lab — track, module, checkpoints cleared, and whether your workspace is intact.
disable-model-invocation: true
allowed-tools: Bash, Read
---

Show the participant where they are. Read, do not narrate.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" show
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" verify
```

Present it compactly:

- their track and mode
- which modules are done, which is open
- checkpoints cleared, and the last one
- the scoreboard, if `eval_history` has entries
- whether the workspace is intact; if `verify` reports missing files, name them and offer
  `/lab:catchup`

If there is no state file, say so and point at `/lab:start`. Do not invent progress: if a
script did not report something, do not claim it.

End with the single next action — usually `/lab:next`.
