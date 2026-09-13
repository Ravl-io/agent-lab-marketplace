#!/usr/bin/env python3
"""Validate a participant's MCP graph server by speaking the protocol to it.

Same approach as the retrieval tool check: launch it the way a client does and judge what
comes back. The extra checks here are about the failure specific to graph tools — an empty
result that reads as a real answer of "none" when the traversal was simply wrong.

    check_kg_tool.py           validate the project's graph server
    check_kg_tool.py --json    machine-readable
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

PROTOCOL = "2024-11-05"
SERVER = os.path.join("mcp", "kg_server.py")
# The shapes the module exists for. A server missing one of these cannot answer one of the
# three question classes, whatever else it offers.
REQUIRED = {
    "search": ("kg_search",),
    "entity": ("kg_entity",),
    "multi-hop": ("kg_reach", "kg_path"),
    "completeness": ("kg_coverage",),
    "temporal": ("kg_as_of",),
    "schema": ("kg_ontology",),
}


def converse(root: str, messages: list[dict], timeout: int = 90) -> tuple[list[dict], str]:
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


def handshake(extra: list[dict]) -> list[dict]:
    return [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": PROTOCOL, "capabilities": {},
                    "clientInfo": {"name": "lab-gate", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        *extra,
    ]


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
        report(problems + [f"{SERVER} does not exist yet"], notes, found, args.as_json)
        return 1

    config = os.path.join(root, ".mcp.json")
    if not os.path.exists(config):
        problems.append(".mcp.json is missing — the server exists but nothing launches it")
    else:
        try:
            servers = (json.load(open(config)).get("mcpServers") or {})
            if not any("kg_server.py" in json.dumps(v) for v in servers.values()):
                problems.append(".mcp.json does not declare the graph server. Module 2's "
                                "retrieval server is already in there — add a second entry "
                                "beside it rather than replacing it")
            elif len(servers) < 2:
                notes.append("only one server in .mcp.json; the retrieval server from "
                             "Module 2 should still be declared too")
        except ValueError:
            problems.append(".mcp.json is not valid JSON, so the client will ignore it")

    replies, stderr = converse(root, handshake([
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]))
    if not replies:
        problems.append(f"the server produced no replies. stderr: {stderr.strip()[:300]}")
        report(problems, notes, found, args.as_json)
        return 1

    init = by_id(replies, 1).get("result") or {}
    if not init:
        problems.append("no reply to initialize — a client would give up here")
    elif "tools" not in (init.get("capabilities") or {}):
        problems.append("initialize does not advertise a 'tools' capability, so a client "
                        "will never ask for your tools")

    listed = (by_id(replies, 2).get("result") or {}).get("tools")
    if listed is None:
        problems.append("no reply to tools/list")
    elif not listed:
        problems.append("tools/list returned an empty list — TOOLS is still a TODO")
    else:
        found = [t.get("name", "") for t in listed]
        for shape, options in REQUIRED.items():
            if not any(name in found for name in options):
                problems.append(f"nothing covers the {shape} shape "
                                f"(expected one of {', '.join(options)})")
        for tool in listed:
            name = tool.get("name", "?")
            desc = (tool.get("description") or "").strip()
            schema = tool.get("inputSchema") or {}
            if len(desc) < 40:
                problems.append(f"{name}: the description is too thin for the model to "
                                f"choose it on purpose ({len(desc)} chars)")
            if schema.get("type") != "object":
                problems.append(f"{name}: inputSchema is not an object schema")
            if "sql" in name.lower() or "sql" in desc.lower():
                problems.append(f"{name}: exposes SQL. The model would have to know your "
                                f"schema and your date semantics, and it will get the "
                                f"temporal ones wrong silently. Offer question shapes")
        as_of_tool = next((t for t in listed if t.get("name") == "kg_as_of"), None)
        if as_of_tool:
            desc = (as_of_tool.get("description") or "").lower()
            if not any(word in desc for word in
                       ("date", "when", "currently", "at the time", "changed")):
                notes.append("kg_as_of's description never names the words that should "
                             "trigger it — the model will not infer that 'at the time' "
                             "means an as-of query")
        coverage_tool = next((t for t in listed if t.get("name") == "kg_coverage"), None)
        if coverage_tool:
            desc = (coverage_tool.get("description") or "").lower()
            if not any(word in desc for word in ("missing", "absence", "no ", "gap",
                                                 "not covered", "without")):
                notes.append("kg_coverage's description does not say it answers questions "
                             "about absence, which is the only reason it exists")

    # --- behaviour: the graph has to actually answer, and a wrong path must not read as none
    if found:
        calls, _ = converse(root, handshake([
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "kg_ontology", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
             "params": {"name": "kg_reach",
                        "arguments": {"start": "nothing:here",
                                      "path": ["definitely_not_a_relation"]}}},
        ]))
        onto = by_id(calls, 3).get("result") or {}
        text = ((onto.get("content") or [{}])[0].get("text") or "")
        if "kg_ontology" in found:
            if onto.get("isError") or not text.strip():
                problems.append("kg_ontology returned nothing. Without it the model invents "
                                "relation names, gets an empty set, and reports 'none'")
            elif "relation" not in text.lower():
                notes.append("kg_ontology's output does not appear to list relations; the "
                             "model needs their names and directions to compose a path")
        bad = by_id(calls, 4).get("result") or {}
        bad_text = ((bad.get("content") or [{}])[0].get("text") or "")
        if "kg_reach" in found and bad:
            said_so = bad.get("isError") or any(
                word in bad_text.lower()
                for word in ("no such", "unknown", "not a relation", "invalid", "wrong"))
            if not said_so:
                problems.append("kg_reach answered a nonsense relation with a plain empty "
                                "result. An empty set reads as a real answer of 'none' — "
                                "say when the path itself was wrong")

    report(problems, notes, found, args.as_json)
    return 1 if problems else 0


def report(problems: list[str], notes: list[str], found: list[str], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"ok": not problems, "problems": problems,
                          "notes": notes, "tools": found}, indent=2))
        return
    print("MCP GRAPH TOOL CHECK")
    print("====================")
    if found:
        print(f"\n  tools offered: {', '.join(found)}")
    if problems:
        print("\nNOT READY:")
        for item in problems:
            print(f"  x {item}")
    else:
        print("\nReady — covers every question shape, and says when a path was wrong.")
    if notes:
        print("\nWorth improving (not blocking):")
        for item in notes:
            print(f"  ! {item}")


if __name__ == "__main__":
    sys.exit(main())
