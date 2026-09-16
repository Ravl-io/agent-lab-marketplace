# Step 10 — Run it in a new session (15 minutes)

**What this step teaches:** Claude Code remembers nothing between sessions. The plugin is the
only memory. If the method survives a fresh session on a ticket it has never seen, it is real.

## Opening the step (this session)

Frame in under 5 lines: we are going to install the plugin you just built, close this
conversation, open a fresh one, and run the investigation on a *different* ticket — JIRA-4907,
where Contoso's scheduled email stopped arriving. Four words. Then we judge it.

Get the install commands from the validator so the paths are absolute:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_plugin.py" first-look-plugin
```

Then give them these instructions, numbered, exactly:

1. Type the first install command (`/plugin marketplace add <absolute path>`), then the
   second (`/plugin install first-look@<marketplace name>`). If it says
   *Run /reload-plugins to activate*, type `/reload-plugins`.
2. **Start a new session** in this same folder. In VS Code: open a new Claude Code
   conversation. In a terminal: type `exit`, then `claude` again. Do not continue in this
   conversation — the point is that the new one starts empty.
3. In the new session, type exactly: **First look on JIRA-4907.**
4. Watch the first thing it does: it should read the `first-look` skill. Then let it run,
   approving the read-only prompts and the one that creates `tickets/JIRA-4907/findings.md`.
   Say no to anything that changes a customer's configuration.
5. When it finishes, say **next** in that new session. The lab remembers where you are.

Mark the step open and stop. Do not judge anything in this session.

## Judge — when they say "next" (this will be the new session)

First confirm the plugin was actually used: ask *"Did you see it read the first-look skill
before it started?"* If not, the description did not match the words they typed — see below.

Then run the checker and read the sheet:

```
python3 scripts/check_findings.py tickets/JIRA-4907/findings.md
```

The outcome should be **different in kind** from JIRA-4821: not a product bug. Check for:

- `ops/config-audit.log`, **2026-09-13T02:14:37Z**: j.park (Contoso's own admin) changed
  `timezone` from America/Toronto to **UTC**.
- `logs/scheduler-2026-09-16.log`: schedule S-771 ran at 10:00Z (06:00 Toronto) with
  900–1,500 rows and `status=sent` up to 09-12; from 09-13 it runs at **06:00Z = 02:00
  Toronto**, `rows=0`, `status=suppressed_empty`, and the ETL finishes at 03:5x local —
  **after** the run.
- The docs (`docs/reports/scheduling.md`): changing the tenant timezone moves every schedule;
  the ETL finishes about 04:00 local; an empty report means the email is suppressed.
- Verdict: timezone change by the customer's admin → schedule runs before the data is ready →
  empty → suppressed — **VERIFIED**. Product bug — **RULED OUT** (runs are logged, no
  errors, no deploy in the window). Remediation: reset the timezone or move the schedule to
  05:00 local or later; the tenant admin can do it today. Escalation: **NO**.
- Nice detail if present: the ticket says "since Monday" but the log shows the weekend runs
  were already empty.

Tell them plainly which of these the sheet has. Then the sentence the whole lab builds to:
**same method, different ticket, opposite outcome — one was escalate to development, this one
is explain to the customer and fix a doc.** The plugin did not know the answer. It knew the
method.

## If the plugin did not fire

The words they typed did not match the skill's description. Have them ask, in this session:
*"Change the first-look skill's description so it triggers when I say 'first look on' a
ticket key."* Then `/reload-plugins`, a new session, and try again. This is not a failure;
it is the most common edit a plugin ever gets.

## If the sheet blames the product

Judge, edit one line, run again: have them ask Claude Code to add one sentence to the
skill's steps, for example *"Check the config-audit log for changes made by the customer's
own admins before considering a product bug."* Then `rm -rf tickets/JIRA-4907` (they can ask
Claude Code to delete that folder), new session, run it again.

## Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" clear S10
```
