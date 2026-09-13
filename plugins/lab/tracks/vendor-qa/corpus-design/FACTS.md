# vendor-qa corpus — the fact sheet

**Facilitator reference. Not shipped to participants.** Every document in `workspace/data/`
is written from this table. Change a fact here first, then fix every document that states it.
`corpus-design/check_consistency.py` enforces the machine-checkable parts.

Northwind has engaged **Halbrook Systems** to deliver a payments integration across three
milestones. M1 and M2 are accepted; **M3 is under review** — that is the participant's job.

## Milestones

| Ref | Scope | Submitted | Findings issued | Outcome |
|---|---|---|---|---|
| M1 | Authentication and token handling | 2026-03-06 | 2026-03-18 | Accepted 2026-03-27 |
| M2 | Payment authorise and capture | 2026-05-08 | **2026-05-22** | Accepted with conditions 2026-06-02 |
| M3 | Refunds, idempotency, rate limits | 2026-09-01 | *not yet* | **Under review** |

MSA 4.2 gives the Client ten business days from submission to issue findings. Both issued
dates are inside that window; M3's window closes 2026-09-15.

## The MSA and its amendments — the temporal trap

The contract has been amended **twice**. A milestone is judged against the clauses in force
at **its own submission date**, which is not today's.

| Amendment | Effective | What changed |
|---|---|---|
| — | 2026-01-15 | Original MSA |
| A1 | **2026-06-30** | Clause 7.2: Severity 2 resolution extended from **2 to 3 business days** |
| A2 | **2026-08-15** | New clause 5.4: an API deliverable must include a **machine-readable OpenAPI file**, not only a specification document |

Consequences the corpus depends on:

- **VQ-M2-003** was issued 2026-05-22, before A1. Its S2 resolution term is **2 business
  days**. The worked example in `data/examples/findings-pack-example.md` states 2 days and is
  period-accurate. A participant who copies that number into an M3 finding is **wrong** — M3
  was submitted after A1, so M3's S2 term is 3 business days.
- **Clause 5.4 only exists for M3.** M1 and M2 could not have failed it. M3 *does* fail it —
  the deliverables contain a specification document and no machine-readable file. A reviewer
  working from the original MSA misses this finding entirely.

## Requirements register

| Req | Requirement | Milestone | Verified by | Status |
|---|---|---|---|---|
| R-01 | Authenticate a client and issue a token | M1 | AC-1 (M1) | verified 2026-03-27 |
| R-02 | Refresh a token without re-authenticating | M1 | AC-2 (M1) | verified 2026-03-27 |
| R-03 | Authorise a payment | M2 | AC-3 (M2) | verified 2026-06-02 |
| R-04 | Capture an authorised payment | M2 | AC-4 (M2) | verified 2026-06-02 |
| R-05 | Refund a captured payment | M3 | AC-5 | pending |
| R-06 | Idempotent retries on all write endpoints | M3 | AC-3 | pending |
| R-07 | Rate limiting with documented behaviour | M3 | AC-4 | pending |
| R-08 | Error codes mapped to remediation | M3 | AC-7 | pending |
| R-09 | No production personal data in artifacts | all | AC-6 | pending |
| R-10 | Backwards compatible with M2 clients | M3 | AC-8 | pending |
| R-11 | Machine-readable API definition | M3 | **nothing** | **coverage gap** |
| R-12 | Webhook delivery guarantees documented | M4 | — | not yet due |

**R-11 is the planted coverage gap.** It exists because of amendment A2, but the M3 SOW was
written on 2026-08-20 and its criteria were not updated — so no acceptance criterion verifies
it. A requirement nobody verifies is a gap, never a pass.

## Findings history

