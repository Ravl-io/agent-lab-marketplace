# OpenReport 3.2.0 — release notes (vendor)

_Local copy of https://openreport.example.org/releases/3.2 — kept here because the lab sandbox has no web access._

## Paginated export
Paginated export now **flushes every 500,000 rows** instead of writing a single pass. Throughput on large datasets improves by 20–40 %, but each page is committed before the next starts, so the **wall-clock time to the first byte increases**. Callers with request-level timeouts must raise them accordingly.

## Known issues
- **#412** — exports over 1M rows that completed within 60–90 s on 3.1 may exceed 120 s on 3.2 when the source query is unsorted. Workaround: raise the caller timeout, or set `paginate_threshold` above the report size. Fix planned for 3.2.2.

## Other changes
- Excel writer updated; dates now respect the caller's locale.
- Dropped support for the legacy `csv-v1` format.
