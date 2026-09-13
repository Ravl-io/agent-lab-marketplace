# Findings pack — Milestone 2

Issued 2026-05-22 by Aisha Bello. Judged against the MSA as at 2026-01-15 — **before
Amendment 1**, so Severity 2 resolution is two business days throughout this pack.

Five findings. Four closed. **VQ-M2-003 remains open and disputed.**

---

## FINDING VQ-M2-001

**Severity:** 1
**Criterion not met:** AC-6 — no production personal data in any artifact
**Clause:** MSA 6.1

**What we found:** The capture test evidence contains a cardholder name and a partial card
number for what appears to be a real transaction.

**Evidence:** `M2-test-report.md`, test T-07 sample response.

**Required to close:** Redact and re-issue. Confirm in writing that the data did not originate
from production.

**Resolution due:** 8 hours from issue (MSA 7.1).

**Status:** Closed 2026-05-25. Halbrook confirmed the data was synthetic but agreed the format
was indistinguishable from production and re-issued with obvious placeholders.

---

## FINDING VQ-M2-002

**Severity:** 2
**Criterion not met:** AC-5 (M2) — test evidence for authorise and capture
**Clause:** MSA 4.1

**What we found:** No evidence for partial capture, which AC-4 (M2) explicitly requires.

**Evidence:** `M2-test-report.md`, test list T-01 to T-09.

**Required to close:** Add a partial capture test with evidence.

**Resolution due:** 2 business days from issue (MSA 7.2, original term).

**Status:** Closed 2026-05-29.

---

## FINDING VQ-M2-003

**Severity:** 2
**Criterion not met:** AC-4 — rate limits stated per endpoint, with behaviour on exceeding
**Clause:** MSA 5.1 — specification must cover all endpoints

**What we found:** The specification states that the API "is rate limited" without giving a
limit for any endpoint, and does not say what happens when a limit is exceeded.

**Evidence:** `M2-api-spec.md`, section "Rate limits", single sentence, no per-endpoint table.

**Required to close:** A per-endpoint rate limit table, and the response returned when the
limit is exceeded, including any `Retry-After` behaviour.

**Resolution due:** 2 business days from issue (MSA 7.2, original term).

**Status:** **Open.** Disputed by Halbrook 2026-05-27 — see `history/vendor-response-M2.md`.
Carried into Milestone 3 as a condition of M2 acceptance.

---

## FINDING VQ-M2-004

**Severity:** 3
**Criterion not met:** AC-7 (M2) — error catalogue for the payment path
**Clause:** MSA 5.1

**What we found:** Error codes are listed with one-word meanings and no remediation.

**Evidence:** `M2-api-spec.md`, errors table.

**Required to close:** Map each code to what an integrator should do about it.

**Resolution due:** 5 business days from issue (MSA 7.3).

**Status:** Closed 2026-06-01.

---

## FINDING VQ-M2-005

**Severity:** 2
**Criterion not met:** AC-8 (M2) — backwards compatibility statement against M1
**Clause:** MSA 5.1

**What we found:** The statement reads "M1 clients continue to work" with no detail of what
was checked.

**Evidence:** `M2-api-spec.md`, section "Compatibility".

**Required to close:** State which M1 endpoints were exercised against the M2 build, and the
result.

**Resolution due:** 2 business days from issue (MSA 7.2, original term).

**Status:** Closed 2026-05-30.
