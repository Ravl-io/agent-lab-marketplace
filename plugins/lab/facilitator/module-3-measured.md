# Module 3 — what the numbers actually do

**Facilitator reference.** Measured while building the module, on the shipped corpora with
the reference ontology and verified graph. Quote your own track's row.

## The headline: 8/8, and why that is not the interesting part

The verified graph answers all eight graph questions exactly — precision 1.0, recall 1.0,
complete sets with no extras, across all three question shapes.

| Shape | Queries | Exact |
|---|---|---|
| multi-hop | 3 | 3 |
| aggregation | 3 | 3 |
| temporal | 2 | 2 |

That number is necessary but it is not the lesson. A graph built to answer eight questions
answering those eight questions is close to tautological. The lesson is what the *retrieval*
harness says about the same questions.

## The finding: the anchor metric lies about these questions

Module 2 scores retrieval by asking whether the answering phrase appears in the retrieved
text. Run the three Module 2 "unreachable" queries — the ones this module opens on — and the
harness reports them as **answered**:

| Retriever | Unreachable queries reported "answered" |
|---|---|
| lexical baseline | **2 of 3** (G13, G15) |
| structural chunking | 1 of 3 (G15) |
| parent_child | 1 of 3 (G15) |
| naive chunking | 0 of 3 |

None of those is a real answer. G13 asks which accounts are exposed to KI-77; its anchor,
*"accounts in region `eu-west` only"*, sits in `known-issues.md`, so any retriever that
returns that file scores a hit — while the actual answer needs the account list and their
platform versions, which appear in no document at all. G15 is the same trick with the
entitlement matrix: the phrase is retrieved, the account's plan and the date arithmetic are
not.

**This is the cold open, and it is stronger than "retrieval fails".** Retrieval does not fail
loudly here. It fails while a metric says it succeeded. Say that out loud, because it is the
most transferable idea in the module: a metric is only valid for the question shapes it was
designed for, and reusing it outside them produces confident nonsense.

It is also the argument for scoring this module differently. "Which accounts", "how many",
"as of when" have answers you can be *incomplete* about, and incompleteness is invisible to
a phrase check. `eval_graph.py` compares sets and reports precision and recall separately, so
returning four of six slipped milestones reads as recall 0.67 rather than as a hit.

## Why a graph rather than SQL — the honest answer

Worth having ready, because on `support-triage` somebody will ask it within five minutes, and
they are right to.

Most of what CQ1 needs is already relational data in `support.db`. What is *not* in the
database is KI-77's scope: **"affects accounts in region `eu-west` only"** exists in one line
of prose in `known-issues.md` and nowhere else. The fix version is in `vendor_cases`; the
region scope is in a markdown file; the accounts and their versions are in SQL. No single
source answers the question, and the graph is the layer where a fact extracted from prose
sits beside a row from a database and gets traversed with it.

So the claim to make is **not** "graphs are better than SQL". It is: *the graph is where your
documents and your database become one queryable thing, with provenance on every fact.* If a
participant's real corpus is entirely in one database, tell them plainly that they may not
need this module's machinery — and that knowing so is worth the two hours.

The other two tracks land differently and it is worth knowing which room you are in:

| Track | Corpus | What the graph is doing |
|---|---|---|
| `support-triage` | 12 documents **plus a database** | joining prose facts to database rows |
| `vendor-qa` | 15 documents, no database | structuring facts scattered across contracts, registers and findings |
| `docgen` | 21 documents, no database | the same, across charters, minutes and status updates |

## The validator earns its place

Four realistic extraction errors, injected into the verified graph, all caught by
`kg/compile.py` before anything was queryable:

| Injected | Reported as |
|---|---|
| edge pointed the wrong way round | names the declared direction and the actual one |
| dangling edge to a node that does not exist | dangling edge |
| a type the ontology does not declare | unknown type |
| two nodes with the same id | duplicate identity — entity resolution |

Use that list when someone asks why the ontology is worth writing before the extraction. A
graph hides a bad fact far better than a document does: nothing looks wrong about a tidy row.
