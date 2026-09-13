# Module 3 — Knowledge graphs and ontologies

**Two hours.** They end with plugin v0.3: an ontology, a graph with provenance and validity
dates, the graph exposed as a tool, and a skill that routes on the shape of the question.

## What this module is for

By the end they should be able to answer, out loud, to a colleague: *which questions is
retrieval structurally unable to answer, what do I build instead, and when is building it
not worth it?*

The last part is not a throwaway. A graph nobody maintains is worse than no graph, and the
participants most likely to build one are the ones who need to hear when not to.

## The arc

| Step | Time | What they do | Checkpoint |
|---|---|---|---|
| **0** | 5m | **Setup** — `pyyaml`, and nothing else | `M3.C0-setup` |
| **1** | 14m | **The cold open** — run the three broken questions. Watch the scoreboard say two of them *passed* | |
| **2** | 16m | **Competency questions → ontology** — 6-10 types, 8-12 relations, derived from the questions | `M3.C1-ontology` |
| **3** | 20m | **Extract and compile** — nodes, edges, provenance, validity. Then diff against the verified graph | `M3.C2-graph` |
| **4** | 12m | **Query it by hand** — answer the three questions that were broken an hour ago | |
| **5** | 15m | **The graph as a tool** — MCP, intent-level, no SQL | `M3.C3-tool` |
| **6** | 20m | **Route by shape** — graph for structure, retrieval for evidence, both for most real questions | `M3.C4-hybrid` |
| **7** | 8m | **Governance, and when not to build one** | module complete |

**Authoring status:** all four modules are authored.

## The result this module rests on

Measured on all three tracks, with the shipped corpora and the reference ontologies:

**The verified graph answers all eight graph questions exactly** — precision 1.0, recall 1.0,
across multi-hop, aggregation and temporal.

That is necessary but it is not the lesson. A graph built to answer eight questions answering
those eight questions is nearly tautological. **The lesson is what the retrieval harness says
about the same questions**, and it is in `facilitator/module-3-measured.md`. Read that before
you teach this, because step 1 depends on it and it is not what anybody expects.

## Every track runs this module, and the graph argument differs on each

| Track | Corpus | What the graph is doing |
|---|---|---|
| `support-triage` | 12 documents **and a database** | joining prose facts to database rows |
| `vendor-qa` | 15 documents, no database | structuring facts scattered across contracts, a register and findings packs |
| `docgen` | 21 documents, no database | the same, across charters, minutes and status updates |

On `support-triage` somebody will ask "why not just write SQL?" within five minutes, and they
are right to. Have the answer ready — it is in the facilitator notes, and it is specific:
KI-77's fix version is in the database, its region scope is in one line of prose, and neither
source answers the question alone.

Their three questions come from `track.json` → `graph_questions`, and they are already in the
ontology template the stage installs. Do not read another track's questions to the room.

---

## Step 0 — Setup (5 minutes)

```
python3 -m pip install --quiet pyyaml
```

Into the same virtualenv Module 2 created. That is the whole of it: the graph is SQLite,
which ships with Python, and the ontology is YAML.

