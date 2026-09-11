# Agent Lab — Plan

A tutor plugin for an 8-hour hands-on training (4 x 2h) that teaches AI agents, the
Claude Code harness, plugin authoring, RAG, agentic RAG, ontologies/knowledge graphs,
and the new AI SDLC — by having each participant **build one real plugin, progressively,
across all four modules.**

---

## 1. The core idea

> The participants learn the harness by **building a plugin**, taught **by a plugin**.

Three properties drive every design decision below:

1. **One running artifact.** Not four disconnected exercises. Each group starts a plugin in
   Module 1 (v0.1) and ends Module 4 with v1.0: skills + tools + hooks + a vector store +
   a knowledge graph + an eval suite + a human approval gate. They take it home and it runs.
2. **Do before name.** Every concept is introduced as a *felt limitation* of the previous
   step, then named. They hit the wall, then get the word for it. Concepts are never
   lectured ahead of the pain they solve.
3. **The tutor is the exemplar.** The tutor is itself a plugin with commands, tools, skills
   and hooks. The first hands-on activity of Module 1 is *reading the plugin that is
   teaching you*. Every primitive taught has a live, working reference two directories away.

## 2. Audience, format, outcomes

| | |
|---|---|
| **Format** | 4 separate 2h sessions = 8h, hands-on from minute 5, days apart |
| **Environment** | Claude Code inside VS Code, one repo per participant/group |
| **Participants** | Technical, mixed agent experience; split into **3 groups by domain track** |
| **Facilitator** | Live, with a run-of-show and a rescue path per checkpoint |
| **Deliverable** | A working, installed plugin per group + the concepts to redeploy it at work |

**Exit outcomes.** A participant can: name and choose between harness primitives
(command / tool / skill / hook / plugin); write a skill whose description actually triggers;
chunk and enrich a corpus and *prove* the retrieval improved with an eval; explain why a
vector store cannot answer relational, aggregate or temporal questions and design a minimal
ontology from competency questions; wire a hybrid retrieval+graph answer with citations; and
describe the AI SDLC loop from intent to human-approved change, with the human's role in it.

## 3. The three tracks

Same concepts, same checkpoints, same timeline — different corpus and task. This is what
keeps facilitation sane: **one clock, three datasets.**

| Track | Domain task | Final v1.0 behaviour |
|---|---|---|
| **A — `docgen`** | Document transformation & report generation | Ingests source docs, produces a structured report from a template, cited, with a human sign-off gate before publish |
| **B — `vendor-qa`** | QA of a third-party vendor's deliverables | Checks deliverables against contract/spec/SLA, produces findings with severity + evidence, human approves the findings pack |
| **C — `support-triage`** | L2 support diligence on user-reported tickets | Reads a Salesforce ticket, checks account config and the audit database, classifies it as configuration / user error / product defect, and proposes the resolution — customer reply, config fix, or vendor escalation — **behind a human approval gate** |

Track C is a real participant's job — an L2 support team taking user-reported tickets from
Salesforce — so it is built **first** as the reference implementation and answer key; A and B
are reskins of the same architecture. It exercises documents *and* a database while staying a
familiar, well-bounded task, which makes it the best lead track as well as the most
requested. The convergence lesson in Module 4 is unchanged: three unrelated domains, one
architecture.

## 4. Architecture

### 4.1 Two repos, cleanly separated

```
agent-lab/            # the tutor plugin — facilitator ships, participants install
workbench/            # the participant's repo — where THEIR plugin is built
└── <track>-plugin/   # their deliverable, v0.1 -> v1.0
```

The tutor **never writes into the participant's plugin** except scaffolding it explicitly
hands over. It reads, validates, grades and coaches. A read-only grader agent enforces that.

### 4.2 Tutor plugin layout

```
agent-lab/
├── .claude-plugin/plugin.json
├── skills/
│   ├── agent-lab/                     # the tutor: thin router (<200 lines)
│   │   ├── SKILL.md
│   │   ├── modules/01..04-*.md        # teaching content + exercise scripts
│   │   ├── concepts/                  # loaded on demand by /lab:explain
│   │   │   harness-primitives, context-engineering, chunking-strategies,
│   │   │   metadata-strategies, retrieval-evals, agentic-rag-patterns,
│   │   │   ontology-design, graphrag-patterns, temporality, ai-sdlc,
│   │   │   autonomy-ladder, misconceptions
│   │   ├── templates/                 # what participants copy and fill
│   │   ├── pedagogy.md                # teaching loop, quiz bank, known confusions
│   │   └── checkpoints/               # known-good state per checkpoint per track
│   ├── lab-doctor/                    # env preflight  (also an exemplar skill)
│   └── lab-eval/                      # runs the eval suites (also an exemplar skill)
├── agents/
│   ├── lab-tutor.md                   # orchestrator: state, pacing, gating
│   ├── lab-grader.md                  # READ-ONLY validator of artifacts + evals
│   └── lab-coach.md                   # unblocks without giving the answer
├── commands/  lab-start lab-status lab-next lab-track lab-doctor
│              lab-checkpoint lab-catchup lab-hint lab-eval
│              lab-explain lab-quiz lab-reset
├── hooks/hooks.json                   # SessionStart progress banner; checkpoint nudge
├── tracks/{docgen,vendor-qa,support-triage}/
│   ├── track.yaml  corpus/  data/  golden/  ontology-hint.yaml
│   ├── holdout/                       # unseen capstone cases
│   └── reference-solution/            # complete v1.0 — rescue + post-course study
├── facilitator/  run-of-show.md pre-flight.md troubleshooting.md
│                 talking-points.md rubric.md
└── scripts/  setup.sh verify.sh seed_chroma.py build_kg.py eval.py
```

