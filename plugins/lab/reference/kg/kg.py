#!/usr/bin/env python3
"""Query kg.db. The primitives the graph tools and the answering skill are both built on.

    python3 kg/kg.py entity KI-77
    python3 kg/kg.py neighbors acc-1042 --rel on_plan
    python3 kg/kg.py reach KI-77 --path scoped_to_region,<in_region
    python3 kg/kg.py coverage Ticket --missing escalated_to
    python3 kg/kg.py as-of plan:Growth includes_feature --date 2026-04-15

Seven operations, and each one exists because a question shape needs it. They are
deliberately generic: a traversal is described by the relations it follows, so the same
code answers "which accounts are exposed to this defect" and "which projects depend on
this one" without knowing anything about defects or projects.

A relation prefixed with `<` is traversed backwards. `Defect -scoped_to_region-> Region`
and `Account -in_region-> Region` both point AT the region, so getting from a defect to the
accounts in its scope means going forwards then backwards: `scoped_to_region,<in_region`.
That asymmetry is not a wart — it is what edge direction means, and reading a path aloud is
how you catch a modelling mistake.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys

DB_NAME = "kg.db"


def project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def connect(root: str | None = None) -> sqlite3.Connection:
    path = os.path.join(root or project_root(), DB_NAME)
    if not os.path.exists(path):
        raise SystemExit(f"no {DB_NAME} — compile the graph first: python3 kg/compile.py")
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def _node(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "type": row["type"], "label": row["label"],
            "props": json.loads(row["props"] or "{}"), "source": row["source"]}


def _valid(clause_alias: str = "e") -> str:
    """An edge is in force at :as_of when it started by then and has not ended.

    NULL valid_from means "as far back as we know", NULL valid_to means "still true". Both
    have to pass through, or every undated edge disappears from an as-of query — which is
    the most common way a temporal graph starts returning nothing.
    """
    return (f"(:as_of IS NULL OR (({clause_alias}.valid_from IS NULL "
            f"OR {clause_alias}.valid_from <= :as_of) AND ({clause_alias}.valid_to IS NULL "
            f"OR {clause_alias}.valid_to > :as_of)))")


# ---------------------------------------------------------------- the operations

def search(con, text: str, limit: int = 10) -> list[dict]:
    """Find nodes by name. The entry point: an agent has words, not identifiers."""
    like = f"%{text.lower()}%"
    rows = con.execute(
        "SELECT * FROM nodes WHERE lower(label) LIKE :like OR lower(id) LIKE :like "
        "ORDER BY length(label) LIMIT :limit", {"like": like, "limit": limit})
    return [_node(r) for r in rows]


def entity(con, node_id: str, as_of: str | None = None) -> dict:
    """One node, its properties, its provenance, and every edge touching it."""
    row = con.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
    if row is None:
        raise KeyError(node_id)
    out = _node(row)
    out["out_edges"] = [
        {"rel": r["rel"], "to": r["dst"], "label": r["label"], "type": r["type"],
         "valid_from": r["valid_from"], "valid_to": r["valid_to"], "source": r["source"]}
        for r in con.execute(
            f"SELECT e.*, n.label, n.type FROM edges e JOIN nodes n ON n.id = e.dst "
            f"WHERE e.src = :id AND {_valid()} ORDER BY e.rel, e.dst",
            {"id": node_id, "as_of": as_of})]
    out["in_edges"] = [
        {"rel": r["rel"], "from": r["src"], "label": r["label"], "type": r["type"],
         "valid_from": r["valid_from"], "valid_to": r["valid_to"], "source": r["source"]}
        for r in con.execute(
            f"SELECT e.*, n.label, n.type FROM edges e JOIN nodes n ON n.id = e.src "
            f"WHERE e.dst = :id AND {_valid()} ORDER BY e.rel, e.src",
            {"id": node_id, "as_of": as_of})]
    return out


def neighbors(con, node_id: str, rel: str | None = None, direction: str = "out",
              as_of: str | None = None) -> list[dict]:
    """One hop. `direction` is out, in, or both."""
    results, seen = [], set()
    specs = [("out", "src", "dst")] if direction == "out" else \
            [("in", "dst", "src")] if direction == "in" else \
            [("out", "src", "dst"), ("in", "dst", "src")]
    for label, from_col, to_col in specs:
        sql = (f"SELECT e.rel, n.* FROM edges e JOIN nodes n ON n.id = e.{to_col} "
               f"WHERE e.{from_col} = :id AND {_valid()}")
        params = {"id": node_id, "as_of": as_of}
        if rel:
            sql += " AND e.rel = :rel"
            params["rel"] = rel
        for row in con.execute(sql + " ORDER BY e.rel, n.id", params):
            key = (label, row["rel"], row["id"])
            if key in seen:
                continue
            seen.add(key)
            item = _node(row)
            item["via"] = ("" if label == "out" else "<") + row["rel"]
            results.append(item)
    return results


def reach(con, start: str, path: list[str], as_of: str | None = None) -> list[dict]:
    """Follow a relation path from one node and return where you land.

    This is the multi-hop operation, and the reason similarity search cannot do this job:
    each step is exact, and the set you end with is complete rather than top-k.
    """
    frontier = {start}
    trail: list[dict] = []
    for step in path:
        backwards = step.startswith("<")
        rel = step.lstrip("<")
        from_col, to_col = ("dst", "src") if backwards else ("src", "dst")
        placeholders = ",".join("?" * len(frontier))
        sql = (f"SELECT DISTINCT e.{to_col} AS id FROM edges e "
               f"WHERE e.rel = ? AND e.{from_col} IN ({placeholders}) "
               f"AND (? IS NULL OR ((e.valid_from IS NULL OR e.valid_from <= ?) "
               f"AND (e.valid_to IS NULL OR e.valid_to > ?)))")
        args = [rel, *sorted(frontier), as_of, as_of, as_of]
        frontier = {r["id"] for r in con.execute(sql, args)}
        trail.append({"step": step, "landed_on": len(frontier)})
        if not frontier:
            break
    if not frontier:
        return []
    placeholders = ",".join("?" * len(frontier))
    rows = con.execute(f"SELECT * FROM nodes WHERE id IN ({placeholders}) ORDER BY id",
                       sorted(frontier))
    return [_node(r) for r in rows]


def paths(con, src: str, dst: str, max_hops: int = 4) -> list[list[str]]:
    """Every shortest chain of relations connecting two nodes, direction-agnostic.

    Used to answer "how are these two things related at all", which is often the question
    behind "why did this happen".
    """
    if src == dst:
        return [[src]]
    frontier: list[list[str]] = [[src]]
    visited = {src}
    for _hop in range(max_hops):
        found: list[list[str]] = []
        nxt: list[list[str]] = []
        for chain in frontier:
            tail = chain[-1]
            for row in con.execute(
                    "SELECT dst AS id, rel FROM edges WHERE src = ? "
                    "UNION SELECT src AS id, rel FROM edges WHERE dst = ?", (tail, tail)):
                nid = row["id"]
                if nid == dst:
                    found.append(chain + [f"-{row['rel']}-", nid])
                elif nid not in visited:
                    nxt.append(chain + [f"-{row['rel']}-", nid])
        if found:
            return found
        visited |= {c[-1] for c in nxt}
        frontier = nxt
        if not frontier:
            break
    return []


def coverage(con, node_type: str, missing_rel: str, direction: str = "out",
             as_of: str | None = None) -> list[dict]:
    """Nodes of a type with NO edge of a given relation. The completeness operation.

    This is the shape top-k retrieval cannot express at all. "Which requirements has
    nobody verified" is a question about absence, and a similarity search has no way to
    return the things it did not find.
    """
    col = "src" if direction == "out" else "dst"
    sql = (f"SELECT n.* FROM nodes n WHERE n.type = :type AND NOT EXISTS ("
           f"  SELECT 1 FROM edges e WHERE e.{col} = n.id AND e.rel = :rel AND {_valid()}"
           f") ORDER BY n.id")
    rows = con.execute(sql, {"type": node_type, "rel": missing_rel, "as_of": as_of})
    return [_node(r) for r in rows]


def as_of(con, node_id: str, rel: str, date: str | None = None) -> list[dict]:
    """What a temporal relation said on a particular date.

    Run it twice with two dates and the difference is the answer to "what changed".
    """
    rows = con.execute(
        f"SELECT e.*, n.label, n.type FROM edges e JOIN nodes n ON n.id = e.dst "
        f"WHERE e.src = :id AND e.rel = :rel AND {_valid()} ORDER BY n.id",
        {"id": node_id, "rel": rel, "as_of": date})
    return [{"to": r["dst"], "label": r["label"], "valid_from": r["valid_from"],
             "valid_to": r["valid_to"], "source": r["source"]} for r in rows]


OPERATIONS = ("search", "entity", "neighbors", "reach", "paths", "coverage", "as-of")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("op", choices=OPERATIONS)
    ap.add_argument("args", nargs="*")
    ap.add_argument("--root", default=None)
    ap.add_argument("--rel", default=None)
    ap.add_argument("--path", default=None, help="comma-separated relations, < to reverse")
    ap.add_argument("--missing", default=None)
    ap.add_argument("--direction", default="out", choices=("out", "in", "both"))
    ap.add_argument("--date", default=None)
    ap.add_argument("--max-hops", type=int, default=4)
    args = ap.parse_args()
    con = connect(args.root)

    try:
        if args.op == "search":
            out = search(con, " ".join(args.args))
        elif args.op == "entity":
            out = entity(con, args.args[0], args.date)
        elif args.op == "neighbors":
            out = neighbors(con, args.args[0], args.rel, args.direction, args.date)
        elif args.op == "reach":
            if not args.path:
                sys.exit("reach needs --path, e.g. --path scoped_to_region,<in_region")
            out = reach(con, args.args[0], args.path.split(","), args.date)
        elif args.op == "paths":
            out = paths(con, args.args[0], args.args[1], args.max_hops)
        elif args.op == "coverage":
            if not args.missing:
                sys.exit("coverage needs --missing <relation>")
            out = coverage(con, args.args[0], args.missing, args.direction, args.date)
        else:
            out = as_of(con, args.args[0], args.args[1], args.date)
    except KeyError as exc:
        sys.exit(f"no such node: {exc}")
    except IndexError:
        sys.exit(f"{args.op} needs more arguments — see --help")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