Say that out loud, because it sets expectations correctly for the whole module: **a knowledge
graph is a few hundred rows in a database you already have.** Nobody needs a graph database
to answer the questions in this room, and the ones who think they do will spend three months
on procurement instead.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M3.C0-setup
```

---

## Step 1 — The cold open (14 minutes)

The most important fourteen minutes in the module. Everything after this is construction.

### 1.1 Run the three broken questions

They left Module 2 with three questions deliberately unanswered. Run the retrieval
scoreboard again and look at the `unreachable` tier.

```
/lab:eval where we left off
```

### 1.2 Read out what the harness says, and let it sit

On `support-triage` with the lexical baseline, the harness reports **two of the three as
answered**. With structural chunking, one of three.

Let the room notice. Someone will say "so retrieval can do it after all?"

### 1.3 Now show them why that is wrong

Take G13 — *which other accounts are exposed to KI-77?* Its anchor phrase is *"accounts in
region `eu-west` only"*, which sits in `known-issues.md`. Any retriever that returns that
file scores a hit.

Then ask the question the metric cannot: **which accounts?**

The answer needs the account list and each account's platform version. Those are in the
database. **No document in the corpus contains them.** The phrase was retrieved; the answer
was never there.

Say the general form plainly, because it is the most transferable idea in the module:

> Retrieval did not fail loudly here. It failed while a metric said it succeeded.

And the consequence: **a metric is only valid for the question shapes it was designed for.**
Module 2's anchor check is a good metric for "does the answering sentence come back". Reused
on "which ones, how many, as of when", it produces confident nonsense — which is exactly what
happens when a team takes an eval that worked and points it at a new class of question.

### 1.4 Name the three shapes

| Shape | Their question | Why retrieval cannot do it |
|---|---|---|
| **Relational** | the multi-hop one | the answer is several hops apart, in no single passage |
| **Aggregation** | the "how many / which all" one | top-k returns the most similar few; it has no way to return what it missed |
| **Temporal** | the "as of" one | two versions are equally relevant and only their dates separate them |

The third one they have already met — Module 2's metadata step. Say so: **filters got them
one date-aware answer, and it did not generalise.** A filter can exclude a superseded
document. It cannot tell you what the scope *was* in April, or reconstruct a state.

### 1.5 Do not let them start modelling yet

Someone will want to draw boxes and arrows. Hold them off for one more beat, because the
method is the point of step 2 and they will skip it if they have already started.

---

## Step 2 — Competency questions, then the ontology (16 minutes)

### 2.1 Install the template and read it

```
/lab:next
```

Stage `m3s1-ontology` installs `ontology/ontology.yaml`, **already carrying their own three
questions**. That is deliberate: the questions are the specification.

### 2.2 The one rule

> **Derive the ontology from the questions you have to answer, never from the data you
> happen to have.**

Modelling the data gives you a database schema with extra steps, and it grows without limit
because every column looks like it might matter. Modelling the questions gives you the
smallest graph that answers them — the only kind anybody maintains.

The test for every candidate type: **which of the three questions traverses it?** If the
answer is none, it does not go in. Not yet.

### 2.3 They write the traversals first, in words

Before any YAML. For each question: *start at X, follow A to Y, then B backwards to Z, then
compare a property.*

This is the step they will skip and the step that does the work. Writing the traversal is how
you discover which relations you need and which way each one points. Insist on it.

### 2.4 Then the types and relations

6-10 types, 8-12 relations. Two things to be firm about:

**Read every relation aloud as a sentence.** "Account on_plan Plan." If it does not read as
one, the direction is probably wrong — and a backwards edge does not error, it answers
questions incorrectly and looks completely normal.

**Whatever changes over time gets `temporal: true`.** Their temporal question turns on exactly
one relation. Find it.

### 2.5 The two traps worth planting deliberately

Both were hit while building this module, on real corpora. Raise them when the room gets near.

**Identity is a decision, not a lookup.** On `vendor-qa` there are three different criteria
called AC-4, one per milestone, and they say different things. Keying on `AC-4` alone merges
them, and the multi-hop question then answers confidently with the wrong requirements.
Nothing about the result looks broken. Ask every room: *what makes two mentions the same
thing?* and make them write the rule down.

**A flag describes whatever you attach it to.** On `docgen` both charter versions live in one
file, so a per-project "current scope" cannot be right for both halves — validity has to hang
off a version node. This is Module 2's metadata lesson one level deeper, and worth naming as
the same lesson.

### 2.6 Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_ontology.py"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M3.C1-ontology
```

The gate checks design properties, not spelling: derived from questions, the right size, time
modelled where a question needs it, no orphan types, every relation between declared types.

---

## Step 3 — Extract and compile (20 minutes)

### 3.1 Install the pipeline

```
/lab:next
```

Stage `m3s2-extract` installs `kg/compile.py` and `kg/kg.py` — **given, not written.** The
SQLite plumbing is not the lesson and there is no time to spend on it. It also installs an
extraction skill with the procedure left to them, and their graph eval set.

Tell them the compiler is worth reading even though they did not write it, because what it
*validates* is the ontology's whole value.

### 3.2 They write the extraction

Four things, and each has a failure behind it:

| Do | Because |
|---|---|
| decide identity per type, and write the rule down | the compiler catches two nodes with one id; it cannot catch one node that should have been two |
| record `source` on every node | an answer nobody can trace is not usable by whoever has to act on it |
| read every edge aloud before writing it | a backwards edge answers questions wrongly and looks fine |
| close a fact, never overwrite it | the closed edge is the only thing that can answer what was true then |

That last one is the one to press. The instinct is to keep what is true now and drop the rest.
**Measured, deleting the closed rows breaks the temporal question immediately** — on
`support-triage`, dropping the closed entitlement edges makes "was Kestrel entitled in April"
unanswerable, and the gate names it.

### 3.3 Compile, and read the validation

```
python3 kg/compile.py
```

It validates before it writes. Four classes of error, all of which were injected into a
working graph and all of which it caught:

