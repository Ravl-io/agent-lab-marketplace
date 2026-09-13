# Requirements register — Payments Integration

Maintained by the PMO. A requirement with no verifying criterion is a **coverage gap**, not a
pass.

| Req | Requirement | Milestone | Verified by | Status |
|---|---|---|---|---|
| R-01 | Authenticate a client and issue a token | M1 | AC-1 (M1) | verified 2026-03-27 |
| R-02 | Refresh a token without re-authenticating | M1 | AC-2 (M1) | verified 2026-03-27 |
| R-03 | Authorise a payment | M2 | AC-3 (M2) | verified 2026-06-02 |
| R-04 | Capture an authorised payment, including partial capture | M2 | AC-4 (M2) | verified 2026-06-02 |
| R-05 | Refund a captured payment | M3 | AC-5 | pending |
| R-06 | Idempotent retries on all write endpoints | M3 | AC-3 | pending |
| R-07 | Rate limiting with documented behaviour | M3 | AC-4 | pending |
| R-08 | Error codes mapped to remediation | M3 | AC-7 | pending |
| R-09 | No production personal data in artifacts | all | AC-6 | pending |
| R-10 | Backwards compatible with M2 clients | M3 | AC-8 | pending |
| R-11 | Machine-readable API definition | M3 | — | **no verifying criterion** |
| R-12 | Webhook delivery guarantees documented | M4 | — | not yet due |

## Note on R-11

R-11 was added on 2026-08-15 when MSA Amendment 2 introduced clause 5.4. The Milestone 3
statement of work was drafted on 2026-08-20 and its acceptance criteria were **not** updated
to cover it. Nothing in AC-1 to AC-8 verifies R-11.

This is a gap in our own paperwork, not in Halbrook's delivery — but the requirement is
contractual from 2026-08-15, and M3 was submitted 2026-09-01.
