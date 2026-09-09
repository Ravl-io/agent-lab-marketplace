# Agent Lab Marketplace

A Claude Code plugin marketplace that distributes the hands-on lab sandboxes for the
Enterprise AI Fluency course. Each module ships as one installable plugin.

## Available plugins

| Plugin | Module | What it installs |
|---|---|---|
| `agent-lab-module-1` | 1 — Claude Code & Agent Harnesses | The `summarize-ops` Agent Skill, and `/agent-lab-setup`, which creates the Crestview Wealth ops-reporting sandbox |

## For participants

This repository is **private**. Participants need read access to the
`Ravl-io` organisation, or the repository must be made public before the session,
or `/plugin marketplace add` will fail for them.

```
/plugin marketplace add Ravl-io/agent-lab-marketplace
/plugin install agent-lab-module-1@agent-lab
/agent-lab-setup
```

The last command creates a sandbox directory, initialises git in it so the reset
instructions work, and verifies the style checker runs. Then `cd` into that directory and
start a new Claude Code session there, so the project's `CLAUDE.md` and permission policy
load. Task cards are in `tasks/TASK-CARDS.md`.

## For facilitators

Test any change locally before publishing:

```
claude plugin validate .                       # marketplace manifest
claude plugin validate plugins/agent-lab-module-1
/plugin marketplace add ./agent-lab-marketplace
/plugin install agent-lab-module-1@agent-lab
```

Run `/plugin marketplace update` after pushing changes, or participants keep the cached
version.

### What is deliberately not in this repository

`demo-crib.md` is the facilitator crib sheet. It contains the prepared demo prompts and the
behaviours to narrate, including the intended resolution of the severity ambiguity in the
Aug 15 webhook report. It is excluded because a marketplace is a distribution channel and
participants install from it. Keep it in the private facilitator materials.

The workspace payload also ships in its **starting state**. The Aug 24 summary that Card A
asks participants to produce is not included, and `summaries/index.md` lists only the
earlier summary. If you regenerate the payload from a working sandbox, strip those again or
participants will find the answer already written.

## Adding a module

1. Create `plugins/agent-lab-module-<n>/` with a `.claude-plugin/plugin.json`.
2. Put skills in `skills/<name>/SKILL.md` and commands in `commands/<name>.md`. Both
   directories are auto-discovered; they do not need declaring in the manifest.
3. Add an entry to the `plugins` array in `.claude-plugin/marketplace.json`.
4. Run `claude plugin validate .` and install it locally before pushing.

## Layout

```
.claude-plugin/marketplace.json      the marketplace manifest
plugins/
  agent-lab-module-1/
    .claude-plugin/plugin.json       the plugin manifest
    skills/summarize-ops/SKILL.md    the Agent Skill participants observe firing
    commands/agent-lab-setup.md      creates the sandbox in the working directory
    workspace/                       the lab files, copied by the setup command
```
