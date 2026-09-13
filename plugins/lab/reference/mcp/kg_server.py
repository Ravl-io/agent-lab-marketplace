#!/usr/bin/env python3
"""An MCP server exposing the knowledge graph to the agent. Reference implementation.

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


TOOLS = [
    {
        "name": "kg_search",
        "description": (
            "Find things in the knowledge graph by name and get their ids. Start here: the "
            "other graph tools take ids, and you will usually have a name — an account, a "
            "defect, a project, a requirement. Returns the id, type and label of each match."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Part of a name or an id."},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["text"],
        },
    },
    {
        "name": "kg_entity",
        "description": (
            "Everything the graph knows about one thing: its properties, every relationship "
            "in and out, and the source document or table each fact came from. Use it to "
            "ground an answer about a specific entity, and to cite where a fact came from."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "as_of": {"type": "string",
                          "description": "YYYY-MM-DD. Relationships that had ended by then "
                                         "are excluded. Omit for what is true now."},
            },
            "required": ["id"],
        },
    },
    {
        "name": "kg_neighbors",
        "description": (
            "One hop from a thing: what it relates to, or what relates to it. Use it to "
            "explore when you do not yet know which relationship you need. If you already "
            "know the chain of relationships, kg_reach follows the whole chain in one call."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "relation": {"type": "string", "description": "Optional filter."},
                "direction": {"type": "string", "enum": ["out", "in", "both"],
                              "default": "out"},
                "as_of": {"type": "string"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "kg_reach",
        "description": (
            "Follow a chain of relationships from one thing and return the COMPLETE set of "
            "things at the end. This is the multi-hop tool, and the reason the graph exists: "
            "'which other accounts are affected by this defect' is a chain, not a search. "
            "Prefix a relation with < to follow it backwards — needed whenever two relations "
            "point at the same thing. Use kg_ontology first if you are unsure of the names."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "start": {"type": "string", "description": "The id to start from."},
                "path": {"type": "array", "items": {"type": "string"},
                         "description": "Relations in order, e.g. "
                                        "[\"scoped_to_region\", \"<in_region\"]"},
                "as_of": {"type": "string"},
            },
            "required": ["start", "path"],
        },
    },
    {
        "name": "kg_coverage",
        "description": (
            "Things of a given type that have NO relationship of a given kind — the gap "
            "report. Use it for any question about absence or completeness: what is "
            "untested, unverified, unassigned, never escalated, not covered. Retrieval "
            "cannot answer these at all, because it can only return what it found. Set "
            "direction to 'in' when the relation points AT the type you are asking about."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "A node type from the ontology."},
                "missing_relation": {"type": "string"},
                "direction": {"type": "string", "enum": ["out", "in"], "default": "out"},
                "as_of": {"type": "string"},
            },
            "required": ["type", "missing_relation"],
        },
    },
    {
        "name": "kg_as_of",
        "description": (
            "What a time-varying relationship said on a particular date. Use it whenever a "
            "question contains a date, a month, or a word like 'then', 'at the time', "
            "'currently' or 'still' — and call it twice with two dates to answer 'what "
            "changed'. An answer about entitlements, scope or contract terms with no date "
            "attached is not an answer; this is how you attach one."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "relation": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["id", "relation"],
        },
    },
    {
        "name": "kg_ontology",
        "description": (
            "The graph's schema: the types, the relations, which direction each one points, "
            "and which carry validity dates. Read this before composing a kg_reach path, or "
            "you will guess a relation name and get an empty set that looks like a real "
            "answer of 'none'."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "kg_path",
        "description": (
            "How two things are connected, if they are: the shortest chains of relationships "
            "between them. Use it for 'why' and 'how are these related' questions. Note that "
            "shortest is not always the most meaningful route — read the chain before "
            "relying on it."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "from": {"type": "string"},
                "to": {"type": "string"},
                "max_hops": {"type": "integer", "default": 4},
            },
            "required": ["from", "to"],
        },
    },
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
    if name == "kg_ontology":
        return text(ontology_summary())
    kg = _kg()
    con = kg.connect(project_root())
    if name == "kg_search":
        return text(kg.search(con, args["text"], int(args.get("limit", 10))))
    if name == "kg_entity":
        try:
            return text(kg.entity(con, args["id"], args.get("as_of")))
        except KeyError:
            return {"content": [{"type": "text",
                                 "text": f"No node with id {args['id']!r}. "
                                         f"Try kg_search to find it."}],
                    "isError": True}
    if name == "kg_neighbors":
        return text(kg.neighbors(con, args["id"], args.get("relation"),
                                 args.get("direction", "out"), args.get("as_of")))
    if name == "kg_reach":
        landed = kg.reach(con, args["start"], list(args["path"]), args.get("as_of"))
        # An empty result reads as "none" to a model, and "none" is a real answer it will
        # report. Say which it is, because a mistyped relation looks identical otherwise.
        if not landed:
            known = {r["name"] for r in ontology_summary().get("relations", [])}
            unknown = [s for s in (p.lstrip("<") for p in args["path"]) if s not in known]
            if unknown:
                return {"content": [{"type": "text",
                                     "text": f"No such relation(s): {', '.join(unknown)}. "
                                             f"This is not an empty answer — the path is "
                                             f"wrong. Call kg_ontology for the real names."}],
                        "isError": True}
        return text({"start": args["start"], "path": args["path"],
                     "count": len(landed), "results": landed})
    if name == "kg_coverage":
        gaps = kg.coverage(con, args["type"], args["missing_relation"],
                           args.get("direction", "out"), args.get("as_of"))
        return text({"type": args["type"], "missing": args["missing_relation"],
                     "count": len(gaps), "results": gaps})
    if name == "kg_as_of":
        return text({"id": args["id"], "relation": args["relation"],
                     "date": args.get("date"),
                     "results": kg.as_of(con, args["id"], args["relation"],
                                         args.get("date"))})
    if name == "kg_path":
        return text(kg.paths(con, args["from"], args["to"],
                             int(args.get("max_hops", 4))))
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
