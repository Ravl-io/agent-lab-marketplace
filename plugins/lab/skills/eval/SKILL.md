---
name: eval
description: Score your retrieval against the golden set and add a row to the scoreboard.
argument-hint: "[label for what changed]"
disable-model-invocation: true
allowed-tools: Bash, Read
---

Score the participant's retrieval and record it.

## Run it

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/eval_retrieval.py" --retriever rag/retrieve.py --label "$ARGUMENTS"
```

If `$ARGUMENTS` is empty, **ask what changed** before running — a scoreboard of rows labelled
"unlabelled" is worthless a week later. One phrase is enough: "naive chunking", "added
metadata filter", "parent-child".

If `rag/retrieve.py` does not exist yet, run the baseline instead and say why:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/eval_retrieval.py" --retriever rag/baseline_retrieve.py --label "lexical baseline"
```

## Read the result with them

Two numbers matter and they pull against each other:

- **answered** — the retrieved text contained the phrase that answers the query. This is the
  headline.
- **tokens per answer** — what each answer cost. The harness prints this next to the
  per-query figure, and it is the one to read out: "2,300 tokens per answer, down to 700".

A run that answers more for fewer tokens is better. A run that answers more by returning
more text has not necessarily improved anything, and the per-answer figure will show that.

Point at the specific misses rather than the average. The harness names them, and whether a
miss was "right file, wrong passage" or "wrong file entirely" tells them which thing to fix:
the first is chunking, the second is the embedding or the query.

## Do not re-run to get a better number

If they ask to re-run without changing anything, say no and explain why: the retrieval is
deterministic, so the number will not move, and a scoreboard with duplicate rows stops
showing the arc. Change something, then measure.

## The three unreachable queries

Reported separately and expected to fail. If one passes, check whether the retrieved passage
could genuinely answer it — retrieving a related document is not the same thing. If it truly
can, the query is mis-tiered and should move to `hard`; say so rather than quietly counting
it.

## Then show the arc

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" show
```

The scoreboard is the module. One row per change, in order, so the effect of each decision is
visible instead of remembered.
