# Intent: L2 triage with its evidence attached

Author: Agent Lab participant
Status: Draft

## Problem

Level 2 spends most of its day establishing what a ticket actually *is* before anyone can act
on it. Roughly two thirds of what arrives as "a bug" turns out to be configuration or a plan
limitation, and each one that reaches the vendor as a defect costs about a week of turnaround
and some credibility. Worse, the reasoning is never written down, so a classification cannot
be checked afterwards — only redone.

## Proposed outcome

One triage note per case that states the classification and the evidence it rests on, in the
house format, so a colleague can check the conclusion in two minutes instead of repeating the
investigation.

## Affected users and systems

- L2 engineers write and read these; L1 learns from them what to collect next time.
- The platform vendor receives fewer returned escalations.
- Reads: Salesforce ticket exports, `support.db` (accounts, audit log, entitlements, case
  history), the internal knowledge base.
- Deliberately does not touch: the production platform, and any customer communication.

## Constraints

- `data/` is read-only evidence. A wrong source document is a finding, not a file to fix.
- Every classification cites a database row, a setting or a document — never an inference.
- Configuration and entitlement are each ruled out with evidence before a defect is proposed.
- Entitlement is answered as of the ticket's date, not today's.
- Nothing reaches the customer or the vendor without a human approving it.

## Open questions

- Who owns a knowledge base article that triage finds is stale?
- Do "need more information" outcomes get recorded anywhere, or only replied to?
- What decides linking to an existing vendor case versus opening a new one?