| Ref | Milestone | Severity | Criterion | Issued | Status |
|---|---|---|---|---|---|
| VQ-M1-001 | M1 | 3 | AC-2 (M1) | 2026-03-18 | Closed 2026-03-25 |
| VQ-M1-002 | M1 | 2 | AC-4 (M1) | 2026-03-18 | Closed 2026-03-26 |
| VQ-M2-001 | M2 | 1 | AC-6 | 2026-05-22 | Closed 2026-05-25 |
| VQ-M2-002 | M2 | 2 | AC-5 (M2) | 2026-05-22 | Closed 2026-05-29 |
| VQ-M2-003 | M2 | 2 | AC-4 | 2026-05-22 | **Open** — disputed by Halbrook, re-raised on M3 |
| VQ-M2-004 | M2 | 3 | AC-7 | 2026-05-22 | Closed 2026-06-01 |
| VQ-M2-005 | M2 | 2 | AC-8 | 2026-05-22 | Closed 2026-05-30 |

VQ-M2-003 (rate limits not quantified) was **disputed** in Halbrook's response of 2026-05-27
and never closed. MSA 4.3 says a deliverable rejected twice for the same finding escalates to
the steering group — so if M3 fails AC-4 again, that is the **second** rejection and it
escalates. That fact requires the M2 findings pack *and* the vendor response *and* MSA 4.3.

## What M3 actually fails

The answer key for the participant's review. Every one is evidenced in the deliverables:

| Finding | Severity | Criterion | Clause | Evidence |
|---|---|---|---|---|
| Credential in the specification | **1** | AC-6 | MSA 6.2 | `M3-api-spec.md`, the `/oauth/token` example |
| Production personal data in test evidence | **1** | AC-6 | MSA 6.1 | `M3-test-report.md`, the T-03 sample response |
| Rate limits not quantified per endpoint | 2 | AC-4 | MSA 5.1 | `M3-api-spec.md`, "Rate limits" section — **second rejection, escalates under 4.3** |
| Idempotency not documented | 2 | AC-3 | MSA 5.1 | `M3-api-spec.md` — no idempotency key on any write endpoint |
| No machine-readable OpenAPI file | 2 | — *(no AC covers it)* | **MSA 5.4, as amended 2026-08-15** | deliverables contain no `.yaml`/`.json` definition |
| Test evidence has no build identifier | 2 | AC-5 | MSA 5.2 | `M3-test-report.md` states an environment but no build id |
| Error catalogue has no remediation | 3 | AC-7 | MSA 5.1 | `M3-api-spec.md`, the four-row error table |
| Refund endpoint has no test evidence | 2 | AC-5 | MSA 4.1 | `M3-test-report.md` covers T-01…T-04, none of them refund |

## The three questions retrieval must get wrong

1. **Multi-hop** — "Which requirements are verified by a criterion that M3 fails?"
   Needs the requirements register (req → AC) *and* the M3 findings (which AC failed). Neither
   document contains both halves.
2. **Aggregation** — "How many requirements has nobody verified across the whole engagement?"
   The complete set across the register and three findings packs. Top-k returns the most
   similar rows, never the complete set. The answer is **R-11**, plus everything still pending.
3. **Temporal** — "What is the resolution deadline for a Severity 2 finding on M3, and was it
   the same for M2?" Three business days for M3, two for M2, because of A1 on 2026-06-30.

## Metadata that has to exist for filters to matter

| Field | Why a filter needs it |
|---|---|
| `milestone` (M1 / M2 / M3) | "the M2 findings" must not retrieve M1's |
| `doc_type` (msa / amendment / sow / register / deliverable / findings / vendor-response / acceptance) | "what did the vendor say" should not return our own findings |
| `valid_from` / `valid_to` | the amended clauses |
| `severity` | the S1 questions |

## People

Northwind: Dana Whitfield (programme director) · Rina Petrova (PMO) ·
Aisha Bello (delivery manager, issues the findings) · Fen Alvarez (finance)
Halbrook Systems: Gregor Halbrook (account director) · Sunil Menon (delivery lead) ·
Elke Vogt (QA lead)