| What goes wrong | What it says |
|---|---|
| edge pointed the wrong way | names the declared direction and the actual one |
| edge to a node that does not exist | dangling edge |
| a type the ontology does not declare | unknown type |
| two nodes with the same id | duplicate identity — entity resolution |

Use that list to answer "why write the ontology first". **A graph hides a bad fact far better
than a document does** — nothing looks odd about a tidy row, and there is no passage to read
and disbelieve.

### 3.4 Diff against the verified graph

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_graph.py"
```

It compiles, scores against their eval set, and diffs against a verified graph.

**Be explicit that a difference is not a mistake.** If their graph answers every question,
they modelled it differently, and that is a conversation about trade-offs rather than a
correction. What matters is the score.

Watch for one signature in particular: **precision 1.0 with recall below 1.0.** That means
the graph is right about everything it contains and is missing facts — an extraction gap, not
a modelling error. The two need different fixes and look identical in a summary.

Their score is recorded on its own board, separate from Module 2's:

```
/lab:status
```

Two boards, and they are separate on purpose: retrieval is scored on whether the answering
phrase came back, the graph on whether a **set** was complete. Averaging them would hide the
one thing that matters here.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M3.C2-graph
```

---

## Step 4 — Query it by hand (12 minutes)

### 4.1 Answer the three questions

No tools, no agent. `kg/kg.py` from the command line, or SQL against `kg.db`.

```
python3 kg/kg.py reach KI-77 --path scoped_to_region,'<in_region'
python3 kg/kg.py coverage Ticket --missing escalated_to
python3 kg/kg.py as-of plan:Growth includes_feature --date 2026-04-15
```

**Quote the `<`.** It means "traverse this relation backwards", and to a shell it means
redirect input — unquoted, the command fails with something that looks nothing like the
real problem. Somebody will hit this; it is thirty seconds to say and five minutes to debug.

(Those are the `support-triage` examples. Use their own track's relation names — `kg_ontology`
or the ontology file has them.)

Doing it by hand first matters. When the agent gets these tools in step 5 and composes a
traversal, they need to already know what a right answer looks like.

### 4.2 The moment to point at

An hour ago these three questions were unanswerable. Now they are one command each. Let that
land before moving on — it is the payoff the whole module was built for.

### 4.3 Two things they will notice, and both are real

**`<` in a path.** `Defect -scoped_to_region-> Region` and `Account -in_region-> Region` both
point *at* the region, so getting from a defect to the accounts in its scope means forwards
then backwards. That asymmetry is not a wart; it is what edge direction means, and reading a
path aloud is how you catch a modelling mistake.

**Shortest is not always most meaningful.** `paths CASE-4123 version:5.4.1` returns a two-hop
route through the account, not the four-hop route through the defect and its fix. Both are
true. The shorter one is less interesting. Say so, because it is the limit of "just find a
connection".

---

## Step 5 — The graph as a tool (15 minutes)

### 5.1 Install it

```
/lab:next
```

Stage `m3s3-kg-tool` installs `mcp/kg_server.py` with the plumbing written and the tool
surface left to them — the same division as Module 2's retrieval server, because the surface
is the lesson both times.

**They add a second server block to `.mcp.json` beside the retrieval one.** Do not let them
replace it: the point of step 6 is having both.

### 5.2 The one design rule

> Expose **question shapes**, never SQL.

The temptation is a single `query_graph` tool taking SQL. Then the model has to know the
schema, the relation names and the date semantics — and it will get the temporal ones wrong
silently, which is the failure this whole module exists to prevent. The gate fails a server
that exposes SQL.

Six tools cover the shapes: `kg_search`, `kg_entity`, `kg_reach`, `kg_coverage`, `kg_as_of`,
`kg_ontology`.

### 5.3 Two failure modes specific to graph tools

**`kg_ontology` is not optional.** Without it the model invents a relation name, gets an empty
set, and reports "none" — a wrong answer that looks like a real one.

**An empty result must say which kind of empty it is.** A valid traversal that found nothing
and a mistyped relation are indistinguishable in an empty list. The reference server checks
the path against the ontology and says *"this is not an empty answer — the path is wrong"*.
The gate fails a server that does not.

For `kg_as_of`, the description has to name the trigger words — a date, a month, "at the
time", "currently", "still". The model will not infer that "currently" means an as-of query.
Same lesson as the skill description in Module 1, third time around, and it still costs
accuracy when they skip it.

### 5.4 Watch it compose a traversal

