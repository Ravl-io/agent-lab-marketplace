# Step 8 — Write the findings (12 minutes)

**What this step teaches:** a findings sheet has a shape — observed, expected, timeline,
hypotheses with a verdict and evidence, what to do today, whether to escalate. A checker
outside the model decides whether the shape is complete.

## Frame — under 5 lines

Everything they found goes on one sheet, in the team's template. Every possible cause gets a
verdict — verified, ruled out, partial, or unverified — and the evidence sits next to it.
Then a small script checks the sheet is complete. Claude Code writes it; they judge it.

## Ask — two prompts

> **Write the findings sheet for JIRA-4821 to `tickets/JIRA-4821/findings.md`, using
> `templates/findings-template.md`. For each hypothesis say VERIFIED, RULED OUT, PARTIAL or
> UNVERIFIED with the evidence next to it. Include the webhook change as a hypothesis. Give a
> remediation for today, say who can do it and whether it needs approval, and say YES or NO
> on escalating to development.**

Then:

> **Run the findings checker on that file and fix anything it reports.**

Warn them before the first prompt: Claude Code will ask permission to create the file. That is
fine. If it ever asks to change a file under `config/`, the answer is **no** — support does
not change a customer's configuration without approval, and the rules file says so.

## Judge — when they say "next"

Run the checker yourself and read the sheet:

```
python3 scripts/check_findings.py tickets/JIRA-4821/findings.md
```

Then go through this checklist with them, in plain words, and say which items are met:

- [ ] Quotes the docs sentence about exports over 1M rows, with the path.
- [ ] Shows Northwind's 30 s against the default 30 s.
- [ ] Timeline has the first 504 (09:12:04) next to the 2.4.1 deploy (09:09:12).
- [ ] Says the same export **succeeded yesterday** (18:40, 84 s, engine 3.1).
- [ ] Hypotheses: timeout too low — **PARTIAL**; engine 3.2 changed export timing, known
      issue #412 — **VERIFIED**; webhook URL change — **RULED OUT**. Each with `evidence:`.
- [ ] No cause called VERIFIED without a log line, query result or audit entry.
- [ ] Remediation: raise Northwind's `export_timeout` to 120 s — **needs approval**, done by
      support with approval or the tenant admin. Not done by Claude Code.
- [ ] Escalation: **YES** — the engine upgrade in 2.4.1 changed export timing; attach the
      timeline, row count and vendor issue #412.
- [ ] Documentation: `docs/releases/2.4.1.md` does not warn about the timeout impact.
- [ ] The checker prints PASS.

If a required item is missing, do not fix it yourself. Tell them what is missing and give
them the sentence to ask, for example: *"Add the webhook change as a ruled-out hypothesis with
the audit-log line as evidence."* Then they say next again.

Close the step with the observation that matters: the sheet's shape came from the template,
the verdicts came from evidence they saw with their own eyes, and the checker is a rule the
model cannot talk its way past.

## Gate

Only when the checker passes and the checklist is essentially met:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" clear S8
```
