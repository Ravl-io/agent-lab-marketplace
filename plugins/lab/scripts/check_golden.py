#!/usr/bin/env python3
"""Validate a golden retrieval set.

The golden set is what every measurement in Module 2 is scored against, so a wrong path in
it silently makes a query unscoreable — the retrieval looks worse than it is and nobody can
tell why. This checks the set against the corpus it claims to point at.

    check_golden.py                    validate ./evals/retrieval/golden.jsonl
    check_golden.py --file <path> --corpus <dir>
    check_golden.py --json

Exit 0 if the set is scoreable. Notes do not fail it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

TIERS = {"easy", "hard", "filtered", "unreachable"}
EXPECT_UNREACHABLE = 3
MIN_QUERIES = 15


def flatten(text: str) -> str:
    """Collapse whitespace and drop markdown emphasis.

    Anchors are phrases from prose, and prose in these documents is hard-wrapped and often
    partly bolded. Matching the raw text reports a miss for a phrase that is plainly there.
    """
    return " ".join(re.sub(r"[*_`]", "", text).split()).lower()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--file", default=None)
    ap.add_argument("--corpus", default=None)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    path = args.file or os.path.join(args.root, "evals", "retrieval", "golden.jsonl")
    corpus = args.corpus or args.root
    problems: list[str] = []
    notes: list[str] = []

    if not os.path.exists(path):
        problems.append(f"no golden set at {os.path.relpath(path, args.root)}")
        report(path, problems, notes, args.as_json)
        return 1

    rows, seen = [], set()
    for number, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:
            problems.append(f"line {number} is not valid JSON: {exc}")
            continue
        for field in ("id", "tier", "q", "expect"):
            if field not in row:
                problems.append(f"line {number} has no '{field}'")
        if row.get("id") in seen:
            problems.append(f"duplicate id {row.get('id')!r}")
        seen.add(row.get("id"))
        rows.append(row)

    if len(rows) < MIN_QUERIES:
        problems.append(f"{len(rows)} queries; the shipped set is {MIN_QUERIES}")

    tiers: dict[str, int] = {}
    for row in rows:
        tier = row.get("tier")
        if tier not in TIERS:
            problems.append(f"{row.get('id')}: tier {tier!r} is not one of "
                            f"{', '.join(sorted(TIERS))}")
        tiers[tier] = tiers.get(tier, 0) + 1

    if tiers.get("unreachable", 0) != EXPECT_UNREACHABLE:
        problems.append(f"{tiers.get('unreachable', 0)} unreachable queries; there should be "
                        f"{EXPECT_UNREACHABLE} — they are what Module 3 opens on")

    # the part that actually bites: every expected source must exist
    for row in rows:
        for rel in row.get("expect") or []:
            if not os.path.exists(os.path.join(corpus, rel)):
                problems.append(f"{row.get('id')}: expects {rel}, which does not exist")
        if not row.get("expect") and row.get("tier") != "unreachable":
            problems.append(f"{row.get('id')}: no expected sources, so it cannot be scored")
        if not row.get("why"):
            notes.append(f"{row.get('id')}: no 'why' — the facilitator cannot tell what it tests")

    # the anchor is what gets scored, so it must genuinely be in one of the expected files
    for row in rows:
        anchor = row.get("anchor")
        if anchor is None:
            if row.get("tier") != "unreachable":
                problems.append(f"{row.get('id')}: no anchor. The scoreboard scores the "
                                f"passage, not the filename — give it a phrase from the text "
                                f"that answers the question")
            continue
        needle = flatten(anchor)
        where = []
        for rel in row.get("expect") or []:
            full = os.path.join(corpus, rel)
            if os.path.exists(full) and needle in flatten(
                    open(full, encoding="utf-8", errors="replace").read()):
                where.append(rel)
        if not where:
            problems.append(f"{row.get('id')}: anchor {anchor!r} is in none of its expected "
                            f"files, so this query can never score")

    # a query nobody could answer from the corpus at all is a broken query, not a hard one
    for row in rows:
        if row.get("tier") == "unreachable" and not row.get("expect"):
            notes.append(f"{row.get('id')}: unreachable with no expected sources — correct "
                         f"only if the answer is genuinely not in any document")

    added = [r for r in rows if str(r.get("id", "")).startswith("H")]
    if added:
        notes.append(f"{len(added)} query(ies) added by the participant: "
                     f"{', '.join(r['id'] for r in added)}")

    report(path, problems, notes, args.as_json, len(rows), tiers)
    return 1 if problems else 0


def report(path, problems, notes, as_json, count=0, tiers=None) -> None:
    if as_json:
        print(json.dumps({"file": path, "ok": not problems, "queries": count,
                          "tiers": tiers or {}, "problems": problems, "notes": notes},
                         indent=2))
        return
    print("GOLDEN SET CHECK")
    print("================")
    if count:
        spread = ", ".join(f"{k} {v}" for k, v in sorted((tiers or {}).items()))
        print(f"\n{count} queries — {spread}")
    if problems:
        print("\nNOT SCOREABLE:")
        for p in problems:
            print(f"  x {p}")
    else:
        print("\nScoreable — every expected source exists.")
    if notes:
        print("\nWorth knowing:")
        for n in notes:
            print(f"  ! {n}")


if __name__ == "__main__":
    sys.exit(main())
