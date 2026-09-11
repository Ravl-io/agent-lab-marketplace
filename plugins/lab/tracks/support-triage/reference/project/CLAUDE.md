# triage-assistant

@intent.md

This project triages level-2 support tickets escalated from Salesforce, and decides whether
each one is configuration, user error, or a genuine product defect.

- `data/` is **read-only evidence**. Everything a conclusion rests on lives there. If a source
  document is wrong, that is a finding to report, not a file to fix.
- Triage notes go in `triage/`, one file per case id.
- `data/db/support.db` is the ground truth for what a user actually did. The customer's
  description is a report of the symptom, not of the cause.
- Entitlement questions are only answerable **as of a date**. A ticket from April is asking
  about April.
