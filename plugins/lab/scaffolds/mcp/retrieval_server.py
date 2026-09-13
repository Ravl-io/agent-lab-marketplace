#!/usr/bin/env python3
"""An MCP server that exposes your retrieval to the agent.

MCP is a protocol, not a framework: newline-delimited JSON-RPC 2.0 over stdin and stdout.
There is no SDK here on purpose — nothing in this file should be mysterious to you.

Three methods are all a tools server needs:

    initialize      who you are, what you support
    tools/list      the tools you offer, with JSON Schema for their arguments
    tools/call      run one, return content

The plumbing below is written. What is missing is the part that is actually a design
decision: **what tools you offer, and how you describe them.**

One hard rule: anything on stdout that is not a JSON-RPC message corrupts the stream, and
the client will show the server as failed with no useful reason. Print debugging goes to
stderr. `print(..., file=sys.stderr)`.
"""

from __future__ import annotations

import json
import os
import sys
import traceback

PROTOCOL = "2024-11-05"
HERE = os.path.dirname(os.path.abspath(__file__))


def project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _retrieval():
    """Import your own rag/retrieve.py. One implementation, two callers.

    The scoreboard calls it directly; the agent calls it through this server. If those were
    two different implementations you would be measuring one and shipping the other.
    """
    sys.path.insert(0, os.path.join(project_root(), "rag"))
    import retrieve                                          # noqa: PLC0415
    return retrieve


# ---------------------------------------------------------------- the design decision
#
# TODO 1. Declare your tools.
#
# Each entry needs: name, description, inputSchema (JSON Schema for the arguments).
#
# The description is not documentation. It is the only thing the model sees when it decides
# whether to call your tool — it is a skill description under a different name, and the same
# rule applies: say WHEN to reach for this, not just what it does. You measured what a vague
# description costs in module 1. It costs the same here.
#
# Offer three, wrapping the three functions in rag/retrieve.py:
#
#   search_corpus            similarity search over everything
#   search_corpus_filtered   the same, restricted to a slice (doc_type, period, superseded)
#   get_document             one whole document by path
#
# Two things worth getting right:
#
#   - For the filtered one, say in the description WHEN a filter is the right move. The model
#     will not infer that "the current policy" means superseded=false. Tell it.
#   - Expose intent-level operations, never the vector database. No `where` clause, no
#     collection name, no `n_results`. If a caller has to know Chroma's query syntax to use
#     your tool, you have not built a tool — you have leaked a dependency.

TOOLS: list[dict] = [
    # {"name": "...", "description": "...", "inputSchema": {"type": "object", ...}},
]


def format_results(results: list[dict]) -> str:
    """Turn retrieval results into the text the model reads.

    TODO 2. Put the provenance where it cannot be lost.

    The model has to be able to cite what it used. If your text is just the passages run
    together, it will invent plausible-looking citations, and they will be wrong in a way
    that is very hard to spot. Number each passage and name its source and heading.
    """
    if not results:
        return "No passages matched. Try different words, or widen the filters."
    # TODO: build one readable block per result, source first.
    return ""


def call_tool(name: str, args: dict) -> dict:
    """Dispatch one tool call.

    TODO 3. Route each tool name to the right function in rag/retrieve.py, and return

        {"content": [{"type": "text", "text": "..."}]}

    adding "isError": True when the call could not be satisfied — an unknown document, for
    instance. An error the model can read and act on beats an exception it never sees.
    """
    retrieve = _retrieval()
    return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}],
            "isError": True}


# ---------------------------------------------------------------- the plumbing (done)

def handle(message: dict) -> dict | None:
    method = message.get("method")
    mid = message.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": PROTOCOL,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "corpus-retrieval", "version": "0.2.0"},
        }}
    if method in ("notifications/initialized", "initialized"):
        return None                                   # a notification takes no reply
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params") or {}
        try:
            result = call_tool(params.get("name", ""), params.get("arguments") or {})
        except Exception:                                    # noqa: BLE001
            print(traceback.format_exc(), file=sys.stderr)
            result = {"content": [{"type": "text",
                                   "text": "Retrieval failed. Has the corpus been "
                                           "ingested? Run: python3 rag/ingest.py naive"}],
                      "isError": True}
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if mid is None:
        return None                                   # unknown notification, ignore
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
