# Step 3 — What the docs promise (5 minutes)

**What this step teaches:** quote the documentation, do not paraphrase it. The exact sentence
is what you will put in front of the customer and the developers.

## Frame — under 4 lines

Before looking at logs, find out what the product *promises*. The docs say how long an export
is allowed to take depending on its size. We want the exact sentence, and the size of this
report.

## Ask

> **Find the documentation page about report export and quote, word for word, what it says
> about `export_timeout` for reports over 1 million rows. Also tell me how many rows report
> R-2291 has.**

## Judge — when they say "next"

- The page is `docs/reports/export.md`. The sizing table says: **over 1M rows — at least
  120 s**; the default is **30 s**. A quote, with the path, not a summary.
- R-2291 has **2,104,311 rows** (from the `reports` table, or the report's Details tab per
  the docs).

So the report is well over one million rows, and the docs say such an export needs at least
120 seconds. Keep that in your pocket — do not let them (or Claude Code) call it the cause yet.
Say exactly that: *"That looks like the answer. It is not yet. We have not checked what
changed."*

## If it went wrong

- Paraphrased instead of quoted: have them ask "quote the sentence exactly, with the file
  path".
- Could not find the row count: have them ask "query the reports table for R-2291".

## Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" clear S3
```
