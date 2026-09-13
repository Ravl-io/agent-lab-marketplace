# Module 4 — running the capstone

**Facilitator only.** The answer keys below are what you grade against. Participants have not
seen them, and the reference solutions and corpus answer keys are inside the plugin on their
machines — so say at the start that looking them up defeats the exercise, and trust the room.

## What the capstone is

Their system, end to end, on one case: **propose → a human reads it → approve → apply**. Then
`eval_all.py`, then the audit trail.

What is held out is different per track, because the corpora are built differently. On
`support-triage` there is a genuinely unworked case. On the other two the deliverable *is* the
engagement, so what is held out is the answer key — the specific things a good review or
report must catch.

| Track | The capstone input | Why this one |
|---|---|---|
| `support-triage` | **CASE-4495** | Never worked in any module, and it is the hardest of the four: a regression on a version that already contains the fix |
| `vendor-qa` | the Milestone 3 findings pack | The deliverable the whole track exists for; graded on what it catches |
| `docgen` | the August monthly report | Same; graded on completeness and on what it declines to claim |

## support-triage — CASE-4495

**Correct classification: product defect — a regression.**

| What a good proposal has | Why it is the test |
|---|---|
| Saves succeed, `filter_list` returns nothing, and there is **no error code** | The signature of a defect rather than a configuration problem. It is in `support.db :: audit_log`, not in the ticket — three `filter_save` successes and three `filter_list` successes for `acc-3310`, none with an error code |
| The prior case CASE-4123 → VND-411, marked fixed in **5.4.1** | Requires the graph: ticket → vendor case → defect → fix version |
| The account **is** on 5.4.1 | The whole point: the fix is already there and the symptom is back. The customer says so in the ticket — *"Account is on 5.4.1 which I was told contains the fix for this"* — so a proposal that misses it has ignored the input, not just the database |
| It does **not** close the case against KI-77 | `known-issues.md` says explicitly: if you see this on 5.4.1 that is new information, escalate and reference VND-411 |
| `unresolved` names what is genuinely unknown | Whether the other eu-west accounts on 5.4.1 are affected, which needs a query nobody has run |

**The failure to watch for, and it is the common one:** a confident proposal that matches the
symptom to KI-77, sees "fixed in 5.4.1", and concludes the ticket is a duplicate to be closed.
Every individual fact in that chain is correct and the conclusion is wrong. If a group lands
there, do not correct it immediately — ask them which version the account is on, and let the
room find it. That is the most valuable thirty seconds in the module.

## vendor-qa — the Milestone 3 findings pack

Graded against `corpus-design/FACTS.md` → "What M3 actually fails". The two that separate a
good pack from a plausible one:

| What a good pack has | Why it is the test |
|---|---|
| A finding against **clause 5.4** — no machine-readable API definition | Clause 5.4 was inserted by Amendment 2 on 2026-08-15 and M3 was submitted 2026-09-01, so it applies. A reviewer working from the original MSA misses it entirely |
| **Severity 2 resolution stated as 3 business days**, not 2 | M3 postdates Amendment 1 (effective 2026-06-30, in `contract/MSA-amendments.md`). The worked example in `data/examples/` says two days and is period-accurate for M2 — copying it into an M3 finding is wrong |
| The **R-11 coverage gap** reported as a gap in our own paperwork | Not a Halbrook failure. A pack that bills it as a vendor defect is unfair and will be disputed |
| VQ-M2-003 recognised as a **second** rejection under MSA 4.3 | It escalates to the steering group rather than going back to the vendor. Needs the findings pack, the vendor response and the clause |

## docgen — the August monthly report

Graded against `corpus-design/FACTS.md`. The report must be complete where completeness is
claimed, and silent where the sources are silent:

| What a good report has | Why it is the test |
|---|---|
| **Three** milestone slips, with owners | The complete set spans three monthly files. Two is the common answer and it is wrong |
| The **Atlas dependency chain** — Cirrus and Halo both waiting | Stated only in a charter and a July minute. The July steering group explicitly asked for it in the report from then on |
| Halo Reporting absent from anything dated before **2026-07-02** | It did not exist. A report that back-fills it has invented history |
| The Observability owner as **unassigned before 2026-08-26** | Dana took it on that date. "Owned by Dana" for July is wrong |
| Figures that match the metrics files, with anything unsourced flagged | The house style requires it, and it is the thing an agent is most tempted to smooth over |

## How to grade, in ten minutes

Score four things out loud, per group. Do not use a points total; the discussion is the value.

1. **Did the gate hold?** Run `eval_all.py`. Integrity is pass/fail and it is the only part
   with a wrong answer you cannot argue with.
2. **Is every claim cited?** Pick two claims at random and ask for the source.
3. **Did it catch the planted thing?** The table for their track.
4. **Does `unresolved` say something real?** An empty one on a case this hard is a tell.

## Then compare the three tracks, side by side — 5 minutes, and do not skip it

Put the three final artifacts next to each other: a triage note, a findings pack, a monthly
report. Three unrelated domains, three different corpora, one architecture — skill, tool,
hook, retrieval, graph, proposal, gate.

That is the transferable claim of the whole course, and it only lands if they see the other
two tracks. Anybody who spent eight hours on support tickets should leave knowing they built
a pattern, not a triage tool.
