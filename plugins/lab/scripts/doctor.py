#!/usr/bin/env python3
"""Agent Lab environment doctor.

Single source of truth for what the training needs. Three modes:

    doctor.py --checklist      what you need, and how to install it (no checks run)
    doctor.py                  run the checks, human-readable report
    doctor.py --json           run the checks, machine-readable
    doctor.py --quick          fast subset, for the start-of-session resume check

Exit code 0 if every REQUIRED check passes, 1 otherwise. Stdlib only, on purpose:
this must run before the participant has installed anything.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from dataclasses import dataclass, field, asdict

MIN_PYTHON = (3, 10)
MIN_GIT = (2, 30)
MIN_SQLITE = (3, 35)
MIN_NODE = (18, 0)
MIN_DISK_GB = 2.0

PASS, FAIL, WARN, INFO = "pass", "fail", "warn", "info"


@dataclass
class Requirement:
    """One thing the training needs. `check` is filled in when we actually run."""

    id: str
    label: str
    why: str
    required: bool
    install: dict = field(default_factory=dict)   # os -> hint
    quick: bool = True                            # included in --quick?


REQUIREMENTS = [
    Requirement(
        "python", "Python 3.10 or newer",
        "Module 2 and 3 build the retrieval pipeline and the knowledge graph in Python.",
        required=True,
        install={
            "macos": "brew install python@3.12   (or python.org installer)",
            "windows": "winget install Python.Python.3.12   (or python.org installer)",
            "linux": "sudo apt install python3 python3-venv python3-pip",
        },
    ),
    Requirement(
        "pip", "pip (Python package installer)",
        "Installs chromadb and the embedding runtime at the start of Module 2.",
        required=True,
        install={
            "macos": "python3 -m ensurepip --upgrade",
            "windows": "python -m ensurepip --upgrade",
            "linux": "sudo apt install python3-pip",
        },
    ),
    Requirement(
        "venv", "Python venv module",
        "Keeps the lab's packages isolated from your system Python.",
        required=True,
        install={
            "macos": "ships with python3",
            "windows": "ships with python3",
            "linux": "sudo apt install python3-venv",
        },
    ),
    Requirement(
        "sqlite", "SQLite 3.35 or newer (via Python)",
        "Module 3 stores the knowledge graph in SQLite. 3.35+ is needed for RETURNING/CTE support.",
        required=True,
        install={
            "macos": "ships with python3",
            "windows": "ships with python3",
            "linux": "sudo apt install libsqlite3-0",
        },
    ),
    Requirement(
        "git", "Git 2.30 or newer",
        "Every checkpoint is a commit. /lab:catchup and reset depend on git.",
        required=True,
        install={
            "macos": "xcode-select --install   (or brew install git)",
            "windows": "winget install Git.Git",
            "linux": "sudo apt install git",
        },
    ),
    Requirement(
        "writable", "Write access in the lab folder",
        "Your plugin, your notes and your progress are all written here.",
        required=True,
        install={"all": "open VS Code in a folder inside your home directory"},
    ),
    Requirement(
        "disk", f"At least {MIN_DISK_GB:g} GB free disk",
        "The embedding model (~90 MB), the vector index and the graph all live on disk.",
        required=True,
        quick=False,
        install={"all": "free up space, or pick a different drive"},
    ),
    Requirement(
        "network", "Network access to PyPI",
        "Module 2 installs chromadb and downloads the local embedding model once.",
        required=True,
        quick=False,
        install={"all": "check VPN / proxy / firewall, then re-run /lab:doctor"},
    ),
    # ---- recommended, never blocking -------------------------------------
    Requirement(
        "claude_cli", "claude CLI on PATH",
        "Handy for installing the plugin and inspecting it outside VS Code. Not required — "
        "the VS Code extension works without it.",
        required=False,
        install={"all": "npm install -g @anthropic-ai/claude-code"},
    ),
    Requirement(
        "vscode_cli", "code CLI on PATH",
        "Lets the tutor open files in your editor for you.",
        required=False,
        install={"all": "VS Code > Command Palette > 'Shell Command: Install code command in PATH'"},
    ),
    Requirement(
        "node", "Node.js 18 or newer",
        "Only needed if you choose the JavaScript variant of the Module 1 tool exercise.",
        required=False,
        install={
            "macos": "brew install node",
            "windows": "winget install OpenJS.NodeJS.LTS",
            "linux": "sudo apt install nodejs npm",
        },
    ),
    Requirement(
        "sqlite_cli", "sqlite3 command line tool",
        "Handy for poking at the lab database by hand. Not required — Python's sqlite3 "
        "module does everything the lab needs.",
        required=False,
        install={
            "macos": "ships with macOS",
            "windows": "winget install SQLite.SQLite   (or just use Python)",
            "linux": "sudo apt install sqlite3",
        },
    ),
    Requirement(
        "chromadb", "chromadb installed",
        "Installed together in Module 2 — not expected yet.",
        required=False,
        quick=False,
        install={"all": "we install it together at the start of Module 2"},
    ),
]

BY_ID = {r.id: r for r in REQUIREMENTS}


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def _run(cmd: list[str], timeout: int = 8) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.SubprocessError):
        return 127, ""


def _version_tuple(text: str) -> tuple[int, ...]:
    """Pull the first dotted number out of arbitrary version output."""
    num, parts = "", []
    for ch in text:
        if ch.isdigit() or (ch == "." and num):
            num += ch
        elif num:
            break
    for piece in num.split("."):
        if piece.isdigit():
            parts.append(int(piece))
    return tuple(parts) or (0,)


PYTHON_CANDIDATES = ["python3.14", "python3.13", "python3.12", "python3.11", "python3.10",
                     "python3", "python"]


def find_python() -> tuple[str | None, tuple[int, ...], list[tuple[str, tuple[int, ...]]]]:
    """Find the newest interpreter that meets MIN_PYTHON.

    macOS ships /usr/bin/python3 at 3.9, so `python3` being too old does NOT mean the
    participant has no usable Python — it usually means it is installed under another
    name. Returns (best_path, best_version, all_found).
    """
    seen: dict[str, tuple[int, ...]] = {}
    for name in [sys.executable] + PYTHON_CANDIDATES:
        path = name if os.path.isabs(name) else shutil.which(name)
        if not path:
            continue
        real = os.path.realpath(path)
        if real in seen:
            continue
        code, out = _run([path, "-c", "import sys;print('.'.join(map(str,sys.version_info[:3])))"])
        if code != 0:
            continue
        seen[real] = _version_tuple(out)
    found = sorted(seen.items(), key=lambda kv: kv[1], reverse=True)
    for path, ver in found:
        if ver[:2] >= MIN_PYTHON:
            return path, ver, found
    return None, (), found


# Resolved once, reused by check_python and by the JSON payload so that every later
# lab script can be told exactly which interpreter to use.
_PY_BEST, _PY_VER, _PY_ALL = None, (), []


def check_python() -> tuple[str, str]:
    global _PY_BEST, _PY_VER, _PY_ALL
    _PY_BEST, _PY_VER, _PY_ALL = find_python()
    need = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"

    if not _PY_BEST:
        if _PY_ALL:
            have = ", ".join(f"{p} ({'.'.join(map(str, v))})" for p, v in _PY_ALL)
            return FAIL, f"no interpreter >= {need}. Found: {have}"
        return FAIL, f"no Python found on PATH — need {need}+"

    version = ".".join(map(str, _PY_VER))
    default = shutil.which("python3") or shutil.which("python")
    detail = f"{version} at {_PY_BEST}"
    if default and os.path.realpath(default) != os.path.realpath(_PY_BEST):
        code, out = _run([default, "-c",
                          "import sys;print('.'.join(map(str,sys.version_info[:3])))"])
        if code == 0 and _version_tuple(out)[:2] < MIN_PYTHON:
            detail += f" — note: `python3` on your PATH is {out.strip()}, too old. " \
                      f"The lab will use {_PY_BEST}."
    return PASS, detail


def _py() -> str:
    """The interpreter the lab will actually use. Set by check_python, which runs first."""
    return _PY_BEST or sys.executable


def check_pip() -> tuple[str, str]:
    code, out = _run([_py(), "-m", "pip", "--version"])
    if code == 0:
        return PASS, out.splitlines()[0] if out else "available"
    return FAIL, f"{_py()} -m pip is not available"


def check_venv() -> tuple[str, str]:
    code, _ = _run([_py(), "-c", "import venv"])
    if code == 0:
        return PASS, "available"
    return FAIL, f"the venv module is missing from {_py()}"


def check_sqlite() -> tuple[str, str]:
    code, out = _run([_py(), "-c", "import sqlite3;print(sqlite3.sqlite_version)"])
    if code != 0:
        return FAIL, f"sqlite3 is not available in {_py()}"
    version = out.splitlines()[-1].strip()
    if _version_tuple(version) >= MIN_SQLITE:
        return PASS, version
    return FAIL, f"{version} — need {'.'.join(map(str, MIN_SQLITE))}+"


def check_git() -> tuple[str, str]:
    if not shutil.which("git"):
        return FAIL, "git is not on PATH"
    code, out = _run(["git", "--version"])
    if code != 0:
        return FAIL, "git is on PATH but failed to run"
    got = _version_tuple(out)
    if got >= MIN_GIT:
        return PASS, out
    return FAIL, f"{out} — need {'.'.join(map(str, MIN_GIT))}+"


def check_writable(root: str) -> tuple[str, str]:
    probe = os.path.join(root, ".agent-lab-write-probe")
    try:
        os.makedirs(root, exist_ok=True)
        with open(probe, "w") as fh:
            fh.write("ok")
        os.remove(probe)
        return PASS, f"{root} is writable"
    except OSError as exc:
        return FAIL, f"cannot write in {root}: {exc}"


def check_disk(root: str) -> tuple[str, str]:
    try:
        free_gb = shutil.disk_usage(root).free / (1024 ** 3)
    except OSError as exc:
        return WARN, f"could not read free space: {exc}"
    if free_gb >= MIN_DISK_GB:
        return PASS, f"{free_gb:.1f} GB free"
    return FAIL, f"only {free_gb:.1f} GB free — need {MIN_DISK_GB:g} GB"


def check_network() -> tuple[str, str]:
    req = urllib.request.Request("https://pypi.org/simple/", method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            if resp.status < 400:
                return PASS, "pypi.org reachable"
            return FAIL, f"pypi.org returned HTTP {resp.status}"
    except Exception as exc:  # noqa: BLE001 - any network error is the same answer
        return FAIL, f"cannot reach pypi.org ({type(exc).__name__})"


def check_claude_cli() -> tuple[str, str]:
    if not shutil.which("claude"):
        return WARN, "not on PATH — fine, the VS Code extension does not need it"
    code, out = _run(["claude", "--version"])
    return (PASS, out) if code == 0 else (WARN, "on PATH but failed to run")


def check_vscode_cli() -> tuple[str, str]:
    if not shutil.which("code"):
        return WARN, "not on PATH — the tutor will print paths instead of opening files"
    return PASS, "available"


def check_node() -> tuple[str, str]:
    if not shutil.which("node"):
        return WARN, "not installed — only needed for the optional JS variant"
    code, out = _run(["node", "--version"])
    if code != 0:
        return WARN, "on PATH but failed to run"
    got = _version_tuple(out)
    return (PASS, out) if got >= MIN_NODE else (WARN, f"{out} — 18+ recommended")


def check_sqlite_cli() -> tuple[str, str]:
    if not shutil.which("sqlite3"):
        return WARN, "not installed — fine, the lab uses Python's sqlite3 module"
    code, out = _run(["sqlite3", "--version"])
    return (PASS, out.split()[0] if out else "available") if code == 0 else (WARN, "failed to run")


def check_chromadb() -> tuple[str, str]:
    code, out = _run([_py(), "-c", "import chromadb;print(chromadb.__version__)"])
    if code == 0:
        return PASS, f"already installed ({out.splitlines()[-1]})"
    return INFO, "not installed yet — we do this together in Module 2"


def run_checks(root: str, quick: bool = False) -> list[dict]:
    runners = {
        "python": check_python,
        "pip": check_pip,
        "venv": check_venv,
        "sqlite": check_sqlite,
        "git": check_git,
        "writable": lambda: check_writable(root),
        "disk": lambda: check_disk(root),
        "network": check_network,
        "claude_cli": check_claude_cli,
        "vscode_cli": check_vscode_cli,
        "node": check_node,
        "sqlite_cli": check_sqlite_cli,
        "chromadb": check_chromadb,
    }
    results = []
    for req in REQUIREMENTS:
        if quick and not req.quick:
            continue
        status, detail = runners[req.id]()
        row = asdict(req)
        row.update(status=status, detail=detail)
        results.append(row)
    return results


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

def _os_key() -> str:
    return {"darwin": "macos", "win32": "windows"}.get(sys.platform, "linux")


def _install_hint(req: dict) -> str:
    install = req.get("install") or {}
    return install.get(_os_key()) or install.get("all") or ""


def render_checklist() -> str:
    lines = ["AGENT LAB — SETUP CHECKLIST", ""]
    lines.append(f"Detected platform: {_os_key()}")
    lines.append("")
    for group, title in ((True, "REQUIRED — the lab cannot run without these"),
                         (False, "RECOMMENDED — nice to have, never blocking")):
        lines.append(title)
        lines.append("-" * len(title))
        for req in REQUIREMENTS:
            if req.required is not group:
                continue
            lines.append(f"[ ] {req.label}")
            lines.append(f"      why: {req.why}")
            hint = _install_hint(asdict(req))
            if hint:
                lines.append(f"      get: {hint}")
        lines.append("")
    lines.append("Then run /lab:doctor to verify all of it at once.")
    return "\n".join(lines)


SYMBOL = {PASS: "PASS", FAIL: "FAIL", WARN: "WARN", INFO: "INFO"}


def render_report(results: list[dict], quick: bool) -> str:
    required = [r for r in results if r["required"]]
    optional = [r for r in results if not r["required"]]
    failed = [r for r in required if r["status"] == FAIL]

    title = "AGENT LAB — ENVIRONMENT CHECK" + (" (quick)" if quick else "")
    lines = [title, "=" * len(title), ""]
    lines.append("REQUIRED")
    for r in required:
        lines.append(f"  [{SYMBOL[r['status']]}] {r['label']}: {r['detail']}")
    if optional:
        lines.append("")
        lines.append("RECOMMENDED")
        for r in optional:
            lines.append(f"  [{SYMBOL[r['status']]}] {r['label']}: {r['detail']}")
    lines.append("")

    if failed:
        lines.append(f"NOT READY — {len(failed)} required check(s) failed:")
        for r in failed:
            lines.append(f"  * {r['label']}")
            hint = _install_hint(r)
            if hint:
                lines.append(f"      fix: {hint}")
        lines.append("")
        lines.append("Fix those, then run /lab:doctor again.")
    else:
        lines.append("READY — every required check passed.")
        if _PY_BEST and os.path.realpath(_PY_BEST) != os.path.realpath(
                shutil.which("python3") or sys.executable):
            lines.append(f"Use this interpreter for lab scripts: {_PY_BEST}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Agent Lab environment doctor")
    ap.add_argument("--checklist", action="store_true", help="print requirements, run nothing")
    ap.add_argument("--json", action="store_true", dest="as_json", help="machine-readable output")
    ap.add_argument("--quick", action="store_true", help="fast subset for session resume")
    ap.add_argument("--root", default=os.getcwd(), help="lab root directory (default: cwd)")
    args = ap.parse_args()

    if args.checklist:
        if args.as_json:
            print(json.dumps({"platform": _os_key(),
                              "requirements": [asdict(r) for r in REQUIREMENTS]}, indent=2))
        else:
            print(render_checklist())
        return 0

    results = run_checks(args.root, quick=args.quick)
    failed = [r for r in results if r["required"] and r["status"] == FAIL]

    if args.as_json:
        print(json.dumps({
            "platform": _os_key(),
            "root": args.root,
            "quick": args.quick,
            "ready": not failed,
            "python_bin": _PY_BEST or sys.executable,
            "python_version": ".".join(map(str, _PY_VER)) if _PY_VER else None,
            "failed": [r["id"] for r in failed],
            "checks": results,
        }, indent=2))
    else:
        print(render_report(results, args.quick))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
