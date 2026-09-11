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
| The current module is complete, and the next one is not authored | Say so plainly: the module is finished, and the next one opens in the following session. Offer its optional extension and `/lab:status`. Do not invent Module 2. |
| All four modules complete | Congratulate them, briefly. Suggest pointing their system at their own real documents. |

## Step 2 — opening a module for the first time

Only Module 1 exists so far. If `current_module` is null, open it:

1. **The working agreement, once.** Read
   `${CLAUDE_PLUGIN_ROOT}/references/how-the-lab-runs.md` and present it compactly — the
   Frame → Build → Run → Name → Gate loop, the learning contract (*you type, I coach*), and
   checkpoints with `/lab:catchup`. Under 15 lines. This is the only time they see it; do not
   repeat it when opening later modules.

2. **What this module is for.** Read
   `${CLAUDE_PLUGIN_ROOT}/modules/01-harness-and-coding-agent.md` and present its goal and
   its arc — the step table, compressed. They should know what they will have in two hours
   and roughly how they get there. Do not teach the concepts yet; this is a map, not a
   lesson.

3. **Then run the module's first step** from that file. For Module 1 that is Step 0, which
   applies the stage `m1s1-harness` — settings, the tracer hook, and one experiment. Follow
   it as written.

Setup is **incremental**: each step applies the next stage with
`workspace.py stage <stage-id>`, adding only what that step needs. Never run
`workspace.py setup`, which installs a track's whole payload at once; that is for Module 2,
when the full corpus is genuinely needed.

## Step 3 — continuing a module in progress

Read the module file for `current_module`, find the step after the last cleared checkpoint in
`progress.completed_checkpoints`, and run it.

If the module file marks that step as not yet authored, **say so plainly** and hand back to
the facilitator. Do not invent an exercise — a fabricated step wastes the participant's time
and breaks the sequence the rest of the module depends on.

When the last step of a module is cleared, run the module's closing step (the debrief), then
`state.py complete-module <id>`. After that, only Module 1 exists: tell them the next module
opens next session rather than improvising it.

## Step 4 — always finish by saying what is next

One or two lines. What they just cleared, and what the next step is. Then stop and wait.
