#!/usr/bin/env python3
"""The lab tracer: makes the agent loop visible.

Wired to four hook events. Claude Code sends each one a JSON object on stdin.

  UserPromptSubmit  what you sent to the model
  PreToolUse        the model asking the harness to do something
  PostToolUse       what the harness sent back to the model
  Stop              the model's final answer

This hook only observes. It never blocks anything — which tools exist is decided by the
`--tools` flag on the experiment command, not here. An earlier version of this lab enforced
an allowlist in the hook and it blocked the tutor's own tools along with everything else;
capability belongs on the command line, where it applies to one invocation instead of to
the whole session.

Hook stdout is not shown in the session (it goes to the debug log), so the trace is appended
to .claude/lab-trace.log and the participant reads it.

Tracing is on only when LAB_TRACE=1 is set, so the tutor's own housekeeping turns do not
fill the trace with noise. The experiment commands set it.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime

WIDTH = 74


def enabled() -> bool:
    return os.environ.get("LAB_TRACE") == "1"


def project_dir() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def lab_dir() -> str:
    return os.path.join(project_dir(), ".claude")


def log_path() -> str:
    return os.path.join(lab_dir(), "lab-trace.log")


def raw_path() -> str:
    return os.path.join(lab_dir(), "lab-raw.jsonl")


def turn_path() -> str:
    return os.path.join(lab_dir(), ".lab-turn.json")


def tools_label() -> str:
    """What the experiment was given, straight from the command that launched it."""
    value = os.environ.get("LAB_TOOLS")
    if value is None:
        return "unknown"
    value = value.strip()
    return "none — no tools at all" if value in ("", '""') else value


def load_turn() -> dict:
    try:
        with open(turn_path()) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"turn": 0, "calls": 0, "tools": 0}


def save_turn(turn: dict) -> None:
    os.makedirs(lab_dir(), exist_ok=True)
    tmp = turn_path() + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(turn, fh)
    os.replace(tmp, turn_path())


def write(lines: list[str]) -> None:
    os.makedirs(lab_dir(), exist_ok=True)
    with open(log_path(), "a") as fh:
        fh.write("\n".join(lines) + "\n")


def dump_raw(ev: dict) -> None:
    """Every payload the harness sends this hook, verbatim — the real contract."""
    try:
        os.makedirs(lab_dir(), exist_ok=True)
        with open(raw_path(), "a") as fh:
            fh.write(json.dumps(ev, default=str) + "\n")
    except OSError:
        pass


def clip(text: str, limit: int = 400) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + f" … [{len(text)} chars total]"


def block(label: str, body: list[str]) -> list[str]:
    return [f"  {label}"] + [f"      {line}" for line in body]


def prompt_text(ev: dict) -> str:
    for key in ("prompt", "user_prompt", "user_prompt_raw"):
        value = (ev.get(key) or "").strip()
        if value:
            return value
    return "(empty)"


def tool_result_text(ev: dict) -> tuple[str, bool]:
    """Pull the readable result out of a PostToolUse payload.

    The shape depends on the tool: Read returns {"type":"text","file":{"content":...}},
    Bash returns stdout, others a plain string. Field names have also changed between
    versions, so look for whichever is present rather than trusting one name.
    """
    result = None
    for key in ("tool_response", "tool_output", "tool_result", "output", "result"):
        if ev.get(key) not in (None, "", [], {}):
            result = ev[key]
            break
    is_error = bool(ev.get("tool_output_is_error"))
    if result is None:
        return "", is_error
    if isinstance(result, str):
        return result, is_error
    if isinstance(result, dict):
        is_error = is_error or bool(result.get("is_error"))
        nested = result.get("file")
        if isinstance(nested, dict) and isinstance(nested.get("content"), str):
            return nested["content"], is_error
        for key in ("content", "stdout", "output", "text", "message"):
            value = result.get(key)
            if isinstance(value, str) and value:
                return value, is_error
    return json.dumps(result, default=str), is_error


def on_prompt(ev: dict) -> None:
    turn = load_turn()
    turn["turn"] += 1
    turn["calls"] = 1              # the prompt itself is the first call to the model
    turn["tools"] = 0
    save_turn(turn)
    write([
        "",
        "=" * WIDTH,
        f" EXPERIMENT {turn['turn']}   {datetime.now().strftime('%H:%M:%S')}",
        f" tools given to the model: {tools_label()}",
        "=" * WIDTH,
        *block("--> SENT TO THE MODEL   (your prompt)", [f'"{clip(prompt_text(ev))}"']),
    ])


def on_pre_tool(ev: dict) -> None:
    turn = load_turn()
    turn["tools"] += 1
    turn["calls"] += 1             # every tool result means another call to the model
    save_turn(turn)
    args = ev.get("tool_input") or {}
    shown = {k: clip(v, 160) for k, v in list(args.items())[:4]}
    write(block("<-- BACK FROM THE MODEL   (it wants a tool; it cannot run one itself)",
                [f"{ev.get('tool_name', '?')}({', '.join(f'{k}={v!r}' for k, v in shown.items())})"]))
    # Deliberately does not claim the tool ran. Another hook may refuse it, and this
    # tracer cannot see other hooks' decisions — the absence of a RESULT line below is
    # what tells you a request was blocked.
    write(block("--> HANDED TO THE HARNESS", ["(the model is paused, waiting)"]))


def on_post_tool(ev: dict) -> None:
    out, is_error = tool_result_text(ev)
    status = "ERROR" if is_error else "ok"
    write(block(f"<-- RESULT SENT BACK TO THE MODEL   ({status}, {len(out)} chars)",
                [f'"{clip(out)}"']))


def on_stop(ev: dict) -> None:
    turn = load_turn()
    write([
        *block("<-- FINAL ANSWER FROM THE MODEL",
               [f'"{clip(ev.get("last_assistant_message", ""))}"']),
        "-" * WIDTH,
        f" This experiment: {turn.get('calls', 1)} call(s) to the model, "
        f"{turn.get('tools', 0)} tool request(s).",
        "=" * WIDTH,
    ])


def main() -> int:
    if not enabled():
        return 0                   # not an experiment turn: stay silent
    try:
        ev = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    dump_raw(ev)
    try:
        {"UserPromptSubmit": on_prompt, "PreToolUse": on_pre_tool,
         "PostToolUse": on_post_tool, "Stop": on_stop}.get(
            ev.get("hook_event_name"), lambda _e: None)(ev)
    except Exception:              # noqa: BLE001 - a tracer must never break the lab
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
