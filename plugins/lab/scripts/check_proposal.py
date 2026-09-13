#!/usr/bin/env python3
"""Validate a proposal before a human is asked to approve it.

The point of this gate is to protect the approver's attention. A proposal that is missing its
rollback plan, or cites a file that does not exist, or quietly applied itself already, wastes
the one scarce thing in the whole system — somebody's willingness to read carefully.

    check_proposal.py CASE-4471          validate one proposal
    check_proposal.py --json CASE-4471   machine-readable
"""

from __future__ import annotations

import argparse
import json
import os
import sys

LEVELS = {"high", "medium", "low"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("proposal_id")
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    pid = args.proposal_id

    problems: list[str] = []
    notes: list[str] = []

    path = os.path.join(root, "proposals", f"{pid}.json")
    if not os.path.exists(path):
        report(pid, {}, [f"no proposal at proposals/{pid}.json"], [], args.as_json)
        return 1
    try:
        payload = json.load(open(path))
    except ValueError as exc:
        report(pid, {}, [f"proposals/{pid}.json is not valid JSON: {exc}"], [], args.as_json)
        return 1

    # --- the human-readable half
    body_rel = payload.get("body")
    if not body_rel:
        problems.append("no `body` — the machine-readable half is not what a person reads, "
                        "and somebody has to read something before approving it")
    elif not os.path.exists(os.path.join(root, body_rel)):
        problems.append(f"`body` points at {body_rel}, which does not exist")
    else:
        body = open(os.path.join(root, body_rel), encoding="utf-8").read()
        if len(body.strip()) < 200:
            problems.append(f"{body_rel} is {len(body.strip())} characters. An approver "
                            f"cannot judge a proposal this thin")
        if "TODO" in body:
            problems.append(f"{body_rel} still contains a TODO")

    # --- actions: what applying will actually do
    actions = payload.get("actions")
    if not actions:
        problems.append("no `actions` — a proposal that proposes nothing cannot be applied")
    else:
        published = _published(root)
        for action in actions:
            if action.get("type") != "write":
                problems.append(f"action type {action.get('type')!r} is not supported; the "
                                f"apply tool only publishes files, deliberately")
                continue
            target = action.get("path") or ""
            if not target:
                problems.append("an action has no `path`")
                continue
            first = os.path.relpath(os.path.abspath(os.path.join(root, target)),
                                    root).split(os.sep)[0]
            if published and first != published:
                problems.append(f"action writes to {target}, outside the published "
                                f"location ({published}/) the spec declares")
            source = action.get("from") or body_rel
            if source and not os.path.exists(os.path.join(root, source)):
                problems.append(f"an action publishes {source}, which does not exist")

    # --- evidence, and that BOTH systems were used
    evidence = payload.get("evidence") or []
    if not evidence:
        problems.append("no `evidence`. An uncited proposal asks the approver to take the "
                        "agent's word for it, which is the thing this module removes")
    else:
        vias = {str(e.get("via", "")).lower() for e in evidence}
        for item in evidence:
            source = item.get("source") or ""
            if not source:
                problems.append("a piece of evidence names no source")
                continue
            # a database or table reference is not a path; check the file part only
            file_part = source.split("::")[0].strip()
            if file_part and not os.path.exists(os.path.join(root, file_part)):
                problems.append(f"evidence cites {file_part}, which does not exist — an "
                                f"invented citation is worse than none")
            if not item.get("supports"):
                notes.append(f"evidence {source} does not say which claim it supports")
        if "graph" not in vias:
            notes.append("no evidence came from the graph. If the case turns on a complete "
                         "set or an as-of date, retrieval alone will have missed it")
        if "retrieval" not in vias:
            notes.append("no evidence came from retrieval. The graph knows that things are "
                         "related; the reason is in a document")

    # --- the approver's decision inputs
    for field in ("confidence", "risk"):
        value = str(payload.get(field, "")).lower()
        if value not in LEVELS:
            problems.append(f"`{field}` is {payload.get(field)!r}; use one of "
                            f"{', '.join(sorted(LEVELS))}")
    if not payload.get("rollback"):
        problems.append("no `rollback`. The approver is deciding partly on how bad it is if "
                        "this is wrong, and that is unanswerable without it")
    if payload.get("unresolved") is None:
        problems.append("no `unresolved` field. An empty list is a claim; a missing field "
                        "is a question nobody asked")
    elif not payload.get("unresolved"):
        notes.append("`unresolved` is empty — worth a second look. On a real case there is "
                     "usually something")

    # --- nothing may have been applied already
    for action in payload.get("actions") or []:
        target = action.get("path")
        if target and os.path.exists(os.path.join(root, target)):
            approval = os.path.join(root, "approvals", f"{pid}.json")
            consumed = False
            if os.path.exists(approval):
                try:
                    consumed = bool(json.load(open(approval)).get("consumed_at"))
                except (OSError, ValueError):
                    consumed = False
            if not consumed:
                problems.append(f"{target} already exists but this proposal has not been "
                                f"approved and applied. Something wrote published output "
                                f"directly, which is what the gate is for")

    summary = {"actions": len(payload.get("actions") or []),
               "evidence": len(evidence),
               "confidence": payload.get("confidence"), "risk": payload.get("risk"),
               "unresolved": len(payload.get("unresolved") or [])}
    report(pid, summary, problems, notes, args.as_json)
    return 1 if problems else 0


def _published(root: str) -> str | None:
    path = os.path.join(root, "spec", "capability.json")
    if not os.path.exists(path):
        return None
    try:
        return (json.load(open(path)) or {}).get("published_to")
    except (OSError, ValueError):
        return None


def report(pid: str, summary: dict, problems: list[str], notes: list[str],
           as_json: bool) -> None:
    if as_json:
        print(json.dumps({"proposal": pid, "ok": not problems, "problems": problems,
                          "notes": notes, **summary}, indent=2))
        return
    print(f"PROPOSAL CHECK — {pid}")
    print("=" * (17 + len(pid)))
    if summary:
        print(f"\n  {summary['actions']} action(s), {summary['evidence']} piece(s) of "
              f"evidence, {summary['unresolved']} unresolved")
        print(f"  confidence: {summary['confidence']}   risk: {summary['risk']}")
    if problems:
        print("\nNOT READY:")
        for item in problems:
            print(f"  x {item}")
    else:
        print("\nReady for a human to read — cited, reversible, and nothing applied.")
    if notes:
        print("\nWorth improving (not blocking):")
        for item in notes:
            print(f"  ! {item}")


if __name__ == "__main__":
    sys.exit(main())
