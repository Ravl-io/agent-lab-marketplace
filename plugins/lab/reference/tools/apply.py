#!/usr/bin/env python3
"""Apply an approved proposal — the only sanctioned path to published output.

    python3 tools/apply.py CASE-4471

It re-checks the approval itself rather than trusting the hook. That is not belt-and-braces
for its own sake: the hook guards the agent's path to this tool, and this check guards
everything else — a script, a CI job, somebody's terminal. A control that only exists in one
layer is a control that exists until someone takes a different route.

Every apply appends to `audit.jsonl`, whether it succeeded or not. A gate with no audit trail
cannot answer the question anybody actually asks afterwards, which is "who approved this".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone


def project_root() -> str:
    return os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest_of(root: str, proposal_id: str) -> tuple[str, dict]:
    path = os.path.join(root, "proposals", f"{proposal_id}.json")
    with open(path, "rb") as fh:
        raw = fh.read()
    payload = json.loads(raw)
    digest = hashlib.sha256(raw)
    body = payload.get("body")
    if body:
        with open(os.path.join(root, body), "rb") as fh:
            digest.update(fh.read())
    return digest.hexdigest(), payload


def audit(root: str, entry: dict) -> None:
    with open(os.path.join(root, "audit.jsonl"), "a") as fh:
        fh.write(json.dumps({"at": now(), **entry}) + "\n")


def refuse(root: str, proposal_id: str, reason: str) -> int:
    audit(root, {"event": "apply_refused", "proposal": proposal_id, "reason": reason})
    print(f"REFUSED: {reason}", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("proposal_id")
    ap.add_argument("--root", default=None)
    args = ap.parse_args()
    root = os.path.abspath(args.root or project_root())
    pid = args.proposal_id

    proposal_path = os.path.join(root, "proposals", f"{pid}.json")
    if not os.path.exists(proposal_path):
        return refuse(root, pid, f"no proposal at proposals/{pid}.json")
    approval_path = os.path.join(root, "approvals", f"{pid}.json")
    if not os.path.exists(approval_path):
        return refuse(root, pid, f"{pid} has not been approved")

    try:
        digest, payload = digest_of(root, pid)
        with open(approval_path) as fh:
            approval = json.load(fh)
    except (OSError, ValueError) as exc:
        return refuse(root, pid, f"could not read the proposal or its approval: {exc}")

    if approval.get("consumed_at"):
        return refuse(root, pid, f"the approval was already used at "
                                 f"{approval['consumed_at']} — approvals are single-use")
    if approval.get("digest") != digest:
        return refuse(root, pid, f"{pid} has changed since it was approved")

    published = (payload.get("published_to")
                 or _capability(root).get("published_to") or "published")
    written = []
    for action in payload.get("actions") or []:
        kind = action.get("type")
        target = action.get("path")
        if kind != "write" or not target:
            return refuse(root, pid, f"unsupported action {kind!r} — this tool only "
                                     f"publishes files, which is deliberate")
        destination = os.path.abspath(os.path.join(root, target))
        relative = os.path.relpath(destination, root)
        if relative.split(os.sep)[0] != published:
            return refuse(root, pid, f"{relative} is outside the published location "
                                     f"({published}/). An approved proposal still cannot "
                                     f"write anywhere it likes")
        source = os.path.join(root, action.get("from") or payload.get("body") or "")
        if not os.path.exists(source):
            return refuse(root, pid, f"the action's source {action.get('from')} is missing")
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(source, destination)
        written.append(relative)

    if not written:
        return refuse(root, pid, "the proposal declares no actions, so there is nothing "
                                 "to apply")

    approval["consumed_at"] = now()
    with open(approval_path, "w") as fh:
        json.dump(approval, fh, indent=2)
        fh.write("\n")

    audit(root, {"event": "applied", "proposal": pid,
                 "approved_by": approval.get("approved_by"),
                 "approved_at": approval.get("approved_at"),
                 "digest": digest, "written": written})
    print(json.dumps({"applied": pid, "written": written,
                      "approved_by": approval.get("approved_by")}, indent=2))
    return 0


def _capability(root: str) -> dict:
    path = os.path.join(root, "spec", "capability.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as fh:
            return json.load(fh) or {}
    except (OSError, ValueError):
        return {}


if __name__ == "__main__":
    sys.exit(main())