Restart the session, ask their multi-hop question in plain language, and watch the agent call
`kg_ontology` and then `kg_reach` with a path it worked out.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_kg_tool.py"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M3.C3-tool
```

---

## Step 6 — Route by the shape of the question (20 minutes)

### 6.1 They now have two tools that are good at opposite jobs

| | Good at | Bad at |
|---|---|---|
| retrieval | what a document *says* — wording, reasons, quotes | completeness, relationships, as-of a date |
| graph | structure, complete sets, several hops, what was true when | nuance, wording, why somebody decided |

Most real questions need both, and the skill is knowing which part needs which.

### 6.2 Show each one failing at the other's job

Worth doing live, two minutes:

- Ask the graph *why* Cirrus depends on Atlas. It knows **that** it does. The reason is a
  sentence in a charter and the graph does not have it.
- Ask retrieval *which* projects were waiting on Atlas. Measured, it returns status updates,
  which name neither dependant.

### 6.3 The skill

```
/lab:next
```

Stage `m3s4-hybrid` installs `.claude/skills/answer-with-graph/SKILL.md`. Five steps:
classify the question, graph for the structure, retrieval for the evidence, attach a date,
cite and declare gaps.

The order is the content: **graph for the set, retrieval for the sentence.** Retrieving first
and hoping structure emerges is what Module 2 measured failing.

Two constraints to insist on:

- **Never answer a completeness question from retrieval.** Top-k cannot tell you what it
  missed. If the question is "which all", the graph answers or nobody does.
- **Never answer a temporal question without a date.** An entitlement, a scope or a deadline
  quoted with no date attached is not an answer, and it is the specific way these systems
  mislead people who trust them.

### 6.4 The claim they can now make

When a graph traversal returns a set, it is **complete**. "All three" is a stronger and more
useful claim than "here are three", and only the graph entitles them to make it. Point out
that they could not honestly say that at any earlier point in the course.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_skill.py" --name answer-with-graph
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M3.C4-hybrid
```

### 6.5 Package it — plugin v0.3

The skill goes into the plugin; the graph server stays in the project, for the same reason the
retrieval server did — it needs `kg.db`, which is situation, not capability.

```
mv .claude/skills/answer-with-graph <their-plugin>/skills/answer-with-graph
```

Bump `<their-plugin>/.claude-plugin/plugin.json` to `"version": "0.3.0"` and validate:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_plugin.py"
```

---

## Step 7 — Governance, and when not to build one (8 minutes)

### 7.1 The ontology is a contract, so somebody owns it

Three questions to put to the room, and they should leave with answers for their own team:

**Who owns it?** A schema with no owner drifts until it describes nothing. It is usually
whoever owns the vocabulary already — the PMO, the data team, the people who run the register.

**How does it change?** A new question arrives and needs a relation nobody modelled. That is
normal and it is the process, not a failure. The `not_modelled` section is what makes the
conversation cheap: it says what was considered and rejected, so the next person does not
re-litigate it.

**How do you know it is drifting?** `kg_coverage` is the gap report. Run it over the types
that matter and the absences tell you what the extraction is missing or what the ontology
never modelled. Nobody has to remember to check; it is a query.

### 7.2 When not to build a graph — and mean it

The most valuable thing some of them will hear today.

**Do not build one when:**

- Your questions are all "what does the document say". That is retrieval, it is cheaper, and
  Module 2 already did it.
- Your data is already in one relational database and stays there. Then write SQL. A graph
  earns its place when facts from prose have to sit beside rows from a table — which is
  precisely the `support-triage` argument, and is not every team's situation.
- Nobody will maintain the extraction. A graph that silently stops being re-extracted is the
  worst artifact in this course: confident, complete-looking, and quietly describing last
  quarter.

**Build one when** the questions are relational, about completeness, or about state over
time — and when the facts are scattered across documents that no single query can join.

### 7.3 Close

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" complete-module 03
```

Plugin v0.3. What they can do now that they could not this morning is not "build a knowledge
graph" — it is **tell which questions their system cannot answer, and why.** That is the
sentence to end on.

Module 4 takes the whole thing and asks whether it is fit to put in front of a colleague.

---

## If the clock has beaten you

| Keep at all costs | Step 1 (the metric lying) and step 4 (the three questions answered). The module's two moments |
|---|---|
| Cut to a demo | Step 6 — you drive the hybrid skill, they read the routing table |
| Cut hard | Step 3's extraction: hand them the verified graph with `/lab:catchup --with-reference` and spend the time on step 4 |
| Never cut | Step 7.2. A room that leaves ready to build graphs for everything has been taught the wrong thing |

If step 2 overruns, that is usually a good sign — the argument about what a type *is* is the
module working. Take the time out of step 3.
