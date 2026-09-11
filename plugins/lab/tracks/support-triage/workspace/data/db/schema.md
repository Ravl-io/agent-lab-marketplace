# support.db — schema

SQLite. Query it directly; the audit log UI truncates at 1,000 rows (see KI-84).

```
sqlite3 data/db/support.db "SELECT * FROM accounts WHERE account_id='acc-1042';"
```

## accounts
`account_id, name, plan, region, platform_version, sso_enabled, seats, created_at`

`plan` is one of Starter, Growth, Enterprise. `region` matters — some defects are
region-specific. `platform_version` matters whenever a fix version is involved.

## sso_domains
`account_id, domain, added_at`

The registered SSO domains for an account. A login domain absent from this table falls back
to password login. There is no wildcard.

## users
`user_id, account_id, email, name, role, status, created_at`

`role` is Admin or Member.

## entitlements
`plan, feature, enabled, effective_from, effective_to`

**Not a simple matrix.** A row with `effective_to IS NULL` is in force now; a closed row
records what was true in the past. To answer "was this account entitled on date D", filter on
the date rather than taking the current row:

```sql
SELECT enabled FROM entitlements
WHERE plan = ? AND feature = ?
  AND effective_from <= ? AND (effective_to IS NULL OR effective_to > ?);
```

Answering an entitlement question without a date is how you end up telling a customer that
something never worked when it plainly did.

## audit_log
`event_id, account_id, user_id, action, target, result, error_code, detail, created_at`

What users actually did and what the platform told them. `result` is success or denied.
`error_code` is the useful column: `DOMAIN_NOT_REGISTERED`, `NOT_ENTITLED`, `FORBIDDEN`,
`INVALID_INPUT`, or NULL.

A **denied** row with an error code usually means configuration or entitlement. A
**successful** row with a wrong outcome and no error code is the signature of a product
defect — the platform thought it did the right thing.

## vendor_cases
`vendor_case_id, known_issue, title, status, severity, opened_at, resolved_at, fix_version`

Cases with the platform vendor. `fix_version` is only meaningful next to an account's
`platform_version`.

## case_history
`case_id, account_id, subject, classification, resolution, vendor_case, opened_at, closed_at`

Every case we have closed, and how it was classified: `configuration`, `user_error`,
`product_defect`, or NULL when it was never classified. `closed_at IS NULL` means still open.

Check this before anything else. "Has this customer reported this before" changes the answer
more often than any other single fact.
