# Master Services Agreement — relevant clauses

Between Northwind Ltd ("Client") and Halbrook Systems ("Supplier").
Effective 2026-01-15. **Amended 2026-06-30 — see amendment note in clause 7.3.**

## 4. Deliverable acceptance

**4.1** Each deliverable is accepted only when it satisfies every acceptance criterion in the
applicable Statement of Work.

**4.2** The Client has ten business days from submission to issue findings. Findings must
cite the criterion or clause not met.

**4.3** A deliverable rejected twice for the same finding escalates to the steering group.

## 5. Documentation standards

**5.1** Every API deliverable includes an OpenAPI 3.1 specification covering all endpoints,
including error responses.

**5.2** Test evidence must state the environment, the build identifier, and the date of
execution. Evidence without a build identifier is not evidence.

**5.3** Documentation is delivered in English, in a text-based format under version control.

## 6. Security

**6.1** No production personal data may appear in test evidence, screenshots or logs.

**6.2** Any credential appearing in a deliverable is a Severity 1 finding and must be rotated
by the Supplier within 24 hours of notice.

## 7. Service levels

**7.1** Severity 1 defects: acknowledged within 1 hour, resolved within 8 hours.

**7.2** Severity 2 defects: acknowledged within 4 hours, resolved within 3 business days.

**7.3** *Amended 2026-06-30:* Severity 2 resolution was extended from 2 to 3 business days.
Findings issued before 2026-06-30 are judged against the original 2-business-day term.
