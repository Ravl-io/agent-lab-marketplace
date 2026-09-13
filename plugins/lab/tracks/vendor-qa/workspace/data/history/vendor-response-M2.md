# Halbrook Systems — response to the Milestone 2 findings pack

From: Sunil Menon, Delivery Lead, Halbrook Systems
To: Aisha Bello, Northwind
Date: 2026-05-27
Re: Findings pack M2, issued 2026-05-22

Aisha,

Responses to each finding below. Four we accept. One we do not.

**VQ-M2-001 (S1, personal data).** Accepted without reservation. The data was synthetic but
we accept it was indistinguishable from production, which is the point of the clause.
Re-issued 2026-05-25 with obvious placeholders. Our QA process has been changed so generated
test data uses reserved example domains.

**VQ-M2-002 (S2, partial capture evidence).** Accepted. Test added, evidence issued
2026-05-29.

**VQ-M2-003 (S2, rate limits).** **We do not accept this finding.** AC-4 requires rate limits
to be "stated per endpoint". Our position is that the platform applies a single global limit
rather than per-endpoint limits, and that stating one global figure satisfies the criterion as
written. We are willing to document the global figure and the 429 behaviour, but we do not
accept that a per-endpoint table is required by the SOW as drafted. We suggest this is a
drafting issue in AC-4 rather than a defect in the deliverable.

**VQ-M2-004 (S3, error catalogue).** Accepted. Remediation column added, issued 2026-06-01.

**VQ-M2-005 (S2, compatibility statement).** Accepted. Detail added, issued 2026-05-30.

On the resolution windows: we have met the two-business-day term on each of the S2 findings,
but I want to flag that it is not sustainable for anything needing a release across our
timezones. I will raise it separately.

Regards,
Sunil
