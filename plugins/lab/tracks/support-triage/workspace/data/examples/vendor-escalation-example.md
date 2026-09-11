# Vendor escalation — house format

Used when triage lands on **product defect**. The vendor returns anything that is missing an
item from `escalation-policy.md`, and a returned case costs about four days.

---

## ESCALATION — VND-4xx (draft) / Duplicate rows in order export

**Severity:** S2 — major feature returning wrong data, workaround exists (manual dedupe)

**Account:** Marlowe Financial (acc-6620), Enterprise, region eu-west, platform **5.4.0**

**Summary:** Order exports contain duplicated rows for any order amended after creation. The
export completes successfully and reports the wrong row count.

**Reproduction**
1. Create an order, then amend its delivery date
2. Export orders for a range covering that order
3. The amended order appears twice, once per revision

Expected: one row per order. Actual: one row per revision.

**Audit log evidence**
```
event_id  action       result   error_code  detail
88213     order_export success  NULL        41,882 rows written
88214     order_export success  NULL        41,882 rows written
```
Both runs report success. The platform does not consider this an error, which is why nothing
appears in the error columns.

**Ruled out**
- Configuration: export settings are at their defaults; no filters applied
- Entitlement: `bulk_export` enabled for Enterprise, in force since 2024-01-01
- User error: reproduced by us on a clean account

**Scope:** 3 accounts confirmed, all regions, any order with more than one revision.
Approximately 4% of rows in a typical export.

**Known issues checked:** No open entry matches. KI-70 was the same symptom but was closed
as fixed in 5.4.0, which this account is running — flagging that as possibly related.

**Attachments:** export sample (rows redacted), audit log extract.

---

Notes:

- **Ruled out** comes before scope for a reason: it is the section the vendor reads first.
- Always name the platform version. A defect report without it gets returned.
- If a closed known issue matches the symptom, say so. A reopened defect is handled
  differently from a new one.
