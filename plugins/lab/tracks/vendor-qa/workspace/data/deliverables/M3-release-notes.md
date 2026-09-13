# Payments Integration API — Release Notes

Halbrook Systems. Release **5.2.0**, submitted 2026-09-01.

## New in 5.2.0

- `POST /payments/{id}/refund` — refund a captured payment, full or partial
- Rate limiting enabled on all endpoints
- Error responses now return a machine-readable `code` field alongside the HTTP status

## Changed

- `POST /payments/{id}/capture` now accepts a partial `amount`. Omitting it captures the full
  authorised amount, as before.
- Token lifetime is now configured per client rather than fixed at one hour.

## Fixed since 5.1.0

- Duplicate rows in the order export (raised as VQ-M2-004 follow-up)
- Compatibility statement expanded per VQ-M2-005

## Known issues

- Concurrent refunds against the same payment may both succeed. Under investigation.

## Compatibility

Milestone 2 clients continue to work against 5.2.0 without change.
