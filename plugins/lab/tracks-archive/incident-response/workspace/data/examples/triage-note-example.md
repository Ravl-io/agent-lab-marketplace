# Triage note — house format

This is the format an on-call engineer expects. Every triage note we write looks like this,
in this order, with nothing added and nothing left out.

---

## TRIAGE — ALERT-3102 / payments-api p99 latency

**Assessment:** Sev-2. Customer-facing payment latency, revenue-affecting while it lasts.

**Most likely cause:** `ledger-db` connection pool saturation, driven by an overlapping
`settlement-batch` run. This matches INC-204 (2026-07-14), which had the same signature at
almost the same time of night.

**Evidence**
- p99 latency 3,900 ms against a 400 ms baseline, rising from 01:50
- `settlement-batch` nightly run began 01:45
- No `payments-api` deploy in the last 6 hours

**Blast radius:** `payments-api` (direct), `checkout-web` (customer-visible),
`merchant-portal` (degraded reporting). `settlement-batch` is the likely source, not a victim.

**Recommended action:** Raise `LEDGER_POOL_MAX` to 320 and roll restart, per the
`payments-api` runbook. Safe up to 400.

**Rollback:** Restore the previous value and roll restart. No data risk.

**Escalate to:** @rota-payments. Secondary @dara-oyelowo.

**Confidence:** High. Signature matches a known prior incident and the runbook's first check.

---

Notes on the format, for whoever writes the next one:

- **Assessment** is one line with a severity. Not a paragraph.
- **Evidence** is bullets of observable facts, never inference. If you cannot point at a
  number or a log line, it does not go in Evidence.
- **Blast radius** names services, and says which one is the source rather than a victim.
- **Confidence** is High, Medium or Low, with a reason. Low confidence is useful; a confident
  wrong answer at 2am is worse than an honest uncertain one.
