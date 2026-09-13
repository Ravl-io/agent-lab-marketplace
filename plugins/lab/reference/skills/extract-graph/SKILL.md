---
name: extract-graph
description: Extract the knowledge graph from the corpus — every instance of every type and relation the ontology declares — into graph/nodes.jsonl and graph/edges.jsonl with provenance and validity dates. Use when building or re-building the graph, after the ontology changes, or when the corpus has been updated.
---

# Extract the graph from the corpus

Read the corpus, and write out every instance of every type and relation the ontology
declares — as `graph/nodes.jsonl` and `graph/edges.jsonl`.

**Read `ontology/*.yaml` first, and treat it as the contract.** It is not a suggestion: a
type or relation that is not in it does not go in the graph. If you find a fact that has
nowhere to go, that is a finding about the ontology — say so rather than inventing a
relation, because a relation nobody declared is one nobody can query.

## The two files you write

`graph/nodes.jsonl` — one JSON object per line:

```json
{"id": "acc-1042", "type": "Account", "label": "Brightmoor Health",
 "props": {"region": "eu-west"}, "source": "data/db/support.db :: accounts"}
```

`graph/edges.jsonl` — one JSON object per line:

```json
{"src": "KI-77", "rel": "scoped_to_region", "dst": "region:eu-west",
 "valid_from": null, "valid_to": null, "source": "data/knowledge/known-issues.md"}
```

Then compile, which validates against the ontology before it writes anything:

```
python3 kg/compile.py
```

## Procedure

### 1. Identity first

Before extracting anything, decide what makes two mentions the same thing, for each type.
Write the rule down. "Brightmoor Health" and "Brightmoor Health Ltd" are one account or two,
and you have to choose — the compiler will catch two nodes with one id, but it cannot catch
one node that should have been two.

Where the corpus refers to something ambiguously, resolve it by an explicit rule and record
the rule. Guessing per-occurrence produces a graph nobody can reason about.

### 2. Extract nodes, with provenance

Work one type at a time, and finish it before starting the next. Every node carries `source`: the file, and the table or section inside it. Not optional. An
answer that cannot be traced to a document is not usable by the people who will act on it,
and provenance is the only thing that makes a graph auditable.

### 3. Extract edges, and get the direction right

Work one relation at a time, from the ontology's list, so that a relation with no instances
is something you noticed rather than something you missed. Read each edge aloud as a sentence before you write it — "Account on_plan Plan". A backwards
edge does not error; it answers questions incorrectly, and it looks completely normal.

### 4. Dates on anything that changes

For every relation the ontology marks `temporal: true`, carry `valid_from` and `valid_to`.

**Never overwrite a fact that stopped being true.** Write a new edge and close the old one by
setting its `valid_to`. A superseded fact is the only way to answer what was true then, and
"what was true at the time" is most of what anybody asks about a past decision.

### 5. Report what you could not place

List: facts you found with no type or relation to hold them; references you could not
resolve to an identity; and anything the ontology declares that the corpus does not contain.
That last one matters — a relation with no instances is either a missed extraction or an
ontology that is describing something imaginary.

## Constraints

- Never invent a type or relation that the ontology does not declare.
- Never write a node without a `source`.
- Never merge two things that have different identities to make a traversal work.
- Do not extract what no competency question needs. A bigger graph is not a better one.

## How you will be judged

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_graph.py"
```

It compiles your graph against your ontology, scores it against the questions in
`evals/graph/queries.jsonl`, and diffs it against a verified graph. A difference from the
verified graph is not automatically wrong — if yours answers every question, you modelled it
differently, and that is worth discussing rather than fixing.
