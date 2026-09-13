# MSA amendment log

Between Northwind Ltd ("Client") and Halbrook Systems ("Supplier").
Original agreement effective 2026-01-15.

A milestone is judged against the clauses **in force at its own submission date**. This log
is the only place that mapping is recorded, so check it before quoting a term.

---

## Amendment 1 — effective 2026-06-30

**Clause 7.2 replaced.**

- *Before:* Severity 2 defects: acknowledged within 4 hours, **resolved within 2 business
  days**.
- *After:* Severity 2 defects: acknowledged within 4 hours, **resolved within 3 business
  days**.

Rationale recorded at signature: Halbrook's escalation that two business days was not
achievable across timezones for defects requiring a release.

**Applies to:** milestones submitted on or after 2026-06-30. M1 (submitted 2026-03-06) and
M2 (submitted 2026-05-08) remain on the two-business-day term.

---

## Amendment 2 — effective 2026-08-15

**New clause 5.4 inserted.**

> **5.4** An API deliverable must include a machine-readable API definition — an OpenAPI 3.1
> document in YAML or JSON — in addition to any prose specification. A specification document
> alone does not satisfy clause 5.1.

Rationale recorded at signature: Northwind's integration team cannot generate clients from a
prose document, and two integration defects in M2 were traced to ambiguity that a
machine-readable definition would have prevented.

**Applies to:** milestones submitted on or after 2026-08-15. M3 was submitted 2026-09-01 and
is therefore subject to clause 5.4. M1 and M2 were not.
