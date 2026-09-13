# Platform release notes — 5.4.x

Published by the platform vendor. We do not control this document; it is reproduced here as
received.

## 5.4.2 — expected

- Audit log UI search truncation (KI-84 / VND-433) — fix targeted, not yet shipped

## 5.4.1 — released 2026-08-14

- **Saved filters not persisted for eu-west tenants (KI-77 / VND-411) — fixed.** Filter
  records are now written to durable storage rather than a cache tier that was evicted
  nightly.
- Minor: improved error messaging on `sso_login` fallback

## 5.4.0 — released 2026-07-02

- Duplicate rows in order export (KI-70 / VND-402) — fixed
- Scheduled report delivery moved to a new queue. *Known to have introduced the delay
  reported as KI-81 / VND-427.*

## 5.3.4 — released 2026-05-20

- SSO redirect loop on Safari 17 (KI-62 / VND-388) — fixed

## Rollout

Accounts are upgraded on the vendor's schedule, not ours, and not all at once. An account's
current version is in `accounts.platform_version`. **A fix being released is not the same as
an account having it**, and a symptom reappearing on a version that contains the fix is a
regression, not a duplicate of the original defect.
