# Facilitator notes — Support Lab, Module 1

## Before the session

- One empty folder per participant (or pair), Claude Code installed, permission mode **ask**,
  `python3` available. No web access needed.
- Give them the marketplace. From GitHub it is the repo below; locally on a shared machine it is
  the absolute path of a checkout. They run:
  ```
  /plugin marketplace add Ravl-io/agent-lab-marketplace
  /plugin install support-lab@agent-lab
  ```
- Dry-run Steps 8 to 10 once on the real image. Model behaviour drifts, and the plugin Claude
  Code generates in Step 9 is the least predictable artefact in the lab.
- The sandbox payload under `workspace/` is generated in the lab-demo2 sandbox (`build_lab.py`, then
  `sync_workspace.sh`). After a rebuild, copy `plugins/support-lab/` here and bump the version in
  both manifests, or installed copies never pick the change up.

## What the participant types, in order

Every step's exact prompt is in `modules/01/<step>.md` under **Ask**.
The tutor quotes it to them; they copy it. You never need to dictate one, but it helps to
know them:

| Step | They type |
|---|---|
| 1 | What is in this folder, and what rules does CLAUDE.md give you? / How many exports failed today, per tenant? |
| 2 | Read ticket JIRA-4821 and tell me in plain words: which customer, what exactly is failing, since when, what worked before, and what the customer believes changed. |
| 3 | Find the documentation page about report export and quote, word for word, what it says about export_timeout for reports over 1 million rows. Also tell me how many rows report R-2291 has. |
| 4 | Show me Northwind's export_timeout next to the default value, and list every change made to Northwind's configuration in the last 7 days from the config-audit log. |
| 5 | In today's API log, find the first request for report R-2291 that returned status 504, count how many such requests there were in total, and compare the time of the first one with the deploy log. |
| 6 | Did this same export succeed before today with the same settings? Check yesterday's API log and the exports table … |
| 7 | Read the vendor release notes for OpenReport 3.2 under docs/vendor and tell me whether anything there matches what we are seeing. |
| 8 | Write the findings sheet for JIRA-4821 … / Run the findings checker on that file and fix anything it reports. |
| 9 | Show me the process I just used … / Turn that into a Claude Code plugin in a folder called first-look-plugin … |
| 10 | (new session) First look on JIRA-4907. |

## Verified answer keys

| Step | The fact |
|---|---|
| 1 | Exports failed today: northwind 47, status 504, only tenant with exports today |
| 3 | `docs/reports/export.md`: over 1M rows → at least 120 s; default 30. R-2291 = 2,104,311 rows |
| 4 | northwind `export_timeout: 30` = default. Audit: 2026-09-16T08:10:12Z s.okafor webhook URL — red herring |
| 5 | First 504 09:12:04Z; 47 × `status=504` (bare grep gives 48); deploy 2.4.1 at 09:09:12Z, engine 3.1 → 3.2 |
| 6 | Last success 2026-09-15T18:40:07Z, 84,210 ms, openreport-3.1; eight more September successes on 3.1 |
| 7 | Vendor notes: flush every 500k rows, time to first byte increases, raise caller timeouts; known issue #412. `docs/releases/2.4.1.md` says "no configuration changes required" |
| 8 | H1 timeout PARTIAL; H2 engine 3.2 VERIFIED; H3 webhook RULED OUT. Remediation 120 s with approval. Escalate YES. Checker PASS |
| 9 | `check_plugin.py first-look-plugin` passes: marketplace.json, plugin.json, `skills/first-look/SKILL.md` with "first look" in the description, `scripts/check_findings.py` |
| 10 | JIRA-4907: audit 2026-09-13T02:14:37Z j.park timezone America/Toronto → UTC; S-771 runs 06:00Z = 02:00 Toronto since 09-13, rows=0 suppressed_empty, ETL done ~03:5x local after the run. Escalate NO |

## What to watch in the room

- **Step 5, the count.** If someone gets 48, stop the room. It is the cleanest example of
  "a number is not a fact" the lab has.
- **Step 6, the question.** Ask the room before the tutor does: *did it ever work with the
  same settings?* Whoever says "yes, yesterday" has understood the lab.
- **Step 8, the config prompt.** If Claude Code asks to edit `config/tenants/northwind.yaml`,
  the participant must refuse. Make the moment visible.
- **Step 9, the description line.** Put one participant's SKILL.md description on the
  projector. It is the one line that decides whether "First look on JIRA-4907" works.
- **Step 10, the new session.** People will keep typing in the old one. The banner hook
  prints the position in the new session; the tutor in the new session picks up at "next".

## Common problems

| Symptom | Fix |
|---|---|
| "lab start" does nothing | Plugin not loaded: `/plugin` → Installed, or `/reload-plugins`. Slash form `/support-lab:start` always works |
| Setup refuses: folder not empty | They opened Claude Code in an existing project. New empty folder |
| Claude Code answers a count without running a query | Have them ask "show me the query you ran" |
| The generated plugin fails validation | The validator's `problems` list is written as sentences to ask; the tutor relays them |
| "First look on JIRA-4907" ignores the plugin | Description line does not contain "first look"; edit, `/reload-plugins`, new session |
| The 4907 sheet blames the product | Judge, edit one line: add "check config-audit for the customer's own admin changes" to the skill; delete `tickets/JIRA-4907`; run again |
| Behind on time | Step 1's optional delete demo, then Step 7 (fold the vendor note into Step 8's ask) |

## Between cohorts

In each participant folder: say `lab reset` in Claude Code, or from a terminal:

```
python3 <marketplace>/plugins/support-lab/scripts/workspace.py --root <folder> clean
python3 <marketplace>/plugins/support-lab/scripts/state.py --root <folder> reset --force
```

Also `/plugin uninstall first-look@first-look` if the same machine is reused, so the next
participant's install does not collide.
