#!/usr/bin/env python3
"""SessionStart hook: remind the participant where they are in the Support Lab.

Two properties matter more than what it prints:

1. Silent when irrelevant. The plugin is installed for the whole training, so the hook fires
   in every session the participant opens. With no lab state in the working directory it
   prints nothing at all.
2. Never breaks a session. Everything is wrapped and the exit code is always 0.
"""

from __future__ import annotations

import json
import os
import sys

STEP_TITLES = {
    "S0": "Orientation and setup", "S1": "Meet the workspace", "S2": "Read the ticket",
    "S3": "What the docs promise", "S4": "The customer's settings", "S5": "The timeline",
    "S6": "Last known good", "S7": "The vendor's own notes", "S8": "Write the findings",
    "S9": "Capture the process as a plugin", "S10": "Run it in a new session",
    "S11": "Debrief",
}
ORDER = list(STEP_TITLES)


def main() -> int:
    state_file = os.path.join(os.getcwd(), ".support-lab", "state.json")
    if not os.path.exists(state_file):
        return 0
    try:
        with open(state_file) as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        return 0

    prog = state.get("progress") or {}
    open_step = prog.get("open_step")
    cleared = prog.get("cleared_steps") or []
    lines = ["Support Lab is active in this folder."]
    if prog.get("module_complete"):
        lines.append("  Module 1 is complete. Say 'status' to see the summary.")
    elif open_step:
        lines.append(f"  Open step: {open_step} — {STEP_TITLES.get(open_step, '')}")
        if open_step == "S10":
            lines.append("  This is the new-session step: if you installed your first-look plugin, "
                         "type: First look on JIRA-4907.  Then say 'next'.")
        else:
            lines.append("  Say 'next' when you have done it, or 'hint' if you are stuck.")
    else:
        nxt = next((s for s in ORDER if s not in cleared), None)
        if nxt:
            lines.append(f"  Next step: {nxt} — {STEP_TITLES[nxt]}. Say 'next' to open it.")
    lines.append("  'status' shows where you are; 'lab start' resumes the orientation.")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 - a hook must never break a session
        sys.exit(0)
