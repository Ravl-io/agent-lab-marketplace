#!/usr/bin/env python3
"""Pull the reportable facts out of the month's sources, each with where it came from.

Every claim in the report has to be traceable. Doing that by re-reading three source files
and remembering which said what is exactly the sort of thing that drifts between runs, so
it belongs in a tool.

    python3 tools/extract_facts.py
    python3 tools/extract_facts.py --month 2026-08
    python3 tools/extract_facts.py --selftest
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

def project_root() -> str:
    """Where the data lives — the project, not wherever this script happens to sit.

    This matters the moment the tool moves into a plugin. A path computed from __file__
    resolves to the plugin's own directory, and the data is not there. The project is the
    working directory, and hooks and tools are both given CLAUDE_PROJECT_DIR.
    """
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


SOURCES = os.path.join(project_root(), "data", "sources")

ALLOWED_STATUS = {"Not started", "In progress", "At risk", "Complete", "Cancelled"}


def read(name: str) -> tuple[str, list[str]]:
    path = os.path.join(SOURCES, name)
    if not os.path.exists(path):
        return "", []
    with open(path) as fh:
        text = fh.read()
    return text, text.splitlines()


def cite(name: str, index: int) -> str:
    """A fact without a source location is not traceable, so every fact carries one."""
    return f"data/sources/{name}:{index + 1}"


def extract(month: str) -> dict:
    status_name = f"status-updates-{month}.md"
    metrics_name = f"metrics-{month}.md"
    notes_name = f"standup-notes-{month}.md"

    _, status_lines = read(status_name)
    projects, current = [], None
    for i, line in enumerate(status_lines):
        heading = re.match(r"^##\s+(.*)$", line)
        if heading:
            current = {"project": heading.group(1).strip(), "source": cite(status_name, i),
                       "owner": None, "status": None, "milestone": None,
                       "due": None, "delivered": None, "risks": []}
            projects.append(current)
            continue
        if current is None:
            continue
        field = re.match(r"^-\s+\*\*(.+?):\*\*\s*(.*)$", line)
        if not field:
            continue
        key, value = field.group(1).strip().lower(), field.group(2).strip()
        where = cite(status_name, i)
        if key == "owner":
            current["owner"] = value
        elif key.startswith("status"):
            current["status"] = value
        elif key == "milestone":
            current["milestone"] = value
            dates = re.findall(r"\d{4}-\d{2}-\d{2}", value)
            moved = re.search(r"was due (\d{4}-\d{2}-\d{2}).*?now (\d{4}-\d{2}-\d{2})",
                              value, re.I)
            if moved:
                current["due"] = f"{moved.group(1)} -> {moved.group(2)}"
            elif "due" in value.lower() and dates:
                current["due"] = dates[0]
            if "delivered" in value.lower() and len(dates) > 1:
                current["delivered"] = dates[-1]
            elif "delivered" in value.lower() and dates:
                current["delivered"] = dates[0]
        elif key.startswith("risk"):
            current["risks"].append({"risk": value, "state": key, "source": where})
        elif key == "note":
            current["note"] = value

    metrics_text, metrics_lines = read(metrics_name)
    metrics = []
    for i, line in enumerate(metrics_lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")] \
            if line.strip().startswith("|") else []
        if len(cells) == 3 and not set(cells[0]) <= set("-: ") and cells[0] != "Metric":
            metrics.append({"metric": cells[0], "previous": cells[1], "current": cells[2],
                            "source": cite(metrics_name, i)})

    _, note_lines = read(notes_name)
    notes = [{"text": line.strip("- ").strip(), "source": cite(notes_name, i)}
             for i, line in enumerate(note_lines)
             if line.strip().startswith("-") and len(line.strip()) > 12]

    bad_status = [p["project"] for p in projects
                  if p["status"] and p["status"] not in ALLOWED_STATUS]
    unowned = [p["project"] for p in projects if not p["owner"] or
               p["owner"].lower() in ("unassigned", "none", "")]

    return {
        "month": month,
        "milestones": projects,
        "risks": [r for p in projects for r in p["risks"]],
        "metrics": metrics,
        "notes": notes,
        "warnings": {
            "status_values_outside_house_style": bad_status,
            "projects_without_a_named_owner": unowned,
        },
        "sources": [n for n in (status_name, metrics_name, notes_name)
                    if os.path.exists(os.path.join(SOURCES, n))],
    }


def selftest() -> int:
    checks, failures = 0, []

    def expect(label: str, ok: bool) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    d = extract("2026-08")
    names = [m["project"] for m in d["milestones"]]
    expect("all four projects found", len(names) == 4)
    expect("Cirrus API is present", any("Cirrus" in n for n in names))
    cirrus = next(m for m in d["milestones"] if "Cirrus" in m["project"])
    expect("the Cirrus slip is captured as a movement",
           cirrus["due"] == "2026-09-15 -> 2026-09-30")
    expect("the unowned programme is flagged",
           any("Observability" in n for n in d["warnings"]["projects_without_a_named_owner"]))
    expect("every milestone carries a source",
           all(m["source"] for m in d["milestones"]))
    expect("metrics were read", len(d["metrics"]) >= 5)
    expect("same input, same output", extract("2026-08") == d)

    for f in failures:
        print(f"FAIL: {f}", file=sys.stderr)
    print(f"{checks - len(failures)}/{checks} checks passed")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract reportable facts with their sources")
    ap.add_argument("--month", default="2026-08")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    print(json.dumps(extract(args.month), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
