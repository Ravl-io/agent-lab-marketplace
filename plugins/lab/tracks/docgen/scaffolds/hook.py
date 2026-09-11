#!/usr/bin/env python3
""".claude/hooks/write_boundary.py

A write boundary. Your skill *asks* the agent to write its output to {{OUTPUT_DIR}}/ — and
mostly it does. "Mostly" is the problem: a skill is guidance the model chooses to follow, and
the one time it decides a source file would be more accurate if it just fixed it, your
evidence is gone and you cannot tell which number changed.

A hook runs whether the model likes it or not.

Wire it up in .claude/settings.json, alongside the tracer that is already there:

    "PreToolUse": [
      { "matcher": "Write|Edit|MultiEdit|NotebookEdit",
        "hooks": [ { "type": "command",
                     "command": "python3 \\"${CLAUDE_PROJECT_DIR}/.claude/hooks/write_boundary.py\\"" } ] }
    ]

Test it without an agent — feed it a payload by hand:

    echo '{"tool_name":"Write","tool_input":{"file_path":"data/x.md"}}' \\
      | python3 .claude/hooks/write_boundary.py

A deny prints JSON. An allow prints nothing.
"""

from __future__ import annotations

import json
import os
import sys

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def deny(reason: str) -> None:
    """Refuse the tool call. The reason is shown to the model, so make it useful:
    say what was refused, why, and what to do instead."""
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
        return 0          # a malformed payload must not break the session

    # TODO — decide and enforce.
    #
    # Four decisions, in the order they bite:
    #
    #   1. Which tools do you care about? A hook on every tool that inspects file_path will
    #      do nothing useful for Bash or Grep. WRITE_TOOLS is there for a reason.
    #
    #   2. What is off limits? The corpus in data/ is the evidence a conclusion rests on.
    #      Decide whether you are naming what is protected, or naming what is allowed — and
    #      remember Step 1: which of those two can ever be complete?
    #
    #   3. Paths arrive both relative and absolute, and the agent uses absolute ones. Resolve
    #      against os.environ["CLAUDE_PROJECT_DIR"] before comparing anything, or your rule
    #      matches on some runs and not others.
    #
    #   4. What does the refusal say? It goes to the model, which will try something else.
    #      A good reason redirects it; a bad one makes it retry the same thing.
    #
    # And one thing to leave broken on purpose: once this works, try getting round it with
    # Bash. Do not fix that here. Bring it to the debrief.

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:     # noqa: BLE001 - a hook must never break a session
        sys.exit(0)
