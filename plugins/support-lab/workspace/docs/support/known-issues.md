# Known issues (support-maintained)

| ID | Symptom | Cause | Workaround | Fixed in |
|---|---|---|---|---|
| KI-031 | XLSX export shows dates as text | locale not passed to writer | export CSV | 2.4.0 |
| KI-034 | schedule fails for `+` addresses | address validation | remove `+` | 2.4.1 |
| KI-036 | webhook retries stop after 3 attempts | by design | re-enable in Integrations | — |

Add an entry when three or more tickets share a root cause. Use `templates/known-issue-template.md`.
