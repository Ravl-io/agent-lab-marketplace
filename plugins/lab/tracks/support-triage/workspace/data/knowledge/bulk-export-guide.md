# Bulk export, and what to use instead

Last reviewed: 2026-08-05.

## Bulk export

Enterprise only since 2026-06-01. Exports a full dataset for a chosen date range as a single
CSV, generated synchronously, up to 5 million rows.

## The Growth workaround: scheduled reports

Scheduled reports are included on Growth and cover most of what customers want bulk export
for. A scheduled report:

- runs on a schedule, or once on demand
- delivers by email or to a storage bucket
- covers the same fields as bulk export
- is capped at 500,000 rows per run, so a large date range must be split into several runs

Setting one up: Reports → the report you want → Schedule → choose range, frequency and
destination.

## What to tell a Growth customer asking for bulk export

Name the entitlement change, give them the scheduled-report route, and route the upgrade
conversation to their account manager. Do not raise a vendor case — nothing is broken.
