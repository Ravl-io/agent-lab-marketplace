---
name: answer-with-graph
description: TODO — say what this answers and WHEN to use it. It has to win against your retrieval skill for structural questions and lose for evidence ones, so the description has to say which is which.
---

# Answer by routing on the shape of the question

You now have two ways to find things and they are good at opposite jobs:

| | Good at | Bad at |
|---|---|---|
| **Retrieval** (`search_corpus`) | what a document *says* — wording, reasons, quotes, evidence | completeness, relationships, anything as-of a date |
| **Graph** (`kg_*`) | structure, complete sets, several hops, what was true when | nuance, wording, why somebody decided something |

Most real questions need both. The skill is knowing which part of a question needs which,
and that is the whole of this step.

## Procedure

### 1. Classify the question before answering it

TODO — write this step.

Say out loud which shape each part of the question is, because the routing follows from it:

| If the question asks | Shape | Go to |
|---|---|---|
| which/what *other*, what is affected, how are these related | relational | `kg_reach`, `kg_path` |
| how many, which *all*, what is missing, what is not covered | completeness | `kg_coverage`, `kg_reach` |
| as of a date, at the time, then versus now, what changed | temporal | `kg_as_of` |
| what does it say, why, on what grounds, quote it | evidence | `search_corpus` |

A question with two parts gets two routes. Do not pick one and hope.

### 2. Get the structure from the graph first

TODO — write this step.

Start with `kg_search` to turn names into ids, and `kg_ontology` to see the real relation
names before composing a path. **Do not guess a relation name.** A mistyped path returns an
empty set, and an empty set reads exactly like a genuine answer of "none".

When a set comes back, it is complete — say so. "All three" is a different and more useful
claim than "here are three", and only the graph entitles you to make it.

### 3. Get the evidence from retrieval

TODO — write this step.

The graph tells you *that* Cirrus depends on Atlas. It does not tell you the reason anybody
wrote down. Use `search_corpus` on the entities the graph gave you, and quote the document.

This is the order that works: **graph for the set, retrieval for the sentence.** Going the
other way round — retrieving first and hoping the structure emerges — is what Module 2
measured failing.

### 4. Attach a date to anything that has one

TODO — write this step.

If any part of the answer came from a temporal relation, state the date it is true as of. An
entitlement, a scope, a contract term or a deadline quoted without a date is not an answer,
and it is the specific way these systems mislead people who trust them.

Where then and now differ, give both.

### 5. Cite, and say what is missing

TODO — write this step.

Every claim names its source: a document path for retrieved text, and for graph facts the
`source` that `kg_entity` reports. A graph fact is not exempt from citation — it came from a
document too, and the whole reason the extraction recorded provenance was so that you could
say where.

Then say what you could not answer and why: a relation the ontology does not have, an entity
you could not resolve, a date nobody recorded.

## Constraints

- Never answer a completeness question from retrieval. Top-k cannot tell you what it missed.
- Never answer a temporal question without a date.
- Never report an empty graph result as "none" without checking the path was valid.
- Never cite a graph fact without the source the extraction recorded.
- If the graph and a document disagree, say so and quote both. That is a finding, not a
  problem to smooth over — it usually means the extraction is stale or the document changed.

## Output

Write to `{{OUTPUT_DIR}}/<a short slug of the question>.md`:

```markdown
# <the question>

**Answer.** <direct, and complete where the graph entitles you to say so>
**As of.** <date, whenever any part came from a temporal relation>

## How I got here
| Part of the question | Shape | Route |
|---|---|---|
| <part> | relational | kg_reach: KI-77 -scoped_to_region-> <in_region |

## Evidence
- <claim> — `data/path/to/file.md`

## What I could not answer
- <gap, and why>
```
