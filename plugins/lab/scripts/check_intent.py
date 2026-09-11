#!/usr/bin/env python3
"""Validate the intent artifact before the checkpoint lets them past.

Follows the structure from Anthropic's AI-native SDLC playbook: Problem, Proposed outcome,
Affected users and systems, Constraints, Open questions, with Author and Status metadata.

    check_intent.py            validate ./intent.md
    check_intent.py --json     machine-readable

Exit 0 if the intent is usable as the thing everything else is measured against.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

SECTIONS = ["Problem", "Proposed outcome", "Affected users and systems",
            "Constraints", "Open questions"]
MAX_LINES = 60          # it is imported into CLAUDE.md, so it costs context every turn


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    path = os.path.join(args.root, "intent.md")
    problems: list[str] = []
    notes: list[str] = []

    if not os.path.exists(path):
        problems.append("no intent.md at the project root")
        report(problems, notes, args.as_json)
        return 1

    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()

    if "TODO" in text:
        left = [l.strip() for l in lines if "TODO" in l]
        problems.append(f"{len(left)} TODO left, starting with {left[0][:60]!r}")

    title = re.match(r"^#\s*Intent:\s*(.+)$", lines[0].strip()) if lines else None
    if not title:
        problems.append("the first line should be `# Intent: <a title a stranger would "
                        "understand>`")
    elif len(title.group(1).strip()) < 12:
        notes.append("the title is very short — it is what a reader sees first in git history")

    for field in ("Author", "Status"):
        if not re.search(rf"^{field}:\s*\S+", text, re.M):
            notes.append(f"no `{field}:` line — this is a governed artifact, and both show up "
                         f"in review")

    for section in SECTIONS:
        if not re.search(rf"^##\s*{re.escape(section)}\s*$", text, re.M | re.I):
            problems.append(f"missing section: ## {section}")

    # the two sections that do real work downstream
    def body_of(name: str) -> str:
        match = re.search(rf"^##\s*{re.escape(name)}\s*$(.*?)(?=^##\s|\Z)",
                          text, re.M | re.S | re.I)
        return (match.group(1) if match else "").strip()

    constraints = body_of("Constraints")
    bullets = [l for l in constraints.splitlines() if l.strip().startswith(("-", "*"))]
    if constraints and len(bullets) < 2:
        problems.append("Constraints needs at least two concrete rules — they become your "
                        "skill's constraints and your hook")

    outcome = body_of("Proposed outcome")
    if outcome and len(outcome.split()) < 12:
        notes.append("Proposed outcome is very thin — write it so somebody else could tell "
                     "whether it happened")

    questions = body_of("Open questions")
    q_bullets = [l for l in questions.splitlines() if l.strip().startswith(("-", "*"))]
    if not q_bullets:
        problems.append("Open questions is empty. An unwritten question gets silently "
                        "answered by whoever implements it — usually wrongly. Write at "
                        "least one, even if it feels obvious")

    if len(lines) > MAX_LINES:
        notes.append(f"{len(lines)} lines. It is imported into CLAUDE.md, so it is paid for "
                     f"on every turn — aim under {MAX_LINES}")

    report(problems, notes, args.as_json)
    return 1 if problems else 0


def report(problems: list[str], notes: list[str], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"artifact": "intent.md", "ok": not problems,
                          "problems": problems, "notes": notes}, indent=2))
        return
    print("INTENT CHECK")
    print("============")
    if problems:
        print("\nNOT READY:")
        for item in problems:
            print(f"  x {item}")
    else:
        print("\nReady — this is something the rest of the module can be measured against.")
    if notes:
        print("\nWorth improving (not blocking):")
        for item in notes:
            print(f"  ! {item}")


if __name__ == "__main__":
    sys.exit(main())
