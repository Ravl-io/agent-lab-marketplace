---
name: track
description: Show the Agent Lab tracks, choose one, or switch. With no argument, shows your current track.
argument-hint: "[track-id]"
disable-model-invocation: true
allowed-tools: Bash, Read, AskUserQuestion
---

Show or change the participant's track.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" show --json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" tracks --json
```

## No track chosen yet

Present all three: name, tagline, `best_for`, `data_you_get`, and `final_deliverable`. Then
use **AskUserQuestion** to let them pick, with each track's tagline as the option
description. Record it:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" set-track <id>
```

## A track is already chosen

Show the current track in useful detail — the scenario, what they will have built by the end
of each module (`you_will_build`), and the final deliverable. Then mention they can switch
with `/lab:track <other-id>`, and list the other two ids.

## They asked to switch

`$ARGUMENTS` may name the track directly. Before switching, check `progress` in the state:

- **Nothing completed yet** — switch without ceremony.
- **Module 1 or later already completed** — warn first, then let them decide. Their plugin,
  their corpus and their golden queries are all track-specific, so switching now means
  starting the plugin over. The tutor keeps their progress record either way, and the switch
  is logged with a reason. Ask for confirmation, and pass their reason through:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" set-track <id> --reason "<why they switched>"
```

An unknown track id makes the script exit non-zero and list the valid ids — show that rather
than guessing what they meant.
