# Intent: A monthly report you can check

Author: Agent Lab participant
Status: Draft

## Problem

Somebody spends a day a month turning sync notes, status updates and metric extracts into the
delivery report. It is slow, it reads differently depending on who wrote it, and about half
the claims in it cannot be traced to anything — so the reader cannot tell which numbers to
trust, and quietly stops trusting all of them.

## Proposed outcome

The monthly report produced in house style, in the same shape every month, with every claim
traceable to a source file and anything unsourced named as a gap rather than dropped.

## Affected users and systems

- The delivery director reads it; programme leads are named in it and correct it.
- Reads: `data/sources/` for the month, the template, the house style, last month's report.
- Deliberately does not touch: publication or circulation, and the source documents themselves.

## Constraints

- `data/` is read-only evidence. Every number in the report is defended by it.
- Every claim carries a source file and line; an unsourced claim becomes a gap in section 5.
- Absolute dates, named owners, and only the five permitted status values.
- A date that moved is written as `old -> new`, never just the new one.
- No adjectives about progress. State what moved.

## Open questions

- When the sync notes and the status updates disagree on a date, which wins?
- Who is accountable for a programme recorded as `unassigned`?
- Should the report flag claims that were in last month's report and have since vanished?
