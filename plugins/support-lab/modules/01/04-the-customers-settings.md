# Step 4 — The customer's settings (6 minutes)

**What this step teaches:** check the customer's configuration against the default, and check
whether *they* changed anything — the customer said "nothing changed on our side". Also: a
change that is real can still be irrelevant.

## Frame — under 4 lines

Every customer has a settings file, and every change to it is written to a log with who
changed what, when. Two questions: what is Northwind's export timeout set to, and has anyone
at Northwind changed anything this week?

## Ask

> **Show me Northwind's `export_timeout` next to the default value, and list every change
> made to Northwind's configuration in the last 7 days from the config-audit log.**

## Judge — when they say "next"

- Northwind `export_timeout: 30` — **equal to the default** (`config/tenants/northwind.yaml`
  and `config/tenants/_defaults.yaml`). Below the 120 s the docs ask for, but it has always
  been 30.
- One change in 7 days, in `ops/config-audit.log`: **2026-09-16T08:10:12Z, s.okafor changed
  the webhook URL** (`integrations.webhooks.url`).

Now ask them two questions, one at a time, and wait for their answer each time:

1. *"The customer said nothing changed on their side. True?"* — Not quite: they changed the
   webhook address at 08:10 this morning.
2. *"Does changing where notifications are sent explain an export timing out?"* — No. The
   failures are on the export itself. This change is real and irrelevant. A good findings
   sheet will say so explicitly, as **ruled out**, rather than ignore it.

Then say: the timeout setting is tempting again. It has been 30 for weeks. Something else
changed today. Next: the timeline.

## If it went wrong

- Only one file read: have them ask for the defaults file too.
- The audit log was summarised without the timestamp or user: ask for "the exact lines".

## Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" clear S4
```
