---
name: handbook
description: Open the Agent Lab handbook — the reference guide covering the modules, the commands, the concepts and what to do when something breaks.
disable-model-invocation: true
allowed-tools: Bash, Read
---

Open the handbook for the participant.

It is a single self-contained HTML file, and there are two copies. **Prefer the one in their
own folder** — it is the one they can bookmark, and the path is short enough to read out:

```
./handbook.html                             <- copied into their workspace at setup
${CLAUDE_PLUGIN_ROOT}/reference/handbook.html   <- the plugin's copy, always present
```

If `./handbook.html` does not exist yet, they have not run the Module 1 setup step. Copy it
for them rather than sending them into the plugin cache:

```
cp "${CLAUDE_PLUGIN_ROOT}/reference/handbook.html" ./handbook.html
```

## What to do

Open it in their browser, picking the command for their platform:

```
open handbook.html            # macOS
xdg-open handbook.html        # Linux
start "" handbook.html        # Windows
```

If that fails, or you cannot tell which platform they are on, **print the path and stop**.
They can open it from the file tree in VS Code, which is usually faster than any of this. Do
not keep trying different commands.

## Then say what is in it, in one or two lines

The parts they are most likely to want:

- **Start here** — the three commands, and what module 1 actually needs installed
- **Module 1** — the nine steps, with the traces and the measured results
- **Commands** — every command, the seven experiments, and how to read a trace
- **When it breaks** — the trust dialog, a skill that will not fire, a hook that is not registered

Modules 2 to 4 are outlines in there and marked as such; the handbook does not pretend they
are written yet.

## Notes

- It works offline, and it works on a network that blocks external sites. The only thing it
  fetches is the web font; without it the page renders in fallback faces and nothing else
  changes. This is why the handbook is a file in their folder rather than a link.
- Do **not** read the file into context to answer a question from it. It is 80 KB of HTML.
  Answer from the `agent-lab` tutor skill and the module files instead, and point them at the
  handbook to read for themselves.
