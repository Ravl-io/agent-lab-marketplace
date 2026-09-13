---
name: retrieve-and-answer
description: Answer a question from the project's own documents, with citations — decomposing it into parts, retrieving for each, checking whether the evidence is actually sufficient, and retrieving again when it is not. Use when asked anything about our policies, tickets, contracts, history or knowledge base, and whenever an answer needs to be backed by a source rather than recalled.
---

# Answer a question from the corpus, with citations

One retrieval, one answer fails in a specific way: when a question has more than one part,
the top passages cover the loudest part and silently miss the rest. The answer reads well
and is incomplete, which is more dangerous than an answer that is obviously wrong.

This skill decides what it needs, gets it, **checks whether what came back is enough**, and
goes again if it is not.

## What you have

| | |
|---|---|
| `search_corpus` | similarity search over the whole corpus |
| `search_corpus_filtered` | the same, restricted by `doc_type`, `period`, or `superseded` |
| `get_document` | one whole document, once you know its path |
| `{{OUTPUT_DIR}}/` | where your answers go |

These are MCP tools. Call them. Do not read `rag/` directly and do not shell out to python.

## Procedure

### 1. Decompose before retrieving

Break the question into the separate things you would have to look up, and write them down
before retrieving anything. "Has this been seen before, and is the fix released?" is two
lookups. "What is the current policy, and when did it change?" is two.

List the sub-questions in your answer. The reader needs to see what you thought you needed,
and the list is what you check your evidence against in step 3.

### 2. Retrieve for each part

One search per sub-question. State which tool you used and why.

When the question carries a qualifier, use `search_corpus_filtered`:

| The question says | The filter |
|---|---|
| current, latest, in force, now | `superseded=false` |
| a month or a quarter | `period` |
| "in the knowledge base", "in the tickets" | `doc_type` |

### 3. Assess sufficiency

For each sub-question, state plainly whether the answer is in what came back.

The test is not *did I get plausible passages*. It is **can I point at the sentence that
answers this**. If you cannot, you have not retrieved it, however relevant the passages look.

When something is missing, say what you will change, then do it:

- different words — the corpus may not use the questioner's vocabulary
- a filter, if the question had a qualifier you ignored
- `get_document` on a file a passage pointed at, when the passage is clearly part of a
  larger argument

**Budget: two extra rounds, then stop.** An agent that retrieves forever is not thorough,
it is stuck, and it spends the context window getting there.

### 4. Answer, with citations

Every claim names the file it came from. A claim you cannot cite does not go in the answer.

Structure:

1. the direct answer, first, in a sentence or two
2. the evidence, each point citing its source
3. the sub-questions and what you found for each

### 5. Say what you could not find

If a sub-question is still unanswered after the extra rounds, say so, and say what you looked
for. This is the most valuable line in the output. A gap you declare is a gap someone can
fix; a gap you paper over becomes a wrong decision downstream.

## Constraints

- Never answer from your own knowledge. If it is not in a retrieved passage, it is not known.
- Never cite a document you did not retrieve in this run.
- A superseded document is evidence about the past, never about what is true now. If you
  quote one, say that is what you are doing.
- Stop after two extra retrieval rounds and report what is missing.
- Do not write into `data/` — it is the evidence, and it is read-only.

## Output

Write to `{{OUTPUT_DIR}}/<a short slug of the question>.md`:

```markdown
# <the question>

**Answer.** <one or two sentences>

## Evidence
- <claim> — `data/path/to/file.md`

## What I looked for
| Sub-question | Answered | Source |
|---|---|---|
| <part one> | yes | `data/...` |
| <part two> | no — searched X, Y | — |
```
