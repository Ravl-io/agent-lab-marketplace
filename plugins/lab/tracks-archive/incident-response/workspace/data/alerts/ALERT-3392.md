# ALERT-3392

```
severity:     P2
fired_at:     2026-09-08T09:41:07Z
service:      webhook-dispatcher
monitor:      webhook_queue_depth
condition:    > 50000
observed:     58,400 and rising
```

## Metrics at fire time

| Metric | Value | Baseline |
|---|---|---|
| `webhook_queue_depth` | 58,400 | 1,200 |
| `webhook_delivery_failures` | 31% | 1.8% |
| `event_bus_consumer_lag` | 400 | 250 |
| `webhook_workers_busy` | 8 / 8 | 3 / 8 |

## Failures by merchant, last 15 minutes

```
mrc-4417   14,902
mrc-8841       61
mrc-2205       44
mrc-9910       31
(212 other merchants, all under 20)
```

## Recent log lines

```
09:40:51 webhook-dispatcher  WARN  delivery attempt 4 failed merchant=mrc-4417 status=504 elapsed=30001ms
09:40:55 webhook-dispatcher  WARN  all workers busy, queue growing
09:41:02 webhook-dispatcher  WARN  delivery attempt 5 failed merchant=mrc-4417 status=504 elapsed=30002ms
```

## Deploys in the last 6 hours

```
none
```
