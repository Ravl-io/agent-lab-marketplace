# Module 2 — what the numbers actually do

**Facilitator reference.** Measured while building the module, on all three tracks, with the
shipped golden sets. Quote your own track's row, and expect a participant's numbers to differ
from it — theirs is their chunker, not this one.

Measured with `k=5` and Chroma's default local embedding model (all-MiniLM-L6-v2, ONNX).

## The matrix

| Track | Strategy | Answered | Tokens/query | Tokens per answer | MRR |
|---|---|---|---|---|---|
| `support-triage` | lexical baseline | **11/12** | 2,111 | 2,303 | 0.83 |
| | naive | 6/12 | 665 | 1,331 | 0.74 |
| | **structural** | 10/12 | **585** | **702** | 0.66 |
| | parent_child | 8/12 | 668 | 1,001 | 0.60 |
| `vendor-qa` | lexical baseline | **12/12** | 2,013 | 2,013 | 0.79 |
| | naive | 8/12 | 685 | 1,028 | 0.65 |
| | structural | 7/12 | 638 | 1,094 | 0.56 |
| | **parent_child** | 10/12 | 734 | **881** | 0.55 |
| `docgen` | lexical baseline | 8/12 | 1,606 | 2,409 | 0.47 |
| | naive | 8/12 | 596 | 894 | 0.40 |
| | **structural** | 8/12 | **453** | **679** | 0.71 |
| | parent_child | **9/12** | 585 | 780 | 0.60 |

**Tokens per answer** is the cost figure the scoreboard prints, and the one to say out loud:
"the baseline costs 2,300 tokens for every question it answers, structural chunking costs
700." The JSON also carries *answers per 1k tokens*, the same ratio inverted, but it
compresses this whole table into the range 0.4–1.5 and is not what you read off the screen.

Every row here was re-measured with the shipped scaffolds and reference solutions, so a
participant who gets the implementation right lands on these numbers. Expect the **chunked**
rows to drift one or two percent between ingests — Chroma's ordering is not perfectly stable
on ties — while the answered counts hold. The baseline row is deterministic and pinned by
`selftest.py`; the chunked rows deliberately are not.

## Three things this says, and none of them is the thing I expected

### 1. Chunking does not make retrieval more accurate. It makes it affordable.

On answered count alone, the sixty-line lexical baseline **beats every chunked strategy** on
`support-triage` (11 against 10) and `vendor-qa` (12 against 10). Only `docgen` sees chunking
win outright, and by one query.

What chunking buys is the token bill: **roughly a third of the context** for roughly the same
answers. On eighteen documents that is a curiosity. On eighteen thousand it is the difference
between a system that works and one you cannot afford to run.

**Do not tell the room that chunking improves retrieval.** Tell them it changes the price, and
show them the two columns.

### 2. There is no best chunker, and that is the actual lesson.

`structural` wins on `support-triage`. `parent_child` wins on `vendor-qa` and `docgen`.
`naive` loses almost everywhere, which is the one part of the received wisdom that holds up.

The reason differs by corpus: `support-triage` is prose under clear headings, so a heading
path is a strong signal. `vendor-qa` is table-heavy, so whole sections embed poorly and the
small-child-big-parent split does better. Nobody could have predicted that from first
principles — which is why the module hands them a scoreboard rather than a recommendation.

### 3. MRR mostly gets worse, and that is fine.

Chunking splits one strong document match into several weaker chunk matches, so the first
useful result often ranks lower. It does not matter much when the agent reads all five. Say
so if someone spots it, and use it to make the point that a metric can move the wrong way
without the system getting worse — which is why you watch more than one.

## Step 4 measured: what the filter actually buys

The claim in step 4 is not "similarity search struggles with versions". It is worse than
that, and it is measured:

| Track | Query | Unfiltered top hit | Filter |
|---|---|---|---|
| `support-triage` | is a Growth account entitled to bulk export | the **superseded** matrix, rank 1 (0.653 vs 0.703) | `superseded=false` removes it entirely |
| `docgen` | what is the current scope of the Atlas programme | the **superseded** charter, rank 1 | `superseded=false` removes it entirely |
| `vendor-qa` | what is the Severity 2 resolution time | `MSA-excerpt.md`, which contains **both** the 2-day and the 3-day term | no filter helps — nothing is superseded |

### The scored row, and where it exists

`support-triage` carries a sixteenth golden query in a tier of its own, `filtered`, reported
separately so it never moves the headline the chunkers are judged on. It goes **0/1 → 1/1**
across the metadata step, and the 0 comes with a named cause: *returned
plan-entitlements-2026-01.md, which is superseded*.

