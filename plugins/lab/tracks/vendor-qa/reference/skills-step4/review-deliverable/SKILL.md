---
name: review-deliverable
description: Review a vendor's submitted deliverables against the contract and the statement of work — producing findings with a severity, the acceptance criterion not met, the contract clause behind it, and the evidence location, plus a coverage report of requirements nobody has verified. Use when asked to review, QA, assess or accept a vendor deliverable or milestone.
---

# Review a vendor deliverable

Establish whether what was promised is what shipped, with evidence, because the findings go
back to the supplier and they will push back. Done means: every acceptance criterion has a
verdict, every finding cites both a criterion and a clause, and the requirements nobody
verified are named rather than assumed passed.

## Where things are

All paths are relative to the project root. Do not go looking for them.

| | |
|---|---|
| `data/contract/MSA-excerpt.md` | the master agreement — acceptance, standards, security, SLAs |
| `data/contract/SOW-milestone-3.md` | what this milestone promised, and its acceptance criteria |
| `data/requirements-register.md` | every requirement, and which criterion verifies it |
| `data/deliverables/` | what the supplier actually submitted — the thing under test |
| `data/examples/findings-pack-example.md` | the format findings are issued in |

Write the finished findings pack to `findings/<milestone>-findings.md`.

**Run the scan before you read anything.** It finds the things you cannot reliably spot by
eye — credentials, production personal data — and collects the structural facts the criteria
ask about:

```
python3 tools/deliverable_scan.py
```

## Procedure

1. **Read the SOW acceptance criteria first.** They are the checklist. Everything else is
   evidence for or against them.
2. **Read the MSA clauses.** Note the amendment date and which term applies: a milestone is
   judged against the clause version **in force at its submission date**, not today's.
3. **Read the requirements register.** Note which requirements this milestone was meant to
   verify, and which have no verifying criterion at all.
4. **Read every file in `data/deliverables/`.** All of them, before writing any finding.
5. **Give every acceptance criterion a verdict**: met, not met, or cannot tell. "Cannot tell"
   is a legitimate verdict and becomes a finding asking for what is missing.
6. **Check the security clauses from the scan output**, not by reading. `secrets` and
   `personal_data` are Severity 1 under MSA 6.1 and 6.2, and they are what a reviewer skims
   past late in the day. A regex does not skim. An empty result is evidence of absence only
   because the scan is tested — that is why it has a `--selftest`.
7. **Assign severity from the MSA**, not from how serious it feels or how loudly anyone is
   escalating.
8. **Produce the coverage report**: requirements with no verifying criterion, and criteria
   with no evidence. A requirement nobody verified is a gap, not a pass.
9. **Write the findings pack**, findings in severity order.

## Output

Write to `findings/<milestone>-findings.md`, and match
`data/examples/findings-pack-example.md` exactly — same fields, same order. Read it
before writing. Each finding carries: severity, criterion not met, clause, what we found,
evidence location, what is required to close, and the resolution due date from the SLA.

## Constraints

- **Every finding needs both a criterion and a clause.** A finding with only one of them will
  be argued away by the supplier.
- **Evidence points at a location** in the deliverable — a section, a line, a code block. Not
  a summary, a location.
- **Judge against the clause version in force at the submission date.** The MSA has been
  amended once and one SLA term changed; using today's term on an earlier milestone is wrong
  in the supplier's favour or ours, and either way it is wrong.
- **A requirement with no verifying criterion is a coverage gap**, reported as such. Never
  record it as passed.
- **Do not soften severity** because the relationship is good, and do not raise it because a
  deadline is close.