### 4.3 State and progress

`workbench/.claude/state.json` — track, group, mode, current module/checkpoint,
per-checkpoint validation flags, artifact map, quiz results, open issues, timings, and
**`eval_history`** — the running scoreboard.

The scoreboard is a deliberate motivational device: from Module 2 onward every improvement
is *measured*, and `/lab:status` shows the number climbing (naive chunking -> structural ->
+metadata -> +hybrid -> +agentic -> +graph). Evals stop being an abstraction.

### 4.4 Two modes

- **guided** (default): full explanations, quizzes, checkpoint gates.
- **fast**: terse, artifact-gated, for participants who already know the basics.

Plus `/lab:explain <concept>` for on-demand depth, so fast groups skip and curious ones dig
without derailing the clock.

### 4.5 The rescue path (non-negotiable for live training)

Every module has 3-4 **checkpoints**. `/lab:catchup` fast-forwards a stuck participant to the
current checkpoint's known-good state from `checkpoints/`. Nobody is ever stranded, and one
broken laptop never stalls the room. This is why the reference solution gets built first.

### 4.6 The resume ritual (because sessions are days apart)

Each session opens with a 5-minute cold-start recovery, driven by `/lab:start`:

1. Read `state.json` — show the scoreboard and "here is what you built last time".
2. `/lab:doctor --quick` — verify the environment still works (new laptop, expired venv, moved repo).
3. Verify the artifacts from the last checkpoint still exist and still run.
4. If anything drifted, offer `/lab:catchup` to restore the last checkpoint.
5. 3-minute recap of the previous module's concept, then straight into the first exercise.

This is why checkpoints are stored as **self-contained state**, not as conversation context:
a participant must be able to resume on a fresh machine with an empty session.

### 4.7 One primitive, two invocation modes (a correction to the ladder)

Verified against the current docs while scaffolding: **a "command" and a "skill" are the same
primitive.** `commands/*.md` is documented as "skills as flat Markdown files", and the real
distinction is *who decides to invoke it*:

- `disable-model-invocation: true` — only the user can invoke it. This is what everyone calls
  a slash command.
- no flag — the **model** decides, from the `description`, whether to load it.

This sharpens Module 1 rather than complicating it. The ladder becomes:

| Rung | What it fixes |
|---|---|
| **Prompt** | gets a result, once |
| **User-invoked skill** (a "command") | repeatable, versioned, shareable |
| **Tool** | deterministic action, structured output |
| **Model-invoked skill** | the agent decides *when* to apply it — from the description |
| **Hook** | enforcement the model cannot skip |
| **Plugin** | packages all of it, installable, versioned |

The pedagogical payoff is bigger than the old framing: the participant writes one file, flips
one frontmatter flag, and watches it change from something they invoke into something the
agent invokes. **The description stops being documentation and becomes the trigger.** That is
the single most useful thing to understand about skills, and it now has a two-minute exercise
attached to it.

## 5. Technical decisions (recommended defaults)

| Decision | Choice | Why |
|---|---|---|
| Embeddings | **Local ONNX** (Chroma default `all-MiniLM-L6-v2`), pre-cached in offline bundle | No API key, no rate limits, works on bad wifi. API embeddings optional as a 5-min quality-comparison exercise |
| Vector store | **ChromaDB**, persistent local | As specified; no server to run |
| Graph store | **SQLite** property/triple store + **MCP server** | No Neo4j, no Docker. Mirrors the shape of the `onthos-kg` tools. Cypher covered conceptually only |
| Tool surfaces | 1 CLI tool (M1) + 2 MCP servers (M2 retrieval, M3 kg) | They learn both surfaces and when each fits |
| Language | **Python** for RAG/KG scripts, Markdown-first for skills/commands | Chroma ecosystem; keeps skills readable |
| Distribution | Marketplace `agent-lab`, plugin **`lab`** | Plugin skills are namespaced `/<plugin>:<skill>`, so naming the plugin `lab` yields `/lab:start`, `/lab:doctor`, `/lab:track` |
| Command layout | `skills/<name>/SKILL.md` with `disable-model-invocation: true` — not `commands/` | `commands/` is documented as legacy ("skills as flat markdown files; use `skills/` for new plugins"). The plugin is the exemplar, so it models current practice |

