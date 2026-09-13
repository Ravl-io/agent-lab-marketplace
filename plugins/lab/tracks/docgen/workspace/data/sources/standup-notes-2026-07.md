# Engineering sync notes — July 2026

## 2026-07-01

- Atlas migration: Priya reports backfill throughput on staging is about 60% of what the
  rehearsal suggested. Wants to re-forecast before committing to the 5 August cutover.
- Beacon rollout: still waiting on security. Tomas has escalated twice with no date back.
- Cirrus: Lena's team started the integration design. Nothing to report yet.
- Observability: unowned. Raised again. No decision.

## 2026-07-08

- Atlas migration: re-forecast done — Priya wants one more week, so 12 August. Flagged that
  once the backfill runs the rollback window closes, so the rehearsal has to happen first.
- Cirrus: Lena raised CR-11 to extend scope to include refunds. Dana asked for a cost before
  it goes to steering.
- Halo: Marcus is pre-reading the CR-12 material ahead of formal start.

## 2026-07-16

- Beacon rollout: security review landed. Two minor items, both fixed same day. Tomas expects
  to restart on the 19th and hit 30% by the 28th.
- Cirrus: CR-11 rejected at steering — refunds stay out of scope for this phase.
- Observability: raised at steering. Rina's minute records it as unresolved. Third month.
- Halo: formally in the programme since the 2nd. Marcus has started discovery.

## 2026-07-23

- Atlas migration: rehearsal completed on staging. Priya confident on the 12th.
- Cirrus: design sign-off went through on the 22nd, on the date. Lena flagged that the
  vendor's published rate limits are lower than the design assumed — she opened R-03 on the
  15th and now has numbers: 120 requests/minute against a design assumption of 500.
- Halo: discovery on track for the 31st.

## 2026-07-30

- Beacon rollout: 30% traffic since the 26th, no issues.
- Halo: discovery finished a day early, on the 29th. Marcus notes finance have not seen the
  scope yet, which he thinks is a risk.
- Cirrus: Lena estimates two weeks of caching work to live within the vendor's limits. Not
  yet a date change — she wants to confirm with the vendor first.
