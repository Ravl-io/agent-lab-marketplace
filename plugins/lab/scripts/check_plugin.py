#!/usr/bin/env python3
"""Validate the plugin a participant assembled in Step 6.

Checks the things that make a plugin *portable* rather than merely present. The failure this
catches most is a skill that refers to its own tool by a project-relative path: it works in
the folder it was built in and breaks the moment anybody installs it.

    check_plugin.py             validate the track's expected plugin
    check_plugin.py --name foo  validate a specific directory
    check_plugin.py --json      machine-readable

Exit 0 if the plugin would work on somebody else's machine, 1 if not.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def track_meta(root: str) -> dict:
    state = os.path.join(root, ".agent-lab", "state.json")
    if not os.path.exists(state):
        return {}
    try:
        with open(state) as fh:
            track = json.load(fh).get("track")
        with open(os.path.join(PLUGIN_ROOT, "tracks", track, "track.json")) as fh:
            return json.load(fh)
    except (OSError, ValueError, TypeError):
        return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--name", default=None)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    meta = track_meta(root)
    name = args.name or meta.get("system_name")
    skill, tool = meta.get("first_skill"), meta.get("first_tool")
    if not name:
        sys.exit("no plugin name known — pass --name, or run /lab:start first")

    base = os.path.join(root, name)
    problems: list[str] = []
    notes: list[str] = []

    manifest = os.path.join(base, ".claude-plugin", "plugin.json")
    if not os.path.exists(manifest):
        problems.append(f"no manifest at {name}/.claude-plugin/plugin.json")
        report(name, problems, notes, args.as_json)
        return 1

    try:
        declared = json.load(open(manifest))
    except ValueError as exc:
        problems.append(f"{name}/.claude-plugin/plugin.json is not valid JSON: {exc}")
        declared = {}

    if declared.get("name") != name:
        problems.append(f"manifest name is {declared.get('name')!r} but the directory is "
                        f"{name!r} — the name sets the command namespace, so they must match")
    description = str(declared.get("description") or "")
    if not description:
        problems.append("the manifest has no description — it is what somebody reads before "
                        "installing")
    elif "TODO" in description:
        problems.append("the manifest description is still the scaffold's TODO")
    elif len(description) < 40:
        notes.append("the description is very short for something a stranger reads first")
    if not declared.get("version"):
        notes.append("no version in the manifest — set one, even 0.1.0")

    # the components must actually be in the plugin, not left behind in the project
    skill_path = os.path.join(base, "skills", skill or "", "SKILL.md")
    if skill and not os.path.exists(skill_path):
        problems.append(f"the skill is not in the plugin: expected "
                        f"{name}/skills/{skill}/SKILL.md")
    tool_path = os.path.join(base, "tools", f"{tool}.py") if tool else None
    if tool and not os.path.exists(tool_path):
        problems.append(f"the tool is not in the plugin: expected {name}/tools/{tool}.py")

    hooks_json = os.path.join(base, "hooks", "hooks.json")
    if not os.path.exists(hooks_json):
        notes.append(f"no {name}/hooks/hooks.json — the hook stays project-local, which is a "
                     f"choice, but then it does not travel with the plugin")
    else:
        text = open(hooks_json).read()
        try:
            json.loads(text)
        except ValueError as exc:
            problems.append(f"{name}/hooks/hooks.json is not valid JSON: {exc}")
        if "CLAUDE_PROJECT_DIR" in text:
            problems.append("hooks.json points at ${CLAUDE_PROJECT_DIR} — inside a plugin the "
                            "script lives at ${CLAUDE_PLUGIN_ROOT}, and the project-relative "
                            "path will not exist on anybody else's machine")
        elif "CLAUDE_PLUGIN_ROOT" not in text:
            notes.append("hooks.json does not use ${CLAUDE_PLUGIN_ROOT}; check the path "
                         "resolves when the plugin is installed from elsewhere")
        referenced = os.path.join(base, "hooks", "write_boundary.py")
        if "write_boundary" in text and not os.path.exists(referenced):
            problems.append(f"hooks.json references write_boundary.py but "
                            f"{name}/hooks/write_boundary.py is missing")

    # the portability trap: a skill calling its tool by a project-relative path
    if os.path.exists(skill_path) and tool:
        body = open(skill_path).read()
        if f"tools/{tool}.py" in body and "CLAUDE_PLUGIN_ROOT" not in body:
            problems.append(f"the skill calls `tools/{tool}.py` by a project-relative path. "
                            f"Inside a plugin that resolves against whoever installed it, not "
                            f"against this folder — use ${{CLAUDE_PLUGIN_ROOT}}")

    # the real validator, when it is available
    if shutil.which("claude"):
        result = subprocess.run(["claude", "plugin", "validate", base],
                                capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            problems.append("`claude plugin validate` failed: "
                            + (result.stdout + result.stderr).strip()[-200:])
    else:
        notes.append("the claude CLI is not on PATH, so `claude plugin validate` was skipped")

    # the two files that make this a project rather than a pile
    for filename, purpose in (("CLAUDE.md", "what is true for every task in this project"),
                              ("intent.md", "what the thing is for")):
        path = os.path.join(root, filename)
        if not os.path.exists(path):
            notes.append(f"no {filename} at the project root — {purpose}")
        elif "TODO" in open(path).read():
            problems.append(f"{filename} still contains the scaffold's TODOs")

    # intent only drives anything if it is actually loaded
    claude_md = os.path.join(root, "CLAUDE.md")
    if os.path.exists(claude_md) and os.path.exists(os.path.join(root, "intent.md")):
        body = open(claude_md).read()
        if not re.search(r"^\s*@intent\.md\s*$", body, re.M):
            problems.append("CLAUDE.md does not import intent.md. Without a line reading "
                            "`@intent.md`, the intent is a document nobody loads — add the "
                            "import so it is in context every turn")

    report(name, problems, notes, args.as_json)
    return 1 if problems else 0


def report(name: str, problems: list[str], notes: list[str], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"plugin": name, "ok": not problems,
                          "problems": problems, "notes": notes}, indent=2))
        return
    print(f"PLUGIN CHECK — {name}")
    print("=" * (15 + len(name)))
    if problems:
        print("\nNOT READY:")
        for item in problems:
            print(f"  x {item}")
    else:
        print("\nReady — this would work on somebody else's machine.")
    if notes:
        print("\nWorth improving (not blocking):")
        for item in notes:
            print(f"  ! {item}")


if __name__ == "__main__":
    sys.exit(main())
