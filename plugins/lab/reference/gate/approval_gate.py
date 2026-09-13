#!/usr/bin/env python3
"""The approval gate: nothing reaches the outside world without a human approving THAT thing.

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


def proposal_digest(root: str, proposal_id: str) -> str | None:
    """The hash of exactly what is being applied: the actions AND the body they publish."""
    path = os.path.join(root, "proposals", f"{proposal_id}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
        payload = json.loads(raw)
    except (OSError, ValueError):
        return None
    digest = hashlib.sha256(raw)
    # The body is a separate file and is the part a human actually read. Hashing only the
    # JSON would let the prose change under an approval that still verified.
    body = payload.get("body")
    if body:
        body_path = os.path.join(root, body)
        if os.path.exists(body_path):
            with open(body_path, "rb") as fh:
                digest.update(fh.read())
    return digest.hexdigest()


def check_approval(root: str, proposal_id: str) -> str | None:
    """Return a refusal reason, or None if this apply may proceed."""
    approval_path = os.path.join(root, "approvals", f"{proposal_id}.json")
    if not os.path.exists(approval_path):
        return (f"Refused: proposal {proposal_id} has not been approved. A human reviews it "
                f"and runs /approve {proposal_id}. Nothing is applied before that.")
    try:
        with open(approval_path) as fh:
            approval = json.load(fh)
    except (OSError, ValueError):
        return f"Refused: approvals/{proposal_id}.json is not readable JSON."

    if approval.get("consumed_at"):
        return (f"Refused: the approval for {proposal_id} was already used at "
                f"{approval['consumed_at']}. An approval is single-use — a replayable one "
                f"is a standing permission with extra steps. Re-approve if you mean it.")

    current = proposal_digest(root, proposal_id)
    if current is None:
        return f"Refused: proposal {proposal_id} does not exist or is not readable."
    if approval.get("digest") != current:
        return (f"Refused: {proposal_id} has changed since it was approved. The approval "
                f"covers the proposal that was read, not whatever is there now. Have it "
                f"reviewed and approved again.")
    if not approval.get("approved_by"):
        return f"Refused: the approval for {proposal_id} records no approver."
    return None


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
