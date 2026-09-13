#!/usr/bin/env python3
"""Build the verified graph for docgen — the answer key participants compare against.

No database on this track either. Every fact was read out of a charter, a minute, a register
or a status update, and the file is recorded next to the fact. The interesting property of
this corpus is how *scattered* it is: the complete set of milestone slips exists in three
different monthly files, and the two Atlas dependencies are stated in two different document
kinds, neither of them a status update.

    python3 build_reference_graph.py            # writes ../reference/graph/
    python3 build_reference_graph.py --check    # fails if the committed files are stale
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)
CORPUS = os.path.join(TRACK, "workspace")
OUT = os.path.join(TRACK, "reference", "graph")

CHARTERS = "data/sources/charters/"
CRS = "data/sources/registers/change-requests.md"
RISKS = "data/sources/registers/risk-register.md"
MIN_JUL = "data/sources/minutes/steering-2026-07-16.md"

PEOPLE = {
    "priya": "Priya Raghunathan", "tomas": "Tomas Lindqvist",
    "lena": "Lena Okonkwo", "dana": "Dana Whitfield",
    "marcus": "Marcus Bell", "fen": "Fen Alvarez",
    "unassigned": "unassigned",
}

PROJECTS = {
    "atlas": {"name": "Atlas Migration", "owner": "priya", "status": "complete",
              "entered": None, "source": f"{CHARTERS}atlas-charter.md"},
    "beacon": {"name": "Beacon Rollout", "owner": "tomas", "status": "complete",
               "entered": None, "source": "data/sources/status-updates-2026-06.md"},
    "cirrus": {"name": "Cirrus API Integration", "owner": "lena", "status": "at risk",
               "entered": None, "source": f"{CHARTERS}cirrus-charter.md"},
    "observability": {"name": "Observability Programme", "owner": "dana",
                      "status": "not started", "entered": None,
                      "source": "data/sources/status-updates-2026-06.md"},
    "halo": {"name": "Halo Reporting", "owner": "marcus", "status": "in progress",
             "entered": "2026-07-02", "source": f"{CHARTERS}halo-charter.md"},
}

# The multi-hop answer, and neither of these is in any status update.
DEPENDENCIES = [
    ("cirrus", "atlas", f"{CHARTERS}cirrus-charter.md"),
    ("halo", "atlas", MIN_JUL),
]

# (id, project, name, due, delivered, slipped, moved_from, moved_to, reported_in, source)
MILESTONES = [
    ("ms:atlas-cutover", "atlas", "Atlas schema cutover", "2026-08-12", "2026-08-11",
     True, "2026-08-05", "2026-08-12", "2026-07",
     "data/sources/status-updates-2026-07.md"),
    ("ms:beacon-10", "beacon", "Beacon 10% traffic", "2026-06-24", "2026-06-24",
     False, None, None, "2026-06", "data/sources/status-updates-2026-06.md"),
    ("ms:beacon-30", "beacon", "Beacon 30% traffic", "2026-07-28", "2026-07-26",
     False, None, None, "2026-07", "data/sources/status-updates-2026-07.md"),
    ("ms:beacon-100", "beacon", "Beacon 100% traffic", "2026-08-22", "2026-08-22",
     False, None, None, "2026-08", "data/sources/status-updates-2026-08.md"),
    ("ms:cirrus-signoff", "cirrus", "Cirrus design sign-off", "2026-07-22", "2026-07-22",
     False, None, None, "2026-07", "data/sources/status-updates-2026-07.md"),
    ("ms:cirrus-live", "cirrus", "Cirrus integration live", "2026-09-30", None,
     True, "2026-09-15", "2026-09-30", "2026-08",
     "data/sources/status-updates-2026-08.md"),
    ("ms:observability-scoping", "observability", "Observability scoping", "2026-09-30",
     None, True, "2026-06-30", "2026-09-30", "2026-07", MIN_JUL),
    ("ms:halo-discovery", "halo", "Halo discovery", "2026-07-31", "2026-07-29",
     False, None, None, "2026-07", "data/sources/status-updates-2026-07.md"),
    ("ms:halo-build", "halo", "Halo build", "2026-09-12", None,
     False, None, None, "2026-08", "data/sources/status-updates-2026-08.md"),
]

# Both versions live in one file, which is why the flag has to hang off the version.
CHARTER_VERSIONS = [
    ("charter:atlas-v1", "atlas", "Atlas charter version 1", "2026-02-10", "2026-05-14"),
    ("charter:atlas-v2", "atlas", "Atlas charter version 2", "2026-05-14", None),
]

SCOPE = {
    "scope:ledger-schema": "Ledger schema migration to the new model",
    "scope:backfill": "Backfill of all historical ledger records",
    "scope:cutover": "Cutover of the payments write path",
    "scope:decommission": "Decommissioning of the legacy schema after a 30-day hold",
    "scope:reporting-views": "Reporting views migration, including the monthly finance extracts",
}
IN_SCOPE = {
    "charter:atlas-v1": ["scope:ledger-schema", "scope:backfill", "scope:cutover",
                         "scope:decommission", "scope:reporting-views"],
    "charter:atlas-v2": ["scope:ledger-schema", "scope:backfill", "scope:cutover",
                         "scope:decommission"],
}

CHANGE_REQUESTS = [
    ("CR-11", "Extend Cirrus API scope to include refunds", "lena", "2026-07-08",
     "2026-07-16", "rejected", ["cirrus"], None, []),
    ("CR-12", "Add the monthly finance reporting capability as its own project", "fen",
     "2026-06-25", "2026-07-02", "approved", ["atlas"], "halo", []),
    ("CR-13", "Move Cirrus API go-live from 2026-09-15 to 2026-09-30", "lena",
     "2026-08-19", "2026-08-26", "approved", ["cirrus"], None, ["ms:cirrus-live"]),
]

RISK_ROWS = [
    ("R-01", "Rollback impossible once the Atlas backfill completes", "atlas", "priya",
     "High", "2026-06-03", "2026-08-11"),
    ("R-02", "Beacon security review has no committed date", "beacon", "tomas",
     "High", "2026-06-10", "2026-07-18"),
    ("R-03", "Cirrus vendor sustains 120 req/min against a design assumption of 500",
     "cirrus", "lena", "Medium", "2026-07-15", None),
    ("R-04", "Observability Programme has no owner", "observability", "dana",
     "Medium", "2026-06-17", None),
    ("R-05", "Reporting DB replica lag", "observability", "dana", "Low",
     "2026-05-20", "2026-06-20"),
    ("R-06", "Halo scope not agreed with finance", "halo", "marcus", "Medium",
     "2026-08-05", None),
]


def build() -> tuple[list[dict], list[dict]]:
    nodes: list[dict] = []
    edges: list[dict] = []

    def node(nid, ntype, label, props=None, source=""):
        nodes.append({"id": nid, "type": ntype, "label": label,
                      "props": props or {}, "source": source})

    def edge(src, rel, dst, source="", valid_from=None, valid_to=None):
        edges.append({"src": src, "rel": rel, "dst": dst,
                      "valid_from": valid_from, "valid_to": valid_to, "source": source})

    for pid, name in PEOPLE.items():
        node(f"person:{pid}", "Person", name, {}, "data/sources/")

    for pid, meta in PROJECTS.items():
        node(f"project:{pid}", "Project", meta["name"],
             {"status": meta["status"], "entered_programme": meta["entered"]},
             meta["source"])
        edge(f"project:{pid}", "owned_by", f"person:{meta['owner']}", meta["source"])

    for src, dst, source in DEPENDENCIES:
        edge(f"project:{src}", "depends_on", f"project:{dst}", source)

    for (mid, project, name, due, delivered, slipped, moved_from, moved_to,
         reported_in, source) in MILESTONES:
        node(mid, "Milestone", name, {
            "due": due, "delivered": delivered, "slipped": slipped,
            "moved_from": moved_from, "moved_to": moved_to,
            "reported_in": reported_in}, source)
        edge(f"project:{project}", "has_milestone", mid, source)

    for vid, project, name, effective, superseded in CHARTER_VERSIONS:
        node(vid, "CharterVersion", name,
             {"effective": effective, "superseded_on": superseded},
             f"{CHARTERS}atlas-charter.md")
        edge(f"project:{project}", "has_version", vid, f"{CHARTERS}atlas-charter.md",
             valid_from=effective, valid_to=superseded)

    for sid, textual in SCOPE.items():
        node(sid, "ScopeItem", textual, {}, f"{CHARTERS}atlas-charter.md")
    for version, items in IN_SCOPE.items():
        for item in items:
            edge(version, "in_scope", item, f"{CHARTERS}atlas-charter.md")

    for (cid, request, raiser, raised, decided, outcome, affects, establishes,
         moves) in CHANGE_REQUESTS:
        node(cid, "ChangeRequest", request,
             {"raised": raised, "decided": decided, "outcome": outcome}, CRS)
        edge(cid, "raised_by", f"person:{raiser}", CRS)
        for project in affects:
            edge(cid, "affects", f"project:{project}", CRS)
        if establishes:
            edge(cid, "establishes", f"project:{establishes}", CRS)
        for milestone in moves:
            edge(cid, "moved", milestone, CRS)

    for rid, textual, project, owner, severity, opened, closed in RISK_ROWS:
        node(rid, "Risk", textual,
             {"severity": severity, "opened": opened, "closed": closed}, RISKS)
        edge(rid, "risk_against", f"project:{project}", RISKS)
        edge(rid, "risk_owned_by", f"person:{owner}", RISKS)

    # ---------------------------------------------------------------- guards
    corpus = ""
    for dirpath, _dirs, names in os.walk(os.path.join(CORPUS, "data")):
        for name in sorted(names):
            if name.endswith(".md"):
                corpus += open(os.path.join(dirpath, name), encoding="utf-8",
                               errors="replace").read()

    for name in PEOPLE.values():
        if name != "unassigned" and name not in corpus:
            sys.exit(f"person {name!r} is in the fact table but not in the corpus")
    for meta in PROJECTS.values():
        if meta["name"] not in corpus:
            sys.exit(f"project {meta['name']!r} is not in the corpus")
    for cid, *_ in CHANGE_REQUESTS:
        if cid not in corpus:
            sys.exit(f"{cid} is in the fact table but not in the corpus")
    for rid, *_ in RISK_ROWS:
        if rid not in corpus:
            sys.exit(f"{rid} is in the fact table but not in the corpus")
    found_crs = set(re.findall(r"\bCR-\d\d\b", corpus))
    missing = sorted(found_crs - {c[0] for c in CHANGE_REQUESTS})
    if missing:
        sys.exit(f"the corpus names change requests the fact table does not: "
                 f"{', '.join(missing)}")
    found_risks = set(re.findall(r"\bR-0\d\b", corpus))
    missing = sorted(found_risks - {r[0] for r in RISK_ROWS})
    if missing:
        sys.exit(f"the corpus names risks the fact table does not: {', '.join(missing)}")
    slipped = [m[0] for m in MILESTONES if m[5]]
    if len(slipped) != 3:
        sys.exit(f"the corpus states there are exactly three milestone slips; the fact "
                 f"table has {len(slipped)}: {', '.join(slipped)}")
    return nodes, edges


def dump(rows: list[dict]) -> str:
    return "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    nodes, edges = build()
    os.makedirs(OUT, exist_ok=True)
    stale = []
    for name, body in {"nodes.jsonl": dump(nodes), "edges.jsonl": dump(edges)}.items():
        path = os.path.join(OUT, name)
        if args.check:
            if (open(path).read() if os.path.exists(path) else "") != body:
                stale.append(name)
        else:
            open(path, "w").write(body)
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
