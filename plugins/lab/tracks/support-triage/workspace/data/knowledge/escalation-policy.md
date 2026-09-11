# Escalating to the platform vendor

Last reviewed: 2026-08-22. The platform is built and operated by a third-party vendor;
product defects are resolved by them, not by us.

## Before you escalate

An escalation is refused and returned to us if any of these is missing. Returned cases cost
about four days.

1. **Configuration ruled out**, with the account setting or audit row that proves it.
2. **Entitlement ruled out**, with the entitlement row for the account's plan.
3. **A reproduction** — the exact steps, and what happened versus what was expected.
4. **Audit log evidence** — the rows showing the action being permitted and the wrong result.
   Query the database directly; the audit log UI truncates (see KI-84).
5. **Scope** — how many users and accounts are affected, and whether it is region-specific.
6. **The account's platform version.**
7. **A check against the known issues register.** If it matches an open entry, link to that
   vendor case instead of opening a new one.

## Severity

| Severity | Meaning | Vendor response |
|---|---|---|
| S1 | Platform unusable, no workaround | 1 hour ack, 8 hour fix target |
| S2 | Major feature broken, workaround exists | 4 hour ack, 3 business days |
| S3 | Minor or cosmetic | 5 business days |

Severity is set from impact, not from customer pressure. A single account with a workaround
is an S2 however loudly it is escalated.

## When a fix comes back

The vendor's word that something is fixed is not a resolution. We validate it:

1. Confirm the account is actually on the version containing the fix.
2. Re-run the original reproduction from the ticket.
3. Check the audit log for the same error signature.
4. Only then reply to the customer and close.

If the symptom returns on a version that supposedly contains the fix, that is a **regression**
and it is new information. Escalate it referencing the original vendor case; do not quietly
close it against the old entry.
