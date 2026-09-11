# Runbook — payments-api

Last reviewed: 2026-08-11. Owner: Payments.

## What it does

Authorises and captures card payments. Every checkout goes through it. If it is degraded,
the business is losing money for as long as the degradation lasts.

## Health signals

- `payments_api_p99_latency_ms` — normal under 400 ms, page above 1200 ms for 5 minutes
- `payments_api_5xx_rate` — normal under 0.1%, page above 1%
- `payments_api_auth_declines` — a sudden *drop* is as suspicious as a spike; it usually
  means we are failing before reaching the issuer

## First five minutes

1. Check whether `ledger-db` connection pool is saturated:
   `SELECT count(*) FROM pg_stat_activity WHERE datname='ledger';`
   Above 180 of 200 means saturation. This is the single most common cause.
2. Check `fx-rates` response times. It calls a third-party vendor, and a slow vendor shows up
   here as payment latency. See the `fx-rates` runbook.
3. Check whether a deploy landed in the last 30 minutes. `payments-api` deploys are the
   second most common cause.

## Mitigations

| Situation | Action | Risk |
|---|---|---|
| Connection pool saturated | Raise `LEDGER_POOL_MAX` to 320 and restart rolling | Higher DB load; safe up to 400 |
| Recent bad deploy | Roll back to the previous release tag | Loses the deploy's changes; always safe |
| `fx-rates` vendor slow | Enable `FX_CACHE_FALLBACK=1` to serve rates up to 15 min stale | Slightly stale FX; finance must be told |

## Do not

- Do not restart all instances at once. Card authorisation is stateful mid-flight; a full
  restart drops in-flight authorisations and creates reconciliation work for Finance.
- Do not flush the `card-vault` cache. It requires a Security-approved change.
