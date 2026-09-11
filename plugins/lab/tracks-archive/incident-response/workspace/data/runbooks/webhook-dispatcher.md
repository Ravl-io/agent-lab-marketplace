# Runbook — webhook-dispatcher

Last reviewed: 2026-03-02. Owner: Integrations.

**Note: this runbook is overdue for review.** The retry policy described below changed in
release 4.2 and this document has not been updated.

## What it does

Delivers payment events to merchant endpoints. Backlog is normal in small amounts; sustained
growth is not.

## Health signals

- `webhook_queue_depth` — normal under 5,000, page above 50,000
- `webhook_delivery_failures` — normal under 2% (merchant endpoints are unreliable by nature)

## First five minutes

1. Check `event-bus` consumer lag. If the dispatcher is not consuming, the queue grows even
   with healthy merchants.
2. Identify whether failures concentrate on a few merchants. One large merchant with a broken
   endpoint routinely looks like a platform incident.
   `SELECT merchant_id, count(*) FROM webhook_failures GROUP BY 1 ORDER BY 2 DESC LIMIT 10;`
3. Check whether `payments-api` is healthy. No payments means no events, which shows up as a
   *falling* queue depth — a quiet dispatcher can mean an upstream outage.

## Mitigations

| Situation | Action | Risk |
|---|---|---|
| Single merchant failing | Pause that merchant's subscription | That merchant stops receiving events; they must be notified |
| Consumer lag, healthy merchants | Scale dispatcher workers from 8 to 24 | More load on merchant endpoints |
| Queue above 200,000 | Enable `WEBHOOK_SHED_LOW_PRIORITY=1` | Low-priority events are dropped, not delayed. Irreversible |
