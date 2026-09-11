---
name: checklist
description: Show what needs to be installed for Agent Lab, and how to install it on this platform.
disable-model-invocation: true
allowed-tools: Bash, Read
---

Show the participant what the training requires.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" --checklist
```

Present the output as two short lists — **required** and **recommended** — keeping each
item's one-line reason, because "why do I need this" is the question that actually gets
asked. Use the install hint the script printed for their platform; it already detected the
platform, so do not offer instructions for the other operating systems.

This command only *lists* requirements. It does not check anything. Close by telling them to
run `/lab:doctor` to verify their machine, or `/lab:start` if they have not started yet.
