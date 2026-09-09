#!/usr/bin/env python3
"""House-style checker for weekly ops summaries.

Usage: python scripts/check_style.py summaries/2026-08-24-weekly-summary.md
Exit code 0 = pass, 1 = issues found.
"""
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = ["## Impact", "## What we're changing"]
MAX_WORDS = 450  # ~one page, small buffer over the 400 guidance
MAX_TLDR_SENTENCES = 3
MAX_CHANGE_BULLETS = 4
MAX_WATCH_ITEMS = 2
SEVERITIES = {"SEV1", "SEV2", "SEV3"}

# An owner is one or more capitalised name tokens, optionally with initials,
# optionally several people joined by "and", "&" or a comma.
_NAME = r"[A-Z][A-Za-z.'\-]*(?: [A-Z][A-Za-z.'\-]*)*"
OWNER_RE = re.compile(rf"{_NAME}(?:(?:,| and| &) {_NAME})*")

# A severity cell is a bare code, optionally followed by a parenthetical note,
# e.g. "SEV2" or "SEV2 (unsettled, see Watch items)".
SEV_CELL_RE = re.compile(r"(SEV\w*)(?:\s*\((.+)\))?")
# A separator row cell is dashes and colons — it must contain at least one dash,
# so that an empty severity cell is not mistaken for one.
TABLE_RULE_RE = re.compile(r"[-: ]*-[-: ]*")


def check(path: Path) -> list[str]:
    issues = []
    text = path.read_text(encoding="utf-8")

    # Title
    if not re.match(r"^# Weekly Ops Summary — .+", text.splitlines()[0] if text.splitlines() else ""):
        issues.append("Title: first line must be '# Weekly Ops Summary — <date range>'.")

    # Length
    words = len(re.findall(r"\S+", text))
    if words > MAX_WORDS:
        issues.append(f"Length: {words} words — house style is one page (~400, hard cap {MAX_WORDS}).")

    # TL;DR
    m = re.search(r"\*\*TL;DR\*\*\s*[—-]?\s*(.+?)(?=\n## |\Z)", text, re.S)
    if not m:
        issues.append("TL;DR: missing (expected a '**TL;DR**' paragraph before the Impact section).")
    else:
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", m.group(1).strip()) if s.strip()]
        if len(sentences) > MAX_TLDR_SENTENCES:
            issues.append(f"TL;DR: {len(sentences)} sentences — maximum {MAX_TLDR_SENTENCES}.")

    # Required sections in order
    pos = 0
    for sec in REQUIRED_SECTIONS:
        idx = text.find(sec, pos)
        if idx == -1:
            issues.append(f"Structure: missing or out-of-order section '{sec}'.")
        else:
            pos = idx

    # Impact table severities — read the final cell of every data row, so that a
    # note after the code cannot make the cell escape validation entirely.
    m = re.search(r"## Impact\s*\n(.*?)(?=\n## |\Z)", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if not line.strip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            cell = cells[-1] if cells else ""
            if cell.lower() == "severity" or TABLE_RULE_RE.fullmatch(cell):
                continue  # header or separator row
            sm = SEV_CELL_RE.fullmatch(cell)
            if not sm:
                issues.append(
                    f"Severity: cell '{cell[:40]}' must be a severity code, optionally "
                    "followed by a note in parentheses, e.g. 'SEV2 (unsettled, see Watch items)'."
                )
            elif sm.group(1) not in SEVERITIES:
                issues.append(f"Severity: '{sm.group(1)}' is not one of {sorted(SEVERITIES)}.")

    # Changes bullets + owners
    m = re.search(r"## What we're changing\s*\n(.*?)(?=\n## |\Z)", text, re.S)
    if m:
        bullets = re.findall(r"^\s*[-*] .+$", m.group(1), re.M)
        if len(bullets) > MAX_CHANGE_BULLETS:
            issues.append(f"Changes: {len(bullets)} bullets — maximum {MAX_CHANGE_BULLETS}.")
        for b in bullets:
            parts = re.split(r"\s—\s|\s-\s", b.rstrip())
            if len(parts) < 2:
                issues.append(f"Changes: bullet missing an owner (append '— <Name>'): {b.strip()[:60]}…")
                continue
            owner = parts[-1].strip()
            if not OWNER_RE.fullmatch(owner):
                issues.append(
                    f"Changes: bullet ends with '{owner[:40]}', which is not an owner's "
                    f"name (append '— <Name>'): {b.strip()[:60]}…"
                )

    # Watch items
    m = re.search(r"## Watch items\s*\n(.*?)(?=\n## |\Z)", text, re.S)
    if m:
        bullets = re.findall(r"^\s*[-*] .+$", m.group(1), re.M)
        if len(bullets) > MAX_WATCH_ITEMS:
            issues.append(f"Watch items: {len(bullets)} — maximum {MAX_WATCH_ITEMS}.")

    return issues


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"No such file: {path}")
        return 1
    issues = check(path)
    if issues:
        print(f"STYLE CHECK: {len(issues)} issue(s) in {path}")
        for i in issues:
            print(f"  - {i}")
        return 1
    print(f"STYLE CHECK: PASS — {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
