#!/usr/bin/env python3
"""Support Lab state.

All progress lives in <lab-root>/.support-lab/state.json and is only ever changed through
this script, so the tutor never hand-edits JSON and the file cannot drift into a shape the
rest of the lab does not understand.

    state.py init                 create the state file if it is missing
    state.py show [--json]        current state (JSON adds open_step / next_step details)
    state.py touch-session        stamp the start of a session
    state.py open <step>          mark a step as opened (presented, not yet judged)
    state.py clear <step>         mark a step as cleared (judged and good)
    state.py set <key.path> <v>   generic setter (JSON value, else string)
    state.py complete             mark the module complete
    state.py reset --force        delete the state file

Stdlib only. Exits non-zero with a message on stderr when something is wrong.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

SCHEMA_VERSION = "0.1"
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_DIR = os.path.join(PLUGIN_ROOT, "modules", "01")

# The arc of Module 1. Order matters: `next_step` is the first one not yet cleared.
STEPS = [
    ("S0", "Orientation and setup", "00-orientation.md", 5),
    ("S1", "Meet the workspace", "01-meet-the-workspace.md", 8),
    ("S2", "Read the ticket", "02-read-the-ticket.md", 4),
    ("S3", "What the docs promise", "03-what-the-docs-promise.md", 5),
    ("S4", "The customer's settings", "04-the-customers-settings.md", 6),
    ("S5", "The timeline", "05-the-timeline.md", 8),
    ("S6", "Last known good", "06-last-known-good.md", 6),
    ("S7", "The vendor's own notes", "07-the-vendors-notes.md", 4),
    ("S8", "Write the findings", "08-write-the-findings.md", 12),
    ("S9", "Capture the process as a plugin", "09-capture-the-process.md", 12),
    ("S10", "Run it in a new session", "10-run-it.md", 15),
    ("S11", "Debrief", "11-debrief.md", 5),
]
STEP_IDS = [s[0] for s in STEPS]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def state_path(root: str) -> str:
    return os.path.join(root, ".support-lab", "state.json")


def blank_state(root: str) -> dict:
    return {
        "version": SCHEMA_VERSION,
        "lab": {"root": os.path.abspath(root), "created_at": now(),
                "last_session_at": None, "sessions": 0},
        "participant": {"name": None},
        "progress": {"open_step": None, "cleared_steps": [], "module_complete": False},
        "notes": [],
    }


def load(root: str) -> dict:
    path = state_path(root)
    if not os.path.exists(path):
        sys.exit(f"no lab state at {path} — say 'lab start' first")
    with open(path) as fh:
        return json.load(fh)


def save(root: str, state: dict) -> None:
    path = state_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)  # atomic: a killed session never leaves half a file


def step_info(step_id: str | None) -> dict | None:
    for sid, title, fname, minutes in STEPS:
        if sid == step_id:
            return {"id": sid, "title": title, "minutes": minutes,
                    "file": os.path.join(MODULE_DIR, fname)}
    return None


def next_step(state: dict) -> dict | None:
    cleared = set(state["progress"].get("cleared_steps") or [])
    for sid, *_ in STEPS:
        if sid not in cleared:
            return step_info(sid)
    return None


def enrich(state: dict) -> dict:
    out = dict(state)
    prog = state["progress"]
    out["open_step_info"] = step_info(prog.get("open_step"))
    out["next_step"] = next_step(state)
    out["steps"] = [
        {"id": sid, "title": title, "minutes": minutes,
         "status": ("cleared" if sid in (prog.get("cleared_steps") or [])
                    else "open" if sid == prog.get("open_step") else "todo")}
        for sid, title, _f, minutes in STEPS
    ]
    return out


def render(state: dict) -> str:
    prog = state["progress"]
    cleared = prog.get("cleared_steps") or []
    open_id = prog.get("open_step")
    lines = ["SUPPORT LAB — MODULE 1 — STATUS", "=" * 31, ""]
    for sid, title, _f, minutes in STEPS:
        mark = "[x]" if sid in cleared else ("[>]" if sid == open_id else "[ ]")
        lines.append(f"  {mark} {sid:<4} {title:<34} {minutes:>2} min")
    lines.append("")
    if prog.get("module_complete"):
        lines.append("Module 1 complete.")
    elif open_id:
        info = step_info(open_id)
        lines.append(f"Open step: {open_id} — {info['title'] if info else ''}  (say 'next' when done)")
    else:
        nxt = next_step(state)
        lines.append(f"Next step: {nxt['id']} — {nxt['title']}  (say 'next')" if nxt else "Nothing left.")
    lines.append(f"Sessions: {state['lab'].get('sessions', 0)}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_init(args) -> int:
    path = state_path(args.root)
    if os.path.exists(path):
        print(f"already initialised: {path}")
        return 0
    save(args.root, blank_state(args.root))
    print(f"initialised: {path}")
    return 0


def cmd_show(args) -> int:
    state = load(args.root)
    print(json.dumps(enrich(state), indent=2) if args.as_json else render(state))
    return 0


def cmd_touch_session(args) -> int:
    state = load(args.root)
    state["lab"]["last_session_at"] = now()
    state["lab"]["sessions"] = int(state["lab"].get("sessions") or 0) + 1
    save(args.root, state)
    print(f"session {state['lab']['sessions']}")
    return 0


def _check_step(step_id: str) -> None:
    if step_id not in STEP_IDS:
        sys.exit(f"unknown step '{step_id}' — expected one of {', '.join(STEP_IDS)}")


def cmd_open(args) -> int:
    _check_step(args.step)
    state = load(args.root)
    state["progress"]["open_step"] = args.step
    save(args.root, state)
    info = step_info(args.step)
    print(f"opened {args.step} — {info['title']}")
    print(f"file: {info['file']}")
    return 0


def cmd_clear(args) -> int:
    _check_step(args.step)
    state = load(args.root)
    cleared = state["progress"].setdefault("cleared_steps", [])
    if args.step not in cleared:
        cleared.append(args.step)
        cleared.sort(key=STEP_IDS.index)
    if state["progress"].get("open_step") == args.step:
        state["progress"]["open_step"] = None
    save(args.root, state)
    nxt = next_step(state)
    print(f"cleared {args.step} ({len(cleared)} of {len(STEPS)})")
    print(f"next: {nxt['id']} — {nxt['title']}" if nxt else "next: none — module finished")
    return 0


def cmd_set(args) -> int:
    state = load(args.root)
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        value = args.value
    node = state
    parts = args.key.split(".")
    for part in parts[:-1]:
        if not isinstance(node.get(part), dict):
            node[part] = {}
        node = node[part]
    node[parts[-1]] = value
    save(args.root, state)
    print(f"{args.key} = {json.dumps(value)}")
    return 0


def cmd_complete(args) -> int:
    state = load(args.root)
    state["progress"]["module_complete"] = True
    state["progress"]["open_step"] = None
    save(args.root, state)
    print("module 1 complete")
    return 0


def cmd_reset(args) -> int:
    path = state_path(args.root)
    if not args.force:
        sys.exit("refusing to delete state without --force")
    if os.path.exists(path):
        os.remove(path)
        print(f"removed {path}")
    else:
        print("no state file to remove")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Support Lab state")
    ap.add_argument("--root", default=os.getcwd(), help="lab root (default: cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init"); p.set_defaults(fn=cmd_init)
    p = sub.add_parser("show"); p.add_argument("--json", action="store_true", dest="as_json"); p.set_defaults(fn=cmd_show)
    p = sub.add_parser("touch-session"); p.set_defaults(fn=cmd_touch_session)
    p = sub.add_parser("open"); p.add_argument("step"); p.set_defaults(fn=cmd_open)
    p = sub.add_parser("clear"); p.add_argument("step"); p.set_defaults(fn=cmd_clear)
    p = sub.add_parser("set"); p.add_argument("key"); p.add_argument("value"); p.set_defaults(fn=cmd_set)
    p = sub.add_parser("complete"); p.set_defaults(fn=cmd_complete)
    p = sub.add_parser("reset"); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_reset)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
