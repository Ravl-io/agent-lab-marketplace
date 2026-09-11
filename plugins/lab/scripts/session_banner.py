#!/usr/bin/env python3
"""SessionStart hook: remind the participant where they are in the lab.

Two properties matter more than what it prints:

1. **Silent when irrelevant.** This plugin is installed for the whole training, so the hook
   fires in every session the participant opens, including their real work. With no lab state
   in the working directory it prints nothing at all.
2. **Never breaks a session.** A hook that raises turns into an error banner on every single
   session start. Everything is wrapped, and the exit code is always 0.

It is also the first hook participants read in Module 1, which is why it is commented.
"""

from __future__ import annotations

import json
import os
import sys

MODULE_TITLES = {
    "01": "Harness and coding agent",
    "02": "RAG and retrieval systems",
    "03": "Knowledge graphs and ontologies",
    "04": "The full AI system",
}


def main() -> int:
    state_file = os.path.join(os.getcwd(), ".agent-lab", "state.json")
    if not os.path.exists(state_file):
        return 0                      # not a lab folder — say nothing

    try:
        with open(state_file) as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        return 0                      # unreadable or half-written: not worth a warning

    track = state.get("track") or "no track chosen"
    progress = state.get("progress") or {}
    current = progress.get("current_module")
    done = progress.get("completed_modules") or []
    checkpoints = progress.get("completed_checkpoints") or []

    if current:
        position = f"Module {current} — {MODULE_TITLES.get(current, '')}".strip(" —")
    elif done:
        position = f"{len(done)} of 4 modules complete, next one not opened yet"
    else:
        position = "not started — run /lab:start"

    lines = [
        "Agent Lab is active in this folder.",
        f"  Track: {track}",
        f"  Position: {position}",
    ]
    if checkpoints:
        lines.append(f"  Last checkpoint: {checkpoints[-1]}")
    if not state.get("env", {}).get("ready", False):
        lines.append("  Environment not validated — run /lab:doctor")
    lines.append("  /lab:start to resume.")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:                 # noqa: BLE001 - a hook must never break a session
        sys.exit(0)
