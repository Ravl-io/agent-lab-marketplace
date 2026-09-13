# Findings pack — Milestone 1

Issued 2026-03-18 by Aisha Bello. Judged against the MSA as at 2026-01-15.
Both findings closed; milestone accepted 2026-03-27.

---

## FINDING VQ-M1-001

**Severity:** 3
**Criterion not met:** AC-2 (M1) — token lifetime and refresh behaviour documented
**Clause:** MSA 5.1 — specification must cover all endpoints

**What we found:** Token lifetime is given as "configurable per client" with no default and no
range. A client integrator cannot tell how often to refresh.

**Evidence:** `M1-auth-spec.md`, section "Authentication", paragraph 2.

**Required to close:** State the default lifetime and the permitted range.

**Resolution due:** 5 business days from issue (MSA 7.3).

**Status:** Closed 2026-03-25.

---

## FINDING VQ-M1-002

**Severity:** 2
**Criterion not met:** AC-4 (M1) — test evidence with environment and build id
**Clause:** MSA 5.2 — evidence without a build identifier is not evidence

**What we found:** The test report names the environment but gives no build identifier, so the
evidence cannot be tied to a specific release.

**Evidence:** `M1-test-report.md`, header block.

**Required to close:** Re-issue the test report with the build identifier of the tested build.

**Resolution due:** 2 business days from issue (MSA 7.2, original term).

**Status:** Closed 2026-03-26.
