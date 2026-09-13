# Project charter — Halo Reporting

Owner: Marcus Bell · Programme: Northwind Delivery
Effective 2026-07-02, on approval of CR-12.

## Purpose

Deliver the monthly finance reporting capability that was descoped from Atlas Migration in
May 2026, as a project in its own right with its own release cadence.

## In scope

- Monthly finance extracts
- The reporting views themselves
- A scheduled delivery mechanism for finance

## Out of scope

- Ad-hoc analytical querying
- Anything that writes to the ledger

## Dependencies

- The reporting views read the migrated ledger schema, so this work cannot complete before
  Atlas Migration has cut over.

## Open items at charter approval

- Finance have not reviewed the scope. Fen Alvarez to confirm. Tracked as R-06.
