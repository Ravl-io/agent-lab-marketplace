# Project charter — Cirrus API Integration

Owner: Lena Okonkwo · Programme: Northwind Delivery
Effective 2026-04-02. Not revised.

## Purpose

Integrate the Cirrus third-party pricing API so quotes are priced against live vendor rates
rather than the nightly extract.

## In scope

- Integration design and vendor contract review
- The integration service itself, and its caching layer
- Cutover of the quote path from the nightly extract to the live API

## Out of scope

- Refunds. Requested under CR-11 on 2026-07-08 and **rejected at steering on 2026-07-16**;
  refunds remain on the nightly extract for this phase.

## Dependencies

- **Atlas Migration must complete before Cirrus can go live.** Cirrus writes priced quotes
  against the ledger, and the integration is built against Atlas's new ledger schema. Until
  the Atlas cutover lands, there is no schema to write to.
- Vendor sandbox access, granted 2026-04-10.

## Assumptions

- The vendor will sustain **500 requests per minute**. This is the assumption the design rests
  on, and it is the one that later proved wrong — see R-03.
