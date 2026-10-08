#!/usr/bin/env python3
"""Prepare this machine's Claude Code for the lab: two one-time fixes.

    host_setup.py trust [--root DIR]    trust the lab folder, so settings.json permissions apply
    host_setup.py cli                   make `claude` runnable from a terminal
    host_setup.py all [--root DIR]      both, as /lab:start runs it
    add --json for machine-readable output, --check to report without changing anything

Why these exist. Claude Code ignores a project's `permissions` block until the folder is
trusted, and the trust dialog only appears in an interactive session — which a participant
working in the VS Code extension may never open. And the Module 1 experiments start a
separate `claude -p` session, but the VS Code extension ships its own `claude` binary
without putting it on PATH. Both used to be thirty seconds to fix by hand and ten minutes
to diagnose mid-exercise.

Every change is idempotent, and nothing is overwritten that this script did not create:
~/.claude.json is backed up before it is touched and rewritten atomically, an existing
`claude` command is never replaced, and the shell profile gets one marked block, once.
Stdlib only: this runs before the participant has installed anything.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile

PASS, FAIL, WARN, CHANGED = "pass", "fail", "warn", "changed"
MARKER = "# Added by Agent Lab: the claude command"
IS_WINDOWS = sys.platform == "win32"

# Editors that install the Claude Code extension, newest-binary-wins across all of them.
EXTENSION_DIRS = [".vscode/extensions", ".vscode-insiders/extensions",
                  ".cursor/extensions", ".windsurf/extensions"]


def _home() -> str:
    return os.path.expanduser("~")


# --------------------------------------------------------------------------
# trust
# --------------------------------------------------------------------------

def config_path() -> str:
    """Where Claude Code keeps per-project state, including the trust flag."""
    base = os.environ.get("CLAUDE_CONFIG_DIR") or _home()
    return os.path.join(base, ".claude.json")


def project_key(root: str) -> str:
    key = os.path.abspath(root)
    return key.replace("\\", "/") if IS_WINDOWS else key


def is_trusted(root: str) -> bool:
    try:
        with open(config_path(), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return False
    entry = (data.get("projects") or {}).get(project_key(root)) or {}
    return entry.get("hasTrustDialogAccepted") is True


def trust(root: str, check_only: bool = False) -> tuple[str, str]:
    key = project_key(root)
    if os.path.realpath(key) in (os.path.realpath(_home()), os.path.realpath(os.sep)):
        return FAIL, f"refusing to trust {key}: the lab needs its own folder"
    if is_trusted(root):
        return PASS, f"{key} is already trusted"
    if check_only:
        return WARN, f"{key} is not trusted yet"

    path = config_path()
    data: dict = {}
    mode = 0o600
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except ValueError as exc:
            # Never overwrite a file we cannot parse: it holds the participant's login state.
            return FAIL, f"{path} is not valid JSON ({exc}); left untouched"
        mode = stat.S_IMODE(os.stat(path).st_mode)
        shutil.copy2(path, path + ".agent-lab-backup")

    data.setdefault("projects", {}).setdefault(key, {})["hasTrustDialogAccepted"] = True
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".claude.json.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except OSError as exc:
        if os.path.exists(tmp):
            os.remove(tmp)
        return FAIL, f"could not write {path}: {exc}"
    return CHANGED, f"trusted {key} in {path}"


# --------------------------------------------------------------------------
# the claude command
# --------------------------------------------------------------------------

def _version_key(path: str) -> tuple[int, ...]:
    """anthropic.claude-code-2.1.293-darwin-arm64 -> (2, 1, 293)."""
    name = os.path.basename(path).split("anthropic.claude-code-", 1)[-1]
    parts = []
    for piece in name.split("-", 1)[0].split("."):
        if not piece.isdigit():
            break
        parts.append(int(piece))
    return tuple(parts)


def find_bundled() -> str | None:
    """The newest `claude` binary shipped inside an installed Claude Code editor extension."""
    exe = "claude.exe" if IS_WINDOWS else "claude"
    found = []
    for rel in EXTENSION_DIRS:
        pattern = os.path.join(_home(), rel, "anthropic.claude-code-*")
        for ext in glob.glob(pattern):
            binary = os.path.join(ext, "resources", "native-binary", exe)
            if os.path.isfile(binary) and os.access(binary, os.X_OK):
                found.append((_version_key(ext), binary))
    return max(found)[1] if found else None


def find_claude() -> str | None:
    """`claude` as a terminal would find it, or the shim this script installs, or the
    extension's own binary. exp.py carries a copy of this order."""
    on_path = shutil.which("claude")
    if on_path:
        return on_path
    shim = shim_path()
    if os.path.exists(shim):
        return shim
    return find_bundled()


def bin_dir() -> str:
    return os.path.join(_home(), ".local", "bin")


def shim_path() -> str:
    return os.path.join(bin_dir(), "claude.cmd" if IS_WINDOWS else "claude")


