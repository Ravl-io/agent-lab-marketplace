# Payments Integration API — Specification

Halbrook Systems. Submitted 2026-09-01. Build `hb-m3-rc4`.

## Authentication

Bearer tokens issued by `POST /oauth/token`. Tokens are valid for a period configured per
client.

Example request:

```
POST /oauth/token
client_id=northwind-prod&client_secret=s3cr3t-hb-9911&grant_type=client_credentials
```

## Endpoints

### POST /payments/authorise
Authorises a payment. Returns `201` with a payment id.

### POST /payments/{id}/capture
Captures an authorised payment. Returns `200`.

### POST /payments/{id}/refund
Refunds a captured payment. Returns `200`.

### GET /payments/{id}
Returns the payment.

## Errors

| Code | Meaning |
|---|---|
| 400 | Bad request |
| 401 | Unauthorised |
| 409 | Conflict |
| 500 | Server error |

## Rate limits

The API is rate limited to protect the service.

## Compatibility

Milestone 2 clients continue to work.
