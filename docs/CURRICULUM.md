# Agent Lab — Detailed Curriculum

4 modules x 120 min. Every exercise is timeboxed; **checkpoints (`C1..C3`) are the cut lines** —
if the clock is lost, skip forward via `/lab:catchup` and keep the room together.

Sessions run **days apart**, so each module opens with the 5-minute resume ritual
(`/lab:start`: scoreboard, quick env check, artifact verification, optional `/lab:catchup`)
and closes with one **optional** homework extension that never gates advancement.

**The teaching loop, used for every block:**

```
FRAME (2m)  why this — what broke last time
BUILD (8-15m) they type, tutor coaches, facilitator floats
RUN   (2m)  see the actual output / the actual score
NAME  (3m)  now the concept gets its name and its boundaries
GATE  (1m)  /lab:checkpoint — validate, save, scoreboard
```

---

## Module 1 — Harness and coding agent (120 min)

**Question the module answers:** what is an agent, what is the harness made of, and which
primitive do I reach for?

**The ladder** — the intellectual core. Each rung exists because the previous one broke:

| Rung | Fixes | Still broken |
|---|---|---|
| **Prompt** | gets a result once | not repeatable, not shareable |
| **User-invoked skill** (a "command") | repeatable, versioned, shareable prompt | no determinism, can't act outside the model |
| **Tool** | deterministic action, structured output | agent doesn't know *when* or *how* to use it |
| **Model-invoked skill** | the agent decides when to apply it, from the description | the model can still choose to skip it |
| **Hook** | enforcement the model cannot bypass — guardrails and gates | not distributable on its own |
| **Plugin** | packages all of it, installable, versioned | — |

A command and a skill are **the same file format**, one frontmatter flag apart
(`disable-model-invocation`). Rung 2 and rung 4 are the same artifact invoked two different
ways, which is why the ladder spends a step turning one into the other.

| # | Time | Activity | Concept named |
|---|---|---|---|
| 1.0 | 10m | `/lab:doctor`, `/lab:start`, pick track. Open the tutor plugin in VS Code and read its `plugin.json`, a command, a skill, a hook | Agent = model + loop + tools + context. The harness. Claude Code as an AI coding agent |
| 1.1 | 10m | Do your track's task by **raw prompt** on the seed corpus. Run it twice. Note the inconsistency in `notes/pain.md` | Non-determinism; why demos lie |
| 1.2 | 12m | Convert it to `commands/<task>.md`. Run twice, compare | Prompt as a versioned artifact. Context engineering |
| — | — | **C1** — command works, pain documented | |
| 1.3 | 15m | Write a real tool: a small CLI script the agent calls, returning **JSON** | Determinism, idempotence, structured output, tool boundaries. CLI vs MCP tradeoff |
| 1.4 | 20m | Take the command from 1.2 and **delete one frontmatter line** (`disable-model-invocation`). Now rewrite the `description` until the agent fires it on a natural request — no slash command typed. Add a bundled template | Skills. **The description is the trigger, not documentation** — it is the only thing the agent sees before deciding to load. Progressive disclosure |
| — | — | **C2** — skill triggers on a natural request | |
| 1.5 | 12m | Add hooks: `PreToolUse` guard (block writes outside `workbench/`), `SessionStart` banner | Hooks as the trust boundary. Model-independent enforcement |
| 1.6 | 20m | Assemble: `plugin.json`, `CLAUDE.md`, **`intent.md`**. Install locally, run end-to-end | Plugins. Intent before code — the seed of spec-driven development |
| — | — | **C3** — plugin v0.1 installed and demoed | |
| 1.7 | 10m | Debrief: the ladder poster; choosing a primitive; anti-patterns (a skill that should be a hook, a hook that should be a skill, the mega-skill) | |

**Artifacts:** `workbench/<track>-plugin/` v0.1 — 1 command, 1 tool, 1 skill, 2 hooks,
`CLAUDE.md`, `intent.md`.

---

## Module 2 — RAG and retrieval systems (120 min)

**Question:** the agent has no idea what's in our documents. How do we ground it, and how do
we *know* we improved it?

**The device that carries this module: one scoreboard.** The same 15 golden queries are
re-scored after every change. Evals become visceral instead of academic.

