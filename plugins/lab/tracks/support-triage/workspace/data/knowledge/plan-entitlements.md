# Plan entitlement matrix

Last reviewed: 2026-09-01. **This matrix changed on 2026-06-01 — see the note at the end.**

| Feature | Starter | Growth | Enterprise |
|---|---|---|---|
| Standard reports | yes | yes | yes |
| Scheduled reports | no | yes | yes |
| Bulk export | no | **no** | yes |
| API access | no | yes | yes |
| Saved filters | yes | yes | yes |
| SSO | no | yes | yes |
| Multiple SSO domains | no | no | yes |
| Audit log retention | 30 days | 90 days | 2 years |
| Sandbox tenant | no | no | yes |

## Behaviour when a feature is not entitled

The platform **hides or disables** the control, and if the action is attempted anyway — by
API, or by a UI element still cached in the browser — it is refused and written to the audit
log as:

```
result=denied  error_code=NOT_ENTITLED
```

A disabled control that does nothing on click is the expected behaviour for an unentitled
feature. It is not a defect, though it reliably gets reported as one.

## Note on the 2026-06-01 change

**Bulk export moved from Growth to Enterprise on 2026-06-01.** Accounts on Growth that used
bulk export before that date lost it, with 30 days' notice sent to account administrators.

This is the single most common source of "it used to work and now it doesn't" tickets. If a
customer on Growth says a feature worked earlier in the year, check this list before
concluding anything is broken.

Customers who need it back go to their account manager, not to the vendor. The workaround is
a scheduled report, which Growth does include — see `bulk-export-guide.md`.
