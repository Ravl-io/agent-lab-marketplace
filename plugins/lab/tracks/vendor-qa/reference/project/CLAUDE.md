# vendor-review

@intent.md

This project reviews a third-party vendor's submitted deliverables against the contract and
the statement of work, and produces the findings pack that goes back to them.

- `data/` is **read-only evidence**: the contract, the SOW, the requirements register, and
  what the vendor actually submitted. Never write there.
- Findings packs go in `findings/`, one per milestone.
- A finding needs **both** the acceptance criterion it fails and the contract clause behind
  it. With only one, the vendor argues it away.
- The MSA has been amended. A milestone is judged against the clause version in force at its
  submission date, not today's.
