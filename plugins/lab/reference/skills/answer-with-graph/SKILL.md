---
name: answer-with-graph
description: Answer a question using the knowledge graph for structure and retrieval for evidence — routing on the shape of the question. Use for anything asking which others, how many, what is missing, what was true at a date, or how two things are related; and alongside retrieval whenever an answer needs both a complete set and a quotation.
---

# Answer by routing on the shape of the question

Two ways to find things, good at opposite jobs:

| | Good at | Bad at |
|---|---|---|
| retrieval (`search_corpus`) | what a document *says* — wording, reasons, quotes, evidence | completeness, relationships, anything as-of a date |
| graph (`kg_*`) | structure, complete sets, several hops, what was true when | nuance, wording, why somebody decided something |

Most real questions need both. Knowing which part needs which is the whole job.

## Procedure

### 1. Classify before answering

Name the shape of each part of the question out loud, because the route follows from it:

| The question asks | Shape | Route |
|---|---|---|
| which *other*, what is affected, how are these related | relational | `kg_reach`, `kg_path` |
| how many, which *all*, what is missing, what is not covered | completeness | `kg_coverage`, `kg_reach` |
| as of a date, at the time, then versus now, what changed | temporal | `kg_as_of` |
| what does it say, why, on what grounds, quote it | evidence | `search_corpus` |

A question with two parts gets two routes. State the split before retrieving anything.

### 2. Structure first, from the graph

Call `kg_ontology` before composing a path, every time. Relation names and directions are
not guessable, and a mistyped relation returns an empty set that reads exactly like a
genuine answer of "none".

Then `kg_search` to turn names into ids, and `kg_reach` or `kg_coverage` for the set.

When a traversal returns a set, it is **complete** — say so explicitly. "All three" is a
stronger claim than "here are three", and only the graph entitles you to make it.

### 3. Evidence second, from retrieval

The graph knows *that* two things are related. It does not know the reason somebody wrote
down. Take the entities the graph gave you and `search_corpus` for the passage.

This order is not interchangeable: **graph for the set, retrieval for the sentence.**
Retrieving first and hoping the structure emerges is the failure this module measured.

### 4. Attach a date to anything that has one

If any part of the answer came from a temporal relation, state the date it holds as of. An
entitlement, a scope, a contract term or a deadline quoted with no date is not an answer.

Where then and now differ, give both, and say which one the question was about.

### 5. Cite, and declare the gaps

Every claim names its source: the document path for retrieved text, and for a graph fact
the `source` that `kg_entity` reports. A graph fact is not exempt — it came from a document
too, and the extraction recorded the provenance precisely so you could say where.

Then say what you could not answer: a relation the ontology does not model, an entity you
could not resolve, a date nobody recorded.

## Constraints

- Never answer a completeness question from retrieval. Top-k cannot report what it missed.
- Never answer a temporal question without a date.
- Never report an empty graph result as "none" without checking the path was valid.
- Never cite a graph fact without the source the extraction recorded.
- If the graph and a document disagree, say so and quote both. That is a finding — it
  usually means the extraction is stale or the document changed under it.

## Output

Write to `{{OUTPUT_DIR}}/<a short slug of the question>.md`:

```markdown
# <the question>

**Answer.** <direct, and complete where the graph entitles you to say so>
**As of.** <date, whenever any part came from a temporal relation>

## How I got here
| Part of the question | Shape | Route |
|---|---|---|
| <part> | relational | kg_reach: <start> -<rel>-> <rel backwards> |

## Evidence
- <claim> — `data/path/to/file.md`

## What I could not answer
- <gap, and why>
```
