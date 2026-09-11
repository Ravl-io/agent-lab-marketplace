# Payments Integration API — Test Report

Halbrook Systems. Submitted 2026-09-01.

## Summary

All tests passed.

| Test | Endpoint | Result |
|---|---|---|
| T-01 | POST /payments/authorise | PASS |
| T-02 | POST /payments/{id}/capture | PASS |
| T-03 | GET /payments/{id} | PASS |
| T-04 | POST /oauth/token | PASS |

Environment: staging. Executed by the Halbrook QA team.

## Sample response captured during T-03

```json
{
  "payment_id": "pay_88213",
  "amount": 4200,
  "currency": "GBP",
  "cardholder": "Marta Villanueva",
  "email": "m.villanueva@example-merchant.co.uk",
  "card_last4": "4417",
  "status": "captured"
}
```
