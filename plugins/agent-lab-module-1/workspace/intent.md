# Intent: weekly ops summary, Aug 10–23
Author: Ops reporting lead (Crestview platform team). Status: draft.

<!-- Format from Anthropic's AI-native SDLC playbook (Aug 2026): a proto-spec in the
     originator's own words — what is wanted, why, under which constraints.
     Version-controlled. The agent reads it alongside CLAUDE.md. Update it per task. -->

## Problem
Leadership receives raw incident reports written in a hurry by on-call engineers.
They cannot act on them without reading every report and reconciling severities.

## Proposed outcome
A one-page weekly ops summary for Aug 10–23 that a busy executive can act on
without opening a single raw report: what happened, what it cost, what we are changing.

## Affected users and systems
Leadership (readers) · platform on-call engineers (authors of raw reports) ·
`reports/` (source, read-only) · `summaries/` and `summaries/index.md` (output).

## Constraints
- House style in CLAUDE.md is non-negotiable: one page, TL;DR ≤ 3 sentences, cited severities.
- Every claim traces to a raw report in `reports/`; ambiguities are flagged, never guessed.
- Nothing under `reports/` is modified.

## What "done" means
`python scripts/check_style.py <summary>` passes with no findings, `summaries/index.md`
is updated (newest first), and the summary names an owner for every change.

## Open questions
Is the Aug 15 webhook backlog a SEV2 (degradation) or a SEV3 (internal only)? The raw
report is ambiguous — say so rather than decide.
