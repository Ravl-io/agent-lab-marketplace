---
name: triage-ticket
description: Triage an escalated L2 support ticket — classify it as configuration, user error, product defect, or need-more-information, with evidence from the account database and the knowledge base. Use when asked to triage, diagnose, investigate or work a support case or ticket, or when given a case number like CASE-4471.
---

# Triage an escalated ticket

You are doing first diligence on a ticket that level 1 has escalated. Decide what this
actually is, with evidence, before anyone promises the customer anything.

## Where things are

All paths are relative to the project root. Do not go looking for them.

| | |
|---|---|
| `data/tickets/` | the escalated tickets |
| `data/db/support.db` | accounts, users, entitlements, audit log, case history, vendor cases |
| `data/db/schema.md` | what is in the database, and the queries that matter |
| `data/knowledge/` | triage policy, escalation policy, plan entitlements, known issues, how-to guides |
| `data/examples/triage-note-example.md` | the output format you must match |

Query the database with `sqlite3 data/db/support.db "<sql>"`.

Write the finished triage note to `triage/<CASE-ID>.md`.

## Procedure

Work in this order. Do not skip ahead to a conclusion.

1. **Read the ticket** in `data/tickets/`. Note the account id, the platform version, the
   dates, and what level 1 already checked.
2. **Check whether it has happened before**:
   ```sql
   SELECT case_id, subject, classification, resolution, vendor_case, opened_at, closed_at
   FROM case_history WHERE account_id = ?;
   ```
   A repeat report changes the answer more often than any other single fact.
3. **Look at what the user actually did.** The audit log is the ground truth, not the
   customer's description:
   ```sql
   SELECT action, target, result, error_code, detail, created_at
   FROM audit_log WHERE account_id = ? ORDER BY created_at DESC LIMIT 30;
   ```
   A **denied** row with an error code points at configuration or entitlement. A
   **successful** row with a wrong outcome and no error code is the signature of a defect.
4. **Rule out configuration.** Compare the account's settings against what the customer
   believes. For login problems that means `sso_domains` against the affected users' email
   domains.
5. **Rule out entitlement, as of the relevant date** — not as of today:
   ```sql
   SELECT enabled FROM entitlements
   WHERE plan = ? AND feature = ?
     AND effective_from <= ? AND (effective_to IS NULL OR effective_to > ?);
   ```
6. **Only then consider a product defect.** Check `data/knowledge/known-issues.md` first. If
   an entry matches, compare its `fix_version` against the account's `platform_version` — a
   defect "fixed" in a version the account is already running is new information.
7. **Classify and write it up** in the house format.

## The four classifications

Defined in `data/knowledge/triage-policy.md`. Read it if you are unsure of the boundary.
In short: **configuration** (their setup is wrong), **user error** (their plan, role or
permissions do not allow it), **product defect** (the platform did the wrong thing given a
correct setup), **need more information** (you cannot responsibly say yet — a legitimate
answer, not a failure).

## Output

Write to `triage/<CASE-ID>.md`, and match `data/examples/triage-note-example.md` exactly — same sections, same order. Read it
before writing.

## Constraints

- **Evidence is observable rows and settings**, never inference. If you cannot point at a
  database row, a setting or a document, it does not go in Evidence.
- **Never classify as a product defect without ruling out configuration and entitlement**,
  each with its own evidence. Two thirds of tickets escalated as bugs are neither, and a
  defect raised with the vendor that turns out to be configuration costs a week.
- **Do not invent a fix.** Recommend what the runbook or knowledge base says.
- **State confidence** as High, Medium or Low, with a reason. Low is useful.
- Query the database directly; the audit log UI truncates (see KI-84).
