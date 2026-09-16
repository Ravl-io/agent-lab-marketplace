# Step 5 — The timeline (8 minutes)

**What this step teaches:** find the *first* failure, count them, and put the first one next
to the deploy log. Whatever happened just before the first failure is your prime suspect.

## Frame — under 5 lines

Logs are long. We never read them top to bottom; we search. We want three numbers: when the
first failure happened, how many there were, and what the platform itself was doing around
that time — every release is written to a deploy log with a timestamp.

## Ask

> **In today's API log, find the first request for report R-2291 that returned status 504,
> count how many such requests there were in total, and compare the time of the first one with
> the deploy log.**

## While it runs — for the executing Claude

Search the log with `grep`; never print the whole file. Count lines matching `status=504`,
not the bare number 504 (a request id in the file also contains "504", which gives 48 instead
of 47).

## Judge — when they say "next"

- First 504: **2026-09-16T09:12:04Z**, from the web UI, `duration_ms=30004`, engine
  `openreport-3.2`.
- Count: **47** lines with `status=504` today (one every ten minutes from 09:12 to 16:52 —
  the customer's webhook consumer retrying, exactly as the ticket said).
- Deploy log (`ops/deploys.log`): **2026-09-16T09:09:12Z, release 2.4.1** — notes say
  *"export engine openreport 3.1 -> 3.2"*. The API log has the same deploy line on all
  three nodes.

If the count is **48**, say so: Claude Code counted every line containing "504", and one of
them is a request id. Have them ask: *"Count only lines where the status is 504."* This is
worth two minutes — it is the difference between a number and a fact.

Then ask them: *"What happened three minutes before the first failure?"* Wait for it. A new
release, with a new export engine. Now they have a suspect with a timestamp.

## Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" clear S5
```
