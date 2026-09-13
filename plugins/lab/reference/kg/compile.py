#!/usr/bin/env python3
"""Compile nodes.jsonl + edges.jsonl into kg.db, validating against the ontology.

    python3 kg/compile.py                       # ontology/<track>.yaml, graph/, kg.db
    python3 kg/compile.py --strict              # cardinality violations become errors

The validation is the point. An extraction that invents a type, points an edge the wrong
way round, or leaves an edge dangling will answer questions confidently and wrongly — and
a graph is far better at hiding that than a document is, because nothing looks odd about a
tidy row. The ontology is the contract; this is where it gets enforced.

Nothing here is clever. It is a few hundred rows in SQLite, which is the right size for
almost every knowledge graph anybody actually needs.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys

SCHEMA = """
CREATE TABLE nodes (
    id       TEXT PRIMARY KEY,
    type     TEXT NOT NULL,
    label    TEXT,
    props    TEXT,              -- JSON
    source   TEXT               -- where the fact came from. Never optional in practice.
);
CREATE TABLE edges (
    src        TEXT NOT NULL,
    rel        TEXT NOT NULL,
    dst        TEXT NOT NULL,
    valid_from TEXT,            -- NULL = as far back as we know
    valid_to   TEXT,            -- NULL = still true
    source     TEXT
);
CREATE INDEX edges_src ON edges (src, rel);
CREATE INDEX edges_dst ON edges (dst, rel);
CREATE INDEX nodes_type ON nodes (type);
"""


def project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def load_ontology(path: str) -> dict:
    try:
        import yaml
    except ImportError:
        sys.exit("pyyaml is not installed for this interpreter.\n"
                 "Module 3's setup step installs it: pip install pyyaml")
    with open(path) as fh:
        data = yaml.safe_load(fh) or {}
    if not data.get("types") or not data.get("relations"):
        sys.exit(f"{os.path.basename(path)} declares no types or no relations yet")
    return data


def read_jsonl(path: str) -> list[dict]:
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path) as fh:
        for number, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                rows.append(json.loads(line))
            except ValueError as exc:
                sys.exit(f"{os.path.basename(path)} line {number}: {exc}")
    return rows


def validate(ontology: dict, nodes: list[dict], edges: list[dict]) -> tuple[list, list]:
    """Everything the ontology promises, checked. Errors block; warnings do not."""
    errors: list[str] = []
    warnings: list[str] = []

    types = set(ontology["types"])
    relations = {r["name"]: r for r in ontology["relations"]}

    by_id: dict[str, dict] = {}
    for node in nodes:
        nid = node.get("id")
        if not nid:
            errors.append(f"a node has no id: {json.dumps(node)[:90]}")
            continue
        if nid in by_id:
            # Two rows claiming the same identity is the entity-resolution failure, and it
            # is silent: the second simply wins and takes the first one's edges with it.
            errors.append(f"duplicate node id {nid!r} — two things claim one identity")
        if node.get("type") not in types:
            errors.append(f"{nid}: type {node.get('type')!r} is not in the ontology")
        if not node.get("source"):
            warnings.append(f"{nid}: no source recorded — the answer will not be traceable")
        by_id[nid] = node

    seen_many_to_one: dict[tuple, str] = {}
    for edge in edges:
        src, rel, dst = edge.get("src"), edge.get("rel"), edge.get("dst")
        spec = relations.get(rel)
        if spec is None:
            errors.append(f"{src} -{rel}-> {dst}: relation {rel!r} is not in the ontology")
            continue
        if src not in by_id:
            errors.append(f"{rel}: source node {src!r} does not exist (dangling edge)")
            continue
        if dst not in by_id:
            errors.append(f"{rel}: target node {dst!r} does not exist (dangling edge)")
            continue
        actual_from, actual_to = by_id[src].get("type"), by_id[dst].get("type")
        if actual_from != spec["from"] or actual_to != spec["to"]:
            errors.append(
                f"{src} -{rel}-> {dst}: the ontology says "
                f"{spec['from']} -> {spec['to']}, this edge is {actual_from} -> "
                f"{actual_to}. Check the direction before you change the ontology")
        if spec.get("temporal") and not edge.get("valid_from"):
            warnings.append(f"{src} -{rel}-> {dst}: {rel} is temporal but has no "
                            f"valid_from, so an as-of query cannot place it")
        if not spec.get("temporal") and (edge.get("valid_from") or edge.get("valid_to")):
            warnings.append(f"{src} -{rel}-> {dst}: carries dates but {rel} is not "
                            f"declared temporal — one of the two is wrong")
        if spec.get("cardinality") in ("many-to-one", "one-to-one"):
            key = (src, rel)
            if key in seen_many_to_one and seen_many_to_one[key] != dst:
                warnings.append(
                    f"{src} has two {rel} edges ({seen_many_to_one[key]}, {dst}) but the "
                    f"ontology says {spec['cardinality']}")
            seen_many_to_one[key] = dst

    declared = set(relations)
    used = {e.get("rel") for e in edges}
    for unused in sorted(declared - used):
        warnings.append(f"relation {unused!r} is declared but never used — either the "
                        f"extraction missed it or the ontology does not need it")
    for empty in sorted(types - {n.get("type") for n in nodes}):
        warnings.append(f"type {empty!r} has no instances")
    return errors, warnings


def fail(message: str, as_json: bool) -> int:
    """Exit reporting a problem in whatever format the caller asked for.

    A gate that asked for --json and got a bare sentence on stderr parses an empty object
    and concludes there was nothing wrong — which is how a workspace with no graph at all
    passed the graph check.
    """
    if as_json:
        print(json.dumps({"ok": False, "errors": [message], "warnings": [],
                          "nodes": 0, "edges": 0}, indent=2))
    else:
        print(message, file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--ontology", default=None)
    ap.add_argument("--graph", default="graph")
    ap.add_argument("--out", default="kg.db")
    ap.add_argument("--strict", action="store_true",
                    help="treat warnings as errors")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    root = os.path.abspath(args.root or project_root())

    ontology_path = args.ontology
    if not ontology_path:
        folder = os.path.join(root, "ontology")
        candidates = sorted(f for f in os.listdir(folder)
                            if f.endswith((".yaml", ".yml"))) if os.path.isdir(folder) else []
        if not candidates:
            return fail("no ontology/*.yaml found — step 3.1 comes before this",
                        args.as_json)
        ontology_path = os.path.join(folder, candidates[0])
    elif not os.path.isabs(ontology_path):
        ontology_path = os.path.join(root, ontology_path)

    try:
        ontology = load_ontology(ontology_path)
    except SystemExit as exc:
        return fail(str(exc), args.as_json)
    nodes = read_jsonl(os.path.join(root, args.graph, "nodes.jsonl"))
    edges = read_jsonl(os.path.join(root, args.graph, "edges.jsonl"))
    if not nodes:
        return fail(f"no nodes in {args.graph}/nodes.jsonl — extract the graph first",
                    args.as_json)

    errors, warnings = validate(ontology, nodes, edges)
    if errors or (args.strict and warnings):
        payload = {"ok": False, "errors": errors, "warnings": warnings,
                   "nodes": len(nodes), "edges": len(edges)}
        if args.as_json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"NOT COMPILED — {len(errors)} error(s)\n")
            for item in errors:
                print(f"  x {item}")
            for item in warnings:
                print(f"  ! {item}")
        return 1

    db_path = os.path.join(root, args.out)
    if os.path.exists(db_path):
        os.remove(db_path)                 # a recompile replaces; it never merges
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO nodes VALUES (?,?,?,?,?)",
                    [(n["id"], n["type"], n.get("label"),
                      json.dumps(n.get("props") or {}), n.get("source")) for n in nodes])
    con.executemany("INSERT INTO edges VALUES (?,?,?,?,?,?)",
                    [(e["src"], e["rel"], e["dst"], e.get("valid_from"),
                      e.get("valid_to"), e.get("source")) for e in edges])
    con.commit()
    counts = {t: n for t, n in con.execute(
        "SELECT type, count(*) FROM nodes GROUP BY type ORDER BY 1")}
    rels = {r: n for r, n in con.execute(
        "SELECT rel, count(*) FROM edges GROUP BY rel ORDER BY 1")}
    con.close()

    payload = {"ok": True, "db": os.path.relpath(db_path, root),
               "nodes": len(nodes), "edges": len(edges),
               "by_type": counts, "by_relation": rels, "warnings": warnings}
    if args.as_json:
        print(json.dumps(payload, indent=2))
        return 0
    print(f"COMPILED {os.path.relpath(db_path, root)} — "
          f"{len(nodes)} nodes, {len(edges)} edges")
    print("\n  " + "  ".join(f"{t}:{n}" for t, n in counts.items()))
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for item in warnings:
            print(f"  ! {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
