#!/usr/bin/env python3
"""Stop hook: save Claude's final reply to response.md in the lab folder.

The file is overwritten on every turn, so it only ever holds the latest reply. The harness
does the writing, not the model: no extra tool call, no tokens, and nothing to forget.

Three properties matter:

1. **Silent when irrelevant.** With no lab state in the project directory it does nothing,
   so it never writes into the participant's real work.
2. **Skips the experiments.** `experiments/exp.py` starts its sessions with LAB_TRACE=1.
   Those sessions are the subject of the experiment, and must not overwrite the reply.
3. **Never breaks a session.** Everything is wrapped, and the exit code is always 0.
"""

from __future__ import annotations

import json
import os
import sys


def main() -> int:
    if os.environ.get("LAB_TRACE") == "1":
        return 0                      # an experiment session — leave response.md alone

    event = json.load(sys.stdin)
    root = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    if not os.path.exists(os.path.join(root, ".agent-lab", "state.json")):
        return 0                      # not a lab folder — say nothing

    last = None
    with open(event["transcript_path"]) as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except ValueError:
                continue              # a half-written last line
            if entry.get("type") != "assistant":
                continue
            content = (entry.get("message") or {}).get("content") or []
            for block in content if isinstance(content, list) else []:
                if block.get("type") == "text" and block.get("text", "").strip():
                    last = block["text"]

    if last:
        with open(os.path.join(root, "response.md"), "w") as fh:   # "w": clean every turn
            fh.write(last.rstrip() + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:                 # noqa: BLE001 - a hook must never break a session
        sys.exit(0)