It scores on a condition no other query uses. The anchor from the current matrix is retrieved
either way, so anchor alone would score the unfiltered run as a success while the retired
matrix ranked above it. The query forbids the retired file instead — retrieving both versions
is contradictory evidence, not partial credit.

`docgen` and `vendor-qa` have no such row and should not be told to look for one: `docgen`
keeps both charter versions in a single file, so no file can be forbidden, and `vendor-qa` has
nothing superseded at all.

### The trap this step is really about

A `validity()` that marks a document superseded whenever the word appears near the top flags
**the current Atlas charter**, because it says "Superseded: version 1" — naming the version it
replaced. Filtering to `superseded=false` then removed the only file holding the current
scope: the filter did not return a stale answer, it made the question unanswerable. Measured,
before the fix, `atlas-charter.md` was unreachable under the filter.

The reference now (a) counts only self-declarations and (b) computes the flag **per section**,
so the Version 1 section is flagged and Version 2 is not. Two transferable rules: a mention is
not a declaration, and metadata granularity has to match document granularity.

Two different failures, and the second is the more valuable one to teach. On `vendor-qa` a
filter cannot save you, because the corpus does not have a superseded document: the old
wording lives inside the current one, and what decides which term applies (the submission
date) is in a third file. That is a temporal question wearing a retrieval costume, and it is
the cleanest hand-off into Module 3 in the whole course.

Say the counter-intuitive part out loud: **similarity has no idea which version is current.**
The room's instinct is that it would prefer the newer document. It ranks the retired one
first.

## Not measured: whether agentic retrieval is worth it

Everything else in this document came off a harness. Step 6 did not, and the module says so
rather than implying otherwise.

Judging decompose-retrieve-assess-retrieve against single-shot needs a real agent loop, not
a scoring script, and that has not been run on these corpora. The module asks the room to
compare the two answers on three specific things — coverage of every part, citations that
hold, and whether it declares what it could not find — and to treat their own comparison as
the evidence.

**If a session produces a result here, record it in this file.** A cohort finding the agentic
version no better on their track is a real finding and the most likely thing this course is
currently wrong about.

## The step order, and why the baseline goes first

This is the authoritative ordering for Module 2. It changed late, on the strength of the
table above: the lexical baseline started as a footnote and ended up as the opening move,
because it is the only thing that makes *why build a vector store at all?* a real question
instead of a rhetorical one.

| # | Time | What happens | What it is for |
|---|---|---|---|
| 2.0 | 6m | Create the venv, install `chromadb` into it | The setup step arrives when the module needs it, not before |
| 2.1 | 14m | `/lab:next` installs `rag/baseline_retrieve.py` and `evals/retrieval/golden.jsonl`. Read the golden set, add three of your own, run `/lab:eval` | The floor, and the scoreboard that every later change is judged against |
| 2.2 | 12m | Ingest with naive fixed-window chunking. Re-run | Embeddings; and the first honest delta |
| 2.3 | 18m | Structural, then parent-child. Re-run each. **C1** | Chunking as a cost decision |
| 2.4 | 15m | Metadata schema, re-ingest, filtered retrieval | Filters as first-class retrieval |
| 2.5 | 15m | Retrieval as an MCP tool. **C2** | Tool surface design |
| 2.6 | 20m | The agentic RAG skill, against single-shot. **C3** | Retrieve-critique-retrieve |
| 2.7 | 10m | Debrief, then three questions that stay broken | Module 3's cold open |

### Running 2.1

Four beats, and the third one is the whole module:

1. **Run the baseline before anything is installed.** Sixty lines, no dependencies, no vector
   store, no embedding model. On `support-triage` it answers 11 of 12.
2. **Ask the room: so why would you build anything else?** Let it sit. Someone will say
   "it won't scale", which is correct and is not yet an argument — they have no number for it.
3. **Show the token column.** 2,111 tokens a query, because the thing returns whole
   documents. That is the answer to their own question, and now they have the number.
4. **Say what you are about to do to it.** The rest of the module does not chase the
   baseline's accuracy. It tries to keep that accuracy at a third of the price.

Do not skip beat 1 to save time. A participant who never sees the floor spends the module
tuning a chunker with no idea whether it is winning, and the scoreboard becomes homework
rather than evidence.

### If someone asks whether they should just ship the baseline

Sometimes yes, and say so — on a few hundred documents that fit in a context window, lexical
search over whole files is a defensible system and cheaper to run than the alternative. What
breaks it is scale (the token bill grows with document size, not with relevance), and
questions whose wording shares no words with the answer, which is where embeddings earn
their place. `docgen` is the track where the baseline is weakest (8/12) and it is worth
pointing at when this comes up.

If a participant's numbers contradict this table, theirs is the real result. This one was
measured with the reference chunkers on the shipped corpus, and a different chunk size or a
different heading rule moves it.
