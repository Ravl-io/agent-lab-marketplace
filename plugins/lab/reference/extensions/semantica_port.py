#!/usr/bin/env python3
"""Rebuild your graph with Semantica instead of kg/compile.py — an optional comparison.

    python3 extensions/semantica_port.py              rebuild and run the three questions
    python3 extensions/semantica_port.py --as-of 2026-04-15

**Nothing in the lab needs this.** It exists so you can see the same graph expressed in a
real library rather than in the 800 lines you wrote, and decide for yourself which one you
would want at work. Install it first, into the same virtualenv, and read the note in
`extensions/semantica.md` before you do — it is a 2 GB install.

    pip install semantica

It reads the `graph/nodes.jsonl` and `graph/edges.jsonl` you already produced, so your
extraction is the input to both paths. That is the whole point of the comparison: same facts,
two implementations.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date as _date

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = _date.today().isoformat()


def project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(HERE)


def read_jsonl(path: str) -> list[dict]:
    rows = []
    if not os.path.exists(path):
        sys.exit(f"no {os.path.basename(path)} — extract your graph first "
                 f"(Module 3, step 3)")
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                rows.append(json.loads(line))
    return rows


def require_semantica():
    try:
        from semantica.kg import GraphBuilder                # noqa: PLC0415
    except ImportError:
        sys.exit("semantica is not installed in this interpreter.\n"
                 "  pip install semantica\n"
                 "It is optional and nothing else in the lab needs it. Read "
                 "extensions/semantica.md first — the install is about 2 GB.")
    return GraphBuilder


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--as-of", default=None,
                    help="a date, to see the temporal question answered twice")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    root = os.path.abspath(args.root or project_root())

    GraphBuilder = require_semantica()
    nodes = read_jsonl(os.path.join(root, "graph", "nodes.jsonl"))
    edges = read_jsonl(os.path.join(root, "graph", "edges.jsonl"))

    # Semantica's graph is a plain dict of entities and relationships, which is why it needs
    # no database: persistence is json.dump. Your kg.db is the same information in two
    # tables — pick whichever you would rather hand to a colleague.
    graph = {
        "entities": [{"id": n["id"], "type": n.get("type"),
                      "name": n.get("label") or n["id"],
                      "provenance": n.get("source")} for n in nodes],
        "relationships": [],
    }

    builder = GraphBuilder(enable_temporal=True)
    temporal = 0
    for e in edges:
        if e.get("valid_from") or e.get("valid_to"):
            builder.add_temporal_edge(
                graph, e["src"], e["dst"], e["rel"],
                valid_from=e.get("valid_from"), valid_until=e.get("valid_to"),
                provenance=e.get("source"))
            temporal += 1
        else:
            graph["relationships"].append({
                "source": e["src"], "target": e["dst"], "type": e["rel"],
                "provenance": e.get("source")})

    summary = {
        "entities": len(graph["entities"]),
        "relationships": len(graph["relationships"]),
        "temporal_edges": temporal,
    }

    # The temporal question, answered at two dates.
    #
    # Use create_temporal_snapshot, not query_temporal. In 0.6.8 query_temporal ignores its
    # `query` argument entirely and hands back the whole snapshot — the library says so in a
    # comment: "Basic query execution (simplified) / In a real implementation, this would use
    # a proper query engine". It also raises KeyError on the dict its own docstring
    # documents, from a log line doing query[:50]. The snapshot function does the real work.
    #
    # So the relation filter is ours, which is the honest shape of this comparison: the
    # library gives you the temporal model, and you still write the query.
    if args.as_of:
        relation = next((e["rel"] for e in edges if e.get("valid_to")), None)
        if relation:
            for label, date in (("as of " + args.as_of, args.as_of), ("today", TODAY)):
                snapshot = builder.create_temporal_snapshot(graph, timestamp=date)
                rels = [r for r in snapshot.get("relationships", [])
                        if r.get("type") == relation]
                summary.setdefault("as_of", {})[label] = len(rels)
            summary["relation_compared"] = relation

    out = os.path.join(root, "graph", "semantica.json")
    with open(out, "w") as fh:
        json.dump(graph, fh, indent=2, default=str)
    summary["written"] = os.path.relpath(out, root)

    if args.as_json:
        print(json.dumps(summary, indent=2))
        return 0
    print("SEMANTICA PORT")
    print("==============")
    print(f"\n  {summary['entities']} entities, {summary['relationships']} "
          f"relationships, {summary['temporal_edges']} of them temporal")
    print(f"  written to {summary['written']} — a JSON file, no database")
    if summary.get("as_of"):
        rel = summary.get("relation_compared")
        print(f"\n  {rel} edges in force, at two dates:")
        for label, count in summary["as_of"].items():
            print(f"    {label:<20} {count}")
    print("\n  Same facts as your kg.db. Compare the two and decide which one you would")
    print("  rather maintain — that is the only question this script exists to ask.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
