# Step 11 — Debrief (5 minutes)

No new work. Three ideas to name, now that they have felt each one, and one habit to keep.

## Say this, compactly

**Three things that were doing the work today:**

1. **Standing context.** `CLAUDE.md` was in every request. Claude Code never had to be told
   the database is read-only or that config changes need approval; the team's rules were
   simply there. That is where a team's rules go.
2. **Guardrails outside the model.** The query script refused anything but a read. The
   findings checker refused a sheet with a verdict and no evidence. Neither depended on the
   model being careful. When something must never happen, put it in a script, not a prompt.
3. **A plugin is a method written down.** Ten prompts became four words. The plugin did not
   contain the answer to JIRA-4907 — it contained the *order of questions* and the *standard
   for an answer*. That is why it worked on a ticket it had never seen.

**The habit:** judge, edit one line, run again. When the plugin gets something wrong, do not
write a better prompt. Add one sentence to the skill, so the next person gets it too.

## Ask them one thing, and wait

*"In one sentence: what would Claude Code have got wrong on JIRA-4907 if you had not written
the method down?"*

A good answer is any version of "it would have looked at the symptom and not at what the
customer's own admin changed". Do not grade it. Acknowledge it and close.

## Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" clear S11
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" complete
```

Tell them what they leave with: a findings sheet for two tickets, and a plugin in
`first-look-plugin/` that is theirs to keep, install anywhere, and improve one line at a time.
