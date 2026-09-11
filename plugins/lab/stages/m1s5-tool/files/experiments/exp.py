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

import os
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

    cmd = ["claude", "--tools", exp["tools"], "--strict-mcp-config"]
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
        print("The `claude` command is not on your PATH.\n"
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
