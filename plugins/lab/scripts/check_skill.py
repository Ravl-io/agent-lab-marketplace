#!/usr/bin/env python3
"""Validate a participant's skill before the checkpoint lets them past.

A checkpoint that only records progress is not a gate. This is what makes Step 3's gate
mean something: it checks the things that silently stop a skill working, in the order they
bite.

    check_skill.py                 validate the track's expected skill
    check_skill.py --name my-skill validate a specific one
    check_skill.py --json          machine-readable

Exit 0 if the skill would work, 1 if not. Warnings do not fail it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def track_skill_name(root: str) -> str | None:
    state = os.path.join(root, ".agent-lab", "state.json")
    if not os.path.exists(state):
        return None
    try:
        with open(state) as fh:
            track = json.load(fh).get("track")
        with open(os.path.join(PLUGIN_ROOT, "tracks", track, "track.json")) as fh:
            return json.load(fh).get("first_skill")
    except (OSError, ValueError, TypeError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--name", default=None)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    name = args.name or track_skill_name(args.root)
    if not name:
        sys.exit("no skill name known — pass --name, or run /lab:start first")

    path = os.path.join(args.root, ".claude", "skills", name, "SKILL.md")
    problems: list[str] = []
    notes: list[str] = []

    if not os.path.exists(path):
        problems.append(f"no skill at .claude/skills/{name}/SKILL.md — the folder name and "
                        f"the file name both matter, and the file must be SKILL.md")
        report(name, path, problems, notes, args.as_json)
        return 1

    text = open(path, encoding="utf-8").read()

    if not text.startswith("---"):
        problems.append("no frontmatter — the file must open with a --- line")
        report(name, path, problems, notes, args.as_json)
        return 1

    parts = text.split("---", 2)
    front = parts[1] if len(parts) > 2 else ""
    body = parts[2] if len(parts) > 2 else ""

    declared = re.search(r"^name:\s*(\S+)", front, re.M)
    if not declared:
        problems.append("frontmatter has no `name:`")
    elif declared.group(1) != name:
        problems.append(f"frontmatter name is '{declared.group(1)}' but the folder is "
                        f"'{name}' — they must match")

    desc = re.search(r"^description:\s*(.+(?:\n\s+.+)*)", front, re.M)
    if not desc:
        problems.append("frontmatter has no `description:` — without it the skill can never "
                        "be chosen")
    else:
        value = " ".join(desc.group(1).split())
        if len(value) < 40:
            problems.append(f"the description is {len(value)} characters. It is the only part "
                            f"the agent sees before deciding to open the skill; say what the "
                            f"skill does AND when to use it")
        elif not re.search(r"\buse (this )?when\b|\bwhen (asked|the user|someone)\b",
                           value, re.I):
            notes.append("the description says what the skill does but not explicitly when "
                         "to use it — skills with a 'use when …' clause get chosen earlier")

    leftover = [line.strip() for line in text.splitlines() if "TODO" in line]
    if leftover:
        problems.append(f"{len(leftover)} TODO left in the file, starting with: "
                        f"{leftover[0][:70]!r}")

    if not re.search(r"^#+\s", body, re.M):
        problems.append("the body has no sections — a procedure the agent can follow needs "
                        "structure")
    else:
        if not re.search(r"^#+.*\b(procedures?|steps?|how)\b", body, re.I | re.M):
            notes.append("no Procedure section found — the ordered steps are the part that "
                         "changes what the agent does")
        if not re.search(r"^#+.*\b(outputs?|formats?|results?)\b", body, re.I | re.M):
            notes.append("no Output section found — without it the agent invents a shape")
        if not re.search(r"^#+.*\b(constraints?|rules?|never|must)\b", body, re.I | re.M):
            notes.append("no Constraints section found — the rules a new starter gets wrong")

    if len(body.split()) < 40:
        problems.append("the body is nearly empty — the description decides whether the "
                        "skill opens, but the body is what it does")

    report(name, path, problems, notes, args.as_json)
    return 1 if problems else 0


def report(name: str, path: str, problems: list[str], notes: list[str], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"skill": name, "path": path, "ok": not problems,
                          "problems": problems, "notes": notes}, indent=2))
        return
    print(f"SKILL CHECK — {name}")
    print("=" * (14 + len(name)))
    if problems:
        print("\nNOT READY:")
        for item in problems:
            print(f"  x {item}")
    else:
        print("\nReady — this skill would be picked up and followed.")
    if notes:
        print("\nWorth improving (not blocking):")
        for item in notes:
            print(f"  ! {item}")


if __name__ == "__main__":
    sys.exit(main())
