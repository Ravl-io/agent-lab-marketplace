# Ops Reporting Sandbox — Project Memory

This repository is the weekly operations reporting workspace for the (fictional)
Crestview Wealth platform team. Agents working here follow these rules.

## What this project is

- `reports/` — raw incident reports, written in a hurry by on-call engineers. Messy on purpose. Never edit these.
- `summaries/` — polished weekly ops summaries for the leadership audience, plus `index.md` listing them.
- `scripts/` — small utilities, including `check_style.py` which validates a summary against house style.
- `tasks/` — lab task cards (for training participants; not part of the ops workflow).

## House style for summaries (non-negotiable)

1. One page maximum (~400 words).
2. Structure, in order: title (`# Weekly Ops Summary — <date range>`), **TL;DR** (3 sentences max),
   **Impact** (table: incident · duration · customer impact · severity), **What we're changing**
   (max 4 bullets, each names an owner), **Watch items** (optional, max 2).
3. Executive tone: no internal jargon, no acronyms without expansion on first use, no blame.
4. Every claim traces to a raw report — do not invent details. If a raw report is ambiguous, say so in the summary.
5. Severity scale: SEV1 (customer-facing outage), SEV2 (degradation), SEV3 (internal only).

## Workflow rules for agents

- New summaries go in `summaries/` named `YYYY-MM-DD-weekly-summary.md` (date = the Monday the summary is published).
- After writing or editing a summary, run `python scripts/check_style.py <file>` and fix anything it flags before declaring the work done.
- Whenever a summary is added or renamed, update `summaries/index.md` (newest first).
- Use the `summarize-ops` skill for any request that involves producing or revising a weekly summary.
- Never delete anything under `reports/`.
- The current task's intent lives in `intent.md` (outcome, constraints, what "done" means). Read it before planning.

## Verifying your work

- Style: `python scripts/check_style.py summaries/<file>.md` (must print `STYLE CHECK: PASS`; never weaken the checker to pass)
- Index: `summaries/index.md` lists the new summary first

Run both before reporting any task complete, and paste the checker output. If the checker fails, fix the summary, not the script.

## Things agents get wrong here

- Guessing a severity when the raw report is ambiguous — flag it instead.
- Editing anything under `reports/` (denied by policy; do not try to work around it).
- Expanding the summary past one page to "be thorough".

## Tone of this team

Plain language, short sentences, no drama. We report what happened, what it cost, and what we're changing.
