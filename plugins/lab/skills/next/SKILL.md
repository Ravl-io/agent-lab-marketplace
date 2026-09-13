---
name: next
description: Continue the Agent Lab — open the next module or advance to the next step.
disable-model-invocation: true
allowed-tools: Bash, Read, AskUserQuestion
---

Advance the participant to the next thing they should be doing.

## Output discipline

- Never narrate the mechanics. Run the scripts, present the result.
- Teach at the depth the module file asks for, and no deeper. Do not pre-empt a later
  module's punchline.
- **You do not do their work.** You explain, review, unblock and validate. See the learning
  contract in `${CLAUDE_PLUGIN_ROOT}/references/how-the-lab-runs.md`.

## Step 1 — work out where they are

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" show --json
```

Then route, in this order — the first one that matches wins:

| Condition | What to do |
|---|---|
| No state file | Tell them to run `/lab:start` first. Stop. |
| `track` is null | Tell them to run `/lab:start` to pick a track. Stop. |
| `env.ready` is false | Send them to `/lab:doctor`. Do not teach on a broken environment. Stop. |
| `progress.current_module` is null | **Open Module 1** — go to Step 2. |
| A module is in progress | **Continue it** — go to Step 3. |
| The current module is complete, and the next one **is** authored | Open it — go to Step 2. Sessions are days apart, so check first whether they want to start now or stop here. |
| The current module is complete, and it is Module 4 | The course is finished. Show the full scoreboard with `/lab:status` and suggest pointing the system at their own documents. |
| All four modules complete | Congratulate them, briefly. Suggest pointing their system at their own real documents. |

## Step 2 — opening a module for the first time

**Authored modules and their files:**

| Module | File |
|---|---|
| `01` | `modules/01-harness-and-coding-agent.md` |
| `02` | `modules/02-rag-and-retrieval.md` |
| `03` | `modules/03-knowledge-graphs-and-ontologies.md` |
| `04` | `modules/04-the-full-ai-system.md` |

All four modules are authored.

Opening any of them follows the same three beats:

1. **The working agreement, once — Module 1 only.** Skip this entirely when opening a
   later module; they have seen it. Read
   `${CLAUDE_PLUGIN_ROOT}/references/how-the-lab-runs.md` and present it compactly — the
   Frame → Build → Run → Name → Gate loop, the learning contract (*you type, I coach*), and
   checkpoints with `/lab:catchup`. Under 15 lines. This is the only time they see it; do not
   repeat it when opening later modules.

2. **What this module is for.** Read the module's file from the table above and present
   its goal and its arc — the step table, compressed. They should know what they will have in two hours
   and roughly how they get there. Do not teach the concepts yet; this is a map, not a
   lesson.

3. **Then run the module's first step** from that file. Module 1 opens on Step 0, which
   applies the stage `m1s1-harness` — settings, the tracer hook, one experiment. Module 2
   opens on its Step 0, which is the virtualenv and `chromadb`, and nothing else. Follow the
   module file as written.

Setup is **incremental in every module**: each step applies the next stage with
`workspace.py stage <stage-id>`, adding only what that step needs. Never run
`workspace.py setup` — it installs a track's whole payload at once and destroys the point of
the sequence. The stage ladder is:

| Module 1 | `m1s1-harness` · `m1s2-data` · `m1s3-corpus` · `m1s4-skill` · `m1s5-tool` · `m1s6-hook` · `m1s7-plugin` |
|---|---|
| **Module 2** | `m2s1-baseline` · `m2s2-vectors` · `m2s3-mcp` · `m2s4-agentic` |
| **Module 3** | `m3s1-ontology` · `m3s2-extract` · `m3s3-kg-tool` · `m3s4-hybrid` |
| **Module 4** | `m4s1-spec` · `m4s2-propose` · `m4s3-gate` · `m4s4-runbook` |

## Step 3 — continuing a module in progress

Read the module file for `current_module`, find the step after the last cleared checkpoint in
`progress.completed_checkpoints`, and run it.

All four modules are authored, so this should not happen — but if a module file ever marks a
step as not yet authored, **say so plainly** and hand back to
the facilitator. Do not invent an exercise — a fabricated step wastes the participant's time
and breaks the sequence the rest of the module depends on.

When the last step of a module is cleared, run the module's closing step (the debrief), then
`state.py complete-module <id>`. After Module 4 the course is finished: show them the full
scoreboard and suggest pointing the system at their own documents.

## Step 4 — always finish by saying what is next

One or two lines. What they just cleared, and what the next step is. Then stop and wait.