def _on_path(directory: str) -> bool:
    want = os.path.normcase(os.path.realpath(directory))
    return any(os.path.normcase(os.path.realpath(p)) == want
               for p in os.environ.get("PATH", "").split(os.pathsep) if p)


def _install_shim(binary: str) -> tuple[bool, str]:
    """Link (or, on Windows, wrap) the bundled binary. Returns (changed, what happened).

    A symlink to one extension version goes stale when the extension updates and VS Code
    deletes the old folder — so a dangling link we made is replaced, and /lab:start runs
    this every session. A real file, or a link pointing somewhere we did not put it, is
    somebody else's `claude` and is left alone.
    """
    os.makedirs(bin_dir(), exist_ok=True)
    shim = shim_path()
    if IS_WINDOWS:
        content = f'@"{binary}" %*\r\n'
        if os.path.exists(shim) and open(shim, encoding="utf-8").read() == content:
            return False, f"{shim} runs {binary}"
        with open(shim, "w", encoding="utf-8") as fh:
            fh.write(content)
        return True, f"wrote {shim}"
    if os.path.islink(shim):
        target = os.readlink(shim)
        if target == binary:
            return False, f"{shim} -> {binary}"
        if os.path.exists(shim) and "anthropic.claude-code-" not in target:
            return False, f"left {shim} alone: it points at {target}"
        os.remove(shim)
    elif os.path.exists(shim):
        return False, f"left {shim} alone: it is not a link this lab created"
    os.symlink(binary, shim)
    return True, f"linked {shim} -> {binary}"


def _profile_file() -> str:
    shell = os.path.basename(os.environ.get("SHELL", ""))
    if shell == "zsh":
        return os.path.join(os.environ.get("ZDOTDIR") or _home(), ".zshrc")
    if shell == "bash":
        name = ".bash_profile" if sys.platform == "darwin" else ".bashrc"
        return os.path.join(_home(), name)
    if shell == "fish":
        return os.path.join(_home(), ".config", "fish", "config.fish")
    return os.path.join(_home(), ".profile")


def _add_to_path() -> tuple[bool, str]:
    """Put ~/.local/bin on PATH for new terminals. Open terminals keep their old PATH."""
    if IS_WINDOWS:
        script = ("$p=[Environment]::GetEnvironmentVariable('Path','User');"
                  f"$d='{bin_dir()}';"
                  "if(($p -split ';') -notcontains $d){"
                  "[Environment]::SetEnvironmentVariable('Path',($p.TrimEnd(';')+';'+$d).TrimStart(';'),'User')}")
        result = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                                capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"could not update the user PATH: {result.stderr.strip()[:160]}"
        return True, f"{bin_dir()} is on the user PATH"

    profile = _profile_file()
    existing = open(profile, encoding="utf-8").read() if os.path.exists(profile) else ""
    if MARKER in existing:
        return False, f"{profile} puts ~/.local/bin on PATH"
    if profile.endswith("config.fish"):
        line = "fish_add_path $HOME/.local/bin"
    else:
        line = 'export PATH="$HOME/.local/bin:$PATH"'
    os.makedirs(os.path.dirname(profile), exist_ok=True)
    with open(profile, "a", encoding="utf-8") as fh:
        fh.write(("" if existing.endswith("\n") or not existing else "\n")
                 + f"\n{MARKER}\n{line}\n")
    return True, f"added ~/.local/bin to PATH in {profile}"


def cli(check_only: bool = False) -> tuple[str, str]:
    on_path = shutil.which("claude")
    if on_path:
        return PASS, f"already on PATH at {on_path}"
    binary = find_bundled()
    if not binary:
        return FAIL, ("no `claude` on PATH and no Claude Code editor extension found — "
                      "install it with: npm install -g @anthropic-ai/claude-code")
    if check_only:
        return WARN, f"not on PATH; the VS Code extension bundles one at {binary}"
    steps = [_install_shim(binary)]
    if not _on_path(bin_dir()):
        steps.append(_add_to_path())
    detail = "; ".join(msg for _, msg in steps)
    if not _on_path(bin_dir()):
        detail += " — terminals opened from now on will have `claude`"
    return (CHANGED if any(changed for changed, _ in steps) else PASS), detail


# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=["trust", "cli", "all"])
    ap.add_argument("--root", default=os.getcwd(), help="the lab folder (default: here)")
    ap.add_argument("--check", action="store_true", help="report only, change nothing")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    results = {}
    if args.action in ("trust", "all"):
        results["trust"] = trust(args.root, args.check)
    if args.action in ("cli", "all"):
        results["cli"] = cli(args.check)

    ok = all(status != FAIL for status, _ in results.values())
    if args.json:
        print(json.dumps({"ok": ok, **{k: {"status": s, "detail": d}
                                       for k, (s, d) in results.items()}}, indent=2))
    else:
        for name, (status, detail) in results.items():
            print(f"[{status.upper()}] {name}: {detail}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
