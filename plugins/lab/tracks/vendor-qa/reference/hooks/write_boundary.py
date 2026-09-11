#!/usr/bin/env python3
"""A write boundary: the corpus in data/ is evidence, and evidence does not get edited.

Your skill *asks* the agent to write its output to findings/. Mostly it does. "Mostly"
is the problem — a skill is guidance the model chooses to follow, and the one time it decides
a source file would be more accurate if it just fixed it, your evidence is gone and you have
no idea which number changed.

This runs on every write, before the write happens, and it cannot be talked out of it.

Wired up in .claude/settings.json:

    "PreToolUse": [
      { "matcher": "Write|Edit|MultiEdit|NotebookEdit",
        "hooks": [ { "type": "command",
                     "command": "python3 \\"${CLAUDE_PROJECT_DIR}/.claude/hooks/write_boundary.py\\"" } ] }
    ]

Exit 0 with a deny decision refuses the tool call. Exit 0 with no output lets it through.

## What this does not cover

This matches the write *tools*. It does not stop `Bash`, which can do the same damage with
`rm`, `mv`, `sed -i` or a `>` redirect. Try it and see.

Do not fix that by pattern-matching shell commands. You cannot enumerate the ways to write a
file, and a rule that greps for "data/" also blocks `sqlite3 data/db/support.db "SELECT ..."`,
which is a read. This is the same lesson as Step 1: a deny list is incomplete by
construction.

The real controls are layered, and this hook is only one layer:

  * **which tools exist at all** — `--tools "Read,Write,Skill"` and no `Bash` (Step 1)
  * **which of them may run unprompted** — `permissions` in settings.json
  * **what a permitted tool may touch** — this hook
  * **who approves the consequential action** — Module 4's gate

Any one of them alone is theatre. The point of a hook is that it is the layer the model
cannot argue with, not that it is the only layer you need.
"""

from __future__ import annotations

import json
import os
import sys

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}

# Everything under here is evidence: the documents a conclusion is drawn from. If the agent
# can edit them, nothing it concludes can be checked afterwards.
PROTECTED = ("data",)


def project_root() -> str:
    return os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0                                  # never break a session over a bad payload

    if event.get("tool_name") not in WRITE_TOOLS:
        return 0                                  # reads, searches and commands are fine

    target = (event.get("tool_input") or {}).get("file_path")
    if not target:
        return 0

    root = project_root()
    absolute = os.path.abspath(os.path.join(root, target))

    try:
        relative = os.path.relpath(absolute, root)
    except ValueError:                            # different drive on Windows
        deny(f"Refused: {target} is outside the project.")
        return 0

    if relative.startswith(os.pardir):
        deny(f"Refused: {relative} is outside the project. Writes stay inside the lab.")
        return 0

    first = relative.split(os.sep)[0]
    if first in PROTECTED:
        deny(f"Refused: {relative} is source evidence and must not be edited. "
             f"If it is wrong, that is a finding to report, not a file to fix. "
             f"Write your output to findings/ instead.")
        return 0

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:                             # noqa: BLE001 - a hook must not break a session
        sys.exit(0)
