# Agent Lab Sandbox — Module 1: Claude Code & Agent Harnesses

A self-contained sandbox for the RAVL "Enterprise AI Fluency" training (prepared for IGM).
It simulates the weekly ops reporting workspace of a fictional company (Crestview
Wealth). Nothing here is real; everything here is safe to break.

## Setup (before the session)

1. Install Claude Code and sign in (see the setup guide your IT team received).
2. Clone or unzip this repository anywhere on your machine.
3. From the repo root, run `claude` and ask: *"What is this project?"*
   If the answer mentions ops reporting and house style, you're ready — the agent
   read `CLAUDE.md`.

Python 3.10+ is needed for `scripts/check_style.py` (the agent will run it for you).

## What's inside

| Path | What it is |
|---|---|
| `CLAUDE.md` | Project memory: house style and workflow rules the agent reads every session |
| `intent.md` | Stated task intent: the outcome and constraints for the current task (intent-based prompting) |
| `.claude/skills/summarize-ops/` | An Agent Skill: the team's written procedure for weekly summaries |
| `.claude/settings.json` | The permission policy — what runs freely, what asks, what's forbidden |
| `reports/` | Raw incident reports (messy on purpose; read-only by policy) |
| `summaries/` | Polished weekly summaries + index (the agent's output goes here) |
| `scripts/check_style.py` | House-style checker the skill uses to verify output |
| `tasks/TASK-CARDS.md` | Your lab task cards — builder & practitioner variants (pick one card) |

## During the lab

Start in plan mode, pick ONE task card, and keep the observation questions in view:
what did it read, what did it ask, what did it delegate, how did it know it was done?

## Reset

`git checkout . && git clean -fd` returns the sandbox to its starting state
(or re-unzip the archive).
