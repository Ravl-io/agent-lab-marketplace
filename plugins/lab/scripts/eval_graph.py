#!/usr/bin/env python3
"""Score a knowledge graph against the questions it was built to answer.

Module 2's harness asks "was the answering phrase in the retrieved text". That cannot judge
"which requirements has nobody verified" — the answer is a SET, and the way it fails is
incompleteness. Returning four of five slipped milestones is not a near miss you can spot by
reading; it is a wrong answer that looks complete. So this scores sets, and reports precision
and recall separately.

    eval_graph.py                        score kg.db against evals/graph/queries.jsonl
    eval_graph.py --json                 machine-readable
    eval_graph.py --no-record            do not touch the scoreboard

Each query names the traversal that should answer it, so this measures the GRAPH — whether
the facts and edges are there — not the agent's phrasing. That is the same separation Module
2 kept: measure the artifact, then judge the agent against it.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone

SHAPES = ("multi-hop", "aggregation", "temporal")


def load_kg(root: str):
    """Import the participant's own kg/kg.py — the primitives are theirs, not ours."""
    path = os.path.join(root, "kg", "kg.py")
    if not os.path.exists(path):
        sys.exit("no kg/kg.py — this module's query primitives come first")
    spec = importlib.util.spec_from_file_location("participant_kg", path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(path))
    spec.loader.exec_module(module)
    return module


def read_jsonl(path: str) -> list[dict]:
    rows = []
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


def compare(value, operator: str, target) -> bool:
    if operator == "eq":
        return value == target
    if operator == "ne":
        return value != target
    if value is None:
        return False
    try:
        if operator == "lt":
            return value < target
        if operator == "lte":
            return value <= target
        if operator == "gt":
            return value > target
        if operator == "gte":
            return value >= target
    except TypeError:
        return False
    raise ValueError(f"unknown filter operator {operator!r}")


def apply_filter(nodes: list[dict], spec: dict | None) -> list[dict]:
    if not spec:
        return nodes
    prop, operator, target = spec["prop"], spec.get("op", "eq"), spec.get("value")
    out = []
    for node in nodes:
        value = node.get("props", {}).get(prop, node.get(prop))
        if compare(value, operator, target):
            out.append(node)
    return out


def run_op(kg, con, op: dict) -> list[str]:
    """Execute one declared traversal and return the ids it lands on."""
    kind = op.get("kind")
    if kind == "reach":
        nodes = kg.reach(con, op["start"], op["path"], op.get("as_of"))
    elif kind == "nodes":
        rows = con.execute("SELECT * FROM nodes WHERE type = ? ORDER BY id", (op["type"],))
        nodes = [{"id": r["id"], "label": r["label"],
                  "props": json.loads(r["props"] or "{}")} for r in rows]
        if op.get("has_rel"):
            keep = {r[0] for r in con.execute(
                "SELECT DISTINCT src FROM edges WHERE rel = ?", (op["has_rel"],))}
            nodes = [n for n in nodes if n["id"] in keep]
        if op.get("missing_rel"):
            drop = {r[0] for r in con.execute(
                "SELECT DISTINCT src FROM edges WHERE rel = ?", (op["missing_rel"],))}
            nodes = [n for n in nodes if n["id"] not in drop]
    elif kind == "coverage":
        nodes = kg.coverage(con, op["type"], op["missing_rel"],
                            op.get("direction", "out"), op.get("as_of"))
    else:
        raise ValueError(f"unknown op kind {kind!r}")

    nodes = apply_filter(nodes, op.get("filter"))
    ids = {n["id"] for n in nodes}

    # `then` continues from the filtered set. "How many milestones slipped, and who owns
    # them" is one question with two halves: select the set, then hop to the owners. Without
    # this the second half is unmeasurable, and half a measured question is how a metric
    # starts drifting from what people actually asked.
    if op.get("then"):
        landed: set[str] = set()
        for start in sorted(ids):
            landed |= {n["id"] for n in kg.reach(con, start, list(op["then"]),
                                                 op.get("as_of"))}
        ids = landed

    if op.get("exclude"):
        ids -= set(run_op(kg, con, op["exclude"]))
    return sorted(ids)


