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
| 2.0 | 6m | Create a virtualenv and install `chromadb` into it — the setup step arrives when the module needs it. **M2.C0-setup** | Dependency isolation; why the lab does not install everything up front |
| 2.1 | 14m | **The floor first.** Run `rag/baseline_retrieve.py` — sixty lines, no dependencies, no vector store. It answers 11 of 12. Read `evals/retrieval/golden.jsonl`, add 3 queries of your own, then look at the token column | Golden sets; answered vs retrieved; context cost as a first-class metric. *Why retrieval at all* becomes a real question because the cheap thing already works. **M2.C1-baseline** |
| 2.2 | 12m | Ingest the corpus into **ChromaDB** with naive fixed-window chunking. Re-run the scoreboard. Cost collapses — and so do the answers | Embeddings intuition and their limits; the first honest delta |
| 2.3 | 18m | **Chunking lab**: implement structural (heading-aware) and parent-child (small-to-big). Re-run after each. Record the deltas | Fixed vs recursive vs structural vs semantic vs contextual chunking; chunk/retrieve asymmetry; chunking as a cost decision, not an accuracy one |
| — | — | **M2.C2-chunking** — all three strategies measured, deltas on the scoreboard | |
| 2.4 | 15m | **Metadata lab**: define a metadata schema (source, section path, doc type, validity dates, entities, version), re-ingest, add filtered retrieval. On `support-triage` one golden query (tier `filtered`, scored separately) is *only* solvable with a filter and goes 0/1 → 1/1; the other two tracks demonstrate it by hand, because their corpora hold both versions in one file or nothing superseded at all. **M2.C3-metadata** | Authored vs derived metadata; filters as first-class retrieval; provenance; temporal validity |
| 2.5 | 15m | Wrap retrieval as an **MCP tool**: `search`, `search_filtered`, `get_document` | Tool surface design: expose intent-level operations, never the raw vector DB |
| — | — | **M2.C4-tool** — retrieval tool callable by the agent over MCP | |
| 2.6 | 20m | Build the **agentic RAG skill**: decompose → retrieve → assess sufficiency → re-retrieve → answer with citations. Compare against single-shot on the golden set | Agentic RAG: query decomposition, multi-query, retrieve-critique-retrieve, self-grading, stop conditions. Hybrid search + reranking (concept + optional exercise) |
| — | — | **M2.C5-agentic** — agentic retrieval answers more of a multi-part question | |
| 2.7 | 10m | Debrief on the scoreboard — then run **3 questions that are still broken** ("which vendors are affected by X", "how many incidents traced to Y", "what changed since the last version"). Leave them broken. That's Module 3's cold open | Retrieval's ceiling: relational, aggregate and temporal questions |

**The measured result this module is built on:** chunking does not make retrieval more
accurate — the dependency-free baseline beats every chunked strategy on two of three tracks.
It makes retrieval *affordable*, at roughly a third of the tokens. See
`lab/facilitator/module-2-measured.md`.

**Artifacts:** `rag/` (chunkers, ingest, retrieve, and the dependency-free baseline),
`evals/retrieval/golden.jsonl`, `mcp/retrieval_server.py` + `.mcp.json`,
`.claude/skills/retrieve-and-answer/`. Plugin **v0.2**.

