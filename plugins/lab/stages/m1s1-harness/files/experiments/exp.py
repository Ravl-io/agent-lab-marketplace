#!/usr/bin/env python3
"""Run one lab experiment.

Each experiment is the same thing — Claude Code, one prompt — with one difference:
which tools the model is given. That is the `--tools` flag, and it is the whole lesson,
so this script prints the command before it runs it.

    python3 experiments/exp.py 1     no tools at all
    python3 experiments/exp.py 2     one tool: Read
    python3 experiments/exp.py 3     two tools: Read and Write

You do not have to use this script. Copy the command it prints and run it yourself, or
change the prompt and see what happens. That is the point of the exercise.
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# The model is told the truth about its situation in experiment 1. Without this it keeps
# trying to call tools that do not exist, and the output fills up with failed attempts.
NO_TOOLS_SYSTEM = (
    "You have no tools in this session. You cannot read files, run commands, or search. "
    "Answer only from your own knowledge, and when you cannot know something, say so "
    "plainly in one sentence."
)

EXPERIMENTS = {
    "1": {"tools": "", "prompt": "exp1.prompt", "system": NO_TOOLS_SYSTEM,
          "title": "no tools at all"},
    "2": {"tools": "Read", "prompt": "exp2.prompt", "system": None,
          "title": "one tool: Read"},
    "3": {"tools": "Read,Write", "prompt": "exp3.prompt", "system": None,
          "title": "two tools: Read and Write"},
    # 4 and 5 share one prompt on purpose: the only difference is whether a skill exists.
    "4": {"tools": "Read,Write,Bash,Grep,Glob", "prompt": "task.prompt", "system": None,
          "title": "every core tool, and no procedure"},
    "5": {"tools": "Read,Write,Bash,Grep,Glob,Skill", "prompt": "task.prompt", "system": None,
          "title": "the same prompt, with a skill available"},
    # 6 asks for something reasonable-sounding that would destroy your evidence.
    "6": {"tools": "Read,Write,Bash,Grep,Glob,Skill", "prompt": "write-attempt.prompt",
          "system": None, "title": "a request that should be refused"},
    # 7 is the same task again, but the capability arrives from your installed plugin
    # instead of from loose files in this folder.
    "7": {"tools": "Read,Write,Bash,Grep,Glob,Skill", "prompt": "task.prompt",
          "system": None, "title": "the task, from your plugin", "use_plugin": True},
}


def find_claude() -> str:
    """`claude` from PATH, else the copy the lab linked into ~/.local/bin, else the binary
    the VS Code extension ships with. A terminal opened before /lab:start put ~/.local/bin
    on PATH still works this way. Same order as the lab's scripts/host_setup.py."""
    found = shutil.which("claude")
    if found:
        return found
    home = os.path.expanduser("~")
    exe = "claude.exe" if sys.platform == "win32" else "claude"
    shim = os.path.join(home, ".local", "bin",
                        "claude.cmd" if sys.platform == "win32" else "claude")
    if os.path.exists(shim):
        return shim

    def version(path: str) -> tuple[int, ...]:
        tag = os.path.basename(path).split("anthropic.claude-code-", 1)[-1].split("-", 1)[0]
        return tuple(int(p) for p in tag.split(".") if p.isdigit())

    bundled = []
    for rel in (".vscode", ".vscode-insiders", ".cursor", ".windsurf"):
        for ext in glob.glob(os.path.join(home, rel, "extensions", "anthropic.claude-code-*")):
            binary = os.path.join(ext, "resources", "native-binary", exe)
            if os.path.isfile(binary):
                bundled.append((version(ext), binary))
    return max(bundled)[1] if bundled else "claude"


def find_plugin(root: str) -> str | None:
    """Locate the participant's plugin by its manifest, so this script needs no config."""
    for entry in sorted(os.listdir(root)):
        candidate = os.path.join(root, entry)
        if os.path.isdir(candidate) and os.path.exists(
                os.path.join(candidate, ".claude-plugin", "plugin.json")):
            return entry
    return None


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    if which not in EXPERIMENTS:
        print("usage: python3 experiments/exp.py {1|2|3}", file=sys.stderr)
        return 2
    exp = EXPERIMENTS[which]

    prompt_file = os.path.join(HERE, exp["prompt"])
    if not os.path.exists(prompt_file):
        print(f"missing prompt file: {prompt_file}\n"
              f"Experiment {which} may belong to a later step of the module.",
              file=sys.stderr)
        return 2
    with open(prompt_file) as fh:
        prompt = fh.read().strip()

    cmd = [find_claude(), "--tools", exp["tools"], "--strict-mcp-config"]
    plugin = None
    if exp.get("use_plugin"):
        plugin = find_plugin(ROOT)
        if not plugin:
            print("No plugin found here. Experiment 7 needs a directory containing\n"
                  ".claude-plugin/plugin.json — that is what Step 6 builds.",
                  file=sys.stderr)
            return 2
        cmd += ["--plugin-dir", f"./{plugin}"]
    if exp["system"]:
        cmd += ["--append-system-prompt", exp["system"]]
    cmd += ["-p", prompt]

    shown = f'claude --tools "{exp["tools"]}" --strict-mcp-config'
    if plugin:
        shown += f' --plugin-dir ./{plugin}'
    if exp["system"]:
        shown += ' --append-system-prompt "...you have no tools..."'
    shown += f' -p "$(cat experiments/{exp["prompt"]})"'

    print("=" * 74)
    print(f" EXPERIMENT {which} — {exp['title']}")
    print("=" * 74)
    print(f"\n$ {shown}\n")
    print("-" * 74, flush=True)      # flush, or this lands after the child's output

    env = dict(os.environ, LAB_TRACE="1", LAB_TOOLS=exp["tools"])
    try:
        result = subprocess.run(cmd, cwd=ROOT, env=env, stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        print("The `claude` command is not on your PATH, and no Claude Code editor\n"
              "extension was found to borrow it from.\n"
              "Install it with: npm install -g @anthropic-ai/claude-code\n"
              "Or run the command above yourself from a terminal that has it.",
              file=sys.stderr)
        return 1

    print("-" * 74)
    print("\nNow read the trace:  .claude/lab-trace.log")
    print("Count the calls to the model at the bottom of it.\n")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