| # | Time | Activity | Concept named |
|---|---|---|---|
| 2.1 | 12m | Ingest your track's corpus into **ChromaDB** with naive fixed-size chunking. Query it. Watch it fail on ~5 of 15 | Embeddings intuition; why retrieval at all (staleness, cost, citations); context window ≠ knowledge |
| 2.2 | 10m | Open `evals/retrieval/golden.yaml` (shipped, 15 queries; add 3 of your own). Run `/lab:eval retrieval` → **baseline score** | Golden sets. recall@k, MRR/nDCG, precision. Retrieval eval ≠ answer eval |
| 2.3 | 18m | **Chunking lab**: implement heading-aware/structural + parent-child (small-to-big) chunking. Re-run. Record the delta | Fixed vs recursive vs structural vs semantic vs contextual chunking; chunk/retrieve asymmetry |
| — | — | **C1** — chunking delta recorded on the scoreboard | |
| 2.4 | 15m | **Metadata lab**: define a metadata schema (source, section path, doc type, validity dates, entities, version), re-ingest, add filtered retrieval. Re-run. One query is *only* solvable with a filter (e.g. "the **current** SLA") | Authored vs derived metadata; filters as first-class retrieval; provenance; temporal validity |
| 2.5 | 15m | Wrap retrieval as an **MCP tool**: `search`, `search_filtered`, `get_document` | Tool surface design: expose intent-level operations, never the raw vector DB |
| — | — | **C2** — retrieval tool callable by the agent | |
| 2.6 | 20m | Build the **agentic RAG skill**: decompose → retrieve → assess sufficiency → re-retrieve → answer with citations. Compare against single-shot on the golden set + 3 hard multi-part questions | Agentic RAG: query decomposition, multi-query, retrieve-critique-retrieve, self-grading, stop conditions. Hybrid search + reranking (concept + optional exercise) |
| — | — | **C3** — agentic RAG beats single-shot, measurably | |
| 2.7 | 10m | Debrief on the scoreboard — then run **3 questions that are still broken** ("which vendors are affected by X", "how many incidents traced to Y", "what changed since the last version"). Leave them broken. That's Module 3's cold open | Retrieval's ceiling: relational, aggregate and temporal questions |

**Artifacts:** `rag/` (ingest + chunkers), `evals/retrieval/`, MCP retrieval server,
`skills/retrieve-and-answer/`. Plugin **v0.2**.

---

## Module 3 — Knowledge graphs and ontologies (120 min)

**Question:** why does a vector store fail those three questions, and what do we build instead?

**Three failure classes of pure vector search** — the framing for the whole module:
1. **Multi-hop / relational** — "which other accounts are exposed to the defect behind this ticket?"
2. **Aggregation / completeness** — "how many, which *all*, what's *not* covered?" (similarity
   returns the top-k most similar, never the complete set)
3. **Constraint & temporal reasoning** — "does this violate the policy in force *at the time*?"

| # | Time | Activity | Concept named |
|---|---|---|---|
| 3.1 | 12m | Take the 3 broken questions. Write them as **competency questions**. Derive a minimal ontology from them: 6-10 types, 8-12 relations → `ontology/<track>.yaml` | Taxonomy vs ontology vs knowledge graph vs semantic layer. **Design the ontology from the questions you must answer** — not from the data |
| 3.2 | 18m | Extract a graph from the corpus with an LLM-assisted extraction skill → `graph/nodes.jsonl` + `edges.jsonl` **with provenance and validity dates** → compile to `kg.db` (SQLite). Compare your extraction to the verified one | Entity resolution, identity, cardinality; extraction QA; provenance; `valid_from`/`valid_to` and supersession (never silent overwrite) |
| — | — | **C1** — ontology + graph built, spot-checked | |
| 3.3 | 12m | Query it by hand (SQL/CLI) and answer the 3 broken questions | Traversal, paths, impact, coverage/gaps |
| 3.4 | 18m | Wrap it as an **MCP tool**: `kg_search`, `kg_entity`, `kg_neighbors`, `kg_path`, `kg_impact`, `kg_coverage`, `kg_as_of` | Intent-level graph operations; why not "here's a SQL tool, good luck" |
| — | — | **C2** — kg tool callable by the agent | |
| 3.5 | 20m | Build the **hybrid answering skill**: route by question shape — graph for structure and scope, vector for evidence and quotes, both for most real questions. Answers carry citations + an as-of date. Run the combined eval (15 original + 8 graph-only) | GraphRAG patterns: graph-as-router, retrieval expansion, graph-as-answerer, vector-entry → graph-traverse → vector-evidence |
| — | — | **C3** — combined eval passes; scoreboard jumps on the graph-only set | |
| 3.6 | 10m | Ontology governance: who owns it, how it evolves, drift, `kg_coverage` / open questions as a gap report | The semantic layer as the shared contract between humans and agents |
| 3.7 | 10m | Debrief: **when not to build a graph** — build/maintenance cost vs question shape | |

