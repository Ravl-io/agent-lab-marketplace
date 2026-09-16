# Scheduling and delivery

Applies to: Lumen Reports 2.4.x

A schedule runs a saved report at a fixed time and delivers it by email or to a webhook.

## Time and timezone

- Schedules run in the **tenant's configured timezone** (`timezone` in tenant configuration). Changing the tenant timezone moves every schedule of that tenant.
- Daylight-saving transitions are **not** applied automatically to schedules created before the change; verify schedules after a DST switch.
- Times are stored and logged in UTC. The scheduler log shows both the UTC run time and the tenant-local time.

## Data freshness

Report data comes from the nightly ETL. The ETL for a tenant finishes at approximately **04:00 tenant-local time**. A schedule that runs before the ETL has completed reports on the previous day's data — for reports with a "previous business day" window this usually means **no rows**.

## Empty reports

If a scheduled report produces **no rows**, the email is **suppressed** and the run is logged with `status=suppressed_empty`. Recipients receive nothing. This is by design to avoid empty attachments; it can be changed per schedule with `deliver_empty: true`.

## Delivery

| Channel | Notes |
|---|---|
| email | up to 20 recipients; attachments over 10 MB are replaced with a download link |
| webhook | `POST` with the file URL; see [Webhooks](../integrations/webhooks.md) |

## Troubleshooting

| Symptom | Check |
|---|---|
| email never arrives | `schedule_runs.status` for the schedule; mail log on the tenant's side |
| email arrives at the wrong time | tenant `timezone`; the schedule's stored time is local |
| attachment is empty or missing | `status=suppressed_empty`; ETL completion time vs run time |
