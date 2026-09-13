#!/usr/bin/env python3
"""Validate a participant's extracted graph, score it, and diff it against the answer key.

Three things in order, because each depends on the last:

  1. compile — does it satisfy the ontology at all (types, directions, dangling edges)
  2. score   — does it answer the questions it was built for, as complete sets
  3. diff    — where does it differ from the verified graph, and does that matter

The diff is advisory on purpose. A participant who models something differently and still
answers every question has not made a mistake; they have made a different design. The score
is what gates, and the diff is what the conversation is about.

    check_graph.py               validate, score and diff
    check_graph.py --json        machine-readable
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(SCRIPTS)


def track_of(root: str) -> str | None:
    state = os.path.join(root, ".agent-lab", "state.json")
    if not os.path.exists(state):
        return None
    try:
        return json.load(open(state)).get("track")
    except (OSError, ValueError):
        return None


def read_jsonl(path: str) -> list[dict]:
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    pass
    return rows


def diff_against_reference(root: str, track: str) -> dict | None:
    """Compare shapes, not contents: which types and relations differ, and by how much."""
    ref_dir = os.path.join(PLUGIN_ROOT, "tracks", track, "reference", "graph")
    if not os.path.isdir(ref_dir):
        return None
    mine_nodes = read_jsonl(os.path.join(root, "graph", "nodes.jsonl"))
    mine_edges = read_jsonl(os.path.join(root, "graph", "edges.jsonl"))
    ref_nodes = read_jsonl(os.path.join(ref_dir, "nodes.jsonl"))
    ref_edges = read_jsonl(os.path.join(ref_dir, "edges.jsonl"))
    if not ref_nodes:
        return None

    def by_type(rows):
        out: dict[str, int] = {}
        for r in rows:
            out[r.get("type", "?")] = out.get(r.get("type", "?"), 0) + 1
        return out

    def by_rel(rows):
        out: dict[str, int] = {}
        for r in rows:
            out[r.get("rel", "?")] = out.get(r.get("rel", "?"), 0) + 1
        return out

    mine_ids = {n.get("id") for n in mine_nodes}
    ref_ids = {n.get("id") for n in ref_nodes}
    mine_triples = {(e.get("src"), e.get("rel"), e.get("dst")) for e in mine_edges}
    ref_triples = {(e.get("src"), e.get("rel"), e.get("dst")) for e in ref_edges}
    return {
        "nodes": {"mine": len(mine_nodes), "reference": len(ref_nodes)},
        "edges": {"mine": len(mine_edges), "reference": len(ref_edges)},
        "by_type": {"mine": by_type(mine_nodes), "reference": by_type(ref_nodes)},
        "by_relation": {"mine": by_rel(mine_edges), "reference": by_rel(ref_edges)},
        "nodes_only_in_reference": sorted(ref_ids - mine_ids)[:20],
        "nodes_only_in_mine": sorted(mine_ids - ref_ids)[:20],
        "edges_only_in_reference": [" -".join(t[:2]) + "-> " + t[2]
                                    for t in sorted(ref_triples - mine_triples)][:20],
        "edges_only_in_mine": [" -".join(t[:2]) + "-> " + t[2]
                               for t in sorted(mine_triples - ref_triples)][:20],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    problems: list[str] = []
    notes: list[str] = []
    compiled: dict = {}
    scored: dict = {}

    # --- 1. compile
    compiler = os.path.join(root, "kg", "compile.py")
    if not os.path.exists(compiler):
        problems.append("no kg/compile.py yet")
    else:
        result = subprocess.run([sys.executable, compiler, "--root", root, "--json"],
                                capture_output=True, text=True, cwd=root)
        try:
            compiled = json.loads(result.stdout or "{}")
        except ValueError:
            compiled = {}
        if not compiled:
            # No parsable result at all: the compiler refused before it got started, and
            # whatever it said on stderr is the actual finding.
            problems.append("kg/compile.py produced no result: "
                            + ((result.stderr or result.stdout).strip()[:200]
                               or "no output"))
        elif not compiled.get("ok"):
            for item in (compiled.get("errors") or [])[:8]:
                problems.append(f"compile: {item}")
        for item in (compiled.get("warnings") or [])[:6]:
            notes.append(f"compile: {item}")

    # --- 2. score, but only if there is a graph to score
    if compiled.get("ok"):
        queries = os.path.join(root, "evals", "graph", "queries.jsonl")
        if not os.path.exists(queries):
            notes.append("no evals/graph/queries.jsonl, so the graph was not scored")
        else:
            result = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, "eval_graph.py"),
                 "--root", root, "--json", "--no-record"],
                capture_output=True, text=True)
            try:
                scored = json.loads(result.stdout or "{}")
            except ValueError:
                problems.append("eval_graph.py did not return JSON")
            head = (scored.get("headline") or {})
            if head:
                if head["exact"] < head["queries"]:
                    for row in scored["queries"]:
                        if row["exact"]:
                            continue
                        detail = (f"missing {', '.join(row['missing'])}" if row["missing"]
                                  else f"extra {', '.join(row['extra'])}" if row["extra"]
                                  else row.get("error") or "no result")
                        problems.append(f"{row['id']} [{row['shape']}] not answered: "
                                        f"{detail}")
                if head.get("recall", 0) < 1 and head.get("precision", 0) == 1:
                    notes.append("precision is perfect and recall is not: the graph is "
                                 "right about what it contains and missing facts. That is "
                                 "an extraction gap, not a modelling error")

    # --- 3. diff, advisory
    track = track_of(root)
    delta = diff_against_reference(root, track) if track else None
    if delta:
        for rel, count in delta["by_relation"]["reference"].items():
            mine = delta["by_relation"]["mine"].get(rel, 0)
            if mine == 0:
                notes.append(f"the verified graph has {count} {rel} edges and yours has "
                             f"none — if no competency question needs it, that is fine")

    payload = {"ok": not problems, "problems": problems, "notes": notes,
               "compiled": {k: compiled.get(k) for k in ("ok", "nodes", "edges")},
               "score": scored.get("headline"), "diff": delta}
    if args.as_json:
        print(json.dumps(payload, indent=2))
        return 1 if problems else 0

    print("GRAPH CHECK")
    print("===========")
    if compiled.get("ok"):
        print(f"\n  compiled: {compiled['nodes']} nodes, {compiled['edges']} edges")
    if scored.get("headline"):
        h = scored["headline"]
        print(f"  scored:   {h['exact']}/{h['queries']} exact, "
              f"precision {h['precision']}, recall {h['recall']}")
    if delta:
        print(f"  answer key: {delta['nodes']['reference']} nodes, "
              f"{delta['edges']['reference']} edges")
        if delta["edges_only_in_reference"]:
            print(f"\n  In the verified graph, not in yours "
                  f"({len(delta['edges_only_in_reference'])} shown):")
            for item in delta["edges_only_in_reference"][:6]:
                print(f"    - {item}")
        if delta["edges_only_in_mine"]:
            print(f"\n  In yours, not in the verified graph:")
            for item in delta["edges_only_in_mine"][:6]:
                print(f"    + {item}")
        print("\n  A difference is not automatically a mistake. If your graph answers every "
              "\n  question, you modelled it differently — talk about which is better.")
    if problems:
        print("\nNOT READY:")
        for item in problems:
            print(f"  x {item}")
    else:
        print("\nReady — satisfies the ontology and answers every question exactly.")
    if notes:
        print("\nWorth knowing:")
        for item in notes:
            print(f"  ! {item}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