**Stages:** `m2s1-baseline` · `m2s2-vectors` · `m2s3-mcp` · `m2s4-agentic`.
**Gates:** `check_golden.py`, `check_ingest.py`, `check_retrieval_tool.py`,
`check_skill.py --name retrieve-and-answer`.

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
| — | — | **M3.C1-ontology** and **M3.C2-graph** — ontology gated, graph compiled and scored | |
| 3.3 | 12m | Query it by hand (SQL/CLI) and answer the 3 broken questions | Traversal, paths, impact, coverage/gaps |
| 3.4 | 18m | Wrap it as an **MCP tool**: `kg_search`, `kg_entity`, `kg_neighbors`, `kg_path`, `kg_impact`, `kg_coverage`, `kg_as_of` | Intent-level graph operations; why not "here's a SQL tool, good luck" |
| — | — | **M3.C3-tool** — graph tool callable by the agent over MCP | |
| 3.5 | 20m | Build the **hybrid answering skill**: route by question shape — graph for structure and scope, vector for evidence and quotes, both for most real questions. Answers carry citations + an as-of date. Run the combined eval (15 original + 8 graph-only) | GraphRAG patterns: graph-as-router, retrieval expansion, graph-as-answerer, vector-entry → graph-traverse → vector-evidence |
| — | — | **M3.C4-hybrid** — the hybrid skill routes by question shape | |
| 3.6 | 10m | Ontology governance: who owns it, how it evolves, drift, `kg_coverage` / open questions as a gap report | The semantic layer as the shared contract between humans and agents |
| 3.7 | 10m | Debrief: **when not to build a graph** — build/maintenance cost vs question shape | |

**Artifacts:** `ontology/*.yaml`, `graph/nodes.jsonl` + `edges.jsonl`, `kg.db`,
`kg/compile.py` + `kg/kg.py` (given), `mcp/kg_server.py`,
`.claude/skills/{extract-graph,answer-with-graph}/`, `evals/graph/queries.jsonl`.
Plugin **v0.3** — the full plugin: tool + vector store + ontology graph.

**Stages:** `m3s1-ontology` · `m3s2-extract` · `m3s3-kg-tool` · `m3s4-hybrid`.
**Gates:** `check_ontology.py`, `check_graph.py`, `check_kg_tool.py`,
`check_skill.py --name answer-with-graph`.

**Measured:** the verified graph answers 8/8 graph questions on every track, precision and
recall 1.0. And the retrieval harness reports two of the three "unreachable" queries as
answered — a false positive that is the module's cold open. See
`lab/facilitator/module-3-measured.md`.

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
| — | — | **M4.C2-proposal** — a proposal on a real case, fully cited, nothing applied | |
| 4.3 | 20m | Build the **approval gate**: a `PreToolUse` hook that denies `apply` without an approval token + an `/approve` command a human runs. Then apply. (docgen → publish report; vendor-qa → sign off findings; incident → apply remediation) | The gate as the trust mechanism. Least-privilege tools, permissions, audit trail |
| — | — | **M4.C3-gate** — apply refused without approval, refused after an edit, refused twice | |
| 4.4 | 15m | Run the full suite `/lab:eval all`: retrieval + graph + task-level + policy compliance. Check the audit log | Evals as the new tests. Observability, cost, latency |
| 4.5 | 25m | **Capstone**: each group demos on a **held-out case they've never seen**. Graded against the rubric. Then compare the three tracks side by side | Transferability: three unrelated domains, one architecture |
| 4.6 | 15m | Closing debrief: the AI SDLC operating model; where review shifts (to specs and evals); the human's role — intent, taste, boundaries, eval authorship, approval, accountability; maturity roadmap; what to do Monday | |

**Artifacts:** `spec/capability.{md,json}`, `.claude/skills/propose/`,
`.claude/hooks/approval_gate.py`, `gate/approve.py` + `tools/apply.py` (given),
`proposals/`, `approvals/`, `audit.jsonl`, `RUNBOOK.md`. Plugin **v1.0**.

**Stages:** `m4s1-spec` · `m4s2-propose` · `m4s3-gate` · `m4s4-runbook`.
**Gates:** `check_spec.py`, `check_proposal.py`, `eval_all.py`, `check_plugin.py`.

**Measured:** nine gate behaviours verified, including that an approval covers one artifact
(edit it and apply is refused), is single-use, and is re-checked by the apply tool
independently of the hook. See `lab/facilitator/module-4-measured.md`; the capstone answer
keys are in `lab/facilitator/module-4-capstone.md`.

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
