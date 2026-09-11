#!/usr/bin/env python3
"""Everything you need to know about an account, in one call.

Replaces the five or six separate database queries a triage otherwise makes by hand. The
point is not speed: it is that the answer is the same every time, and nobody is composing
SQL on the fly.

    python3 tools/account_snapshot.py acc-1042
    python3 tools/account_snapshot.py acc-2287 --as-of 2026-04-14

--as-of matters. Entitlements change, and "was this account entitled" is only answerable
against a date. It defaults to today, which is the answer to a different question than the
one a ticket from April is asking.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import date

def project_root() -> str:
    """Where the data lives — the project, not wherever this script happens to sit.

    This matters the moment the tool moves into a plugin. A path computed from __file__
    resolves to the plugin's own directory, and the data is not there. The project is the
    working directory, and hooks and tools are both given CLAUDE_PROJECT_DIR.
    """
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


DB = os.path.join(project_root(), "data", "db", "support.db")


def rows(conn: sqlite3.Connection, sql: str, args: tuple = ()) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(r) for r in conn.execute(sql, args)]


def snapshot(account_id: str, as_of: str, audit_limit: int) -> dict:
    if not os.path.exists(DB):
        raise SystemExit(f"database not found at {DB}")
    conn = sqlite3.connect(DB)

    account = rows(conn, "SELECT * FROM accounts WHERE account_id = ?", (account_id,))
    if not account:
        raise SystemExit(f"no such account: {account_id}")
    account = account[0]

    entitlements = rows(conn, """
        SELECT feature, enabled, effective_from, effective_to
        FROM entitlements
        WHERE plan = ?
          AND effective_from <= ?
          AND (effective_to IS NULL OR effective_to > ?)
        ORDER BY feature
    """, (account["plan"], as_of, as_of))

    return {
        "account_id": account_id,
        "as_of": as_of,
        "account": account,
        "sso_domains": [r["domain"] for r in rows(
            conn, "SELECT domain FROM sso_domains WHERE account_id = ? ORDER BY domain",
            (account_id,))],
        "users": rows(conn, """
            SELECT user_id, email, name, role, status, created_at
            FROM users WHERE account_id = ? ORDER BY created_at
        """, (account_id,)),
        "entitlements": {r["feature"]: bool(r["enabled"]) for r in entitlements},
        "entitlement_rows": entitlements,
        "recent_audit": rows(conn, """
            SELECT created_at, user_id, action, target, result, error_code, detail
            FROM audit_log WHERE account_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (account_id, audit_limit)),
        "audit_error_summary": rows(conn, """
            SELECT action, result, error_code, count(*) AS n,
                   min(created_at) AS first_seen, max(created_at) AS last_seen
            FROM audit_log WHERE account_id = ?
            GROUP BY action, result, error_code
            ORDER BY n DESC
        """, (account_id,)),
        "prior_cases": rows(conn, """
            SELECT case_id, subject, classification, resolution, vendor_case,
                   opened_at, closed_at
            FROM case_history WHERE account_id = ? ORDER BY opened_at DESC
        """, (account_id,)),
    }


def selftest() -> int:
    """A tool can be tested. That is most of why it is a tool and not a prompt."""
    checks, failures = 0, []

    def expect(label: str, ok: bool) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    a = snapshot("acc-1042", "2026-09-02", 30)
    expect("acc-1042 is on the Enterprise plan", a["account"]["plan"] == "Enterprise")
    expect("acc-1042 has exactly one registered SSO domain",
           a["sso_domains"] == ["brightmoorhealth.com"])
    expect("the unregistered-domain refusals are visible",
           any(r["error_code"] == "DOMAIN_NOT_REGISTERED" for r in a["audit_error_summary"]))

    # the same input twice must give the same answer, or it is not a tool
    expect("same input, same output", snapshot("acc-1042", "2026-09-02", 30) == a)

    # the entitlement that moved between plans in June
    before = snapshot("acc-2287", "2026-04-14", 5)
    after = snapshot("acc-2287", "2026-09-04", 5)
    expect("bulk export was entitled in April", before["entitlements"]["bulk_export"] is True)
    expect("bulk export is not entitled in September",
           after["entitlements"]["bulk_export"] is False)

    for f in failures:
        print(f"FAIL: {f}", file=sys.stderr)
    print(f"{checks - len(failures)}/{checks} checks passed")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Snapshot one account for triage")
    ap.add_argument("account_id", nargs="?")
    ap.add_argument("--as-of", default=date.today().isoformat(),
                    help="date to judge entitlements against (default: today)")
    ap.add_argument("--audit-limit", type=int, default=30)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.account_id:
        ap.error("account_id is required")
    print(json.dumps(snapshot(args.account_id, args.as_of, args.audit_limit), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
