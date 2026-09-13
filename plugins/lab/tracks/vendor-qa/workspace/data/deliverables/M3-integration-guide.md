# Payments Integration API — Integration Guide

Halbrook Systems. Submitted 2026-09-01. Release 5.2.0.

## Getting started

1. Obtain client credentials from your Halbrook account manager.
2. Exchange them for a bearer token at `POST /oauth/token`.
3. Include the token as `Authorization: Bearer <token>` on every request.

## The payment lifecycle

```
authorise  ->  capture  ->  (optional) refund
```

An authorisation expires if not captured. A capture may be for the full amount or less. A
refund returns funds against a captured payment.

## Sequencing

Call `POST /payments/authorise` first and retain the returned `payment_id`. All subsequent
calls address the payment by that id. Do not assume ordering between concurrent calls on the
same payment; the platform serialises them but does not guarantee which arrives first.

## Retries

If a call fails with a `5xx`, retry it. We recommend an exponential backoff starting at one
second.

## Environments

| Environment | Base URL |
|---|---|
| Sandbox | `https://sandbox.halbrook.example/v5` |
| Production | `https://api.halbrook.example/v5` |

## Support

Raise integration questions with your account manager. Defects follow the process in the
master services agreement.
