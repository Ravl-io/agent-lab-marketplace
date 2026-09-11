# report-builder

@intent.md

This project turns a month of source documents into the Monthly Delivery Report.

- `data/` is **read-only evidence**: the month's sync notes, status updates and metrics, plus
  the template, the house style and last month's published report. Never write there.
- Reports go in `reports/`, named `<YYYY-MM>-monthly-delivery-report.md`.
- **Every claim carries a source.** If no source covers something that matters, it goes in
  section 5 as a gap — it is never inferred and never filled in from general knowledge.
- Dates are absolute, statuses come from the five permitted values, and a date that moved is
  written as `old -> new`.