**Artifacts:** `ontology/`, `graph/`, `kg.db`, MCP kg server, `skills/answer-with-graph/`,
expanded evals. Plugin **v0.3** — the full plugin: tool + vector store + ontology graph.

---

## Module 4 — The full AI system (120 min)

**Question:** now that the agent can find and reason over our knowledge, how do we *work*
this way — and what is the human's job?

**The autonomy ladder** — the spine of the module and the thing they take to their team:

| Level | Agent does | Human does |
|---|---|---|
| L0 | suggests in chat | everything |
| L1 | drafts a diff / a proposal | reads, decides, applies |
| L2 | applies in a sandbox, runs tests + evals | reviews results, promotes |
| L3 | **applies behind an approval gate** | approves per change — *this is where we land today* |
| L4 | applies autonomously with monitoring + rollback | sets policy, audits, owns outcomes |

| # | Time | Activity | Concept named |
|---|---|---|---|
| 4.1 | 15m | Write `spec/` for your track's final capability: acceptance criteria (Gherkin), out-of-scope, policies, approval requirements | Spec-driven development: intent → spec → acceptance criteria → plan → tasks → implement → eval → approve. Why specs beat prompts (durable, reviewable, reusable, testable) |
| 4.2 | 25m | Build the **proposal pipeline**: the agent produces `proposal.md` + `proposal.json` — actions/diff, evidence with citations from RAG **and** KG, confidence, risk, rollback plan. **Nothing is applied** | Separating decision from execution. Evidence as a first-class output |
| — | — | **C1** — a proposal generated on a real case, fully cited | |
| 4.3 | 20m | Build the **approval gate**: a `PreToolUse` hook that denies `apply` without an approval token + an `/approve` command a human runs. Then apply. (docgen → publish report; vendor-qa → sign off findings; incident → apply remediation) | The gate as the trust mechanism. Least-privilege tools, permissions, audit trail |
| — | — | **C2** — apply is blocked without approval, works with it | |
| 4.4 | 15m | Run the full suite `/lab:eval all`: retrieval + graph + task-level + policy compliance. Check the audit log | Evals as the new tests. Observability, cost, latency |
| 4.5 | 25m | **Capstone**: each group demos on a **held-out case they've never seen**. Graded against the rubric. Then compare the three tracks side by side | Transferability: three unrelated domains, one architecture |
| 4.6 | 15m | Closing debrief: the AI SDLC operating model; where review shifts (to specs and evals); the human's role — intent, taste, boundaries, eval authorship, approval, accountability; maturity roadmap; what to do Monday | |

**Artifacts:** `spec/`, proposal pipeline, approval hook + `/approve`, full eval suite,
`RUNBOOK.md`. Plugin **v1.0**.

---

## Cross-cutting: misconceptions the tutor actively corrects

Shipped in `concepts/misconceptions.md` so the tutor catches them whenever they surface:

- "More context is better." → Context is a budget; relevance beats volume.
- "Embeddings understand meaning." → They encode distributional similarity. Similar ≠ relevant ≠ correct.
- "Evals are probabilistic." → **The model is probabilistic. Evals are the measurement system** that accounts for that variance.
- "A knowledge graph replaces RAG." → They answer different question shapes; the win is hybrid.
- "A skill is just a prompt." → A skill is a triggerable, progressively-disclosed procedure with bundled assets.
- "MCP is required to give an agent tools." → A CLI script is a tool. MCP is for a durable, typed, shareable surface.
- "Top-k = the answer set." → Similarity search cannot express completeness; that's an aggregation query.
- "The agent should just be autonomous." → Autonomy is a ladder, and the gate is what makes L3 shippable.

## Cross-cutting: facilitator kit

`facilitator/` — minute-by-minute run-of-show for all four sessions with cut lines;
pre-flight setup instructions to send 48h early; troubleshooting by symptom; talking points
per concept; the capstone rubric; and the offline bundle (vendored wheels, pre-cached
embedding model, prebuilt Chroma index and `kg.db` per track).
