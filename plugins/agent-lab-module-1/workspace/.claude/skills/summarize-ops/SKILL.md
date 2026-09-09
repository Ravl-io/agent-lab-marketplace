---
name: summarize-ops
description: Produce or revise the weekly ops summary from raw incident reports. Use whenever the task involves summarizing incidents, writing the weekly summary, or updating an existing summary in summaries/.
---

# Weekly Ops Summary Procedure

Follow these steps in order. Do not skip the verification step.

## 1. Gather

- Read every raw report in `reports/` that falls inside the requested date range.
  If no range is given, use all reports not yet covered by a summary in `summaries/index.md`.
- Read the most recent existing summary in `summaries/` as a style reference.

## 2. Extract, don't invent

For each incident capture: what happened, start/end time (compute duration), customer impact
(quote or tightly paraphrase the raw report), severity per the scale in CLAUDE.md, and any
follow-up actions the on-call engineer proposed. If the raw report is ambiguous or missing a
fact (e.g., no end time), record the gap explicitly — the summary must say "duration unclear
from report" rather than guessing.

## 3. Write

Produce `summaries/YYYY-MM-DD-weekly-summary.md` following the house style in CLAUDE.md exactly:
title, TL;DR (≤3 sentences), Impact table, "What we're changing" (≤4 bullets, each with an owner —
use the on-call engineer's name from the raw report unless told otherwise), optional Watch items (≤2).
Executive tone. One page (~400 words).

## 4. Verify

- Run `python scripts/check_style.py summaries/<the-new-file>.md` and fix every issue it reports.
- Re-read the summary once against the raw reports: every number and claim must trace back.

## 5. Index

Update `summaries/index.md`: add the new summary at the top of the list (newest first) with
its date range and a one-line description.

## Output

When done, report: the file(s) you created or changed, the check_style result, and any
ambiguities you flagged.
