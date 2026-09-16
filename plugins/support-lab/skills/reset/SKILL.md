---
name: reset
description: Start the Support Lab module over — remove the findings, the built plugin and the progress record. Use when the participant or facilitator says "lab reset", "start over", "reset the lab", or "wipe my progress".
disable-model-invocation: true
allowed-tools: Bash, AskUserQuestion
---

Reset the lab in this folder to its starting state. This deletes the participant's work, so
confirm first.

1. Show what will be removed:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" verify
```

   List, in plain words: findings sheets, the `first-look-plugin/` folder, `out/`, and the
   progress record. The sandbox (docs, logs, tickets, database) stays.

2. Ask with **AskUserQuestion**: reset everything / keep the plugin but reset progress / cancel.

3. On "reset everything":

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" clean
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" reset --force
```

   On "keep the plugin": run `clean` is **not** right — instead delete only
   `tickets/JIRA-*/` and `out/` with `rm -rf`, then `state.py reset --force`.

4. Remind them: if they installed `first-look` earlier, it is still installed
   (`/plugin uninstall first-look@first-look` removes it). Say "lab start" to begin again.
