#!/usr/bin/env python3
"""The approval gate: nothing reaches the outside world without a human approving THAT thing.

You write the two functions under "what you write". The plumbing — reading the event,
matching the tool, emitting the deny decision — is done.

Two rules, both narrow on purpose:

  1. Writes into the published location are refused outright. Publishing is not a file write;
     it goes through `tools/apply.py`, which is the only sanctioned path.
  2. A Bash command that invokes `tools/apply.py` is refused unless a valid, unconsumed
     approval exists for the exact proposal being applied.

Wired up in .claude/settings.json:

    "PreToolUse": [
      { "matcher": "Write|Edit|MultiEdit|NotebookEdit|Bash",
        "hooks": [ { "type": "command",
                     "command": "python3 \\"${CLAUDE_PROJECT_DIR}/.claude/hooks/approval_gate.py\\"" } ] }
    ]

## Why the approval carries a hash

Because approval is of a *specific artifact*, not a standing permission. A human read one
proposal and agreed to that one. If the proposal changes afterwards — a different amount, a
different recipient, one more action in the list — the approval no longer describes what is
about to happen, and the gate must refuse. Recording a hash of the proposal at the moment of
approval is what makes "approved" mean something narrower than "trusted".

That is the whole difference between an approval and a permission, and it is the property
people skip when they build one of these in a hurry.

## Why an approval is single-use

An approval that can be replayed is a permission with extra steps. `tools/apply.py` marks it
consumed, and this gate refuses a consumed one.

## What this does not cover

It does not stop `Bash` from writing to the published location by other means — `cp`, `mv`,
a `>` redirect. That is the same incompleteness Module 1's write boundary had, and the same
answer applies: you cannot enumerate the ways to write a file. The layers that actually
contain it are which tools exist at all, which may run unprompted, and this gate on the one
path that is supposed to be used. A gate is the layer the model cannot argue with, not the
only layer you need.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
APPLY_PATTERN = re.compile(r"tools/apply\.py\s+(\S+)")


def project_root() -> str:
    return os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def published_dir(root: str) -> str:
    """Where applying has an effect. Read from the project so one hook fits every track."""
    config = os.path.join(root, "spec", "capability.json")
    if os.path.exists(config):
        try:
            with open(config) as fh:
                return (json.load(fh) or {}).get("published_to") or "published"
        except (OSError, ValueError):
            pass
    return "published"


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


# ---------------------------------------------------------------- what you write
#
# TODO 1. Hash the proposal.
#
# The approval has to describe ONE artifact, not a standing permission. Hash the proposal
# JSON *and* the prose body it points at — the body is the part a human actually read, and
# hashing only the JSON would let the wording change under an approval that still verified.
#
# Return None when the proposal does not exist. The caller treats that as a refusal.

def proposal_digest(root: str, proposal_id: str) -> str | None:
    # TODO: sha256 over proposals/<id>.json, then over the file named by its "body" key.
    return None


# TODO 2. Decide whether this apply may proceed.
#
# Return a refusal REASON (a string the model will read and act on) or None to allow.
# Four things have to be true, and each one is a property somebody leaves out:
#
#   1. an approval file exists for this proposal
#   2. it has not already been used — an approval is single-use, because a replayable one
#      is a standing permission with extra steps
#   3. its recorded digest still matches the proposal as it is now
#   4. it records who approved it
#
# Write the reasons as sentences a person would want to read. The model surfaces them to the
# participant, and "denied" with no reason is the most annoying possible control.

def check_approval(root: str, proposal_id: str) -> str | None:
    # TODO: implement the four checks above.
    return "Refused: the approval gate is not implemented yet."


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0                                  # never break a session over a bad payload

    root = project_root()
    tool = event.get("tool_name")
    tool_input = event.get("tool_input") or {}

    # --- rule 1: the published location is not writable by hand
    if tool in WRITE_TOOLS:
        target = tool_input.get("file_path")
        if not target:
            return 0
        absolute = os.path.abspath(os.path.join(root, target))
        try:
            relative = os.path.relpath(absolute, root)
        except ValueError:
            return 0
        first = relative.split(os.sep)[0]
        if first == published_dir(root):
            deny(f"Refused: {relative} is published output. Writing it by hand bypasses "
                 f"the approval gate. Write a proposal instead, have it approved, then "
                 f"apply it with tools/apply.py.")
        return 0

    # --- rule 2: applying requires an approval for that exact proposal
    if tool == "Bash":
        command = tool_input.get("command") or ""
        match = APPLY_PATTERN.search(command)
        if not match:
            return 0
        reason = check_approval(root, match.group(1))
        if reason:
            deny(reason)
        return 0

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:                             # noqa: BLE001 - a hook must not break a session
        sys.exit(0)
