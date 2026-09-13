#!/usr/bin/env python3
"""Build the verified graph for support-triage — the answer key participants compare against.

Kept as a script rather than as two hand-edited files so that a corpus change cannot quietly
leave the reference graph describing a corpus that no longer exists. Run it after any edit to
support.db or known-issues.md, then re-run check_consistency.py.

    python3 build_reference_graph.py            # writes ../reference/graph/
    python3 build_reference_graph.py --check    # fails if the committed files are stale

Every node and edge records where the fact came from. That is not bookkeeping: the whole
argument for this graph is that it joins facts from prose to rows from a database, and an
answer nobody can trace back to a source is not usable in support.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)
CORPUS = os.path.join(TRACK, "workspace")
OUT = os.path.join(TRACK, "reference", "graph")
DB = os.path.join(CORPUS, "data", "db", "support.db")

DB_SRC = "data/db/support.db"
KI_SRC = "data/knowledge/known-issues.md"
REL_SRC = "data/knowledge/release-notes-5.4.md"

# ---------------------------------------------------------------- facts that live in prose
# These are the facts no query of support.db can reach. Each one is a line a human wrote in
# a markdown file, and each is the reason a document-only or database-only system gets
# CQ1 wrong.
#
# Region scope convention: every Defect carries scoped_to_region edges. "All regions" is
# recorded as an edge to each region rather than as no edge at all, so a query never has to
# read absence as meaning. Absence here means "we do not know", which is a different fact.
DEFECT_FACTS = {
    "KI-77": {"features": ["saved_filters"], "regions": ["eu-west"], "source": KI_SRC},
    "KI-81": {"features": ["scheduled_reports"], "regions": ["ALL"], "source": KI_SRC},
    "KI-84": {"features": ["audit_log_search"], "regions": ["ALL"], "source": KI_SRC},
    # Closed historical defects: recorded in the database, not in the current register.
    "KI-62": {"features": ["sso"], "regions": ["ALL"], "source": DB_SRC},
    "KI-70": {"features": ["bulk_export"], "regions": ["ALL"], "source": DB_SRC},
}

# Tickets to the feature they are about. Derived from the subject line, which is prose.
TICKET_FEATURES = {
    "CASE-4123": "saved_filters", "CASE-4180": "saved_filters",
    "CASE-4201": "scheduled_reports", "CASE-4233": "sso",
    "CASE-4256": "standard_reports", "CASE-4288": "bulk_export",
    "CASE-4301": "api_access", "CASE-4344": "sso",
    "CASE-4390": "audit_log_search", "CASE-4412": "standard_reports",
}

VERSIONS = ["5.3.4", "5.4.0", "5.4.1", "5.4.2", "5.4.3"]


def sort_key(version: str) -> str:
    """Zero-padded so 5.4.10 sorts after 5.4.9, which plain string comparison gets wrong."""
    return ".".join(f"{int(part):03d}" for part in version.split("."))


def build() -> tuple[list[dict], list[dict]]:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    nodes: list[dict] = []
    edges: list[dict] = []

    def node(nid, ntype, label, props=None, source=DB_SRC):
        nodes.append({"id": nid, "type": ntype, "label": label,
                      "props": props or {}, "source": source})

    def edge(src, rel, dst, source=DB_SRC, valid_from=None, valid_to=None):
        edges.append({"src": src, "rel": rel, "dst": dst,
                      "valid_from": valid_from, "valid_to": valid_to, "source": source})

    # --- accounts, and the three dimensions CQ1 turns on
    regions, plans, features = set(), set(), set()
    for row in con.execute("SELECT * FROM accounts ORDER BY account_id"):
        node(row["account_id"], "Account", row["name"], {
            "plan": row["plan"], "region": row["region"],
            "platform_version": row["platform_version"],
            "seats": row["seats"], "sso_enabled": bool(row["sso_enabled"]),
        })
        regions.add(row["region"])
        plans.add(row["plan"])
        edge(row["account_id"], "on_plan", f"plan:{row['plan']}")
        edge(row["account_id"], "in_region", f"region:{row['region']}")
        edge(row["account_id"], "runs_version", f"version:{row['platform_version']}")

    for plan in sorted(plans):
        node(f"plan:{plan}", "Plan", plan, source="data/knowledge/plan-entitlements.md")
    for region in sorted(regions):
        node(f"region:{region}", "Region", region)
    for version in VERSIONS:
        node(f"version:{version}", "Version", version,
             {"sort_key": sort_key(version)}, source=REL_SRC)

    # --- entitlements: the temporal relation. A closed row is a fact about the past, and
    #     keeping it is the difference between answering CQ3 and guessing at it.
    for row in con.execute("SELECT * FROM entitlements ORDER BY plan, feature, effective_from"):
        features.add(row["feature"])
        if not row["enabled"]:
            continue
        edge(f"plan:{row['plan']}", "includes_feature", f"feature:{row['feature']}",
             valid_from=row["effective_from"], valid_to=row["effective_to"] or None)

    for feature in sorted(features | {"audit_log_search"}):
        src = DB_SRC if feature != "audit_log_search" else KI_SRC
        node(f"feature:{feature}", "Feature", feature, source=src)

    # --- vendor cases and the defects they track
    for row in con.execute("SELECT * FROM vendor_cases ORDER BY vendor_case_id"):
        node(row["vendor_case_id"], "VendorCase", row["title"], {
            "status": row["status"], "severity": row["severity"],
            "opened_at": row["opened_at"], "resolved_at": row["resolved_at"] or None,
        })
        ki = row["known_issue"]
        facts = DEFECT_FACTS.get(ki, {})
        node(ki, "Defect", row["title"],
             {"status": row["status"], "fix_version": row["fix_version"] or None},
             source=facts.get("source", DB_SRC))
        edge(ki, "tracked_by", row["vendor_case_id"])
        if row["fix_version"]:
            edge(ki, "fixed_in", f"version:{row['fix_version']}",
                 source=facts.get("source", DB_SRC))
        for feature in facts.get("features", []):
            edge(ki, "affects_feature", f"feature:{feature}", source=facts["source"])
        for region in facts.get("regions", []):
            targets = sorted(regions) if region == "ALL" else [region]
            for name in targets:
                edge(ki, "scoped_to_region", f"region:{name}", source=facts["source"])

    # --- tickets
    for row in con.execute("SELECT * FROM case_history ORDER BY case_id"):
        closed = row["closed_at"] or None
        node(row["case_id"], "Ticket", row["subject"], {
            "status": "closed" if closed else "open",
            "classification": row["classification"],
            "opened_at": row["opened_at"], "closed_at": closed,
        })
        edge(row["case_id"], "raised_by", row["account_id"])
        if row["vendor_case"]:
            edge(row["case_id"], "escalated_to", row["vendor_case"])
        feature = TICKET_FEATURES.get(row["case_id"])
        if feature:
            edge(row["case_id"], "about_feature", f"feature:{feature}",
                 source=f"{DB_SRC} :: case_history.subject")

    # A hand-written map that has drifted from the corpus produces a graph that is quietly
    # missing edges — which looks like a modelling choice rather than a mistake. Fail loudly.
    real_cases = {r[0] for r in con.execute("SELECT case_id FROM case_history")}
    unknown = sorted(set(TICKET_FEATURES) - real_cases)
    if unknown:
        sys.exit(f"TICKET_FEATURES names cases that are not in case_history: "
                 f"{', '.join(unknown)}")
    uncovered = sorted(real_cases - set(TICKET_FEATURES))
    if uncovered:
        sys.exit(f"these cases have no feature mapped: {', '.join(uncovered)}")

    real_issues = {r[0] for r in con.execute("SELECT known_issue FROM vendor_cases")}
    stray = sorted(set(DEFECT_FACTS) - real_issues)
    if stray:
        sys.exit(f"DEFECT_FACTS names issues with no vendor case: {', '.join(stray)}")
    missing = sorted(real_issues - set(DEFECT_FACTS))
    if missing:
        sys.exit(f"these known issues have no prose facts recorded: {', '.join(missing)}")

    con.close()
    return nodes, edges


def dump(rows: list[dict]) -> str:
    return "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="fail if the committed graph is stale")
    args = ap.parse_args()
    nodes, edges = build()
    os.makedirs(OUT, exist_ok=True)
    targets = {"nodes.jsonl": dump(nodes), "edges.jsonl": dump(edges)}
    stale = []
    for name, body in targets.items():
        path = os.path.join(OUT, name)
        if args.check:
            current = open(path).read() if os.path.exists(path) else ""
            if current != body:
                stale.append(name)
        else:
            with open(path, "w") as fh:
                fh.write(body)
    if args.check:
        if stale:
            print(f"STALE: {', '.join(stale)} — re-run build_reference_graph.py",
                  file=sys.stderr)
            return 1
        print(f"reference graph is current: {len(nodes)} nodes, {len(edges)} edges")
        return 0
    counts: dict[str, int] = {}
    for n in nodes:
        counts[n["type"]] = counts.get(n["type"], 0) + 1
    rels: dict[str, int] = {}
    for e in edges:
        rels[e["rel"]] = rels.get(e["rel"], 0) + 1
    print(json.dumps({"nodes": len(nodes), "edges": len(edges),
                      "by_type": counts, "by_relation": rels}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
