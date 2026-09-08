# raw incident notes — 2026-08-12 — payments latency (on-call: Dana R.)

ok writing this up quick before standup. pagerduty fired 09:41 ET, p99 latency on
POST /v2/payments went from ~180ms to 4.5s. checkout conversions dropping on the
dashboard almost immediately.

timeline (all ET):
- 09:41 alert fires
- 09:48 confirmed it's the payments svc, not the gateway. db connection pool exhausted
- 09:55 found it — the 08:30 deploy added a reporting query on the same pool. no index,
  full table scan on payment_events (230M rows lol)
- 10:02 rolled back the deploy
- 10:11 latency back to normal, pool healthy
- kept watching until 10:40, stable

customer impact: checkout was slow but NOT down. support says 37 tickets, mostly
"payment spinning". we think some carts abandoned but can't quantify yet, marketing
may have numbers next week.

sev: calling it SEV2 (degradation, not outage)

follow ups i think we need:
- reporting queries should NOT share the transactional pool -> separate read replica (me + Priya)
- deploy review should catch unindexed queries on big tables — maybe a lint rule? (Marcus?)
- the alert fired 11 min after latency started climbing, threshold too loose (Dana)
