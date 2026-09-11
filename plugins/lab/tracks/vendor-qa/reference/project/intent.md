# Intent: Findings a supplier cannot argue with

Author: Agent Lab participant
Status: Draft

## Problem

Every milestone arrives as a pile of deliverables and somebody has to establish whether what
was promised is what shipped. Done badly it becomes either a rubber stamp or a fight, both
expensive. The reason it becomes a fight is that findings arrive without the criterion and
the clause attached, so each one is negotiable.

## Proposed outcome

A findings pack per milestone in which every finding carries its severity, the acceptance
criterion it fails, the contract clause behind it, and where in the deliverable to look — plus
a coverage report naming the requirements nobody verified.

## Affected users and systems

- Our delivery manager issues the pack; the supplier's team receives it.
- Reads: the MSA, the SOW, the requirements register, and the submitted deliverables.
- Deliberately does not touch: the supplier's systems, and the issuing of the pack itself.

## Constraints

- `data/` is read-only, including the supplier's submissions. Altering the artefact under
  review destroys the review.
- Every finding cites both a criterion and a clause.
- Severity comes from the MSA, not from tone or deadline pressure.
- A milestone is judged against the clause version in force at its submission date.
- A requirement nobody verified is a coverage gap, never a pass.

## Open questions

- Who arbitrates when we and the supplier read the same clause differently?
- Does a finding closed by the supplier get re-verified by us, or taken on trust?
- What severity applies to a credential that was already rotated before we noticed?
