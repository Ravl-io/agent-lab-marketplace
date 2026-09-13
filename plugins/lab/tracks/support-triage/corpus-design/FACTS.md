# support-triage corpus — the fact sheet

**Facilitator reference. Not shipped to participants.**

This track has two halves and they have different owners:

- **The database** is owned by `build_db.py`. That script *is* the fact sheet for accounts,
  users, entitlements, the audit log, vendor cases and case history. Change facts there and
  re-run it; never hand-edit `support.db`.
- **The documents** are owned by this file. Anything a document asserts that the database
  also knows must agree, and `corpus-design/check_consistency.py` checks the overlaps.

## The three tickets that resolve, and how

| Ticket | Account | Classification | The deciding evidence |
|---|---|---|---|
| CASE-4471 | acc-1042 Brightmoor Health | **Configuration** | 3 users on `brightmoor-health.org`; only `brightmoorhealth.com` is registered; 9 × `DOMAIN_NOT_REGISTERED` |
| CASE-4482 | acc-2287 Kestrel Retail | **User error** | `bulk_export` was enabled for Growth until 2026-06-01 and disabled after; 2 successes in April, 4 `NOT_ENTITLED` denials in September |
| CASE-4495 | acc-3310 Aldermoor Logistics | **Product defect — regression** | Saves succeed, `filter_list` returns 0, no error code; prior CASE-4123 → VND-411 marked fixed in 5.4.1; the account **is** on 5.4.1 |
| CASE-4503 | acc-4188 Thornbury Media | **Need more information** | No contact, no report named, no expected value |

## The entitlement matrix has two versions — the temporal trap

`data/knowledge/plan-entitlements.md` is the **current** matrix, in force from 2026-06-01.
`data/knowledge/plan-entitlements-2026-01.md` is the **superseded** one, in force
2026-01-15 → 2026-06-01, in which **Growth included bulk export**.

Both documents describe the same plans in the same words. Only the validity dates separate
them, and a similarity search returns both as equally relevant. This is the cleanest
document-level temporal failure in the lab: *"was Kestrel entitled to bulk export in April?"*
is **yes** from one document and **no** from the other, and nothing in the text says which
applies.

The database agrees via `entitlements.effective_from` / `effective_to`, which is how the
Module 1 tool gets it right and retrieval alone does not.

## The regression story spans three documents plus the database

`data/knowledge/known-issues.md` records KI-77, fixed in 5.4.1.
`data/knowledge/release-notes-5.4.md` asserts the fix shipped in 5.4.1 on 2026-08-14.
`support.db` `accounts.platform_version` says acc-3310 is on **5.4.1**.
`support.db` `case_history` says CASE-4123 on acc-3310 was closed against VND-411.

Only together do these say "this is a regression". No single document does.

## The three questions retrieval must get wrong

Module 2 ends by demonstrating these and leaving them broken. Module 3 opens on them.

1. **Multi-hop** — "Which other accounts are exposed to KI-77?"
   KI-77's scope (region `eu-west`, fix version 5.4.1) is in a document; which accounts are
   in that region on that version is in the database. Retrieval returns the known-issues page
   and cannot enumerate accounts. The answer is **acc-1042, acc-3310, acc-5501** — eu-west and
   on 5.4.1. acc-6620 is eu-west but still on 5.4.0, so it is not exposed to the regression.
2. **Aggregation** — "How many open tickets are waiting on a vendor case, and which?"
   `case_history` where `closed_at IS NULL` and a vendor case is set: **CASE-4201** (VND-427)
   and **CASE-4390** (VND-433). A complete set, which top-k cannot express.
3. **Temporal** — "Was Kestrel Retail entitled to bulk export in April 2026?"
   Two matrix documents, both relevant, only dates separating them. **Yes** in April, **no**
   from 2026-06-01.

## Cross-document invariants the checker enforces

| Invariant | Why |
|---|---|
| Every `error_code` named in a knowledge document appears in `audit_log` | a documented code nobody emits is a dead reference |
| Every ticket's `account_id` exists in `accounts` | a ticket about an unknown account cannot be triaged |
| Every vendor case named in a document exists in `vendor_cases` | and vice versa for open ones |
| The current matrix says Growth lacks `bulk_export`; the superseded one says it has it | the temporal trap only works if they genuinely disagree |
| Release notes' fix version for KI-77 matches `vendor_cases.fix_version` | the regression depends on both saying 5.4.1 |
| The worked example does not reference a live account | it is a format sample, not evidence |

## People

Northwind support: Rina Petrova and Omar Haddad (L1) · the L2 team (the participant) ·
Dara Oyelowo, Sam Ndiaye, Ines Moreau (platform contacts)
Customers: Yusuf Adeyemi (Brightmoor) · Danielle Marsh (Kestrel) · Peter Nowak (Aldermoor)
