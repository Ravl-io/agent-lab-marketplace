#!/usr/bin/env python3
"""Create and verify the participant's Support Lab workspace.

The workspace IS the lab root — the folder they opened Claude Code in. Project configuration
(`CLAUDE.md`) is read from the project root, so the sandbox has to live there, not in a
subfolder.

    workspace.py setup [--force]     copy the sandbox in (refuses to clobber unrelated files)
    workspace.py verify              is the sandbox intact and does the database answer?
    workspace.py clean               remove generated work (findings, out/, the built plugin)

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAYLOAD = os.path.join(PLUGIN_ROOT, "workspace")

# Files that may already exist in a folder without it counting as "someone's other work".
HARMLESS = {".support-lab", ".claude", ".git", ".gitignore", ".DS_Store", ".vscode",
            "notes.md", "README.md"}

KEY_FILES = [
    "CLAUDE.md",
    "tickets/JIRA-4821.md",
    "tickets/JIRA-4907.md",
    "scripts/query.py",
    "scripts/check_findings.py",
    "data/support.db",
    "ops/deploys.log",
    "ops/config-audit.log",
    "logs/api-2026-09-16.log",
    "logs/api-2026-09-15.log",
    "logs/scheduler-2026-09-16.log",
    "docs/reports/export.md",
    "docs/vendor/openreport-3.2-release-notes.md",
    "templates/findings-template.md",
]


def payload_files() -> list[str]:
    out = []
    for dirpath, _dirs, names in os.walk(PAYLOAD):
        for name in names:
            if name == ".DS_Store":
                continue
            out.append(os.path.relpath(os.path.join(dirpath, name), PAYLOAD))
    return sorted(out)


def cmd_setup(args) -> int:
    root = os.path.abspath(args.root)
    home = os.path.expanduser("~")

    if root == home:
        sys.exit("refusing to set up the lab in your home folder — make an empty folder, "
                 "open Claude Code there, and say 'lab start' again")

    existing = {e for e in os.listdir(root)} if os.path.isdir(root) else set()
    already_lab = os.path.exists(os.path.join(root, "CLAUDE.md")) and \
        os.path.isdir(os.path.join(root, "tickets"))
    foreign = sorted(e for e in existing if e not in HARMLESS)

    if already_lab and not args.force:
        print(json.dumps({"root": root, "status": "already set up", "files_created": 0}, indent=2))
        return 0
    if foreign and not already_lab and not args.force:
        sys.exit("this folder already has other files in it (e.g. "
                 f"{', '.join(foreign[:3])}) — the lab needs its own empty folder")

    created = []
    for rel in payload_files():
        src = os.path.join(PAYLOAD, rel)
        dst = os.path.join(root, rel)
        os.makedirs(os.path.dirname(dst) or root, exist_ok=True)
        shutil.copy2(src, dst)
        created.append(rel)
    for rel in ("scripts/query.py", "scripts/check_findings.py", "scripts/reset.sh"):
        p = os.path.join(root, rel)
        if os.path.exists(p):
            os.chmod(p, 0o755)

    print(json.dumps({
        "root": root,
        "status": "set up",
        "files_created": len(created),
        "directories": sorted({rel.split(os.sep)[0] for rel in created if os.sep in rel}),
    }, indent=2))
    return 0


def cmd_verify(args) -> int:
    root = os.path.abspath(args.root)
    missing = [f for f in KEY_FILES if not os.path.exists(os.path.join(root, f))]
    db_ok, db_msg = False, "not checked"
    if "scripts/query.py" not in missing and "data/support.db" not in missing:
        try:
            p = subprocess.run(
                [sys.executable, os.path.join(root, "scripts", "query.py"),
                 "SELECT COUNT(*) AS n FROM tickets"],
                capture_output=True, text=True, timeout=30, cwd=root)
            db_ok = p.returncode == 0 and "140" in p.stdout
            db_msg = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr.strip()[:200]
        except (OSError, subprocess.SubprocessError) as exc:
            db_msg = str(exc)
    result = {
        "root": root,
        "intact": not missing and db_ok,
        "missing": missing,
        "database": db_msg,
        "findings_4821": os.path.exists(os.path.join(root, "tickets", "JIRA-4821", "findings.md")),
        "findings_4907": os.path.exists(os.path.join(root, "tickets", "JIRA-4907", "findings.md")),
        "built_plugin": os.path.isdir(os.path.join(root, "first-look-plugin")),
    }
    print(json.dumps(result, indent=2))
    return 0 if result["intact"] else 1


def cmd_clean(args) -> int:
    root = os.path.abspath(args.root)
    removed = []
    tickets = os.path.join(root, "tickets")
    if os.path.isdir(tickets):
        for entry in os.listdir(tickets):
            full = os.path.join(tickets, entry)
            if os.path.isdir(full) and entry.startswith("JIRA-"):
                shutil.rmtree(full)
                removed.append(f"tickets/{entry}/")
    for rel in ("out", "first-look-plugin"):
        full = os.path.join(root, rel)
        if os.path.isdir(full):
            shutil.rmtree(full)
            removed.append(rel + "/")
    for rel in ("notes.md",):
        full = os.path.join(root, rel)
        if os.path.exists(full):
            os.remove(full)
            removed.append(rel)
    print(json.dumps({"root": root, "removed": removed}, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Support Lab workspace")
    ap.add_argument("--root", default=os.getcwd(), help="lab root (default: cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("setup"); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_setup)
    p = sub.add_parser("verify"); p.set_defaults(fn=cmd_verify)
    p = sub.add_parser("clean"); p.set_defaults(fn=cmd_clean)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
