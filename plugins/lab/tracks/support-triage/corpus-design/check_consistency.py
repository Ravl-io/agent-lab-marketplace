#!/usr/bin/env python3
"""Cross-check the support-triage corpus against itself and against the database.

This track has two halves — documents in data/knowledge and facts in support.db — and the
interesting exercises all depend on them agreeing. A knowledge page naming an error code the
platform never emits, or a release note claiming a fix version the vendor case does not, turns
a teaching moment into a wild goose chase.

    python3 corpus-design/check_consistency.py [--verbose]

Stdlib only; sqlite3 ships with Python. Exit 1 on any contradiction.
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "workspace", "data")
DB = os.path.join(DATA, "db", "support.db")

TICKET_ACCOUNTS = {"CASE-4471": "acc-1042", "CASE-4482": "acc-2287",
                   "CASE-4495": "acc-3310", "CASE-4503": "acc-4188"}

problems: list[str] = []
notes: list[str] = []
checked = 0


def ok(cond: bool, label: str, detail: str = "", verbose: bool = False) -> None:
    global checked
    checked += 1
    if cond:
        if verbose:
            print(f"  pass  {label}")
    else:
        problems.append(label + (f" — {detail}" if detail else ""))


def read(rel: str) -> str:
    path = os.path.join(DATA, rel)
    return open(path, encoding="utf-8").read() if os.path.exists(path) else ""


def all_docs() -> dict[str, str]:
    out = {}
    for dirpath, _d, names in os.walk(DATA):
        for n in names:
            if n.endswith(".md"):
                full = os.path.join(dirpath, n)
                out[os.path.relpath(full, DATA)] = open(full, encoding="utf-8").read()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    v = ap.parse_args().verbose

    ok(os.path.exists(DB), "support.db exists", DB, verbose=v)
    if not os.path.exists(DB):
        report()
        return 1
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    q = lambda sql, a=(): [dict(r) for r in con.execute(sql, a)]
    docs = all_docs()

    # 1. every ticket names an account that exists, and the one the fact sheet expects
    accounts = {r["account_id"] for r in q("SELECT account_id FROM accounts")}
    for case, acct in TICKET_ACCOUNTS.items():
        body = read(f"tickets/{case}.md")
        ok(bool(body), f"{case}: ticket exists", verbose=v)
        ok(acct in body, f"{case}: names account {acct}", verbose=v)
        ok(acct in accounts, f"{case}: {acct} exists in the database", verbose=v)

    # 2. every account id mentioned anywhere must be real
    for rel, body in docs.items():
        for acct in sorted(set(re.findall(r"\bacc-\d+\b", body))):
            ok(acct in accounts, f"{rel}: {acct} exists in the database", verbose=v)

    # 3. every error code documented must actually be emitted
    emitted = {r["error_code"] for r in q(
        "SELECT DISTINCT error_code FROM audit_log WHERE error_code IS NOT NULL")}
    documented = set(re.findall(r"`([A-Z][A-Z_]{4,})`", read("knowledge/audit-log-reference.md")))
    documented |= set(re.findall(r"\b(DOMAIN_NOT_REGISTERED|NOT_ENTITLED)\b",
                                " ".join(docs.values())))
    for code in sorted(documented - {"FORBIDDEN", "INVALID_INPUT"}):
        ok(code in emitted, f"error code {code} appears in the audit log",
           "documented but never emitted", verbose=v)
    notes.append("FORBIDDEN and INVALID_INPUT are documented but not exercised by the "
                 "seeded audit log — deliberate, they are the codes participants will not "
                 "find evidence for")

    # 4. every vendor case named in a document must exist, with the same fix version
    cases = {r["vendor_case_id"]: r for r in q("SELECT * FROM vendor_cases")}
    for rel, body in docs.items():
        for ref in sorted(set(re.findall(r"\bVND-\d+\b", body))):
            ok(ref in cases, f"{rel}: {ref} exists in vendor_cases", verbose=v)

    # 5. the regression premise: release notes, vendor case and the account must agree
    notes_doc = read("knowledge/release-notes-5.4.md")
    known = read("knowledge/known-issues.md")
    vnd411 = cases.get("VND-411", {})
    ok(vnd411.get("fix_version") == "5.4.1",
       "VND-411 is recorded as fixed in 5.4.1 in the database",
       str(vnd411.get("fix_version")), verbose=v)
    ok("5.4.1" in notes_doc and "KI-77" in notes_doc,
       "the release notes attribute the KI-77 fix to 5.4.1", verbose=v)
    ok("5.4.1" in known, "the known-issues register names the fix version", verbose=v)
    acc3310 = q("SELECT platform_version FROM accounts WHERE account_id='acc-3310'")
    ok(acc3310 and acc3310[0]["platform_version"] == "5.4.1",
       "acc-3310 is on the version that supposedly contains the fix",
       "without this CASE-4495 is not a regression", verbose=v)

    # 6. the two entitlement matrices must genuinely disagree
    current = read("knowledge/plan-entitlements.md")
    old = read("knowledge/plan-entitlements-2026-01.md")
    ok(bool(old), "the superseded entitlement matrix exists", verbose=v)
    row = lambda text: next((l for l in text.splitlines()
                             if l.strip().lower().startswith("| bulk export")), "")
    cur_row, old_row = row(current), row(old)
    ok("**no**" in cur_row.lower() or "| no |" in cur_row.lower(),
       "the current matrix denies Growth bulk export", cur_row.strip(), verbose=v)
    ok("**yes**" in old_row.lower() or "| yes |" in old_row.lower(),
       "the superseded matrix grants Growth bulk export", old_row.strip(), verbose=v)
    ok("Superseded" in old.split("\n")[2] or "Superseded" in old[:400],
       "the superseded matrix says so at the top", verbose=v)
    ok("2026-06-01" in current and "2026-06-01" in old,
       "both matrices name the date the change took effect", verbose=v)

    # 7. the documents must agree with the database on the current entitlement
    rows = q("""SELECT enabled FROM entitlements
                WHERE plan='Growth' AND feature='bulk_export' AND effective_to IS NULL""")
    ok(rows and rows[0]["enabled"] == 0,
       "the database agrees Growth currently lacks bulk export", verbose=v)
    rows = q("""SELECT enabled FROM entitlements
                WHERE plan='Growth' AND feature='bulk_export' AND effective_to='2026-06-01'""")
    ok(rows and rows[0]["enabled"] == 1,
       "the database agrees Growth had bulk export before 2026-06-01", verbose=v)

    # 8. the worked example must not be about a live ticket's account
    example = read("examples/triage-note-example.md")
    for acct in TICKET_ACCOUNTS.values():
        ok(acct not in example,
           f"the worked example does not use {acct}",
           "a format sample about a live ticket gets mistaken for evidence", verbose=v)

    # 9. the three failure questions must stay unanswerable from documents alone
    ok(not re.search(r"\bacc-\d+\b", known),
       "known-issues names no account ids",
       "if it did, the KI-77 exposure question would be a single lookup", verbose=v)
    for rel, body in docs.items():
        ok(not re.search(r"\b(two|2)\s+(open\s+)?tickets?\s+(are\s+)?wait", body, re.I),
           f"{rel} does not state the vendor-case ticket count",
           "the aggregation question has to require the database", verbose=v)

    # 10. the audit log must still carry the evidence each ticket turns on
    sig = q("""SELECT count(*) n FROM audit_log
               WHERE account_id='acc-1042' AND error_code='DOMAIN_NOT_REGISTERED'""")
    ok(sig[0]["n"] == 9, "CASE-4471's nine refusals are still in the audit log",
       f"found {sig[0]['n']}", verbose=v)
    sig = q("""SELECT count(*) n FROM audit_log
               WHERE account_id='acc-2287' AND error_code='NOT_ENTITLED'""")
    ok(sig[0]["n"] == 4, "CASE-4482's four denials are still in the audit log",
       f"found {sig[0]['n']}", verbose=v)
    sig = q("""SELECT count(*) n FROM audit_log
               WHERE account_id='acc-3310' AND action='filter_list' AND detail LIKE '0 filters%'""")
    ok(sig[0]["n"] >= 3, "CASE-4495's empty filter_list rows are still there",
       f"found {sig[0]['n']}", verbose=v)

    report()
    return 1 if problems else 0


def report() -> None:
    print()
    for n in notes:
        print(f"  ! {n}")
    if problems:
        print(f"CONTRADICTIONS — {len(problems)} of {checked} checks failed:")
        for p in problems:
            print(f"  x {p}")
    else:
        print(f"CONSISTENT — {checked} checks passed")


if __name__ == "__main__":
    sys.exit(main())
