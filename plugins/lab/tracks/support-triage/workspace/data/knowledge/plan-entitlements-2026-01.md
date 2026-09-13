# Plan entitlement matrix

**Superseded.** In force 2026-01-15 to 2026-06-01. Retained because findings, tickets and
entitlement answers dated before 2026-06-01 are judged against this version.

For the current matrix see `plan-entitlements.md`.

| Feature | Starter | Growth | Enterprise |
|---|---|---|---|
| Standard reports | yes | yes | yes |
| Scheduled reports | no | yes | yes |
| Bulk export | no | **yes** | yes |
| API access | no | yes | yes |
| Saved filters | yes | yes | yes |
| SSO | no | yes | yes |
| Multiple SSO domains | no | no | yes |
| Audit log retention | 30 days | 90 days | 2 years |
| Sandbox tenant | no | no | yes |

## Behaviour when a feature is not entitled

The platform hides or disables the control, and an attempt made anyway is refused and written
to the audit log as:

```
result=denied  error_code=NOT_ENTITLED
```

## What changed on 2026-06-01

**Bulk export moved from Growth to Enterprise.** Accounts on Growth that used bulk export
before that date lost it, with 30 days' notice to account administrators.

Anything asking whether a Growth account was entitled to bulk export therefore depends
entirely on the date being asked about. Before 2026-06-01, yes. From 2026-06-01, no.
