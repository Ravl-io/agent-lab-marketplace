# INC-204 — Checkout latency during settlement window

- **Date:** 2026-07-14
- **Duration:** 47 minutes (01:52 – 02:39 UTC)
- **Severity:** Sev-2
- **Services affected:** `payments-api`, `checkout-web`
- **Root cause:** `settlement-batch` exhausted the `ledger-db` connection pool

## What happened

`settlement-batch` started its nightly run at 01:45 and opened 140 connections to
`ledger-db`. `payments-api` shares that pool. By 01:52 the pool was saturated at 198 of 200,
and `payments-api` p99 latency rose from 380 ms to 4,200 ms. `checkout-web` surfaced this to
customers as spinning payment buttons. Approximately 1,900 checkouts were affected and an
estimated 240 were abandoned.

## Timeline

| Time | Event |
|---|---|
| 01:45 | `settlement-batch` nightly run begins |
| 01:52 | `payments_api_p99_latency_ms` crosses 1200 ms; page fires |
| 02:03 | On-call checks `payments-api` deploys — none recent. Time lost here |
| 02:19 | Connection pool saturation identified |
| 02:24 | `LEDGER_POOL_MAX` raised 200 → 320, rolling restart |
| 02:39 | Latency back under 400 ms |

## Contributing factors

- The `payments-api` runbook lists pool saturation as the most common cause, but the on-call
  engineer checked deploys first. The runbook order did not match the actual likelihood.
- Nothing in our alerting connected `settlement-batch` activity to `payments-api` latency,
  even though they share `ledger-db`. The dependency is real but was invisible at 2am.

## Actions

- [x] Raise `LEDGER_POOL_MAX` permanently to 320
- [ ] Give `settlement-batch` a separate connection pool — **still open**, owner @dara-oyelowo
- [x] Reorder the `payments-api` runbook to put pool saturation first
