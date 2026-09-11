# INC-231 — Webhook backlog

- **Date:** 2026-08-02
- **Duration:** 3 hours 12 minutes
- **Severity:** Sev-3
- **Services affected:** `webhook-dispatcher`
- **Root cause:** One merchant's endpoint began returning 504s; retries consumed all workers

## What happened

Merchant `mrc-8841` (a large marketplace) deployed a change that made their webhook endpoint
time out at 30 seconds. Our retry policy held workers open for the full timeout, so eight
workers spent three hours retrying one merchant. Queue depth reached 214,000. Every other
merchant's events were delayed by up to two hours.

## Timeline

| Time | Event |
|---|---|
| 09:14 | `mrc-8841` endpoint starts returning 504 |
| 09:40 | `webhook_queue_depth` crosses 50,000; page fires |
| 10:05 | On-call scales workers 8 → 24. Queue keeps growing — scaling did not help, because the problem was one slow consumer, not capacity |
| 11:50 | Per-merchant failure breakdown run; `mrc-8841` identified |
| 11:58 | `mrc-8841` subscription paused |
| 12:26 | Queue drained |

## Contributing factors

- The runbook's first step is to check consumer lag, and its second is the per-merchant
  breakdown. Reversing those two steps would have saved almost two hours.
- Scaling workers is the intuitive response and the wrong one when a single endpoint is slow.
- The `webhook-dispatcher` runbook was last reviewed in March and still describes the
  pre-4.2 retry policy, which had a 5-second timeout rather than 30.

## Actions

- [x] Pause `mrc-8841` until they fixed their endpoint
- [ ] Add a per-merchant circuit breaker — **still open**, owner @sam-ndiaye
- [ ] Update the `webhook-dispatcher` runbook for the 4.2 retry policy — **still open**
