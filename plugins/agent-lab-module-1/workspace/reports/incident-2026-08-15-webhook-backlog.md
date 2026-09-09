# raw notes 2026-08-15 — partner webhook backlog (on-call: Marcus T.)

not paged for this one — partner (Fairmont) emailed their TAM saturday morning
saying they hadn't received trade-confirmation webhooks since friday evening. checked monday.

what happened: webhook dispatcher worker crashed friday ~19:20 ET on an oversized
payload (a bulk statement run with 1,400 accounts, serialized to 9MB, worker has an 8MB
cap). the worker is supervised but the SAME message kept poisoning it on restart —
crash loop all weekend. queue backed up to ~310k undelivered events across 12 partners.

fix monday 09:00-11:30 ET: dead-lettered the poison message, bumped worker memory cap,
drained the backlog by ~14:00. all partners caught up by 14:00 monday.

impact: 12 partner integrations received trade-confirmation events late (up to ~66h). Fairmont is
the only one who complained but they're the biggest. no data lost, everything delivered
eventually. internal only? no — partners are customers, calling it SEV2. honestly could
argue SEV3 since our own app was fine. going with SEV2.

follow-ups:
- dead-letter queue for poison messages instead of crash loop (Marcus, this week)
- alert on queue depth — we had NO alert on dispatcher backlog, found out from a customer
  email, that's embarrassing (Dana)
- payload size: either raise cap properly or split bulk statement runs at source (needs product
  decision — Priya to raise)
