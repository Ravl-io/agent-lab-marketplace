#!/usr/bin/env python3
"""Validate a participant's write-boundary hook before the checkpoint lets them past.

A hook is the one thing in the module the model cannot choose to ignore, so "it looks right"
is not good enough. This feeds it real payloads and checks what it decides.

    check_hook.py            validate .claude/hooks/write_boundary.py
    check_hook.py --json     machine-readable

Exit 0 if the hook enforces the boundary, 1 if not. Notes do not fail it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_REL = os.path.join(".claude", "hooks", "write_boundary.py")


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


def ask(root: str, hook: str, payload: dict) -> tuple[str, str]:
    """Run the hook with one payload. Returns (decision, reason)."""
    env = dict(os.environ, CLAUDE_PROJECT_DIR=os.path.abspath(root))
    try:
        p = subprocess.run([sys.executable, hook], cwd=root, env=env,
                           input=json.dumps(payload), capture_output=True,
                           text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        return "error", str(exc)
    if p.returncode not in (0, 2):
        return "error", f"exit {p.returncode}: {p.stderr.strip()[:120]}"
    out = p.stdout.strip()
    if not out:
        return "allow", ""
    try:
        decision = json.loads(out).get("hookSpecificOutput", {})
        return decision.get("permissionDecision", "allow"), \
            decision.get("permissionDecisionReason", "")
    except ValueError:
        return "error", f"stdout is not valid JSON: {out[:100]}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    hook = os.path.join(root, HOOK_REL)
    problems: list[str] = []
    notes: list[str] = []

    if not os.path.exists(hook):
        problems.append(f"no hook at {HOOK_REL}")
        report(problems, notes, args.as_json)
        return 1

    text = open(hook, encoding="utf-8").read()
    leftover = [l.strip() for l in text.splitlines() if "TODO" in l]
    if leftover:
        problems.append(f"{len(leftover)} TODO left in the file")

    # is it actually wired up? an unregistered hook never runs
    settings_path = os.path.join(root, ".claude", "settings.json")
    if not os.path.exists(settings_path):
        problems.append("no .claude/settings.json — the hook cannot be registered")
    else:
        try:
            settings = json.load(open(settings_path))
        except ValueError as exc:
            problems.append(f".claude/settings.json is not valid JSON: {exc}")
            settings = {}
        entries = (settings.get("hooks") or {}).get("PreToolUse") or []
        registered = any("write_boundary" in json.dumps(e) for e in entries)
        if not registered:
            problems.append("the hook is not registered under PreToolUse in "
                            ".claude/settings.json — it exists but never runs")
        else:
            matchers = [e.get("matcher", "") for e in entries
                        if "write_boundary" in json.dumps(e)]
            if not any(re.search(r"write|\*", m, re.I) for m in matchers):
                notes.append(f"registered with matcher {matchers!r} — check it actually "
                             f"matches the write tools")

    # behaviour is the point, so test it
    out_dir = track_meta(root).get("output_dir") or "notes"
    cases = [
        ("refuses a write into data/", {"tool_name": "Write",
         "tool_input": {"file_path": "data/knowledge/something.md"}}, "deny", True),
        ("refuses an absolute write into data/", {"tool_name": "Edit",
         "tool_input": {"file_path": os.path.join(root, "data", "x.md")}}, "deny", True),
        (f"allows a write into {out_dir}/", {"tool_name": "Write",
         "tool_input": {"file_path": f"{out_dir}/output.md"}}, "allow", True),
        ("allows reading data/", {"tool_name": "Read",
         "tool_input": {"file_path": "data/tickets/x.md"}}, "allow", True),
        ("refuses a write outside the project", {"tool_name": "Write",
         "tool_input": {"file_path": "../escaped.md"}}, "deny", False),
    ]
    for label, payload, expected, blocking in cases:
        got, reason = ask(root, hook, payload)
        if got == "error":
            problems.append(f"{label}: the hook errored — {reason}")
        elif got != expected:
            message = f"{label}: expected {expected}, got {got}"
            (problems if blocking else notes).append(message)
        elif expected == "deny" and blocking and len(reason) < 20:
            notes.append(f"{label}: the refusal reason is very short — it is shown to the "
                         f"model, so say what to do instead")

    report(problems, notes, args.as_json)
    return 1 if problems else 0


def report(problems: list[str], notes: list[str], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"hook": HOOK_REL, "ok": not problems,
                          "problems": problems, "notes": notes}, indent=2))
        return
    print("HOOK CHECK — write_boundary")
    print("=" * 27)
    if problems:
        print("\nNOT READY:")
        for item in problems:
            print(f"  x {item}")
    else:
        print("\nReady — registered, and it enforces the boundary.")
    if notes:
        print("\nWorth improving (not blocking):")
        for item in notes:
            print(f"  ! {item}")


if __name__ == "__main__":
    sys.exit(main())
