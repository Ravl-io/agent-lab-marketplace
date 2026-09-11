# Agent Lab — Curriculum

Four sessions, two hours each. Your plugin grows in every one of them: **v0.1 → v1.0**.

---

## Module 1 — Harness and coding agent

**The question:** what *is* an agent, what is the harness made of, and which primitive should
I reach for?

You will climb a ladder. Each rung exists because the one below it broke:

| Rung | What it fixes | What is still wrong |
|---|---|---|
| **Prompt** | gets you a result, once | not repeatable, not shareable |
| **User-invoked skill** (a "command") | a repeatable, versioned prompt | can't act, can't guarantee anything |
| **Tool** | deterministic action, structured output | the agent doesn't know when to use it |
| **Model-invoked skill** | the agent decides when to apply it, from the description | the agent can still skip it |
| **Hook** | enforcement the model cannot bypass | not distributable on its own |
| **Plugin** | packages all of it, installable, versioned | — |

Rungs 2 and 4 are **the same file format**, one frontmatter line apart. You will write one,
then turn it into the other, and the difference — *who decides to invoke it* — is the most
useful thing to understand about skills.

**You build:** your plugin v0.1 — one command, one tool, one skill, two hooks, a `CLAUDE.md`
and an `intent.md`. Installed, and running on your track's data.

**The wall you hit first:** you do your track's task with a plain prompt, twice, and get two
different answers. Everything after that is a response to that problem.

---

## Module 2 — RAG and retrieval systems

**The question:** the agent knows nothing about our documents. How do we ground it — and how
do we *know* we made it better rather than just different?

Covered: why retrieval at all; embeddings and what they do and don't understand; chunking
strategies (fixed, recursive, structural, semantic, parent-child); metadata strategies
(provenance, section paths, document type, validity dates, entities) and filters as
first-class retrieval; hybrid search and reranking; then **agentic RAG** — query
decomposition, retrieve-critique-retrieve, self-grading, and knowing when to stop. Then
**retrieval evals**: golden sets, recall@k, MRR, and why retrieval quality and answer quality
are two different measurements.

**The device that runs through this module:** one scoreboard. The same 15 golden queries get
re-scored after every change you make — naive chunking, then structural, then metadata
filters, then agentic. You watch the number move. Evals stop being an abstraction.

**You build:** ChromaDB ingestion with real chunking, a metadata schema, retrieval exposed as
an MCP tool, and an agentic RAG skill that cites its sources. Plugin **v0.2**.

**How it ends:** with three questions your retrieval still gets wrong. We leave them broken
on purpose.

---

## Module 3 — Knowledge graphs and ontologies

**The question:** why did those three questions fail, and what do we build instead?

Vector search fails structurally, not accidentally, on three kinds of question:

1. **Multi-hop / relational** — "which other customers are exposed to the defect behind this ticket?"
2. **Aggregation and completeness** — "how many", "which *all*", "what is *not* covered?"
   Similarity search returns the most similar k. It cannot return a complete set.
3. **Constraint and temporal reasoning** — "does this violate the policy that was in force
   at the time?"

Covered: taxonomy vs ontology vs knowledge graph vs semantic layer; designing an ontology
from **competency questions** — the questions you must be able to answer — rather than from
your data; entities, relations, identity and entity resolution; provenance; temporality with
validity dates and supersession, so answers never go quietly stale; and the GraphRAG patterns
that combine graph and vector instead of choosing between them.

**You build:** an ontology derived from the three broken questions, a graph extracted from
your corpus with provenance and dates, compiled into SQLite, exposed as an MCP tool, and a
hybrid skill that routes each question to the graph, the vector store, or both. Plugin
**v0.3** — tool + vector store + ontology graph, working together.

**The moment to watch for:** answering, by hand, the three questions we left broken.

---

## Module 4 — The full AI system

**The question:** you have a system that works on your machine. What stands between that and
something your team would actually rely on — and what is the human's job in running it?

This module is about **validating and improving what you have built** until it is
production-ready and delivers real value. Everything in the first three modules was
construction; this one is measurement, hardening and the operating model around it.

Covered: what "production-ready" means for a system like this — evals as the new tests,
observability, audit trails, cost and latency, and the failure modes you have to design
against; spec-driven development (intent → spec → acceptance criteria → plan → implement →
eval → approve) and why a spec outperforms a prompt: durable, reviewable, reusable, testable;
and the **autonomy ladder**, which is how you decide how much the system is allowed to do on
its own:

| Level | The agent | The human |
|---|---|---|
| L0 | suggests | does everything |
| L1 | drafts a proposal | reads, decides, applies |
| L2 | applies in a sandbox, runs the evals | reviews, promotes |
| L3 | **applies behind an approval gate** | approves each change — *this is where we land* |
| L4 | applies autonomously, with rollback | sets policy, audits, owns the outcome |

**You build:** a spec for your system's final capability; a proposal pipeline that produces
evidence, risk and a rollback plan while applying nothing; a real approval gate — a hook that
refuses to apply without human approval; and the full eval suite that tells you whether the
whole thing actually works. Plugin **v1.0**.

**How it ends:** each group demos on a case it has never seen, and we compare three unrelated
domains that arrived at the same architecture.
