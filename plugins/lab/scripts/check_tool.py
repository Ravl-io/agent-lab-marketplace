#!/usr/bin/env python3
"""Validate a participant's tool before the checkpoint lets them past.

Checks the two properties the module claims a tool has, rather than taking them on trust:
it produces structured output on the agreed interface, and it proves its own behaviour.

    check_tool.py                 validate the track's expected tool
    check_tool.py --name my_tool  validate a specific one
    check_tool.py --json          machine-readable

Exit 0 if the tool would be usable by a skill, 1 if not. Notes do not fail it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_SELFTEST_CHECKS = 3


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


def run(cmd: list[str], cwd: str) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=90)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timed out after 90s"
    except OSError as exc:
        return 1, "", str(exc)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--name", default=None)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    meta = track_meta(args.root)
    name = args.name or meta.get("first_tool")
    if not name:
        sys.exit("no tool name known — pass --name, or run /lab:start first")

    rel = os.path.join("tools", f"{name}.py")
    path = os.path.join(args.root, rel)
    problems: list[str] = []
    notes: list[str] = []

    if not os.path.exists(path):
        problems.append(f"no tool at {rel}")
        report(name, rel, problems, notes, args.as_json)
        return 1

    text = open(path, encoding="utf-8").read()

    leftover = [l.strip() for l in text.splitlines() if "TODO" in l]
    if leftover:
        problems.append(f"{len(leftover)} TODO left in the file, starting with "
                        f"{leftover[0][:70]!r}")
    if "NotImplementedError" in text:
        problems.append("the file still raises NotImplementedError — the scaffold's "
                        "placeholder is still in place")

    # 1. it must prove its own behaviour
    code, out, err = run([sys.executable, rel, "--selftest"], args.root)
    if code != 0:
        problems.append(f"--selftest failed (exit {code}): "
                        f"{(err or out).strip().splitlines()[-1][:120] if (err or out).strip() else 'no output'}")
    else:
        counted = re.search(r"(\d+)\s*/\s*(\d+)\s+checks passed", out)
        if not counted:
            notes.append("--selftest ran but did not report how many checks passed")
        else:
            total = int(counted.group(2))
            if total == 0:
                problems.append("--selftest contains no checks. A tool that asserts nothing "
                                "about itself is a script you hope works")
            elif total < MIN_SELFTEST_CHECKS:
                problems.append(f"--selftest has only {total} check(s); write at least "
                                f"{MIN_SELFTEST_CHECKS}, one of which proves the same input "
                                f"gives the same output")
        if "same input" not in text and "== collect" not in text:
            notes.append("no determinism check spotted — assert that calling it twice with "
                         "the same input gives the same result")

    # 2. it must produce structured output on the agreed interface
    command = meta.get("tool_command") or f"python3 {rel}"
    argv = shlex.split(command)
    if argv and argv[0] in ("python3", "python"):
        argv = [sys.executable] + argv[1:]
    code, out, err = run(argv, args.root)
    if code != 0:
        problems.append(f"`{command}` failed (exit {code}): "
                        f"{(err or '').strip().splitlines()[-1][:120] if err.strip() else 'no stderr'}")
    else:
        try:
            payload = json.loads(out)
        except ValueError:
            problems.append("stdout is not valid JSON. A tool's output is read by a program, "
                            "so print JSON and nothing else — send anything human to stderr")
            payload = None
        if isinstance(payload, dict):
            missing = [k for k in (meta.get("tool_contract") or []) if k not in payload]
            if missing:
                problems.append(f"output is missing the agreed key(s): {', '.join(missing)}. "
                                f"Your skill is going to rely on them")
            if payload and not missing:
                empty = [k for k in (meta.get("tool_contract") or [])
                         if payload.get(k) in (None, [], {}, "")]
                if empty:
                    notes.append(f"present but empty: {', '.join(empty)} — check that is "
                                 f"really the right answer for this input")
        elif payload is not None:
            problems.append("output is JSON but not an object — return a dict of named "
                            "facts, not a bare list")

    report(name, rel, problems, notes, args.as_json)
    return 1 if problems else 0


def report(name: str, rel: str, problems: list[str], notes: list[str], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"tool": name, "path": rel, "ok": not problems,
                          "problems": problems, "notes": notes}, indent=2))
        return
    print(f"TOOL CHECK — {name}")
    print("=" * (13 + len(name)))
    if problems:
        print("\nNOT READY:")
        for item in problems:
            print(f"  x {item}")
    else:
        print("\nReady — deterministic, structured, and usable by a skill.")
    if notes:
        print("\nWorth improving (not blocking):")
        for item in notes:
            print(f"  ! {item}")


if __name__ == "__main__":
    sys.exit(main())
