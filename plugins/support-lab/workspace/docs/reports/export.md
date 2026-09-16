# Report export

Applies to: Lumen Reports 2.4.x

Users export a saved report to CSV or XLSX from the report toolbar, from a schedule (see [Scheduling and delivery](scheduling.md)), or through `POST /v1/reports/{id}/export`.

## How an export runs

1. The API validates the request and the tenant's export settings.
2. The export engine (OpenReport) runs the report query and streams rows to a file.
3. When the file is complete the API returns `200` with a download link. Large exports are also stored for 24 h under **Downloads**.

The HTTP request stays open for the duration of the export. If the engine has not finished when `export_timeout` elapses, the API returns **`504 export timeout`** and no file is produced.

## Sizing and timeouts

| Report size | Recommended `export_timeout` |
|---|---|
| under 100k rows | default (30 s) |
| 100k – 1M rows | 60 s |
| **over 1M rows** | **at least 120 s** |

`export_timeout` is a per-tenant setting (see [Tenant configuration](../admin/tenant-configuration.md)). Exports over 1M rows run in the engine's **paginated mode**, which streams the file in pages instead of one pass.

> Tip: `row_count` for a saved report is visible on the report's **Details** tab and in the `reports` table.

## Errors

| Status | Meaning | First thing to check |
|---|---|---|
| `504 export timeout` | engine did not finish before `export_timeout` | row count vs the table above |
| `413 export too large` | over `export_max_rows` | the tenant's `export_max_rows` |
| `409 export in progress` | same report already exporting | wait, or cancel from Downloads |

## Related
- [Tenant configuration reference](../admin/tenant-configuration.md)
- [OpenReport 3.2 release notes](../vendor/openreport-3.2-release-notes.md)
