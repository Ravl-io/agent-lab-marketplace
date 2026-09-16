# API rate limits

Applies to: Lumen Reports 2.4.x

Each tenant has a request budget of **`rate_limit_per_min`** requests per minute (default 600), plus a burst allowance of **`rate_limit_burst`** (default 100) in any 10-second window. Either limit exhausted returns `429`. When the budget is exhausted the API returns **`429 Too Many Requests`** with a `Retry-After` header.

The limit is counted **per tenant**, across all API clients and users of that tenant. Requests are attributed to a `client_id` in the log so that heavy clients can be identified.

## Responses

| Status | Meaning |
|---|---|
| `429` | budget exhausted; retry after `Retry-After` seconds |
| `200` with header `X-RateLimit-Remaining` | remaining budget in the current minute |

## Recommendations
- Batch reads: `GET /v1/reports?ids=…` instead of one call per report.
- Back off on `429`; do not retry immediately.
- Raising `rate_limit_per_min` is possible but is a commercial change — support does not change it without account management approval.
