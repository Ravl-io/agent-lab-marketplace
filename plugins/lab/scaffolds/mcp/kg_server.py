#!/usr/bin/env python3
"""An MCP server exposing your knowledge graph to the agent.

Same shape as the retrieval server from Module 2 — newline-delimited JSON-RPC 2.0 over
stdio, no SDK — so the only new thing here is the tool surface, which is the actual lesson.

The temptation is to expose one tool called `query_graph` that takes SQL. Do not. The model
would have to know your schema, your relation names and your date semantics, and it would
get the temporal ones wrong silently. These tools expose *question shapes* instead: reach,
coverage, as-of. Each one corresponds to a class of question the graph exists to answer.
"""

from __future__ import annotations

import json
import os
import sys
import traceback

PROTOCOL = "2024-11-05"


def project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _kg():
    """Import the participant's own kg/kg.py. One implementation, two callers."""
    sys.path.insert(0, os.path.join(project_root(), "kg"))
    import kg                                                # noqa: PLC0415
    return kg


# ---------------------------------------------------------------- the design decision
#
# TODO 1. Declare your tools.
#
# You have seven operations in kg/kg.py: search, entity, neighbors, reach, paths, coverage
# and as_of. Wrapping each one as a tool is not the job — deciding what the agent should be
# able to ASK is.
#
# The temptation is one tool called `query_graph` that takes SQL. Do not. The model would
# have to know your schema, your relation names and your date semantics, and it would get
# the temporal ones wrong silently. Expose question SHAPES instead.
#
# Offer at least these, and add any your track needs:
#
#   kg_search      find things by name, and get their ids. The entry point
#   kg_entity      everything about one thing, including where each fact came from
#   kg_reach       follow a chain of relations and return the COMPLETE set at the end
#   kg_coverage    things with NO relation of a given kind — the gap report
#   kg_as_of       what a time-varying relation said on a date
#   kg_ontology    the schema, so the model can compose a path instead of guessing
#
# Three things to get right, and each one has a specific failure behind it:
#
#   - Say WHEN to use each tool, not just what it does. For kg_as_of, name the words that
#     should trigger it: a date, a month, "at the time", "currently", "still".
#   - kg_ontology is not optional. Without it the model invents relation names, gets an
#     empty result, and reports "none" — which is a wrong answer that looks like a real one.
#   - An empty result from a mistyped path must not read as "none". Say which it is.

TOOLS: list[dict] = [
    # {"name": "...", "description": "...", "inputSchema": {"type": "object", ...}},
]


def ontology_summary() -> dict:
    """Read the ontology so the model can compose a traversal instead of guessing."""
    folder = os.path.join(project_root(), "ontology")
    if not os.path.isdir(folder):
        return {"error": "no ontology/ directory"}
    files = sorted(f for f in os.listdir(folder) if f.endswith((".yaml", ".yml")))
    if not files:
        return {"error": "no ontology file"}
    try:
        import yaml                                          # noqa: PLC0415
    except ImportError:
        return {"error": "pyyaml not installed"}
    with open(os.path.join(folder, files[0])) as fh:
        data = yaml.safe_load(fh) or {}
    return {
        "types": sorted(data.get("types") or {}),
        "relations": [
            {"name": r["name"], "from": r["from"], "to": r["to"],
             "temporal": bool(r.get("temporal"))}
            for r in (data.get("relations") or [])],
        "competency_questions": [c.get("q") for c in
                                 (data.get("competency_questions") or [])],
    }


def text(payload) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}


def call_tool(name: str, args: dict) -> dict:
    """Dispatch one tool call.

    TODO 2. Route each tool name to the right function in kg/kg.py, and return

        {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}

    adding "isError": True when the call could not be satisfied. `kg_ontology` is already
    written for you below as the one worked example — read it, then do the rest.
    """
    if name == "kg_ontology":
        return text(ontology_summary())
    kg = _kg()
    con = kg.connect(project_root())

    # TODO: the other tools.

    return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}],
            "isError": True}


def handle(message: dict) -> dict | None:
    method, mid = message.get("method"), message.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": PROTOCOL, "capabilities": {"tools": {}},
            "serverInfo": {"name": "knowledge-graph", "version": "0.3.0"}}}
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params") or {}
        try:
            result = call_tool(params.get("name", ""), params.get("arguments") or {})
        except SystemExit as exc:
            result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        except Exception:                                    # noqa: BLE001
            print(traceback.format_exc(), file=sys.stderr)
            result = {"content": [{"type": "text",
                                   "text": "Graph query failed. Has the graph been "
                                           "compiled? Run: python3 kg/compile.py"}],
                      "isError": True}
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if mid is None:
        return None
    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"Method not found: {method}"}}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            continue
        reply = handle(message)
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
