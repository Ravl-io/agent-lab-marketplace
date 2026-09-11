---
name: handbook
description: Open the Agent Lab handbook — the reference guide covering the modules, the commands, the concepts and what to do when something breaks.
disable-model-invocation: true
allowed-tools: Bash, Read
---

Open the handbook for the participant.

It is a single self-contained HTML file that ships with this plugin:

```
${CLAUDE_PLUGIN_ROOT}/reference/handbook.html
```

## What to do

Try to open it in their browser, picking the command for their platform:

```
open "${CLAUDE_PLUGIN_ROOT}/reference/handbook.html"          # macOS
xdg-open "${CLAUDE_PLUGIN_ROOT}/reference/handbook.html"      # Linux
start "" "${CLAUDE_PLUGIN_ROOT}/reference/handbook.html"      # Windows
```

If that fails, or you cannot tell which platform they are on, **print the full resolved path**
and tell them to open it themselves. Do not keep trying different commands.

## Then say what is in it, in one or two lines

The parts they are most likely to want:

- **Start here** — the three commands, and what module 1 actually needs installed
- **Module 1** — the nine steps, with the traces and the measured results
- **Commands** — every command, the seven experiments, and how to read a trace
- **When it breaks** — the trust dialog, a skill that will not fire, a hook that is not registered

Modules 2 to 4 are outlines in there and marked as such; the handbook does not pretend they
are written yet.

## Notes

- It works offline. The only thing it fetches is the web font, so with no network it renders
  in fallback faces and everything else is unchanged.
- Do **not** read the file into context to answer a question from it. It is 80 KB of HTML.
  Answer from the `agent-lab` tutor skill and the module files instead, and point them at the
  handbook to read for themselves.