def score(expected: list[str], got: list[str]) -> dict:
    want, have = set(expected), set(got)
    hit = want & have
    return {
        "exact": want == have,
        "precision": round(len(hit) / len(have), 3) if have else (1.0 if not want else 0.0),
        "recall": round(len(hit) / len(want), 3) if want else 1.0,
        "missing": sorted(want - have),
        "extra": sorted(have - want),
    }


def record(root: str, payload: dict) -> None:
    state_file = os.path.join(root, ".agent-lab", "state.json")
    if not os.path.exists(state_file):
        return
    try:
        with open(state_file) as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        return
    head = payload["headline"]
    state.setdefault("graph_history", []).append({
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "label": payload["label"],
        "exact": head["exact"], "queries": head["queries"],
        "precision": head["precision"], "recall": head["recall"],
    })
    tmp = state_file + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, state_file)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--queries", default=None)
    ap.add_argument("--label", default=None)
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--no-record", action="store_true")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    os.environ["CLAUDE_PROJECT_DIR"] = root

    path = args.queries or os.path.join(root, "evals", "graph", "queries.jsonl")
    if not os.path.exists(path):
        sys.exit(f"no graph eval set at {os.path.relpath(path, root)}")
    queries = read_jsonl(path)
    kg = load_kg(root)
    con = kg.connect(root)

    rows = []
    for entry in queries:
        try:
            got = run_op(kg, con, entry["op"])
            error = None
        except Exception as exc:                              # noqa: BLE001
            got, error = [], f"{type(exc).__name__}: {exc}"
        result = score(entry.get("expect") or [], got)
        rows.append({"id": entry["id"], "q": entry["q"], "shape": entry.get("shape"),
                     "expect": entry.get("expect") or [], "got": got,
                     "error": error, **result})

    exact = sum(1 for r in rows if r["exact"])
    headline = {
        "queries": len(rows),
        "exact": exact,
        "precision": round(sum(r["precision"] for r in rows) / len(rows), 3) if rows else 0,
        "recall": round(sum(r["recall"] for r in rows) / len(rows), 3) if rows else 0,
    }
    by_shape = {}
    for shape in SHAPES:
        chosen = [r for r in rows if r["shape"] == shape]
        if chosen:
            by_shape[shape] = {"queries": len(chosen),
                               "exact": sum(1 for r in chosen if r["exact"])}
    payload = {"label": args.label or "graph", "headline": headline,
               "by_shape": by_shape, "queries": rows}

    if not args.no_record:
        record(root, payload)

    if args.as_json:
        print(json.dumps(payload, indent=2))
        return 0 if exact == len(rows) else 1

    title = f"GRAPH — {payload['label']}"
    print(title)
    print("=" * len(title))
    print(f"\n  {exact}/{len(rows)} answered exactly"
          f"   precision {headline['precision']}"
          f"   recall {headline['recall']}\n")
    for shape in SHAPES:
        if shape in by_shape:
            s = by_shape[shape]
            print(f"  {shape:<12} {s['exact']:>3}/{s['queries']}")
    wrong = [r for r in rows if not r["exact"]]
    if wrong:
        print(f"\n  Not answered exactly ({len(wrong)}):")
        for r in wrong:
            print(f"    {r['id']} [{r['shape']}]  {r['q'][:56]}")
            if r["error"]:
                print(f"           the traversal failed: {r['error']}")
            if r["missing"]:
                print(f"           missing: {', '.join(r['missing'])}"
                      f"   <- incomplete, the failure that looks like an answer")
            if r["extra"]:
                print(f"           extra:   {', '.join(r['extra'])}")
    else:
        print("\n  Every question answered exactly — complete sets, no extras.")
    return 0 if exact == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
