#!/usr/bin/env python3
"""Agent Lab state.

All progress lives in <lab-root>/.agent-lab/state.json and is only ever changed
through this script, so the tutor never hand-edits JSON and the file cannot drift
into a shape the rest of the lab does not understand.

    state.py init                      create the state file if it is missing
    state.py show [--json]             current state
    state.py tracks [--json]           the tracks available in this plugin
    state.py record-env < doctor.json  store the doctor's findings
    state.py set-track <id> [--reason] choose or switch track
    state.py set <key.path> <value>    generic setter (JSON value, else string)
    state.py touch-session             stamp the start of a session

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
TRACKS_DIR = os.path.join(PLUGIN_ROOT, "tracks")

MODULES = [
    ("01", "Harness and coding agent"),
    ("02", "RAG and retrieval systems"),
    ("03", "Knowledge graphs and ontologies"),
    ("04", "The full AI system"),
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def state_path(root: str) -> str:
    return os.path.join(root, ".agent-lab", "state.json")


def blank_state(root: str) -> dict:
    return {
        "version": SCHEMA_VERSION,
        "lab": {"root": os.path.abspath(root), "created_at": now(), "last_session_at": None,
                "sessions": 0},
        "participant": {"name": None, "group": None},
        "mode": "guided",
        "track": None,
        "track_history": [],
        "env": {"ready": False, "checked_at": None, "platform": None,
                "python_bin": None, "python_version": None, "failed": []},
        "progress": {"current_module": None, "current_checkpoint": None,
                     "completed_checkpoints": [], "completed_modules": []},
        "artifacts": {},
        "eval_history": [],
        "quizzes": {},
        "homework": {},
        "issues": [],
    }


def load(root: str, required: bool = True) -> dict | None:
    path = state_path(root)
    if not os.path.exists(path):
        if required:
            sys.exit(f"no lab state at {path} — run /lab:start first")
        return None
    with open(path) as fh:
        return json.load(fh)


def save(root: str, state: dict) -> None:
    path = state_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)          # atomic: a killed session never leaves half a file


def read_tracks() -> list[dict]:
    tracks = []
    if not os.path.isdir(TRACKS_DIR):
        return tracks
    for entry in sorted(os.listdir(TRACKS_DIR)):
        meta = os.path.join(TRACKS_DIR, entry, "track.json")
        if os.path.exists(meta):
            with open(meta) as fh:
                data = json.load(fh)
            data.setdefault("id", entry)
            tracks.append(data)
    tracks.sort(key=lambda t: t.get("order", 99))
    return tracks


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

def render(state: dict) -> str:
    track = state.get("track")
    tracks = {t["id"]: t for t in read_tracks()}
    track_name = tracks.get(track, {}).get("name", track) if track else "not chosen yet"

    env = state["env"]
    env_line = "not checked yet"
    if env.get("checked_at"):
        env_line = "ready" if env.get("ready") else f"NOT ready ({', '.join(env.get('failed') or [])})"

    prog = state["progress"]
    done = set(prog.get("completed_modules") or [])
    current = prog.get("current_module")

    lines = [
        "AGENT LAB — STATUS",
        "==================",
        "",
        f"Track:   {track_name}" + (f"  [{track}]" if track else ""),
        f"Mode:    {state.get('mode')}",
        f"Env:     {env_line}",
        f"Python:  {env.get('python_bin') or 'unknown'}",
        "",
        "MODULES",
    ]
    for num, title in MODULES:
        mark = "[x]" if num in done else ("[>]" if num == current else "[ ]")
        lines.append(f"  {mark} {num}  {title}")

    checkpoints = prog.get("completed_checkpoints") or []
    lines += ["", f"Checkpoints cleared: {len(checkpoints)}"
                  + (f"  (last: {checkpoints[-1]})" if checkpoints else "")]

    if state.get("eval_history"):
        lines += ["", "SCOREBOARD"]
        for row in state["eval_history"][-6:]:
            lines.append(f"  {row.get('label','?'):<28} {row.get('score','?')}")

    if state.get("issues"):
        lines += ["", "OPEN ISSUES"]
        lines += [f"  - {i}" for i in state["issues"]]

    return "\n".join(lines)


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_init(args) -> int:
    path = state_path(args.root)
    if os.path.exists(path) and not args.force:
        print(f"already initialised: {path}")
        return 0
    save(args.root, blank_state(args.root))
    print(f"initialised: {path}")
    return 0


def cmd_show(args) -> int:
    state = load(args.root)
    print(json.dumps(state, indent=2) if args.as_json else render(state))
    return 0


def cmd_tracks(args) -> int:
    tracks = read_tracks()
    if args.as_json:
        print(json.dumps(tracks, indent=2))
        return 0
    for t in tracks:
        print(f"{t['id']:<20} {t['name']}")
        print(f"{'':20} {t.get('tagline','')}")
    return 0


def cmd_record_env(args) -> int:
    payload = json.load(sys.stdin)
    state = load(args.root)
    state["env"] = {
        "ready": bool(payload.get("ready")),
        "checked_at": now(),
        "platform": payload.get("platform"),
        "python_bin": payload.get("python_bin"),
        "python_version": payload.get("python_version"),
        "failed": payload.get("failed") or [],
    }
    save(args.root, state)
    print("recorded" if state["env"]["ready"] else "recorded (not ready)")
    return 0


def cmd_set_track(args) -> int:
    tracks = {t["id"]: t for t in read_tracks()}
    if args.track_id not in tracks:
        sys.exit(f"unknown track '{args.track_id}' — available: {', '.join(tracks)}")
    state = load(args.root)
    previous = state.get("track")
    if previous == args.track_id:
        print(f"already on {args.track_id}")
        return 0
    state["track"] = args.track_id
    state["track_history"].append({
        "at": now(), "from": previous, "to": args.track_id, "reason": args.reason,
    })
    save(args.root, state)
    if previous:
        print(f"switched {previous} -> {args.track_id}")
    else:
        print(f"track set: {args.track_id}")
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


def cmd_begin_module(args) -> int:
    valid = {num for num, _ in MODULES}
    if args.module_id not in valid:
        sys.exit(f"unknown module '{args.module_id}' — expected one of {sorted(valid)}")
    state = load(args.root)
    state["progress"]["current_module"] = args.module_id
    save(args.root, state)
    print(f"module {args.module_id} started")
    return 0


def cmd_checkpoint(args) -> int:
    state = load(args.root)
    done = state["progress"].setdefault("completed_checkpoints", [])
    if args.checkpoint_id in done:
        print(f"{args.checkpoint_id} already cleared")
        return 0
    done.append(args.checkpoint_id)
    state["progress"]["current_checkpoint"] = args.checkpoint_id
    save(args.root, state)
    print(f"checkpoint {args.checkpoint_id} cleared ({len(done)} total)")
    return 0


def cmd_complete_module(args) -> int:
    valid = {num for num, _ in MODULES}
    if args.module_id not in valid:
        sys.exit(f"unknown module '{args.module_id}' — expected one of {sorted(valid)}")
    state = load(args.root)
    done = state["progress"].setdefault("completed_modules", [])
    if args.module_id not in done:
        done.append(args.module_id)
        done.sort()
    save(args.root, state)
    print(f"module {args.module_id} complete")
    return 0


def cmd_touch_session(args) -> int:
    state = load(args.root)
    state["lab"]["last_session_at"] = now()
    state["lab"]["sessions"] = int(state["lab"].get("sessions") or 0) + 1
    save(args.root, state)
    print(f"session {state['lab']['sessions']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Agent Lab state")
    ap.add_argument("--root", default=os.getcwd(), help="lab root (default: cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init"); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_init)
    p = sub.add_parser("show"); p.add_argument("--json", action="store_true", dest="as_json"); p.set_defaults(fn=cmd_show)
    p = sub.add_parser("tracks"); p.add_argument("--json", action="store_true", dest="as_json"); p.set_defaults(fn=cmd_tracks)
    p = sub.add_parser("record-env"); p.set_defaults(fn=cmd_record_env)
    p = sub.add_parser("set-track"); p.add_argument("track_id"); p.add_argument("--reason", default=None); p.set_defaults(fn=cmd_set_track)
    p = sub.add_parser("set"); p.add_argument("key"); p.add_argument("value"); p.set_defaults(fn=cmd_set)
    p = sub.add_parser("touch-session"); p.set_defaults(fn=cmd_touch_session)
    p = sub.add_parser("begin-module"); p.add_argument("module_id"); p.set_defaults(fn=cmd_begin_module)
    p = sub.add_parser("checkpoint"); p.add_argument("checkpoint_id"); p.set_defaults(fn=cmd_checkpoint)
    p = sub.add_parser("complete-module"); p.add_argument("module_id"); p.set_defaults(fn=cmd_complete_module)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
