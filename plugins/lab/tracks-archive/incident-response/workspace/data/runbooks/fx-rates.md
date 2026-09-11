# Runbook — fx-rates

Last reviewed: 2026-07-28. Owner: Payments.

## What it does

Supplies currency conversion rates to `payments-api`. Calls `vendor-fx`, a third party, and
caches results for 60 seconds.

## Health signals

- `fx_vendor_latency_ms` — normal under 150 ms, concerning above 800 ms
- `fx_cache_hit_rate` — normal above 95%. A drop means the cache is being bypassed

## First five minutes

1. Check `vendor-fx` status page before anything else. Roughly half of `fx-rates` incidents
   are the vendor's, and there is nothing to fix on our side.
2. Check cache hit rate. A deploy that changes the cache key silently drops the hit rate and
   multiplies vendor calls.

## Mitigations

| Situation | Action | Risk |
|---|---|---|
| Vendor slow or down | `FX_CACHE_FALLBACK=1` — serve rates up to 15 min stale | Finance must be notified; do not leave on beyond 4 hours |
| Cache hit rate collapsed after deploy | Roll back | Safe |

## Contractual note

Our agreement with `vendor-fx` allows stale-rate fallback for up to 4 hours per incident.
Beyond that, Finance has to file a rate adjustment. Tell them early, not late.
