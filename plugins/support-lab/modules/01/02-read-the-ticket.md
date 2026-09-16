# Step 2 — Read the ticket (4 minutes)

**What this step teaches:** a ticket is a claim, not evidence. It tells you when the customer
noticed and what they believe. It does not tell you the cause.

## Frame — under 4 lines

Ticket JIRA-4821 came in this morning from Northwind, one of the enterprise customers. First
thing a senior engineer does: read it properly and separate what the customer *saw* from what
the customer *thinks*.

## Ask

> **Read ticket JIRA-4821 and tell me in plain words: which customer, what exactly is failing,
> since when, what worked before, and what the customer believes changed.**

## Judge — when they say "next"

The answer should contain all of these (verify against `tickets/JIRA-4821.md` if unsure):

- Customer: **Northwind**, enterprise plan; reporter s.okafor, the tenant admin.
- Failing: every export of report **R-2291 "Orders — full history"** returns
  `504 export timeout` after about 30 seconds.
- Since: **this morning** (ticket created 09:41 on 2026-09-16).
- Worked before: **yesterday evening**.
- The customer's belief: "nothing changed on our side". Also: their webhook consumer retries
  automatically (so there will be many attempts in the log), and it blocks their finance close.

Then ask them one question and wait for a one-line answer: *"Do we know the cause yet?"* The
right answer is no. The ticket gives a symptom, a time, and an opinion.

## Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" clear S2
```
