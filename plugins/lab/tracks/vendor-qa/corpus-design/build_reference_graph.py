#!/usr/bin/env python3
"""Build the verified graph for vendor-qa — the answer key participants compare against.

There is no database on this track. Every fact below was read out of a markdown file, and
the file is recorded next to the fact. That is the whole shape of this track's graph work:
the facts exist, they are just scattered across contracts, a register and findings packs
that were written by different people and never cross-reference each other.

    python3 build_reference_graph.py            # writes ../reference/graph/
    python3 build_reference_graph.py --check    # fails if the committed files are stale

The guards at the bottom matter more here than on a track with a database: a hand-encoded
fact table that has drifted from the corpus produces a graph that is quietly wrong, and
"quietly wrong" is the failure mode this whole module is about.
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

REG = "data/requirements-register.md"
LOG = "data/history/acceptance-log.md"
MSA = "data/contract/MSA-excerpt.md"
AMD = "data/contract/MSA-amendments.md"
F_M1 = "data/history/findings-M1.md"
F_M2 = "data/history/findings-M2.md"

# ---------------------------------------------------------------- milestones
MILESTONES = {
    "M1": {"name": "Authentication", "submitted": "2026-03-06",
           "decision": "accepted", "decided_on": "2026-03-27"},
    "M2": {"name": "Authorise and capture", "submitted": "2026-05-08",
           "decision": "accepted with conditions", "decided_on": "2026-06-02"},
    "M3": {"name": "Refunds, idempotency, rate limits", "submitted": "2026-09-01",
           "decision": "under review", "decided_on": None},
    "M4": {"name": "Webhooks", "submitted": None,
           "decision": "not yet due", "decided_on": None},
}

# ---------------------------------------------------------------- criteria
# Identified by (milestone, ac_id). Three different AC-4s exist and they say different
# things; merging them is the mistake this track's ontology warns about.
CRITERIA = {
    "M1": {"AC-1": "Client credential flow documented, with token issuance",
           "AC-2": "Token lifetime and refresh behaviour documented",
           "AC-3": "Error responses for authentication failure enumerated",
           "AC-4": "Test evidence for each authentication path, with environment and build id"},
    "M2": {"AC-3": "Authorise endpoint documented, including all error responses",
           "AC-4": "Capture endpoint documented, including partial capture",
           "AC-5": "Test evidence for authorise and capture, with environment and build id",
           "AC-6": "No production personal data in any artifact",
           "AC-7": "Error catalogue for the payment path",
           "AC-8": "Backwards compatibility statement against M1"},
    "M3": {"AC-1": "OpenAPI 3.1 spec covering all endpoints, including every error response",
           "AC-2": "Authentication documented, including token lifetime and refresh behaviour",
           "AC-3": "Idempotency documented for all write endpoints",
           "AC-4": "Rate limits stated per endpoint, with the behaviour on exceeding them",
           "AC-5": "Test evidence for every endpoint, stating environment, build id and date",
           "AC-6": "No production personal data anywhere in the deliverable",
           "AC-7": "Error catalogue mapping every error code to a remediation",
           "AC-8": "Backwards compatibility statement against Milestone 2"},
}

# ---------------------------------------------------------------- requirements
# (requirement, text, milestone, verified_by, status). The verified_by column is written
# both qualified and unqualified in the register; unqualified means the SOW under review,
# which is M3. That resolution is declared in the ontology and applied here.
REQUIREMENTS = [
    ("R-01", "Authenticate a client and issue a token", "M1", "AC-1 (M1)", "verified"),
    ("R-02", "Refresh a token without re-authenticating", "M1", "AC-2 (M1)", "verified"),
    ("R-03", "Authorise a payment", "M2", "AC-3 (M2)", "verified"),
    ("R-04", "Capture an authorised payment, including partial capture", "M2",
     "AC-4 (M2)", "verified"),
    ("R-05", "Refund a captured payment", "M3", "AC-5", "pending"),
    ("R-06", "Idempotent retries on all write endpoints", "M3", "AC-3", "pending"),
    ("R-07", "Rate limiting with documented behaviour", "M3", "AC-4", "pending"),
    ("R-08", "Error codes mapped to remediation", "M3", "AC-7", "pending"),
    ("R-09", "No production personal data in artifacts", "M3", "AC-6", "pending"),
    ("R-10", "Backwards compatible with M2 clients", "M3", "AC-8", "pending"),
    ("R-11", "Machine-readable API definition", "M3", None, "no verifying criterion"),
    ("R-12", "Webhook delivery guarantees documented", "M4", None, "not yet due"),
]

# ---------------------------------------------------------------- findings
# criterion is written as in the pack; unqualified resolves to M3.
FINDINGS = [
    ("VQ-M1-001", "M1", 3, "AC-2 (M1)", ["4.1"], "closed", "2026-03-18", "2026-03-25",
     False, ["M1-auth-spec.md"]),
    ("VQ-M1-002", "M1", 2, "AC-4 (M1)", ["4.1", "7.2"], "closed", "2026-03-18",
     "2026-03-26", False, ["M1-test-report.md"]),
    ("VQ-M2-001", "M2", 1, "AC-6", ["6.1", "7.1"], "closed", "2026-05-22", "2026-05-25",
     False, ["M2-test-report.md"]),
    ("VQ-M2-002", "M2", 2, "AC-5 (M2)", ["4.1", "7.2"], "closed", "2026-05-22",
     "2026-05-29", False, ["M2-test-report.md"]),
    ("VQ-M2-003", "M2", 2, "AC-4", ["5.1", "7.2"], "open", "2026-05-22", None,
     True, ["M2-api-spec.md"]),
    ("VQ-M2-004", "M2", 3, "AC-7 (M2)", ["5.1", "7.3"], "closed", "2026-05-22",
     "2026-06-01", False, ["M2-api-spec.md"]),
    ("VQ-M2-005", "M2", 2, "AC-8 (M2)", ["5.1", "7.2"], "closed", "2026-05-22",
     "2026-05-30", False, ["M2-api-spec.md"]),
]

CLAUSES = {
    "4.1": "Deliverables must include test evidence",
    "4.3": "A deliverable rejected twice for the same finding escalates to the steering group",
    "5.1": "The specification must cover all endpoints",
    "5.4": "An API deliverable must include a machine-readable definition",
    "6.1": "No production personal data in any artifact",
    "7.1": "Severity 1 resolution term",
    "7.2": "Severity 2 resolution term",
    "7.3": "Severity 3 resolution term",
}

AMENDMENTS = {
    "A1": {"summary": "Clause 7.2 replaced — Severity 2 resolution 2 days becomes 3",
           "effective": "2026-06-30", "clauses": ["7.2"]},
    "A2": {"summary": "Clause 5.4 inserted — machine-readable API definition required",
           "effective": "2026-08-15", "clauses": ["5.4"]},
}

# The temporal facts. A closed edge is kept, never overwritten: it is the only way to
# answer what a deadline WAS on the day a finding was issued.
TERMS = [
    ("term:7.1-s1", "8 hours", 1, "7.1", "2026-01-15", None),
    ("term:7.2-s2-original", "2 business days", 2, "7.2", "2026-01-15", "2026-06-30"),
    ("term:7.2-s2-amended", "3 business days", 2, "7.2", "2026-06-30", None),
    ("term:7.3-s3", "5 business days", 3, "7.3", "2026-01-15", None),
]

DELIVERABLES = {
    "M1-auth-spec.md": "M1", "M1-test-report.md": "M1",
    "M2-api-spec.md": "M2", "M2-test-report.md": "M2",
    "M3-api-spec.md": "M3", "M3-test-report.md": "M3",
    "M3-integration-guide.md": "M3", "M3-release-notes.md": "M3",
}


def criterion_id(reference: str) -> str:
    """'AC-4 (M2)' -> 'AC-4 (M2)'; 'AC-4' -> 'AC-4 (M3)'. The resolution rule, in one place."""
    match = re.match(r"^(AC-\d+)\s*\((M\d)\)$", reference.strip())
    if match:
        return f"{match.group(1)} ({match.group(2)})"
    return f"{reference.strip()} (M3)"


def build() -> tuple[list[dict], list[dict]]:
    nodes: list[dict] = []
    edges: list[dict] = []

    def node(nid, ntype, label, props=None, source=""):
        nodes.append({"id": nid, "type": ntype, "label": label,
                      "props": props or {}, "source": source})

    def edge(src, rel, dst, source="", valid_from=None, valid_to=None):
        edges.append({"src": src, "rel": rel, "dst": dst,
                      "valid_from": valid_from, "valid_to": valid_to, "source": source})

    for mid, meta in MILESTONES.items():
        node(mid, "Milestone", meta["name"], {
            "submitted": meta["submitted"], "decision": meta["decision"],
            "decided_on": meta["decided_on"]}, LOG)

    for milestone, criteria in CRITERIA.items():
        for ac, text in criteria.items():
            cid = f"{ac} ({milestone})"
            node(cid, "Criterion", text, {"ac_id": ac, "milestone": milestone},
                 f"data/contract/SOW-milestone-{milestone[-1]}.md")
            edge(cid, "belongs_to", milestone,
                 f"data/contract/SOW-milestone-{milestone[-1]}.md")

    for clause, text in CLAUSES.items():
        node(f"clause:{clause}", "Clause", text, {}, MSA)

    for aid, meta in AMENDMENTS.items():
        node(aid, "Amendment", meta["summary"], {"effective": meta["effective"]}, AMD)
        for clause in meta["clauses"]:
            edge(f"clause:{clause}", "changed_by", aid, AMD)

    for tid, value, severity, clause, valid_from, valid_to in TERMS:
        node(tid, "Term", value, {"severity": severity}, AMD)
        edge(f"clause:{clause}", "specifies_term", tid, AMD,
             valid_from=valid_from, valid_to=valid_to)

    for path, milestone in DELIVERABLES.items():
        node(path, "Deliverable", path, {}, f"data/deliverables/{path}")
        edge(path, "submitted_for", milestone, LOG)

    for rid, text, milestone, verified, status in REQUIREMENTS:
        node(rid, "Requirement", text, {"status": status}, REG)
        edge(rid, "required_at", milestone, REG)
        if verified:
            edge(rid, "verified_by", criterion_id(verified), REG)

    for (fid, milestone, severity, criterion, clauses, status, issued, closed,
         disputed, evidence) in FINDINGS:
        pack = F_M1 if milestone == "M1" else F_M2
        node(fid, "Finding", f"{fid} against {criterion}", {
            "severity": severity, "status": status, "issued_on": issued,
            "closed_on": closed, "disputed": disputed}, pack)
        edge(fid, "raised_on", milestone, pack)
        edge(fid, "against_criterion", criterion_id(criterion), pack)
        for clause in clauses:
            edge(fid, "cites_clause", f"clause:{clause}", pack)
        for item in evidence:
            edge(fid, "evidenced_by", item, pack)

    # the one carried finding, and the fact behind the escalation clause
    edge("VQ-M2-003", "carried_into", "M3", LOG)

    # ---------------------------------------------------------------- guards
    corpus_text = ""
    for dirpath, _dirs, names in os.walk(os.path.join(CORPUS, "data")):
        for name in sorted(names):
            if name.endswith(".md"):
                corpus_text += open(os.path.join(dirpath, name),
                                    encoding="utf-8", errors="replace").read()

    for rid, *_ in REQUIREMENTS:
        if rid not in corpus_text:
            sys.exit(f"{rid} is in the fact table but not in the corpus")
    for fid, *_ in FINDINGS:
        if fid not in corpus_text:
            sys.exit(f"{fid} is in the fact table but not in the corpus")
    found_reqs = set(re.findall(r"\bR-\d\d\b", corpus_text))
    missing = sorted(found_reqs - {r[0] for r in REQUIREMENTS})
    if missing:
        sys.exit(f"the corpus names requirements the fact table does not: "
                 f"{', '.join(missing)}")
    found_findings = set(re.findall(r"\bVQ-M\d-\d{3}\b", corpus_text))
    missing = sorted(found_findings - {f[0] for f in FINDINGS})
    if missing:
        sys.exit(f"the corpus names findings the fact table does not: {', '.join(missing)}")
    # every criterion a finding or requirement points at must exist
    known = {f"{ac} ({m})" for m, acs in CRITERIA.items() for ac in acs}
    for rid, _t, _m, verified, _s in REQUIREMENTS:
        if verified and criterion_id(verified) not in known:
            sys.exit(f"{rid} is verified by {criterion_id(verified)}, which no SOW declares")
    for fid, _m, _sev, criterion, *_rest in FINDINGS:
        if criterion_id(criterion) not in known:
            sys.exit(f"{fid} is against {criterion_id(criterion)}, "
                     f"which no SOW declares")
    return nodes, edges


def dump(rows: list[dict]) -> str:
    return "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    nodes, edges = build()
    os.makedirs(OUT, exist_ok=True)
    targets = {"nodes.jsonl": dump(nodes), "edges.jsonl": dump(edges)}
    stale = []
    for name, body in targets.items():
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
