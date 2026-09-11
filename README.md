# Agent Lab Marketplace

A Claude Code plugin marketplace distributing the hands-on lab for the Enterprise AI Fluency
course: **four two-hour modules in which each participant builds one real plugin**, covering
the Claude Code harness, RAG and retrieval, knowledge graphs and ontologies, and what it takes
to turn any of it into a system a team would rely on.

| Plugin | What it is |
|---|---|
| `lab` | The tutor. Orients you, checks your machine, picks your track, then teaches the modules by having you build |

## For participants

Three commands. Your facilitator will confirm nothing else is needed.

**1. Make an empty folder and open VS Code in it.**

```bash
mkdir ~/agent-lab && cd ~/agent-lab && code .
```

The lab needs its own folder — it becomes a git repository holding your checkpoint commits.
Do not open VS Code in your home directory or an existing project.

**2. In the Claude Code panel, add the marketplace and install the tutor.**

```
/plugin marketplace add Ravl-io/agent-lab-marketplace
/plugin install lab@agent-lab
```

If the install summary says `Run /reload-plugins to activate`, run that.

**3. Start.**

```
/lab:start
```

That orients you, shows the curriculum, lists what you need installed, checks your machine,
and asks which track you are on. It is also the command you run at the beginning of every
session to pick up where you left off.

**Accept the trust prompt** when Claude Code shows it. Until you do, the project's permission
settings are ignored and every tool call stops to ask.

### Commands

| Command | What it does |
|---|---|
| `/lab:start` | Orientation, checklist, environment check, track selection — and your resume command each session |
| `/lab:next` | Start the next module, or move to the next step |
| `/lab:status` | Where you are: track, module, checkpoints, workspace health |
| `/lab:hint` | A nudge when you are stuck — not the answer |
| `/lab:catchup` | Repairs your workspace if something breaks |
| `/lab:checklist` | What you need installed, and how |
| `/lab:doctor` | Verify your machine is ready |
| `/lab:track` | See the tracks, choose one, or switch |

### The three tracks

Same concepts and the same timeline; different corpus and task. Your facilitator may assign
one, or you choose at `/lab:start`.

| Track | The job |
|---|---|
| `support-triage` | L2 support: decide whether a ticket is configuration, user error, or a real product defect — with evidence |
| `vendor-qa` | Check a vendor's deliverables against the contract, and produce findings they cannot argue with |
| `docgen` | Turn a month of messy sources into a cited report in house style |

## Requirements

Python 3.10+, Git 2.30+, and VS Code with the Claude Code extension. Run `/lab:checklist`
for the full list with install commands for your platform, or `/lab:doctor` to check your
machine. macOS ships Python 3.9 as `python3`; the lab detects a newer interpreter
automatically, so that is not a problem.

## For facilitators

- [PLAN.md](PLAN.md) — design, architecture, build phases, risks
- [docs/CURRICULUM.md](docs/CURRICULUM.md) — the module-by-module outline with run-of-show timings
- [plugins/lab/facilitator/session-0-setup.md](plugins/lab/facilitator/session-0-setup.md) — the
  pre-flight message to send 48 hours ahead, how to open the session, and what to do when a
  machine will not cooperate
- [plugins/lab/modules/](plugins/lab/modules/) — the teaching content the tutor follows

Before any change to a track, a stage or a command, run the self-test:

```bash
python3 plugins/lab/scripts/selftest.py
```

It applies every stage for every track and checks the failures that only show up in front of
a room: a stage payload leaking one track's task to every group, an unresolved placeholder, a
file the module tells participants to open that does not exist on their track, or a command
promised in the text but never implemented.

Test the plugin without installing it:

```bash
claude --plugin-dir ./plugins/lab
claude plugin validate ./plugins/lab
claude plugin validate .
```

## Retired

`agent-lab-module-1` — the earlier Crestview Wealth ops-reporting lab. Superseded by `lab`,
which covers the same ground across three domain tracks with progress tracking and validation
gates. Its files remain in `plugins/agent-lab-module-1/` and in git history; it is no longer
listed in the marketplace, so it cannot be installed.
