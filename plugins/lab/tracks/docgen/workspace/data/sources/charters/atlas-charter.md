# Project charter — Atlas Migration

Owner: Priya Raghunathan · Programme: Northwind Delivery

This charter has been revised once. **Both versions are recorded here**; the current one is
whichever has no end date. Read the dates before quoting scope.

---

## Version 2 — effective 2026-05-14

**In scope**

- Ledger schema migration to the new model
- Backfill of all historical ledger records
- Cutover of the payments write path
- Decommissioning of the legacy schema after a 30-day hold

**Out of scope**

- **Reporting views migration.** Descoped from Atlas on 2026-05-14 and moved to a separate
  piece of work, on the grounds that reporting has a different audience and a different
  release cadence. That work later entered the programme as Halo Reporting under CR-12.

**Superseded:** version 1, which ran from 2026-02-10 to 2026-05-14.

---

## Version 1 — effective 2026-02-10, superseded 2026-05-14

**In scope**

- Ledger schema migration to the new model
- Backfill of all historical ledger records
- Cutover of the payments write path
- **Reporting views migration**, including the monthly finance extracts
- Decommissioning of the legacy schema after a 30-day hold

**Out of scope**

- Anything touching the card vault
