#!/usr/bin/env python3
"""An MCP server that exposes retrieval to the agent. Reference implementation.

MCP is a protocol, not a framework: newline-delimited JSON-RPC 2.0 over stdin and stdout.
No SDK is used here on purpose — there is nothing in this file a participant cannot read.

Three methods are all a tools server needs:

    initialize                 who you are, what you support
    tools/list                 the tools, with JSON Schema for their arguments
    tools/call                 run one, return content

Anything written to stdout that is not a JSON-RPC message corrupts the stream. Log to
stderr, which the client shows as server logs.
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
    """Import the participant's own rag/retrieve.py. One implementation, two callers."""
    sys.path.insert(0, os.path.join(project_root(), "rag"))
    import retrieve                                          # noqa: PLC0415
    return retrieve


TOOLS = [
    {
        "name": "search_corpus",
        "description": (
            "Search the project's document corpus for passages relevant to a question. "
            "Returns the passage text with the file it came from, so answers can cite a "
            "source. Use this before answering any question about the organisation's own "
            "documents, policies, tickets or history."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string",
                          "description": "The question, in natural language."},
                "k": {"type": "integer", "default": 5,
                      "description": "How many passages to return. 5 is usually right."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_corpus_filtered",
        "description": (
            "Search the corpus within a named slice of it. Use this when the question is "
            "about a particular kind of document, a particular month, or when only the "
            "currently-in-force version of a policy will do: pass superseded=false. "
            "Prefer this over search_corpus whenever the question has a qualifier."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "k": {"type": "integer", "default": 5},
                "doc_type": {"type": "string",
                             "description": "e.g. knowledge, ticket, contract, register"},
                "period": {"type": "string", "description": "YYYY-MM"},
                "superseded": {"type": "boolean",
                               "description": "false restricts to documents still in force"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_document",
        "description": (
            "Read one whole document by its path, as returned in a search result's source "
            "field. Use it when a retrieved passage is clearly part of a larger argument "
            "and you need the rest of it. Not a search — you must already know the path."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"source": {"type": "string"}},
            "required": ["source"],
        },
    },
]


def format_results(results: list[dict]) -> str:
    """What the model actually reads. Provenance first, so a citation is always available."""
    if not results:
        return "No passages matched. Try different words, or widen the filters."
    out = []
    for index, r in enumerate(results, 1):
        heading = (r.get("meta") or {}).get("heading") or ""
        where = f"{r.get('source', '?')}{' / ' + heading if heading else ''}"
        out.append(f"[{index}] {where}\n{r.get('text', '').strip()}")
    return "\n\n".join(out)


def call_tool(name: str, args: dict) -> dict:
    retrieve = _retrieval()
    if name == "search_corpus":
        results = retrieve.search(args["query"], k=int(args.get("k", 5)))
        return {"content": [{"type": "text", "text": format_results(results)}]}
    if name == "search_corpus_filtered":
        filters = {key: args[key] for key in ("doc_type", "period", "superseded")
                   if key in args}
        results = retrieve.search_filtered(args["query"], k=int(args.get("k", 5)),
                                           **filters)
        return {"content": [{"type": "text", "text": format_results(results)}]}
    if name == "get_document":
        try:
            text = retrieve.get_document(args["source"])
        except FileNotFoundError:
            return {"content": [{"type": "text",
                                 "text": f"No such document: {args['source']}"}],
                    "isError": True}
        return {"content": [{"type": "text", "text": text}]}
    return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}],
            "isError": True}


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
