# docgen corpus — the fact sheet

**Facilitator reference. Not shipped to participants.** Every document in
`workspace/data/` is written from this table. When you add a document, write it from here;
when you change a fact, change it here first and then fix every document that states it.
`corpus-design/check_consistency.py` enforces the parts that are machine-checkable.

The corpus covers **June, July and August 2026** of Northwind's delivery programme.

## Projects

| Project | Owner | Jun | Jul | Aug |
|---|---|---|---|---|
| Atlas Migration | Priya Raghunathan | In progress, cutover due 2026-08-05 | At risk, slipped to 2026-08-12 | **Complete**, delivered 2026-08-11 |
| Beacon Rollout | Tomas Lindqvist | 10% traffic delivered 2026-06-24 | 30% due 2026-07-28, delivered 2026-07-26 | **Complete**, 100% delivered 2026-08-22 |
| Cirrus API Integration | Lena Okonkwo | Design in progress | Sign-off due 2026-07-22, delivered 2026-07-22 | **At risk**, go-live 2026-09-15 → 2026-09-30 |
| Observability Programme | *unassigned* → Dana Whitfield (2026-08-26) | Scoping due 2026-06-30, **Not started** | Not started | Not started |
| Halo Reporting | Marcus Bell | *does not exist yet* | Discovery due 2026-07-31, delivered 2026-07-29 | Build due 2026-09-12, **In progress** |

Halo Reporting enters the programme on **2026-07-02** via CR-12. Anything dated before that
must not mention it.

## Milestone slips — the complete set

There are exactly **three** across the three months. This is the answer to the aggregation
question, and it must be derivable only by reading all three months.

| Milestone | Owner | Moved | Month reported |
|---|---|---|---|
| Atlas schema cutover | Priya Raghunathan | 2026-08-05 → 2026-08-12 | July |
| Cirrus integration live | Lena Okonkwo | 2026-09-15 → 2026-09-30 | August |
| Observability scoping | unassigned | 2026-06-30 → 2026-09-30 | July |

## Dependencies — deliberately scattered

The multi-hop question is *"which projects were waiting on Atlas Migration to finish?"*. The
answer is **Cirrus API and Halo Reporting**, and neither dependency appears in any status
update or metrics file:

| Dependency | Stated only in |
|---|---|
| Cirrus API needs Atlas's ledger schema | `charters/cirrus-charter.md` |
| Halo Reporting reads the migrated schema | `minutes/steering-2026-07-16.md` |

Beacon Rollout depends on nothing. Observability depends on nothing.

## Risks

| Ref | Risk | Owner | Severity | Opened | Closed |
|---|---|---|---|---|---|
| R-01 | Rollback impossible after Atlas backfill | Priya Raghunathan | High | 2026-06-03 | 2026-08-11 |
| R-02 | Beacon security review has no committed date | Tomas Lindqvist | High | 2026-06-10 | 2026-07-18 |
| R-03 | Cirrus vendor rate limits below design assumptions | Lena Okonkwo | Medium | 2026-07-15 | — |
| R-04 | Observability programme has no owner | unassigned → Dana Whitfield | Medium | 2026-06-17 | — |
| R-05 | Reporting DB replica lag | Dana Whitfield | Low | 2026-05-20 | 2026-06-20 |
| R-06 | Halo scope not agreed with finance | Marcus Bell | Medium | 2026-08-05 | — |

Open at each month end: **May 1** (R-05), **June 3** (R-01, R-02, R-04),
**July 3** (R-01, R-03, R-04), **August 3** (R-03, R-04, R-06).

Milestones due / delivered on time / slipped that month:
**June 2 / 1 / 0** · **July 3 / 3 / 2** · **August 2 / 2 / 1**. The three slips are the table
above; June records none because Observability had no new date until July.

## Change requests

| Ref | Request | Raised | Outcome |
|---|---|---|---|
| CR-11 | Extend Cirrus scope to include refunds | 2026-07-08 | Rejected 2026-07-16 |
| CR-12 | Add Halo Reporting to the programme | 2026-06-25 | Approved 2026-07-02 |
| CR-13 | Move Cirrus go-live to 2026-09-30 | 2026-08-19 | Approved 2026-08-26 |

## The charter versions — the temporal question

`charters/atlas-charter.md` carries **two versions in one file**, which is how charters
actually get maintained:

- **v1, 2026-02-10** — scope includes the reporting views migration
- **v2, 2026-05-14** — reporting views **descoped**, moved to what later became Halo Reporting

So *"was the reporting views migration in Atlas's scope in April 2026?"* is **yes**, and in
June it is **no**. An answer without a date is wrong half the time. This is the near-duplicate
that only a validity date separates.

## The three questions retrieval must get wrong

Module 2 ends by demonstrating these and leaving them broken. Module 3 opens on them.

1. **Multi-hop** — "Which projects were waiting on Atlas Migration to finish?"
   Needs the Cirrus charter *and* a July steering minute. Similarity search on "Atlas" returns
   status updates, which do not mention either dependant.
2. **Aggregation** — "How many milestones slipped across the programme, and who owns them?"
   Three, in three different monthly files. Top-k returns the most similar few, never the
   complete set.
3. **Temporal** — "Was the reporting views migration in Atlas's scope in April 2026?"
   Both charter versions are in one file and read as equally relevant. Answering needs the
   validity dates, not the text.

## Metadata that has to exist for filters to matter

| Field | Why a filter needs it |
|---|---|
| `period` (2026-06 / 07 / 08) | "the August figures" must not retrieve June's |
| `doc_type` (status / notes / metrics / minutes / email / register / charter / report) | "what did the steering group decide" should not return standup chatter |
| `valid_from` / `valid_to` | the charter versions, and any superseded fact |
| `project` | the aggregation questions |

## People

Priya Raghunathan (Atlas) · Tomas Lindqvist (Beacon) · Lena Okonkwo (Cirrus) ·
Marcus Bell (Halo) · Dana Whitfield (programme director, Observability from 2026-08-26) ·
Rina Petrova (PMO, writes the minutes) · Fen Alvarez (finance business partner)
