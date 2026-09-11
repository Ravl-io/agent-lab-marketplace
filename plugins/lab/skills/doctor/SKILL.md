---
name: doctor
description: Validate that this machine is ready for Agent Lab. Use --quick for the start-of-session check.
argument-hint: "[--quick]"
disable-model-invocation: true
allowed-tools: Bash, Read
---

Verify the participant's environment and record the result.

Run the checks **once** and reuse the output — do not run the script a second time to read
the result again.

If a lab state file exists (`.agent-lab/state.json` in the current directory):

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" --json $ARGUMENTS > .agent-lab/doctor.json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" record-env < .agent-lab/doctor.json
```

Otherwise just run it and read the output directly:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py" --json $ARGUMENTS
```

Then report:

**When ready** — say so in a line or two. Do not recite all twelve checks. Mention only what
is worth knowing:
- `python_bin` differs from plain `python3` (normal on macOS, where `python3` is 3.9) — tell
  them which interpreter the lab will use.
- a recommended check is a WARN, and it will cost them something later (no `code` on PATH
  means you will print file paths instead of opening files).

**When not ready** — list only the failed required checks. For each: what failed, the actual
detail the script reported, and the platform-specific `install` hint. Offer to run the fix
commands. Then stop; do not paper over it with a workaround.

`--quick` skips the disk, network and chromadb checks. Use it for the start-of-session resume
check, not for first-time setup.
