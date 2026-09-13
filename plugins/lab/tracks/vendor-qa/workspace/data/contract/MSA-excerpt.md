# Master Services Agreement — relevant clauses

Between Northwind Ltd ("Client") and Halbrook Systems ("Supplier").
Effective 2026-01-15. **Amended twice — see `contract/MSA-amendments.md` for the dates and
what each amendment changed.** A milestone is judged against the clauses in force at its own
submission date.

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

**5.4** *Inserted by Amendment 2, effective 2026-08-15.* An API deliverable must include a
machine-readable API definition — an OpenAPI 3.1 document in YAML or JSON — in addition to any
prose specification. A specification document alone does not satisfy clause 5.1.

## 6. Security

**6.1** No production personal data may appear in test evidence, screenshots or logs.

**6.2** Any credential appearing in a deliverable is a Severity 1 finding and must be rotated
by the Supplier within 24 hours of notice.

## 7. Service levels

**7.1** Severity 1 defects: acknowledged within 1 hour, resolved within 8 hours.

**7.2** Severity 2 defects: acknowledged within 4 hours, resolved within **3 business days**.
*Amended by Amendment 1, effective 2026-06-30; the original term was 2 business days, which
still applies to milestones submitted before that date.*

**7.3** Severity 3 defects: acknowledged within 1 business day, resolved within 5 business
days.
