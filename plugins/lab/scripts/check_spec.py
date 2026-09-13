#!/usr/bin/env python3
"""Validate a participant's spec before they build against it.

Checks the properties that make a spec more useful than a long prompt: it is checkable, it
says what is out of scope, and it says who approves what. A spec full of adjectives reads
fine and cannot be tested, which is the failure this gate exists to catch.

    check_spec.py              validate spec/ in the project
    check_spec.py --json       machine-readable
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# Words that feel like acceptance criteria and cannot be checked by anybody.
VAGUE = ("appropriate", "reasonable", "good", "high quality", "as needed", "properly",
         "correctly", "sensible", "user-friendly", "robust", "efficient", "clean")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    problems: list[str] = []
    notes: list[str] = []

    md = os.path.join(root, "spec", "capability.md")
    js = os.path.join(root, "spec", "capability.json")
    if not os.path.exists(md):
        report({}, ["no spec/capability.md yet — step 4.1 is where this comes from"], [],
               args.as_json)
        return 1

    text = open(md, encoding="utf-8").read()
    todos = text.count("TODO")
    if todos:
        problems.append(f"{todos} TODO left in spec/capability.md")

    # --- the machine-readable half, which the gate and the apply tool both read
    if not os.path.exists(js):
        problems.append("no spec/capability.json — the approval gate reads `published_to` "
                        "from it, so without it the gate guards the wrong directory")
        config = {}
    else:
        try:
            config = json.load(open(js)) or {}
        except ValueError as exc:
            problems.append(f"spec/capability.json is not valid JSON: {exc}")
            config = {}
        for field in ("capability", "published_to"):
            if not config.get(field):
                problems.append(f"spec/capability.json has no `{field}`")
        if config.get("requires_approval") is not True:
            problems.append("spec/capability.json does not set requires_approval: true — "
                            "this module's whole claim is that it does")
        approvers = config.get("approvers") or []
        if not approvers or any("TODO" in str(a) for a in approvers):
            problems.append("spec/capability.json names no approvers")
        elif any(re.search(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", str(a)) for a in approvers):
            notes.append("an approver looks like a person's name. A role survives somebody "
                         "leaving; a name does not")

    # --- acceptance criteria, as scenarios
    scenarios = re.findall(r"^\s*Scenario:\s*(.+)$", text, re.M | re.I)
    if not scenarios:
        problems.append("no `Scenario:` blocks. Acceptance criteria written as prose are "
                        "not checkable — that is the difference between a spec and a prompt")
    elif len(scenarios) < 3:
        problems.append(f"{len(scenarios)} scenario(s). Cover at least the normal case, the "
                        f"case where the evidence is missing, and approval being required")
    for name in scenarios:
        if "TODO" in name:
            problems.append(f"a scenario is still named 'TODO': {name[:50]}")
    for keyword in ("Given", "When", "Then"):
        if not re.search(rf"^\s*{keyword}\b", text, re.M):
            problems.append(f"no `{keyword}` step in any scenario")

    # a scenario about approval is the one nobody writes
    if scenarios and not re.search(r"approv", text, re.I):
        problems.append("no scenario covers approval. It is the control this module adds, "
                        "so it needs a criterion like everything else")

    # --- the sections that do the real work
    for heading, why in (
        (r"out of scope", "a capability with no stated boundary grows until it is "
                          "unreviewable, and 'what does this NOT do' is the first question "
                          "a reviewer asks"),
        (r"polic", "the rules that hold regardless of what an individual case makes "
                   "tempting"),
        (r"rollback", "it tells the approver what they are actually deciding"),
    ):
        if not re.search(rf"^#+.*{heading}", text, re.M | re.I):
            problems.append(f"no section on {heading.strip('()')} — {why}")

    found_vague = sorted({w for w in VAGUE if re.search(rf"\b{w}\b", text, re.I)})
    if found_vague:
        notes.append(f"unmeasurable words in the spec: {', '.join(found_vague)}. Each one "
                     f"is a criterion nobody can fail")

    if re.search(r"cannot be undone|irreversible|not reversible", text, re.I):
        notes.append("an irreversible action is named — good. Make sure the proposal says "
                     "so too, not only the spec")

    summary = {"scenarios": len(scenarios), "capability": config.get("capability"),
               "published_to": config.get("published_to")}
    report(summary, problems, notes, args.as_json)
    return 1 if problems else 0


def report(summary: dict, problems: list[str], notes: list[str], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"ok": not problems, "problems": problems, "notes": notes,
                          **summary}, indent=2))
        return
    print("SPEC CHECK")
    print("==========")
    if summary:
        print(f"\n  {summary.get('scenarios', 0)} scenario(s)"
              f"   capability: {summary.get('capability')}"
              f"   publishes to: {summary.get('published_to')}/")
    if problems:
        print("\nNOT READY:")
        for item in problems:
            print(f"  x {item}")
    else:
        print("\nReady — checkable criteria, a stated boundary, and a named approver.")
    if notes:
        print("\nWorth improving (not blocking):")
        for item in notes:
            print(f"  ! {item}")


if __name__ == "__main__":
    sys.exit(main())
