# ALERT-3391

```
severity:     P1
fired_at:     2026-09-08T02:14:22Z
service:      payments-api
monitor:      payments_api_p99_latency_ms
condition:    > 1200 for 5m
observed:     4,380 ms
```

## Metrics at fire time

| Metric | Value | Baseline |
|---|---|---|
| `payments_api_p99_latency_ms` | 4,380 | 380 |
| `payments_api_5xx_rate` | 0.4% | 0.05% |
| `payments_api_auth_declines` | 2.1% | 2.0% |
| `ledger_db_active_connections` | 197 / 200 | 60 / 200 |
| `fx_vendor_latency_ms` | 140 | 130 |

## Recent log lines

```
02:13:58 payments-api  WARN  ledger pool wait 1840ms (queue=44)
02:14:02 payments-api  WARN  ledger pool wait 2210ms (queue=61)
02:14:19 payments-api  ERROR authorise timeout after 5000ms txn=8f21c4
02:14:20 checkout-web  ERROR payment gateway timeout, showing retry to user
```

## Deploys in the last 6 hours

```
none for payments-api
2026-09-07T22:10Z  merchant-portal  v8.3.1
```

## Other activity

```
02:45  settlement-batch  nightly run started (scheduled 01:45, delayed 60m by a retry)
```
