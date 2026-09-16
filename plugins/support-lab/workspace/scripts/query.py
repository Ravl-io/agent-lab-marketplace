#!/usr/bin/env python3
"""Read-only SQL against data/support.db.  Usage: python3 scripts/query.py "SELECT ..."
Only SELECT / WITH statements are executed. Output is a plain table."""
import sqlite3, sys, os
sql = " ".join(sys.argv[1:]).strip()
if not sql:
    print(__doc__); sys.exit(1)
if not sql.lower().lstrip("(").startswith(("select", "with", "pragma table_info", "explain")):
    print("refused: read-only — only SELECT/WITH statements are allowed"); sys.exit(2)
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "support.db")
con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
cur = con.execute(sql)
cols = [d[0] for d in cur.description] if cur.description else []
rows = cur.fetchall()
if cols:
    widths = [max(len(str(c)), *(len(str(r[i])) for r in rows)) if rows else len(str(c)) for i, c in enumerate(cols)]
    print(" | ".join(str(c).ljust(widths[i]) for i, c in enumerate(cols)))
    print("-+-".join("-" * wd for wd in widths))
    for r in rows[:200]:
        print(" | ".join(str(v).ljust(widths[i]) for i, v in enumerate(r)))
    if len(rows) > 200:
        print(f"... {len(rows) - 200} more rows")
print(f"({len(rows)} rows)")
