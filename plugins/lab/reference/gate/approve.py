#!/usr/bin/env python3
"""Record a human's approval of one specific proposal.

    python3 gate/approve.py CASE-4471            approve it
    python3 gate/approve.py CASE-4471 --show     print it for review, approve nothing
    python3 gate/approve.py CASE-4471 --revoke   withdraw an approval

This is the human's half of the gate, and it deliberately does almost nothing: it reads the
proposal, hashes it, and writes down who agreed to that hash and when. The hash is the point
— it is what makes the approval describe a particular artifact rather than a standing trust.

`--show` exists because an approval nobody read is worse than no gate at all: it produces an
audit trail that says a human checked, when no human did.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import sys
from datetime import datetime, timezone


def project_root() -> str:
    return os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def digest_of(root: str, proposal_id: str) -> tuple[str, dict]:
    path = os.path.join(root, "proposals", f"{proposal_id}.json")
    if not os.path.exists(path):
        sys.exit(f"no proposal at proposals/{proposal_id}.json")
    with open(path, "rb") as fh:
        raw = fh.read()
    try:
        payload = json.loads(raw)
    except ValueError as exc:
        sys.exit(f"proposals/{proposal_id}.json is not valid JSON: {exc}")
    digest = hashlib.sha256(raw)
    body = payload.get("body")
    if body:
        body_path = os.path.join(root, body)
        if not os.path.exists(body_path):
            sys.exit(f"the proposal names a body at {body} which does not exist")
        with open(body_path, "rb") as fh:
            digest.update(fh.read())
    return digest.hexdigest(), payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("proposal_id")
    ap.add_argument("--root", default=None)
    ap.add_argument("--show", action="store_true", help="print it for review, approve nothing")
    ap.add_argument("--revoke", action="store_true")
    ap.add_argument("--by", default=None, help="who is approving (defaults to the OS user)")
    ap.add_argument("--note", default=None)
    args = ap.parse_args()
    root = os.path.abspath(args.root or project_root())
    approval_path = os.path.join(root, "approvals", f"{args.proposal_id}.json")

    if args.revoke:
        if not os.path.exists(approval_path):
            sys.exit(f"nothing to revoke for {args.proposal_id}")
        os.remove(approval_path)
        print(f"revoked the approval for {args.proposal_id}")
        return 0

    digest, payload = digest_of(root, args.proposal_id)

    if args.show:
        print(f"PROPOSAL {args.proposal_id}")
        print("=" * (9 + len(args.proposal_id)))
        print(f"\n  capability: {payload.get('capability', '?')}")
        print(f"  confidence: {payload.get('confidence', '?')}"
              f"   risk: {payload.get('risk', '?')}")
        actions = payload.get("actions") or []
        print(f"\n  {len(actions)} action(s) — this is what applying will do:")
        for action in actions:
            print(f"    {action.get('type', '?')}: {action.get('path', '?')}")
        evidence = payload.get("evidence") or []
        print(f"\n  {len(evidence)} piece(s) of evidence:")
        for item in evidence[:8]:
            print(f"    [{item.get('via', '?')}] {item.get('source', '?')}")
        if payload.get("rollback"):
            print(f"\n  rollback: {payload['rollback']}")
        if payload.get("unresolved"):
            print("\n  the agent could not resolve:")
            for gap in payload["unresolved"]:
                print(f"    - {gap}")
        body = payload.get("body")
        if body and os.path.exists(os.path.join(root, body)):
            print(f"\n  full text: {body}")
        print(f"\n  digest: {digest[:16]}…")
        print(f"\nApprove with:  python3 gate/approve.py {args.proposal_id}")
        return 0

    os.makedirs(os.path.dirname(approval_path), exist_ok=True)
    approval = {
        "proposal": args.proposal_id,
        "digest": digest,
        "approved_by": args.by or getpass.getuser(),
        "approved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": args.note,
        "consumed_at": None,
    }
    with open(approval_path, "w") as fh:
        json.dump(approval, fh, indent=2)
        fh.write("\n")
    print(f"approved {args.proposal_id} as {approval['approved_by']}")
    print(f"  digest {digest[:16]}… — editing the proposal now invalidates this")
    print(f"  apply it with: python3 tools/apply.py {args.proposal_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
