# Audit log reference

Last reviewed: 2026-08-30.

The audit log is the ground truth for what a user actually did and what the platform told
them. The customer's description is a report of the symptom; this is a record of the event.

## Reading a row

| Column | What it tells you |
|---|---|
| `action` | what was attempted |
| `target` | what it was attempted against |
| `result` | `success` or `denied` |
| `error_code` | why it was refused, when it was |
| `detail` | free text from the platform, often the most useful column |

## Error codes

| Code | Means | Usually indicates |
|---|---|---|
| `DOMAIN_NOT_REGISTERED` | The email domain is not on the account's SSO domain list | **Configuration** |
| `NOT_ENTITLED` | The feature is not in the account's plan | **User error** — check the date against the entitlement matrix in force |
| `FORBIDDEN` | The user's role does not permit the action | **User error**, or configuration if the role is wrong |
| `INVALID_INPUT` | The request was malformed or out of range | **User error**, occasionally a defect if the input was valid |
| *(null on a denial)* | Refused with no code | Escalate — the platform should always give a reason |

## The signature that matters most

A **denied** row with an error code points at configuration or entitlement. A **successful**
row with a wrong outcome and no error code is the signature of a product defect: the platform
believed it did the right thing, which is why nothing appears in the error columns.

## Retention

Retention follows the plan: 30 days on Starter, 90 on Growth, 2 years on Enterprise. An
absence of rows older than the retention window is not evidence that nothing happened.

## Do not trust the UI for counting

The audit log UI search truncates at 1,000 rows (KI-84). Query the database directly when a
count matters.
