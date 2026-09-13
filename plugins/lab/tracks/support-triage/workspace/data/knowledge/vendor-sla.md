# Platform vendor SLA — extract

From our agreement with the platform vendor. Governs escalations we raise, not tickets our
customers raise with us.

| Severity | Definition | Acknowledge | Resolve |
|---|---|---|---|
| S1 | Platform unusable, no workaround | 1 hour | 8 hours |
| S2 | Major feature broken, workaround exists | 4 hours | 3 business days |
| S3 | Minor or cosmetic | 1 business day | 5 business days |

## What the clock starts on

Acknowledgement is measured from our escalation being accepted, **not** from us raising it.
An escalation returned for missing evidence never started the clock — which is why the
evidence requirements in `escalation-policy.md` matter commercially and not just procedurally.

## Regressions

A symptom that reappears after a fix has been released is treated as a **new escalation at
the same severity**, not as a reopening. The vendor's position is that a reopened case
restarts their internal triage; a new case referencing the original gets to an engineer
faster.

## What the SLA does not cover

- Accounts more than two minor versions behind the current release
- Anything traced to customer configuration
- Feature requests, however they are described
