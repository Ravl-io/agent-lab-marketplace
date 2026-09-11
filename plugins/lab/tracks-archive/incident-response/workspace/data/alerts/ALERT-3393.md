# ALERT-3393

```
severity:     P2
fired_at:     2026-09-08T14:02:44Z
service:      fx-rates
monitor:      fx_vendor_latency_ms
condition:    > 800 for 10m
observed:     2,650 ms
```

## Metrics at fire time

| Metric | Value | Baseline |
|---|---|---|
| `fx_vendor_latency_ms` | 2,650 | 130 |
| `fx_cache_hit_rate` | 96.2% | 96.0% |
| `payments_api_p99_latency_ms` | 610 | 380 |
| `ledger_db_active_connections` | 71 / 200 | 60 / 200 |

## Recent log lines

```
14:02:31 fx-rates  WARN  vendor-fx response 2,610ms (threshold 800ms)
14:02:40 fx-rates  WARN  vendor-fx response 2,701ms
14:02:44 payments-api  WARN  fx lookup slow 2,680ms txn=c41a09
```

## Deploys in the last 6 hours

```
none
```

## External

```
vendor-fx status page: "Investigating elevated API response times" (posted 13:58Z)
```
