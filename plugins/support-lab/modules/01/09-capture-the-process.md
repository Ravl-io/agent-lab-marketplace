# Step 9 — Capture the process as a plugin (12 minutes)

**What this step teaches:** the method they just followed can be written down and handed to
Claude Code, so it follows it every time, for anyone — and it is installable like any other
tool. That is what a plugin is.

## Frame — under 6 lines

You just did a first look the way a senior engineer does it: eight questions, in an order, with
a rule at each step. Next time you want that to be one sentence. Claude Code can write the
method down as a **plugin**: a folder with the steps, the standards, the definition of done,
and the checker script — everything it needs to repeat the investigation without you
prompting each step. You are not going to write it. You are going to ask for it and check it.

## Ask — two prompts

> **Show me the process I just used to investigate this ticket, as a numbered list of steps,
> with the rule for each step.**

Read the list with them. It should be the eight moves: ticket → docs quote → settings and
audit log → first failure and count → deploy log → last known good → vendor notes → findings
sheet and checker. If a step is missing, have them say so: *"You missed checking whether it
worked before. Add it."*

Then:

> **Turn that into a Claude Code plugin in a folder called `first-look-plugin` in this
> workspace, laid out as a marketplace so I can install it: `.claude-plugin/marketplace.json`
> at the top, and the plugin under `plugins/first-look/` with its own
> `.claude-plugin/plugin.json`. It needs one skill named `first-look` whose description says
> to use it when I ask for a first look on a ticket or name a JIRA key. The skill must
> contain the numbered steps, a standard (quote the docs rather than paraphrase; grep the logs
> rather than print them; compare the timeline with the deploy log and the config-audit log
> before naming a cause; never mark a cause VERIFIED without evidence; never change a
> customer's configuration), and a done-when (the findings checker passes, remediation names
> who does it and what needs approval, escalation is YES or NO). Copy
> `scripts/check_findings.py` into the plugin's `scripts` folder and make the skill run it
> from there using `${CLAUDE_PLUGIN_ROOT}`. Keep the skill model-invocable.**

It is long; that is fine. They can paste it. Claude Code will ask permission to create
several files under `first-look-plugin/` — approve those.

## Judge — when they say "next"

Run the validator:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_plugin.py" first-look-plugin
```

- **passes: true** — tell them what the plugin contains in three lines (the manifest, the
  skill and its description line, the script), and read out any `notes`. Then show them the
  two install commands from the `install.in_claude_code` list — you will use them in the next
  step.
- **passes: false** — read the `problems` list and turn each into one sentence they can ask,
  for example *"The skill's description does not say 'first look' — ask Claude Code to change
  the description so it contains those words."* Do not edit the plugin yourself. They say
  next again when it is fixed.

Open the SKILL.md and read the description line aloud. Say why it matters: this one line is
how Claude Code decides to use the skill when someone types "first look on …". Write it in
the words you would use to ask.

## Gate

Only when the validator passes:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" clear S9
```
