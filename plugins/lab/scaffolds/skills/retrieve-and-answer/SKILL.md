---
name: retrieve-and-answer
description: TODO — this is the only part of the skill the model sees before deciding whether to use it. Say what it answers and WHEN to reach for it, in the words a colleague would use.
---

# Answer a question from the corpus, with citations

One retrieval, one answer is the version everybody builds first. It fails in a specific and
predictable way: when the question has more than one part, the top five passages cover the
loudest part and silently miss the rest. The answer reads well and is incomplete, which is
worse than an answer that is obviously wrong.

This skill does something different. It decides what it needs, goes and gets it, **checks
whether what came back is actually enough**, and goes again if it is not.

## What you have

| | |
|---|---|
| `search_corpus` | similarity search over the whole corpus |
| `search_corpus_filtered` | the same, restricted by `doc_type`, `period`, or `superseded` |
| `get_document` | one whole document, once you know its path |
| `{{OUTPUT_DIR}}/` | where your answers go |

These are MCP tools. Call them; do not read `rag/` or shell out to python.

## Procedure

### 1. Decompose before retrieving

TODO — write this step.

Break the question into the separate things you would have to look up. "Has this been seen
before, and is the fix already released?" is two lookups, not one. Write them down before
you retrieve anything, because the list is what you will check your evidence against later.

State the sub-questions in your answer. A reader needs to see what you thought you needed.

### 2. Retrieve for each part

TODO — write this step.

One search per sub-question, not one search for the whole thing. Say which tool you used and
why. When the question carries a qualifier — *current*, *latest*, *this month*, *still open*
— that is `search_corpus_filtered`, and `superseded=false` is what "current" means.

### 3. Assess sufficiency — the step that makes this agentic

TODO — write this step. **This is the one that matters. Do not make it a formality.**

For each sub-question, say plainly: is the answer in what came back, or is it not?

The test is not "did I get plausible passages". It is "can I point at the sentence that
answers this". If you cannot, you have not retrieved it, however relevant the passages look.

When something is missing, say what you will change and try again: different words, a
different filter, or `get_document` on a file a passage pointed at. Give yourself a budget —
**two extra rounds, then stop** — because an agent that retrieves forever is not thorough,
it is stuck.

### 4. Answer, with citations

TODO — write this step.

Every claim names the file it came from. A claim you cannot cite does not go in the answer.

### 5. Say what you could not find

TODO — write this step.

If a sub-question is still unanswered after your extra rounds, **say so**, and say what you
looked for. This is the most valuable line in the whole output and the one most likely to be
dropped: a gap you declare is a gap someone can fix, and a gap you paper over becomes a
wrong decision downstream.

## Constraints

- Never answer from your own knowledge. If it is not in a retrieved passage, it is not known.
- Never cite a document you did not retrieve in this run.
- A superseded document is evidence about the past, never about what is true now. If you
  quote one, say that is what you are doing.
- Stop after two extra retrieval rounds and report what is missing.

## How you will be judged

The scoreboard, against single-shot retrieval on the same golden questions — including the
multi-part ones that single-shot half-answers. Cheaper is not better here; more of the
question answered, with citations that hold up, is better.