**Biggest delivery risk is environment, not content.** Mitigations: `/lab:doctor` preflight, a
pre-flight setup email run 48h early, an offline bundle (vendored wheels + pre-cached
embedding model + prebuilt Chroma index and `kg.db` as fallback), and `/lab:catchup`.

## 6. How we build it

| Phase | Work | Exit criterion | Est. |
|---|---|---|---|
| **P0** Foundations | Repo + plugin scaffold, state schema, `/lab:doctor`, `setup.sh` | doctor green on clean macOS **and** Windows/WSL | 0.5d |
| **P1** Spine | tutor/grader/coach agents, all commands, hooks, checkpoint + catchup mechanics, scoreboard rendering | walk a full 4-module flow end-to-end on stub content | 1d |
| **P2** Lead track | `support-triage` corpus, data, golden sets, holdout, **reference solution v1.0** | reference solution passes every eval suite | 1d |
| **P3** Module 1 content | Primitive ladder exercises, templates, quizzes | dry-run M1 inside 2h wall clock | 0.75d |
| **P4** Module 2 content | Chunkers, Chroma seeding, eval harness, agentic RAG skill template | baseline -> improved deltas reproducible on demand | 1d |
| **P5** Module 3 content | Ontology method, extraction skill, kg build, MCP kg server, hybrid skill, graph golden set | the "3 questions vector can't answer" demo works, repeatably | 1d |
| **P6** Module 4 content | Spec templates, proposal pipeline, approval hook + `/approve`, capstone rubric | full v1.0 e2e on an unseen holdout case | 0.75d |
| **P7** Tracks A + B | Reskin corpus/golden/holdout/reference via the track abstraction | all three tracks pass `verify.sh` | 1d |
| **P8** Facilitator kit + dry run | Run-of-show, pre-flight, troubleshooting, offline bundle, pilot | full 8h dry run with 2-3 pilots; timings corrected | 1d |

**~8-9 working days.** Build order front-loads the risky parts (environment, KG, track data)
and produces a walkable skeleton early, so content lands into a working frame instead of
being integrated at the end. Critical path is P2 and P5.

## 7. Risks

| Risk | Mitigation |
|---|---|
| Environment failures eat session time (higher risk: one repo per participant, x4 sessions) | `/lab:doctor` full + `--quick` at every resume, pre-flight 48h early, pre-cached embedding model, `/lab:catchup` |
| Module overruns (the classic 2h trap) | Minute-level run-of-show, timeboxed exercises, checkpoints as cut lines, optional exercises marked as such |
| Mixed skill levels | guided/fast modes, `/lab:explain`, `/lab:hint`, pair fast+slow within groups |
| Graph extraction quality is noisy live | Ship a verified `kg.db` per track; extraction becomes a *comparison* exercise against the verified one |
| Rate limits with 3 groups running evals | Local embeddings; small golden sets (15-20 queries); LLM-judge used sparingly and cached |
| Participants conflate graph vs vector | Purpose-built golden set where 5 questions are provably unanswerable by vector alone |

## 8. Delivery parameters (settled)

| Parameter | Decision | Consequence for the build |
|---|---|---|
| **Format** | **4 separate 2h sessions** | State must survive across days on a cold machine. Adds the *resume ritual* (§4.6) and optional between-session homework |
| **Track scope** | **Lead track (`support-triage`) fully first**, then reskin | Confirms build order P2 -> P7. Reference solution doubles as answer key and rescue path |
| **Environment** | **pip + network available** | Online path is primary; offline bundle drops to a fallback. Embedding model still pre-cached (3 groups downloading it at once is a slow start, not a broken one) |
| **Group setup** | **Each participant their own repo** | Max learning per person, max environment surface. `/lab:doctor` and `/lab:catchup` carry more weight; capstone demos run on the healthiest machine in each group |

### Between-session homework (optional, never gating)

Because the sessions are separated, each module ends with one small optional extension the
tutor can detect and acknowledge at the next session — but never requires to advance:

| After | Optional homework |
|---|---|
| M1 | Add a second skill to your plugin for a different task in your track |
| M2 | Add 3 golden queries from questions your team actually asks |
| M3 | Extend the ontology with one type + two relations, re-run coverage |

See [CURRICULUM.md](docs/CURRICULUM.md) for the minute-level module outline.
