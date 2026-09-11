# Engineering sync notes — August 2026

## 2026-08-05

- Atlas migration: Priya says the schema cutover is done, backfill running. Expects to finish
  by the 12th. Flagged that the rollback window closes once backfill completes.
- Beacon rollout: paused. Waiting on the security review. Tomas chasing.
- Nobody has picked up the observability work. Third week running.

## 2026-08-12

- Atlas migration: backfill finished on the 11th, a day early. Priya wants it marked done.
- Beacon rollout: security review came back with two items, both minor. Tomas fixing, expects
  to restart the rollout on the 19th.
- Cirrus API: Lena raised that the vendor's rate limits are lower than we designed for. May
  need to renegotiate or add caching. Not yet a blocker but will be by September.

## 2026-08-19

- Beacon rollout: restarted, 30% of traffic. No issues so far.
- Cirrus API: confirmed the rate limit is a real problem. Lena estimates two weeks to add
  caching. Slipping the Cirrus milestone from 2026-09-15 to 2026-09-30.
- Atlas migration: done. Closed.

## 2026-08-26

- Beacon rollout: 100% of traffic since the 22nd. Closed.
- Cirrus API: caching work started. Lena confident on the 30th.
- Observability work: still unowned. Raised to Dana.
