---
name: status
description: Show where the participant is in the Support Lab. Use when they say "status", "lab status", "where am I", "what have I done so far", or ask how far along they are.
allowed-tools: Bash
---

Show the participant where they are. Read, do not narrate.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" show
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" verify
```

Present it compactly, in plain words:

- steps cleared, the open one, and how many remain (with the rough minutes left, from the
  step table)
- what exists on disk: findings for JIRA-4821, findings for JIRA-4907, the built plugin
- if `verify` reports missing files, name them and offer to run "lab start" to repair (it
  never overwrites their findings)

If there is no state file, say so and point at "lab start". Do not invent progress.

End with the single next action: usually *say "next"*.
