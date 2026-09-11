---
name: write-report
description: Write the Monthly Delivery Report from the month's source documents — milestones, risks, changes since last month and decisions needed, in house style, with every claim traceable to a source. Use when asked to write, draft, produce or update a monthly delivery report, a status report or a period report for a given month.
---

# Write the Monthly Delivery Report

Turn this month's raw sources into the report the delivery director reads. Done means: every
section of the template filled, every claim traceable to a source, and anything you could
not source listed as a gap rather than quietly dropped.

## Where things are

All paths are relative to the project root. Do not go looking for them.

| | |
|---|---|
| `data/sources/` | this month's raw material: sync notes, status updates, metrics |
| `data/template/monthly-report-template.md` | the structure to follow, section by section |
| `data/house-style.md` | the rules the writing must obey |
| `data/examples/report-2026-07.md` | last month's published report |

Write the finished report to `reports/<YYYY-MM>-monthly-delivery-report.md`.

**Start with the tool.** One call returns every reportable fact with the file and line it
came from, plus warnings about unowned projects and status values outside house style:

```
python3 "${CLAUDE_PLUGIN_ROOT}/tools/extract_facts.py" --month <YYYY-MM>
```

Use its `source` values as your citations. Read the raw sources only for wording and reasons
the extraction does not carry.

## Procedure

1. **Read the template and the house style first.** Both, before reading any source. They
   determine what you need to extract, and reading sources first means reading them twice.
2. **Read last month's published report.** You need it twice over: as the quality bar, and
   because section 4 is a comparison against it.
3. **Run the extraction** for the month. It gives you the milestones, risks, metrics and
   notes with their sources. Then read the sync notes for the *reasons* — the extraction
   carries facts, not explanations.
4. **Build the milestone table.** One row per milestone: name, owner, due date, status,
   note. Where a date moved, write it as a movement with both dates —
   `2026-09-15 → 2026-09-30` — never just the new one.
5. **Build the risk table.** One row per risk: risk, owner, severity, status, mitigation. A
   risk with no owner is recorded as `unassigned`, which is information, not an omission.
6. **Work out what changed since last month.** Compare against the previous report: slips,
   closures, new risks, changes of owner. This is section 4 and it is the section the reader
   checks first.
7. **Collect the decisions.** Anything needing the reader to decide, phrased as a question.
   If a source raises something unresolved and nobody owns it, that is a decision needed.
8. **Write the summary last.** Three to five sentences: what moved, what did not, and the one
   thing to act on. You cannot write it honestly before the tables exist.
9. **List your sources** in section 6.

## When sources disagree

Prefer the **status updates** for dates and status, and the **sync notes** for reasons. If
they conflict on a fact that matters, say so in the report rather than silently choosing —
one line in the note column is enough.

## Output

Match `data/template/monthly-report-template.md` section for section, in order, and obey
`data/house-style.md`. Read both before writing.

## Constraints

- **Every claim carries a source.** If it is not in a source document, it does not go in the
  report. If it matters and no source covers it, it goes in section 5 as a gap — never
  inferred and never filled in from general knowledge.
- **Absolute dates only.** `2026-09-30`, never "end of next month".
- **Status is one of** Not started, In progress, At risk, Complete, Cancelled. Nothing else.
- **Every milestone and risk has a named owner**, or the literal word `unassigned`.
- **No adjectives about progress.** Not "good progress", not "solid month". State what moved.
- **Do not invent decisions** to fill section 5. If nothing needs deciding, say so.
