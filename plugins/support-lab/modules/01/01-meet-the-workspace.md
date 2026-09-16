# Step 1 — Meet the workspace (8 minutes)

**What this step teaches:** Claude Code reads a rules file on every request (standing
context), and some guardrails live outside the model entirely.

## Frame — say this, in your own words, under 6 lines

There is a file in this folder called `CLAUDE.md`. It holds the team's rules for this desk:
where things are, what is read-only, what never to do. Claude Code reads it on **every**
request, without being asked. Let's see what it says, then let's see one rule that is enforced
by something other than good intentions.

## Ask — give them exactly this to type (two prompts, one after the other)

> **What is in this folder, and what rules does CLAUDE.md give you?**

Then, when that answer is in:

> **How many exports failed today, per tenant?**

Tell them to watch the second one: Claude Code will run a small query script. Note that the
script only accepts read-only queries — nothing Claude Code does can change the database.

Optional, if they are curious (30 seconds): **Try to delete one row from the exports table.**
The script refuses. That refusal came from the script, not from the model choosing to be
careful. Say that sentence; it is the most important idea in the step.

## While it runs — for the executing Claude

Do the real work: read `CLAUDE.md`, list the folder, run
`python3 scripts/query.py "SELECT ..."`. Never answer from memory of this step file.

## Judge — when they say "next"

Check, from what actually appeared in the conversation (or by re-running the query yourself):

1. The five rules were listed: database read-only; compare an error timeline with
   `ops/deploys.log` and `ops/config-audit.log` before naming a cause; never VERIFIED without
   a log line, query result or audit entry; never change a tenant's configuration or draft
   to a customer; no web, vendor notes are local.
2. The failed-exports answer came from a query, and it was **northwind, 47 failures, all
   status 504** — the only tenant with any exports today.

Tell them in two or three lines what was right. If the count was wrong, ask them to ask again
with "use the exports table and count rows with status 504 started today".

## If it went wrong

- Claude Code answered the count without running a query: have them ask "show me the query
  you ran". If there was none, ask again.
- A permission prompt was declined and it stopped: say the prompt was for a read-only query,
  and to approve it this time.

## Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" clear S1
```
