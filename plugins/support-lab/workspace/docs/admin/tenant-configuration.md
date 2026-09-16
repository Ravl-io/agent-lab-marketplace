# Tenant configuration reference

Applies to: Lumen Reports 2.4.x. Tenant configuration lives in `config/tenants/<tenant>.yaml`; unspecified keys take the value in `config/tenants/_defaults.yaml`. Every change is recorded in `ops/config-audit.log`.

| Key | Default | Notes |
|---|---|---|
| `timezone` | `UTC` | IANA name. Affects schedules and time windows. |
| `export_timeout` | `30` | seconds. See [Report export](../reports/export.md) for sizing. |
| `export_max_rows` | `5000000` | hard cap per export |
| `export_engine` | `openreport` | engine and version are set by the release, not per tenant |
| `rate_limit_per_min` | `600` | API requests per minute, per tenant, all clients combined |
| `rate_limit_burst` | `100` | extra requests allowed in a 10 s burst |
| `integrations` | `[]` | enabled integrations and their settings |
| `deliver_empty` | `false` | schedule-level override available |

Changes made in the admin console take effect within one minute and do not require a restart.
