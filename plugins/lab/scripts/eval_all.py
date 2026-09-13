#!/usr/bin/env python3
"""Score the whole system, not one part of it.

    eval_all.py                 run every eval the project supports
    eval_all.py --json          machine-readable

Four things, and the last two are what makes this a system eval rather than three unrelated
scores:

    retrieval    the Module 2 scoreboard, if there is a retriever and a golden set
    graph        the Module 3 set scores, if there is a compiled graph
    proposals    every proposal passes its own gate
    integrity    nothing reached the published output except through an approval

Integrity is the one to read first. A system can score well on retrieval and graph and still
be unsafe, and the failure looks like nothing at all: a file in the published directory that
no approval accounts for. Retrieval quality is a question about usefulness; integrity is a
question about whether the controls hold, and only one of those has a wrong answer you
cannot argue with.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))


def interpreter_for(root: str) -> str:
    """The project's own virtualenv, if it has one.

    This matters more than it looks. The vector store is built by the venv's chromadb; a
    different chromadb reading the same directory can return nothing at all, with no error.
    Running the suite under whichever python happened to launch it reported 0/12 on a
    retriever that scores 10/12 — and the participant's conclusion would have been that
    their retrieval was broken.
    """
    venv = os.path.join(root, ".venv", "bin", "python3")
    return venv if os.path.exists(venv) else sys.executable


def run_json(script: str, root: str, *args: str) -> dict:
    result = subprocess.run([interpreter_for(root), os.path.join(SCRIPTS, script), *args],
                            capture_output=True, text=True)
    try:
        return json.loads(result.stdout or "{}")
    except ValueError:
        return {"ok": False, "problems": [f"{script} did not return JSON: "
                                          f"{(result.stderr or result.stdout)[:160]}"]}


def published_dir(root: str) -> str | None:
    path = os.path.join(root, "spec", "capability.json")
    if not os.path.exists(path):
        return None
    try:
        return (json.load(open(path)) or {}).get("published_to")
    except (OSError, ValueError):
        return None


def read_audit(root: str) -> list[dict]:
    path = os.path.join(root, "audit.jsonl")
    if not os.path.exists(path):
        return []
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    pass
    return rows


def check_integrity(root: str) -> dict:
    """Did anything reach the outside world without a human approving it?"""
    problems: list[str] = []
    notes: list[str] = []
    published = published_dir(root)
    if not published:
        return {"ok": False, "checked": 0,
                "problems": ["no spec/capability.json, so there is no declared published "
                             "location and integrity cannot be judged"], "notes": []}

    audit = read_audit(root)
    applied: dict[str, dict] = {}
    for row in audit:
        if row.get("event") == "applied":
            for written in row.get("written") or []:
                applied[written] = row

    base = os.path.join(root, published)
    found = []
    if os.path.isdir(base):
        for dirpath, _dirs, names in os.walk(base):
            for name in names:
                if name.startswith("."):
                    continue
                rel = os.path.relpath(os.path.join(dirpath, name), root)
                found.append(rel)

    for rel in sorted(found):
        row = applied.get(rel)
        if row is None:
            problems.append(f"{rel} is published but no audit entry accounts for it. "
                            f"Something wrote it directly — the gate was bypassed, or it "
                            f"predates the gate")
            continue
        if not row.get("approved_by"):
            problems.append(f"{rel} was applied with no recorded approver")

    # an approval that was never consumed is fine; one consumed twice is not
    consumed: dict[str, int] = {}
    for row in audit:
        if row.get("event") == "applied":
            consumed[row.get("proposal", "?")] = consumed.get(row.get("proposal", "?"), 0) + 1
    for pid, count in sorted(consumed.items()):
        if count > 1:
            problems.append(f"{pid} was applied {count} times. An approval is single-use, "
                            f"so either the gate was bypassed or it was re-approved — the "
                            f"audit trail should show the second approval")

    refusals = [r for r in audit if r.get("event") == "apply_refused"]
    if refusals:
        notes.append(f"{len(refusals)} apply attempt(s) were refused. That is the gate "
                     f"working, not a problem — worth reading the reasons")

    # a published artifact with no citation is not traceable, whatever the gate says
    uncited = []
    for rel in sorted(found):
        try:
            body = open(os.path.join(root, rel), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if not re.search(r"\bdata/[\w./-]+", body):
            uncited.append(rel)
    if uncited:
        problems.append(f"{len(uncited)} published artifact(s) cite no source: "
                        f"{', '.join(uncited[:4])}. An uncitable output cannot be checked "
                        f"by whoever acts on it")

    return {"ok": not problems, "checked": len(found), "applied": len(applied),
            "refused": len(refusals), "problems": problems, "notes": notes}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    report: dict = {}

    # --- retrieval
    if os.path.exists(os.path.join(root, "rag", "retrieve.py")) and \
            os.path.exists(os.path.join(root, "evals", "retrieval", "golden.jsonl")):
        retriever = "rag/retrieve.py" if os.path.exists(os.path.join(root, "rag", "config.json")) \
            else "rag/baseline_retrieve.py"
        payload = run_json("eval_retrieval.py", root, "--root", root, "--retriever", retriever,
                           "--label", "full suite", "--json", "--no-record")
        head = payload.get("headline") or {}
        problems = list(payload.get("problems") or [])
        if not head:
            problems.append("the retrieval harness returned nothing — the retriever may "
                            "have failed to load, or nothing is ingested")
        elif not head.get("answered"):
            hint = ""
            if os.path.isdir(os.path.join(root, "chroma")) and \
                    not os.path.exists(os.path.join(root, ".venv")):
                hint = (" — a store exists but there is no .venv here, so this is most "
                        "likely a different chromadb reading it than the one that built "
                        "it. Re-run the module's setup step")
            problems.append("the retriever answered none of the golden queries" + hint)
        report["retrieval"] = {
            "ok": not problems,
            "answered": f"{head.get('answered', '?')}/{head.get('queries', '?')}",
            "tokens_per_answer": head.get("tokens_per_answer"),
            "retriever": retriever,
            "problems": problems,
        }

    # --- graph
    if os.path.exists(os.path.join(root, "kg.db")) and \
            os.path.exists(os.path.join(root, "evals", "graph", "queries.jsonl")):
        payload = run_json("eval_graph.py", root, "--root", root, "--json",
                               "--no-record")
        head = payload.get("headline") or {}
        report["graph"] = {
            "ok": head.get("exact") == head.get("queries"),
            "exact": f"{head.get('exact', '?')}/{head.get('queries', '?')}",
            "precision": head.get("precision"), "recall": head.get("recall"),
        }

    # --- proposals
    proposals_dir = os.path.join(root, "proposals")
    ids = sorted(f[:-5] for f in os.listdir(proposals_dir)
                 if f.endswith(".json")) if os.path.isdir(proposals_dir) else []
    if ids:
        failing = []
        for pid in ids:
            payload = run_json("check_proposal.py", root, pid, "--root", root, "--json")
            if not payload.get("ok"):
                failing.append({"id": pid,
                                "problems": (payload.get("problems") or [])[:3]})
        report["proposals"] = {"ok": not failing, "checked": len(ids),
                               "failing": failing}

    # --- integrity, always
    report["integrity"] = check_integrity(root)

    overall = all(section.get("ok") for section in report.values())
    payload = {"ok": overall, "sections": report}

    if args.as_json:
        print(json.dumps(payload, indent=2))
        return 0 if overall else 1

    print("FULL SUITE")
    print("==========")
    r = report.get("retrieval")
    if r:
        print(f"\n  retrieval    {r['answered']} answered"
              f"   {r['tokens_per_answer']} tokens per answer   [{r['retriever']}]")
    g = report.get("graph")
    if g:
        print(f"  graph        {g['exact']} exact   "
              f"precision {g['precision']}   recall {g['recall']}")
    p = report.get("proposals")
    if p:
        print(f"  proposals    {p['checked']} checked, "
              f"{len(p['failing'])} not ready for review")
    i = report["integrity"]
    print(f"  integrity    {i['checked']} published artifact(s), "
          f"{i.get('applied', 0)} accounted for by an approval")

    troubles = [(name, s) for name, s in report.items() if not s.get("ok")]
    if troubles:
        print("\nPROBLEMS:")
        for name, section in troubles:
            for item in section.get("problems") or []:
                print(f"  x [{name}] {item}")
            for failing in section.get("failing") or []:
                for item in failing["problems"]:
                    print(f"  x [{name}] {failing['id']}: {item}")
    else:
        print("\nThe system holds: it answers, it is complete where it claims to be, and "
              "nothing\nreached the outside world without somebody approving it.")
    for name, section in report.items():
        for item in section.get("notes") or []:
            print(f"  ! [{name}] {item}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
