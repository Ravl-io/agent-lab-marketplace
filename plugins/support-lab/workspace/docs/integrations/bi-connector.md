# BI connector

Applies to: Lumen Reports 2.4.x

The BI connector lets Power BI, Tableau and Looker pull report data on a schedule. A tenant admin enables it under **Integrations** and sets a `sync_interval`.

## Settings

| Setting | Default | Notes |
|---|---|---|
| `sync_interval` | `15m` | how often the connector refreshes each connected report. Values under 15m are allowed but not recommended. |
| `reports` | all shared | which reports the connector may read |

## How a sync works

For each connected report the connector calls `GET /v1/reports/{id}/rows` in pages of 1,000 rows, as fast as the API allows. A report with 20,000 rows is 20 requests per sync; all connected reports are fetched in the same sync.

## Notes
- Syncs run as `client_id=bi-sync-connector`.
- The connector polls the export endpoint every 60 s while an export is in progress.
