---
name: catchup
description: Repair or fast-forward the lab workspace — restores the lab's own files, and optionally the reference solution if you are stranded.
argument-hint: "[--with-reference]"
allowed-tools: Bash, Read
disable-model-invocation: true
---

Restore the workspace so nobody sits stuck while the room moves on.

## What it does

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" catchup $ARGUMENTS
```

This replays every stage already applied, in order. Stage payloads are the **lab's** files —
`settings.json`, the tracer hook, the experiment runner and its prompts — so replaying them
repairs anything deleted or broken. It does not touch the participant's own work.

Afterwards, confirm:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" verify
```

Report what was replayed and whether the workspace is now intact. If `verify` still reports
missing files, say which, and stop — do not keep retrying.

## About `--with-reference`

That flag also installs the track's **reference skill**: the answer key. Only use it when the
participant would otherwise be stranded — they have lost the exercise and the room has moved
on. It is a rescue, not a shortcut, and it costs them the learning the exercise was for.

If `$ARGUMENTS` does not include it, do not add it on their behalf. If they ask for it, check
once that they mean it — "that gives you the finished version of the skill you were writing;
do you want that, or a hint first?" — then do as they say. It is their training.

If the track has no reference skill yet, the script reports `NOT AVAILABLE`. Say so plainly
rather than improvising a solution.

## Reassure them, briefly

Using this is not cheating. It exists so that one bad `pip install` or a mistyped `rm` cannot
cost somebody a module. One sentence, then move on — do not make a thing of it.
