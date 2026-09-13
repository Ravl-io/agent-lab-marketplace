#!/usr/bin/env python3
"""Validate a participant's MCP retrieval server by speaking the protocol to it.

Not a source-code read: this launches their server the way a client does, over stdin and
stdout, and checks what comes back. That is the only test that means anything for a
protocol server — a file that looks right and never completes a handshake is worthless.

    check_retrieval_tool.py           validate the project's server
    check_retrieval_tool.py --json    machine-readable

Exit 0 if an agent could actually use it, 1 if not. Notes do not fail it.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

PROTOCOL = "2024-11-05"
SERVER = os.path.join("mcp", "retrieval_server.py")
WANTED = ("search_corpus", "search_corpus_filtered", "get_document")


def converse(root: str, messages: list[dict], timeout: int = 120) -> tuple[list[dict], str]:
    """Send newline-delimited JSON-RPC, collect the replies. One process, like a client."""
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = root
    venv = os.path.join(root, ".venv", "bin", "python3")
    interpreter = venv if os.path.exists(venv) else sys.executable
    payload = "".join(json.dumps(m) + "\n" for m in messages)
    try:
        proc = subprocess.run([interpreter, os.path.join(root, SERVER)],
                              input=payload, capture_output=True, text=True,
                              cwd=root, env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        return [], "the server did not exit when its input closed (timed out)"
    except OSError as exc:
        return [], str(exc)
    out = []
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            return out, (f"the server wrote something that is not JSON-RPC to stdout, "
                         f"which corrupts the stream: {line[:120]!r}. Debug output "
                         f"belongs on stderr.")
    return out, proc.stderr or ""


def by_id(replies: list[dict], mid: int) -> dict:
    for r in replies:
        if r.get("id") == mid:
            return r
    return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    problems: list[str] = []
    notes: list[str] = []
    found: list[str] = []

    if not os.path.exists(os.path.join(root, SERVER)):
        problems.append(f"{SERVER} does not exist yet")
        report(problems, notes, found, args.as_json)
        return 1

    config = os.path.join(root, ".mcp.json")
    if not os.path.exists(config):
        problems.append(".mcp.json is missing — the server exists but nothing launches it")
    else:
        try:
            servers = (json.load(open(config)).get("mcpServers") or {})
            if not servers:
                problems.append(".mcp.json declares no servers under 'mcpServers'")
            else:
                entry = next(iter(servers.values()))
                if SERVER.replace(os.sep, "/") not in json.dumps(entry):
                    notes.append(".mcp.json does not appear to point at "
                                 f"{SERVER} — check the args")
        except ValueError:
            problems.append(".mcp.json is not valid JSON, so the client will ignore it")

    replies, stderr = converse(root, [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": PROTOCOL, "capabilities": {},
                    "clientInfo": {"name": "lab-gate", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ])
    if stderr and not replies:
        problems.append(f"the server produced no replies. stderr: {stderr.strip()[:300]}")
        report(problems, notes, found, args.as_json)
        return 1

    init = by_id(replies, 1).get("result") or {}
    if not init:
        problems.append("no reply to initialize — a client would give up here")
    else:
        if not init.get("protocolVersion"):
            problems.append("initialize did not return a protocolVersion")
        if "tools" not in (init.get("capabilities") or {}):
            problems.append("initialize does not advertise a 'tools' capability, so a "
                            "client will never ask for your tools")
        if not (init.get("serverInfo") or {}).get("name"):
            notes.append("initialize returns no serverInfo.name; the client shows that name")

    listed = (by_id(replies, 2).get("result") or {}).get("tools")
    if listed is None:
        problems.append("no reply to tools/list")
    elif not listed:
        problems.append("tools/list returned an empty list — TOOLS is still a TODO")
    else:
        found = [t.get("name", "") for t in listed]
        for name in WANTED:
            if name not in found:
                problems.append(f"tools/list is missing '{name}'")
        for tool in listed:
            name = tool.get("name", "?")
            desc = (tool.get("description") or "").strip()
            schema = tool.get("inputSchema") or {}
            if len(desc) < 40:
                problems.append(f"{name}: the description is too thin for the model to "
                                f"choose it on purpose ({len(desc)} chars)")
            if schema.get("type") != "object" or not schema.get("properties"):
                problems.append(f"{name}: inputSchema is not an object schema with "
                                f"properties, so arguments cannot be validated")
            if "query" in (schema.get("properties") or {}) \
                    and "query" not in (schema.get("required") or []):
                notes.append(f"{name}: 'query' is not in required — a call with no query "
                             f"will reach your code")
            leaked = [w for w in ("where", "n_results", "collection", "chroma")
                      if w in (schema.get("properties") or {})]
            if leaked:
                problems.append(f"{name}: exposes {', '.join(leaked)} — that is the vector "
                                f"database leaking through. Offer intent, not query syntax")
        filtered = next((t for t in listed if t.get("name") == "search_corpus_filtered"),
                        None)
        if filtered:
            props = (filtered.get("inputSchema") or {}).get("properties") or {}
            if "superseded" not in props:
                problems.append("search_corpus_filtered does not accept 'superseded' — "
                                "that filter is the difference between quoting the policy "
                                "in force and the one it replaced")
            elif "supersed" not in (filtered.get("description") or "").lower():
                notes.append("search_corpus_filtered accepts 'superseded' but its "
                             "description never mentions when to use it; the model will "
                             "not guess that 'current' means superseded=false")

    if not any(p.startswith("tools/list") or "TOOLS is still" in p for p in problems):
        calls, _ = converse(root, [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": PROTOCOL, "capabilities": {},
                        "clientInfo": {"name": "lab-gate", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "search_corpus",
                        "arguments": {"query": "what does the policy say", "k": 3}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
             "params": {"name": "get_document",
                        "arguments": {"source": "data/definitely-not-here.md"}}},
        ])
        result = by_id(calls, 3).get("result") or {}
        content = result.get("content") or []
        text = content[0].get("text", "") if content else ""
        if not content:
            problems.append("search_corpus returned no 'content' array")
        elif result.get("isError"):
            problems.append(f"search_corpus reported an error: {text[:200]}")
        elif len(text.strip()) < 50:
            problems.append("search_corpus returned almost nothing — either the corpus is "
                            "not ingested or format_results is still a TODO")
        elif "data/" not in text:
            problems.append("search_corpus results carry no source path, so the model "
                            "cannot cite what it used and will invent citations")

        missing = by_id(calls, 4).get("result") or {}
        if missing and not missing.get("isError"):
            notes.append("get_document on a non-existent path did not set isError; the "
                         "model cannot tell success from failure")

    report(problems, notes, found, args.as_json)
    return 1 if problems else 0


def report(problems: list[str], notes: list[str], found: list[str], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"ok": not problems, "problems": problems,
                          "notes": notes, "tools": found}, indent=2))
        return
    print("MCP RETRIEVAL TOOL CHECK")
    print("========================")
    if found:
        print(f"\n  tools offered: {', '.join(found)}")
    if problems:
        print("\nNOT READY:")
        for item in problems:
            print(f"  x {item}")
    else:
        print("\nReady — it completes a handshake, lists intent-level tools, and cites "
              "its sources.")
    if notes:
        print("\nWorth improving (not blocking):")
        for item in notes:
            print(f"  ! {item}")


if __name__ == "__main__":
    sys.exit(main())
