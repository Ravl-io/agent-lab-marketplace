# Findings pack — house format

This is the format findings are issued in. One block per finding, in severity order.

**This example is a real finding from Milestone 2, issued 2026-05-22.** Read it for the shape.
Do not copy its resolution deadline: the Severity 2 term changed on 2026-06-30, so a finding
on a later milestone has a different one.

---

## FINDING VQ-M2-003

**Severity:** 2
**Criterion not met:** AC-4 (rate limits stated per endpoint, with behaviour on exceeding)
**Clause:** MSA 5.1 — specification must cover all endpoints

**What we found:** The specification states that the API "is rate limited" without giving a
limit for any endpoint, and does not say what happens when a limit is exceeded.

**Evidence:** `M2-api-spec.md`, section "Rate limits", single sentence, no per-endpoint table.

**Required to close:** A per-endpoint rate limit table, and the response returned when the
limit is exceeded, including any `Retry-After` behaviour.

**Resolution due:** 2 business days from issue (MSA 7.2, as in force on 2026-05-22).

---

Notes on the format:

- **Criterion not met** names the acceptance criterion. **Clause** names the contractual
  basis. A finding needs both, or the supplier will argue it.
- **Evidence** points at a location in the deliverable. Not a summary — a location.
- **Required to close** is written so the supplier knows exactly when they are done.
- Severity comes from the MSA, not from how annoyed you are.
