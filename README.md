# Agent Lab

An 8-hour hands-on training — four sessions of two hours — in which each participant builds
**one real Claude Code plugin**, progressively, and learns how agents work by building the
thing rather than watching slides about it.

It is a training in **AI fluency**: going from understanding how AI agents work to building a
full AI system that accomplishes real, complex work.

| Module | | |
|---|---|---|
| **1** | Harness and coding agent | What an agent is, what the harness is made of, how to extend it |
| **2** | RAG and retrieval systems | Grounding the agent in your own documents, and measuring it |
| **3** | Knowledge graphs and ontologies | The questions retrieval cannot answer, and the semantic layer that can |
| **4** | The full AI system | Validating and improving it until it is production-ready |

Participants are taught by a plugin, so every primitive they learn has a working reference
they can open and read.

## Publishing

This sandbox and the published marketplace repo have **different layouts**, and one field
differs because of it:

| | Here | `Ravl-io/agent-lab-marketplace` |
|---|---|---|
| plugin tree | `lab/` | `plugins/lab/` |
| `plugins[0].source` | `./lab` | `./plugins/lab` |

So a sync is: `rsync -a --delete lab/ <repo>/plugins/lab/`, copy `PLAN.md`, `README.md` and
`docs/CURRICULUM.md`, and then **bump `plugins[0].version` in the repo's own
`.claude-plugin/marketplace.json` rather than copying this one over it.** Copying it verbatim
sets `source` to `./lab`, which does not exist there, and every install fails.

Bump the version in **both** manifests or installed plugins never pick the change up —
`plugin install` reports "already installed" and says nothing else.

- [PLAN.md](PLAN.md) — design, architecture, build phases, risks
- [docs/CURRICULUM.md](docs/CURRICULUM.md) — the detailed module-by-module outline

## For participants

Everything you need is four steps. Your facilitator will confirm the marketplace name.

**1. Make an empty folder and open VS Code in it.**

```bash
mkdir ~/agent-lab && cd ~/agent-lab && code .
```

The lab needs its own folder — it becomes a git repository with your checkpoint commits in
it. Do not open VS Code in your home directory.

**2. Open the Claude Code panel and add the marketplace.**

```
/plugin marketplace add chihebdk/agent-lab
```

**3. Install the plugin.**

```
/plugin install lab@agent-lab
```

If the install summary says `Run /reload-plugins to activate`, run that.

**4. Start.**

```
/lab:start
```

That orients you, shows the curriculum, lists what you need installed, checks your machine,
and asks which track you are on. It is also the command you run at the beginning of every
session to pick up where you left off.

### Commands

| Command | What it does |
|---|---|
| `/lab:start` | Orientation, checklist, environment check, track selection — and your resume command each session |
| `/lab:next` | Start the next module, or move to the next step |
| `/lab:status` | Where you are: track, module, checkpoints, workspace health |
| `/lab:hint` | A nudge when you are stuck — not the answer |
| `/lab:catchup` | Repairs your workspace if something breaks |
| `/lab:checklist` | What you need installed, and how to install it |
| `/lab:doctor` | Verify your machine is ready (`--quick` for a fast resume check) |
| `/lab:track` | See the tracks, choose one, or switch |
| `/lab:handbook` | Open the handbook — the reference guide, shipped with the plugin |

More commands unlock with the modules. `/lab:start` always tells you what is next.

## For the facilitator

### Publish it

```bash
git init && git add -A && git commit -m "Agent Lab"
gh repo create agent-lab --private --source=. --push
```

Then send participants the two commands from step 2 and 3 above. If your repo is not
`chihebdk/agent-lab`, update the `owner/repo` in the instructions you send — the marketplace
name (`agent-lab`) comes from `.claude-plugin/marketplace.json` and is independent of the
repo name.

A private repo works: participants need read access to it, which they get through their own
GitHub authentication.

### Test locally without publishing

```bash
python3 lab/scripts/selftest.py    # static self-test: tracks, stages, substitution, commands
claude --plugin-dir ./lab          # loads the plugin for one session, no install needed
claude plugin validate ./lab       # validate the plugin manifest
claude plugin validate .           # validate the marketplace manifest
```

Run `selftest.py` after any change to a track, a stage or a command. It catches the failures
that only show up in front of a room: a stage payload leaking one track's task to every
group, an unresolved placeholder, a file the module tells participants to open that does not
exist on their track, or a command promised in the text but never implemented.

Run `/reload-plugins` after editing plugin files in a live session.

### Session 0

See [lab/facilitator/session-0-setup.md](lab/facilitator/session-0-setup.md) for the
pre-flight message to send 48 hours ahead, the exact words for walking the room through
install, and what to do when a machine will not cooperate.

## Repository layout

```
.claude-plugin/marketplace.json   the marketplace catalogue
lab/                              the tutor plugin
├── .claude-plugin/plugin.json    plugin manifest — `name: lab` sets the /lab: namespace
├── skills/
│   ├── start/  checklist/  doctor/  track/    user-invoked (disable-model-invocation)
│   └── tutor/                                 model-invoked: teaches, coaches, corrects
├── scripts/
│   ├── doctor.py                 owns the requirement definitions: checklist AND validation
│   ├── state.py                  the only thing that writes .agent-lab/state.json
│   └── session_banner.py         SessionStart hook — silent outside a lab folder
├── hooks/hooks.json
├── references/                   orientation, curriculum, misconceptions
│   └── handbook.html             the course companion: one self-contained file
├── tracks/{support-triage,vendor-qa,docgen}/track.json
└── facilitator/
PLAN.md  docs/                    design and curriculum
```

Participant state lives in **their** folder, at `.agent-lab/state.json` — never in the plugin.
