# Statement of Work — Milestone 3: Payments Integration API

Acceptance criteria drafted 2026-08-20. Submitted for acceptance 2026-09-01.

**Judged against the MSA as amended 2026-08-15.** Both amendments in force at that date
apply; see `contract/MSA-amendments.md` for what they changed. The criteria below were
drafted on 2026-08-20 and have not been reviewed against the amendments since.

## Scope

Halbrook delivers a payments integration API, its specification, and test evidence.

## Acceptance criteria

| ID | Criterion |
|---|---|
| AC-1 | OpenAPI 3.1 spec covering all endpoints, including every error response |
| AC-2 | Authentication documented, including token lifetime and refresh behaviour |
| AC-3 | Idempotency documented for all write endpoints |
| AC-4 | Rate limits stated per endpoint, with the behaviour on exceeding them |
| AC-5 | Test evidence for every endpoint, stating environment, build id and date |
| AC-6 | No production personal data anywhere in the deliverable |
| AC-7 | Error catalogue mapping every error code to a remediation |
| AC-8 | Backwards compatibility statement against Milestone 2 |

## Deliverables

- `M3-api-spec.md` — the API specification
- `M3-test-report.md` — test evidence
