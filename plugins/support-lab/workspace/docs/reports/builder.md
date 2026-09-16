# Report builder

Applies to: Lumen Reports 2.4.x

The builder composes a report from a dataset, filters, groupings and a time window. Saved reports have an `id` (`R-nnnn`), an owner, a dataset and a **row count** that is refreshed after each ETL.

Time windows: `today`, `previous_business_day`, `last_7_days`, `month_to_date`, `custom`. The window is evaluated at run time in the tenant's timezone.
