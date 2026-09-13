#!/usr/bin/env python3
"""Run a read-only query against the case database.

    python3 sql.py "SELECT * FROM accounts WHERE account_id = 'acc-1042'"
    python3 sql.py --tables
    python3 sql.py --schema accounts
    python3 sql.py --json "SELECT plan, count(*) FROM accounts GROUP BY plan"

Why this exists rather than the `sqlite3` command: the **command** is a separate program
that is not installed on Windows and is a package on most Linux distributions. The sqlite3
**module** is part of the Python standard library — if you have Python, you already have a
complete SQLite engine. This file is twenty lines of that module, so the lab needs nothing
installed beyond Python itself.

It refuses anything that is not a read. `data/` is evidence: if it is wrong, that is a
finding to report, not a row to fix. The write-boundary hook says the same thing about
files, and this says it about the database.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys

DB = os.path.join("data", "db", "support.db")
READ_ONLY = ("select", "with", "pragma", "explain")


def connect(path: str) -> sqlite3.Connection:
    if not os.path.exists(path):
        sys.exit(f"no database at {path} — run this from the project root")
    # opened read-only at the driver level too, so a mistake cannot become a change
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("query", nargs="?", help="a SELECT statement")
    ap.add_argument("--db", default=DB)
    ap.add_argument("--tables", action="store_true", help="list the tables")
    ap.add_argument("--schema", metavar="TABLE", help="show one table's columns")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    con = connect(args.db)

    if args.tables:
        rows = con.execute("SELECT name FROM sqlite_master WHERE type='table' "
                           "ORDER BY name").fetchall()
        print("\n".join(r["name"] for r in rows))
        return 0

    if args.schema:
        rows = con.execute(f"PRAGMA table_info({args.schema!r})").fetchall()
        if not rows:
            sys.exit(f"no table called {args.schema!r} — try --tables")
        for r in rows:
            print(f"{r['name']:<20} {r['type'] or 'TEXT'}")
        return 0

    if not args.query:
        ap.error("give a query, or --tables / --schema")

    first = args.query.strip().split(None, 1)[0].lower()
    if first not in READ_ONLY:
        sys.exit(f"refused: {first!r} is not a read. The database is evidence — if it is "
                 f"wrong, that is a finding to report, not a row to change.")

    try:
        rows = con.execute(args.query).fetchall()
    except sqlite3.Error as exc:
        sys.exit(f"SQL error: {exc}")

    if args.as_json:
        print(json.dumps([dict(r) for r in rows], indent=2, default=str))
        return 0
    if not rows:
        print("(no rows)")
        return 0
    headers = rows[0].keys()
    widths = [max(len(str(h)), *(len(str(r[h])) for r in rows)) for h in headers]
    print("  ".join(str(h).ljust(w) for h, w in zip(headers, widths)))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(str(r[h]).ljust(w) for h, w in zip(headers, widths)))
    print(f"\n{len(rows)} row(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
