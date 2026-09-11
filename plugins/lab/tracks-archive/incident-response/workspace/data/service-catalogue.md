# Service catalogue — Northwind Payments

Owner of record for each service, and what it depends on at runtime.
Last reviewed: 2026-08-20.

| Service | Team | Tier | Depends on |
|---|---|---|---|
| `checkout-web` | Storefront | 1 | `payments-api`, `session-store` |
| `payments-api` | Payments | 1 | `ledger-db`, `card-vault`, `fx-rates` |
| `webhook-dispatcher` | Integrations | 2 | `payments-api`, `event-bus` |
| `settlement-batch` | Payments | 2 | `ledger-db`, `bank-sftp` |
| `merchant-portal` | Storefront | 3 | `payments-api`, `reporting-db` |
| `fx-rates` | Payments | 2 | `vendor-fx` (third party) |
| `card-vault` | Security | 1 | — |
| `ledger-db` | Payments | 1 | — |
| `event-bus` | Platform | 1 | — |
| `session-store` | Platform | 2 | — |
| `reporting-db` | Data | 3 | `ledger-db` (replica) |

Tier 1 means customer-facing payment flow: an outage is revenue-affecting and pages
immediately. Tier 3 pages during business hours only.

## Escalation

| Team | Primary | Secondary |
|---|---|---|
| Payments | @rota-payments | @dara-oyelowo |
| Storefront | @rota-storefront | @kim-falk |
| Integrations | @rota-integrations | @sam-ndiaye |
| Platform | @rota-platform | @ines-moreau |
| Security | @rota-security | escalate to CISO on-call |
