# evals/retrieval/

`golden.jsonl` is fifteen questions with the answer each one needs. It is what every
measurement in this module is scored against.

Run a measurement:

```
/lab:eval naive chunking
```

or directly:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/eval_retrieval.py" \
    --retriever rag/baseline_retrieve.py --label "lexical baseline"
```

## What gets scored

**answered** — the retrieved text contained the query's `anchor`, the phrase that actually
answers it.

**tokens per query** — what you spent to get there.

Those two pull against each other, and the interesting number is the third one the harness
prints: **answers per 1k tokens**. A run that answers more by returning more text has not
necessarily improved anything.

Filenames are reported as a diagnostic and deliberately not scored. On a corpus this size
"did the right document come back" is close to free; "did the answer come back, cheaply" is
the whole problem.

## Add three of your own

Copy a line, give it an id starting `H`, and use a question your team actually asks. Check
the set afterwards:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_golden.py" \
    --file evals/retrieval/golden.jsonl --corpus .
```

`--corpus .` is the project root: the `expected` paths are project-relative, so pointing it
at `data/` reports perfectly good queries as broken.

The `anchor` has to be a phrase that really appears in the file you point at —
`check_golden.py` refuses a set where it does not, because such a query can never score and
would look like a retrieval failure forever.
