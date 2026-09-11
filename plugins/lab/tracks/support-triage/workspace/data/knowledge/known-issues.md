# Known issues register

Defects confirmed with the platform vendor. Updated 2026-09-05.

Check this before escalating anything. A ticket that matches an open entry gets linked to the
existing vendor case rather than raising a new one.

---

## KI-77 — Saved filters not persisted for eu-west tenants

- **Vendor case:** VND-411
- **Status:** Fix released in **5.4.1** (2026-08-14)
- **Affects:** accounts in region `eu-west` only
- **Symptom:** saved filters load correctly during the session, then are absent the following
  day. Nothing appears in the audit log — the save succeeds and is acknowledged.
- **Cause (vendor's words):** filter records were written to a cache tier that was evicted
  nightly, and never promoted to durable storage.
- **Note added 2026-09-05:** two accounts already on 5.4.1 have reported the symptom
  returning. Not yet confirmed as a regression. **If you see this on 5.4.1, that is new
  information — escalate it and reference VND-411 rather than closing the ticket against
  this entry.**

## KI-81 — Scheduled report emails delayed

- **Vendor case:** VND-427
- **Status:** Open, vendor investigating
- **Affects:** all regions, scheduled reports over 100,000 rows
- **Symptom:** delivery delayed by up to 6 hours. The report itself is correct.
- **Workaround:** split the range, or deliver to a storage bucket instead of email.

## KI-84 — Audit log search returns partial results

- **Vendor case:** VND-433
- **Status:** Open, fix expected 5.4.3
- **Affects:** all regions
- **Symptom:** the audit log **UI search** silently truncates at 1,000 rows. Direct database
  queries are unaffected.
- **Workaround:** query the database directly. This matters for triage — do not trust the
  audit log UI for counting.

## Closed

| Ref | Title | Vendor case | Closed |
|---|---|---|---|
| KI-62 | SSO redirect loop on Safari 17 | VND-388 | 2026-05-20, fixed in 5.3.4 |
| KI-70 | Duplicate rows in order export | VND-402 | 2026-07-02, fixed in 5.4.0 |
