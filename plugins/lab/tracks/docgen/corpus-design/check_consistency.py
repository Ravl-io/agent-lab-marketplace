#!/usr/bin/env python3
"""Cross-check the docgen corpus against itself.

A corpus of twenty documents written by hand contradicts itself. It did while this one was
being written: the risk counts in the monthly metrics did not match the register they are
derived from. That is not a cosmetic problem — Module 2 scores retrieval against a golden
set, and a golden answer that disagrees with the corpus makes every measurement meaningless.

This derives the facts that appear in more than one document from the single place that owns
them, and checks the others agree.

    python3 corpus-design/check_consistency.py
    python3 corpus-design/check_consistency.py --verbose

Stdlib only. Exit 1 on any contradiction.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.join(os.path.dirname(HERE), "workspace", "data", "sources")

MONTHS = ["2026-06", "2026-07", "2026-08"]
PROJECTS = {"Atlas Migration", "Beacon Rollout", "Cirrus API Integration",
            "Observability Programme", "Halo Reporting"}
ALLOWED_STATUS = {"Not started", "In progress", "At risk", "Complete", "Cancelled"}
HALO_JOINS = date(2026, 7, 2)

problems: list[str] = []
notes: list[str] = []
checked = 0


def ok(condition: bool, label: str, detail: str = "", verbose: bool = False) -> None:
    global checked
    checked += 1
    if condition:
        if verbose:
            print(f"  pass  {label}")
    else:
        problems.append(label + (f" — {detail}" if detail else ""))


def read(rel: str) -> str:
    path = os.path.join(SOURCES, rel)
    return open(path, encoding="utf-8").read() if os.path.exists(path) else ""


def says(text: str, phrase: str) -> bool:
    """Substring match that survives line wrapping.

    Prose in these documents is hard-wrapped, so a phrase that reads as one sentence is
    often split by a newline. Matching literally reports a contradiction that is not there.
    """
    return " ".join(phrase.split()).lower() in " ".join(text.split()).lower()


def parse_register() -> list[dict]:
    """The register owns the risks. Everything else about them is derived from here."""
    rows = []
    for line in read("registers/risk-register.md").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 7 and re.fullmatch(r"R-\d+", cells[0]):
            rows.append({
                "ref": cells[0], "risk": cells[1], "project": cells[2], "owner": cells[3],
                "severity": cells[4], "opened": cells[5], "closed": cells[6],
            })
    return rows


def open_at(rows: list[dict], month: str) -> set[str]:
    """Which risks are open at the last day of `month`."""
    year, mon = (int(x) for x in month.split("-"))
    end = date(year + (mon == 12), (mon % 12) + 1, 1)
    live = set()
    for r in rows:
        opened = date.fromisoformat(r["opened"])
        if opened >= end:
            continue
        if r["closed"] != "—" and date.fromisoformat(r["closed"]) < end:
            continue
        live.add(r["ref"])
    return live


def metric(month: str, name: str) -> int | None:
    """The right-hand column of a metrics table row is that month's figure."""
    for line in read(f"metrics-{month}.md").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0].lower().startswith(name.lower()):
            try:
                return int(cells[2])
            except ValueError:
                return None
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    v = args.verbose

    ok(os.path.isdir(SOURCES), "the sources directory exists", SOURCES, verbose=v)
    if not os.path.isdir(SOURCES):
        report()
        return 1

    register = parse_register()
    ok(len(register) >= 6, "the risk register parses", f"{len(register)} rows", verbose=v)

    # 1. the metrics' risk counts must equal what the register implies
    for month in MONTHS:
        expected = open_at(register, month)
        stated = metric(month, "Open risks at month end")
        ok(stated == len(expected),
           f"{month}: open risks in metrics match the register",
           f"metrics says {stated}, register implies {len(expected)} ({', '.join(sorted(expected))})",
           verbose=v)

        closed = {r["ref"] for r in register
                  if r["closed"] != "—" and r["closed"].startswith(month)}
        stated_closed = metric(month, "Risks closed during month")
        ok(stated_closed == len(closed),
           f"{month}: risks closed in metrics match the register",
           f"metrics says {stated_closed}, register has {len(closed)} ({', '.join(sorted(closed))})",
           verbose=v)

    # 2. status updates: known projects, permitted statuses, owner present
    for month in MONTHS:
        text = read(f"status-updates-{month}.md")
        ok(bool(text), f"{month}: status updates exist", verbose=v)
        found = set(re.findall(r"^##\s+(.+)$", text, re.M))
        unknown = found - PROJECTS
        ok(not unknown, f"{month}: every project in the status updates is a known project",
           ", ".join(sorted(unknown)), verbose=v)
        for status in re.findall(r"^-\s+\*\*Status at month end:\*\*\s*(.+)$", text, re.M):
            ok(status.strip() in ALLOWED_STATUS,
               f"{month}: '{status.strip()}' is a permitted status value", verbose=v)
        owners = re.findall(r"^-\s+\*\*Owner:\*\*\s*(.+)$", text, re.M)
        ok(len(owners) == len(found),
           f"{month}: every project states an owner",
           f"{len(found)} projects, {len(owners)} owners", verbose=v)

    # 3. Halo cannot appear before it joined the programme
    for month in MONTHS:
        joined = date(int(month[:4]), int(month[5:]), 1) >= date(HALO_JOINS.year,
                                                                 HALO_JOINS.month, 1)
        mentions = "Halo" in read(f"status-updates-{month}.md")
        if not joined:
            ok(not mentions, f"{month}: no mention of Halo before CR-12 was approved",
               verbose=v)
        else:
            ok(mentions, f"{month}: Halo appears once it is in the programme", verbose=v)

    # 4. every risk's project must be a real project
    for r in register:
        ok(r["project"] in PROJECTS, f"{r['ref']}: names a known project", r["project"],
           verbose=v)

    # 5. the dependencies must stay where the design puts them, or the multi-hop
    #    question stops being multi-hop
    cirrus = read("charters/cirrus-charter.md")
    ok(says(cirrus, "Atlas Migration must complete"),
       "the Cirrus dependency on Atlas is in the Cirrus charter", verbose=v)
    july = read("minutes/steering-2026-07-16.md")
    ok(says(july, "Halo Reporting") and says(july, "reporting views read the migrated schema"),
       "the Halo dependency on Atlas is in the July steering minute", verbose=v)
    for month in MONTHS:
        text = read(f"status-updates-{month}.md")
        ok("waiting on" not in text.lower() and "depends on" not in text.lower(),
           f"{month}: status updates do not state the dependencies",
           "if they do, the multi-hop question becomes single-hop", verbose=v)

    # 6. the charter must carry both versions, with dates
    atlas = read("charters/atlas-charter.md")
    ok(says(atlas, "effective 2026-02-10") and says(atlas, "effective 2026-05-14"),
       "the Atlas charter carries both dated versions", verbose=v)
    ok(says(atlas, "superseded 2026-05-14"),
       "the Atlas charter marks v1 superseded", verbose=v)
    ok(atlas.count("eporting views") >= 2,
       "reporting views appear in both charter versions",
       "the temporal question needs the same fact stated twice, differently", verbose=v)

    # 6b. the published example reports must not contradict the register. This is where
    #     the first real contradiction in this corpus lived: a report showing a risk as
    #     Open that had closed the month before.
    EXAMPLES = os.path.join(os.path.dirname(SOURCES), "examples")
    for month in ("2026-06", "2026-07"):
        path = os.path.join(EXAMPLES, f"report-{month}.md")
        if not os.path.exists(path):
            notes.append(f"no example report for {month}")
            continue
        body = open(path, encoding="utf-8").read()
        live = open_at(register, month)
        for r in register:
            row = re.search(rf"^\|\s*{re.escape(r['ref'])}\b.*$", body, re.M)
            if not row:
                ok(r["ref"] not in live,
                   f"report-{month}: omits no risk that was open",
                   f"{r['ref']} was open at month end and is not in the report", verbose=v)
                continue
            shown_open = "| Open " in row.group(0) or row.group(0).rstrip().endswith("Open")
            ok((r["ref"] in live) == bool(shown_open or "Open" in row.group(0)),
               f"report-{month}: {r['ref']} status matches the register",
               f"report shows it {'open' if 'Open' in row.group(0) else 'closed'}, "
               f"register says {'open' if r['ref'] in live else 'closed'}", verbose=v)

    # 7. change requests referenced anywhere must exist in the log
    log = read("registers/change-requests.md")
    declared = set(re.findall(r"\bCR-\d+\b", log))
    for rel in sorted(os.listdir(SOURCES)) + ["minutes/steering-2026-07-16.md",
                                              "minutes/steering-2026-08-20.md",
                                              "charters/cirrus-charter.md",
                                              "charters/halo-charter.md"]:
        path = os.path.join(SOURCES, rel)
        if not os.path.isfile(path):
            continue
        for ref in set(re.findall(r"\bCR-\d+\b", open(path, encoding="utf-8").read())):
            ok(ref in declared, f"{rel}: {ref} is in the change request log", verbose=v)

    report()
    return 1 if problems else 0


def report() -> None:
    print()
    if notes:
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
