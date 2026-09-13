# Module 2 — RAG and retrieval systems

**Two hours.** They end with plugin v0.2: a corpus they can search, a measurement they trust,
retrieval exposed as a tool the agent calls, and a skill that cites its sources.

## What this module is for

By the end they should be able to answer, out loud, to a colleague: *how do I ground an agent
in our documents, how do I know whether a change to retrieval helped, and what does chunking
actually buy me?*

The third one is where most of the value is, because the honest answer is not the one they
came in with.

## The arc

| Step | Time | What they do | Checkpoint |
|---|---|---|---|
| **0** | 6m | **Setup** — a virtualenv, and `chromadb` in it. Nothing else | `M2.C0-setup` |
| **1** | 14m | **The floor** — run a retriever with no dependencies. Read the golden set, add three queries. *Why build anything else?* | `M2.C1-baseline` |
| **2** | 12m | **Chunk, embed, search** — naive chunking into Chroma. Re-measure. Cost collapses, answers collapse too | |
| **3** | 18m | **The chunking lab** — structural, then parent-child. Re-measure each | `M2.C2-chunking` |
| **4** | 15m | **Metadata and filters** — the current policy, not the one it replaced | `M2.C3-metadata` |
| **5** | 15m | **Retrieval as a tool** — an MCP server the agent can call | `M2.C4-tool` |
| **6** | 20m | **Agentic retrieval** — decompose, retrieve, assess, retrieve again, cite | `M2.C5-agentic` |
| **7** | 10m | **Debrief** — then three questions that stay broken. Module 3's cold open | module complete |

**Authoring status:** all four modules are authored.

## The result this module rests on, and the claim not to make

Measured on all three tracks with the shipped corpora and the reference solutions:

**Chunking did not make retrieval more accurate.** The sixty-line lexical baseline answered
*more* golden queries than every chunked strategy on two of the three tracks. What chunking
bought was the bill — roughly a third of the tokens for roughly the same answers.

So do not tell the room that chunking improves retrieval. It is not what happens, they will
see that it is not what happens, and you will have spent your credibility in step 3 of a
four-module course. Tell them it changes the price, and show them both columns.

The full matrix is in `facilitator/module-2-measured.md`. Read it before you teach this.
**Quote your own track's row only** — the winning strategy is different on each one.

## Every track runs this module

Track-specific values come from `${CLAUDE_PLUGIN_ROOT}/tracks/<track>/track.json`:

| Field | Use it for |
|---|---|
| `output_dir` | where the agentic skill writes its answers |
| `key_files.policy` | the document whose superseded twin makes the metadata step land |
| `general_question` | a warm-up query if their own three are slow to arrive |

The corpus layout differs by track. Never read the lead track's file names to a group on a
different track — check `data/` in their workspace first.

---

## Step 0 — Setup (6 minutes)

This is plumbing. Do it, do not lecture it.

### 0.1 Why a virtualenv, in one sentence

Because `pip install chromadb` into a shared environment is how you break something else
that was working. That is not hypothetical — it happened while this module was being built:
installing chromadb into a conda environment pulled a `typer` version that broke a different
tool in the same environment. One sentence, then move.

### 0.2 Make it

From the project root:

```
python3 -m venv .venv
.venv/bin/python3 -m pip install --quiet --upgrade pip
.venv/bin/python3 -m pip install --quiet chromadb
```

`.venv` in the project root, that exact name. `.mcp.json` in step 5 refers to
`${CLAUDE_PROJECT_DIR}/.venv/bin/python3`, and the gate looks there too.

The install is 100–200 MB and takes a few minutes on a conference network. Start it, then
talk through 0.3 while it runs.

### 0.3 What they just installed, while it installs

Chroma is a vector database: it stores text next to an embedding of that text, and finds
rows by similarity instead of by keyword. The embedding model here is **all-MiniLM-L6-v2**,
runs locally through ONNX, about 90 MB, downloaded on first ingest.

Say the thing the room actually wants to know: **no API key, no network call, nothing leaves
the machine.** For most of them that is the difference between "interesting" and "allowed".

### 0.4 Verify and record

```
/lab:doctor
```

Module 2's requirements should now pass. Then:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M2.C0-setup
```

If chromadb still reports missing, the usual cause is that `doctor` resolved a different
interpreter than the venv. `/lab:doctor` names the interpreter it checked — read it out.

---

## Step 1 — The floor (14 minutes)

The most important step in the module. Do not shorten it to gain time elsewhere; take the
time out of step 3 instead.

### 1.1 Install it and run it

```
/lab:next
```

That applies stage `m2s1-baseline`: `rag/baseline_retrieve.py` and
`evals/retrieval/golden.jsonl`. Have them read the retriever first — it is about sixty lines
and there is nothing in it they cannot follow. Word counting, an IDF weight so common words
matter less, whole documents returned.

No embeddings. No vector store. No dependencies.

```
/lab:eval lexical baseline
```

### 1.2 Read the number out, then stop talking

| Track | What the baseline answers |
|---|---|
| `support-triage` | **11 of 12** |
| `vendor-qa` | **12 of 12** |
| `docgen` | **8 of 12** |

Then ask the room, and wait:

> **So why would you build anything else?**

Let the silence do the work. Someone will say "it won't scale". That is correct and it is not
yet an argument — they have no number for it. Push once: *how would you know?*

### 1.3 Now show the second column

The baseline costs **2,013 to 2,409 tokens for every question it answers**, because it
returns whole documents. That is the answer to their own question, and now it is a number
instead of an instinct.

Make the stakes concrete: eighteen documents is a curiosity, eighteen thousand is a bill you
cannot pay. Everything in the rest of the module is an attempt to keep this accuracy at a
third of this price.

### 1.4 The golden set

Open `evals/retrieval/golden.jsonl`. Fifteen questions; each carries an **anchor**, the
phrase that has to appear in the retrieved text for the question to count as answered.

| Tier | Count | What it is |
|---|---|---|
| `easy` | 7 | one document, plain wording |
| `hard` | 5 | wording that does not match the document's words, or two documents |
| `unreachable` | 3 | relational, aggregate or temporal. **Not scored.** Module 3 |

Two things to say about the metric, because both get challenged:

**Why the anchor, and not "did the right file come back?"** Because on a corpus this size the
right file comes back almost every time, from almost anything. An earlier version of this
harness scored filenames and gave the sixty-line baseline 12 out of 12 — a perfect score that
measured nothing. Retrieving the document is not answering the question.

**Why are three questions excluded?** Because no chunker reaches them. They are the ceiling
of retrieval itself, and pretending otherwise would teach them to tune a knob that cannot
move. They come back in Module 3.

### 1.5 They add three of their own

Real questions their team actually asks. Copy a line, id starting `H`, and the anchor must be
a phrase that genuinely appears in the file they point at.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_golden.py" --file evals/retrieval/golden.jsonl --corpus .
```

`--corpus .` is the project root, not `data/` — the `expected` paths in the golden set are
project-relative, and pointing this at `data/` makes three shipped queries look broken.

That refuses a set whose anchor does not appear in its document — otherwise the query can
never score, and it looks like a retrieval failure forever. This is worth naming out loud: a
broken eval is more dangerous than no eval, because you will act on it.

Re-run `/lab:eval` with their queries in. Their number differs from the table now, and that
is correct. **From here on their scoreboard is the truth and this document is background.**

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M2.C1-baseline
```

### Questions you may get here

**"Is this just grep?"** Nearly. It is grep with a weighting that prefers rare words. That is
the point — it sets a floor that is embarrassingly easy to build and not embarrassingly easy
to beat.

**"Then why does anyone use vector search?"** Two reasons, and both are honest: cost at
scale, and questions whose wording shares no words with the answer. They will see the second
one in step 3 on the `hard` tier.

---

## Step 2 — Chunk it, embed it, search it (12 minutes)

### 2.1 Install the pipeline

```
/lab:next
```

Stage `m2s2-vectors` installs three files, all theirs to write:

| | |
|---|---|
| `rag/chunkers.py` | three strategies and the metadata that comes off documents |
| `rag/ingest.py` | chunk, embed, store — one collection per strategy |
| `rag/retrieve.py` | search, filtered search, whole document |

In this step they implement **only** `naive` in `chunkers.py`, plus `ingest.py` and
`search()` in `retrieve.py`. Say that explicitly or they will start all three strategies at
once and finish none.

### 2.2 Naive, exactly as described

Fixed 600-character windows, 80 of overlap. They will want to improve it. Do not let them:
its failures are the measurement that makes step 3 mean something. "Build the bad one on
purpose" is a phrase worth using.

The three things that go wrong, in the order they go wrong:

1. **Appending instead of replacing.** A second ingest that adds rather than replaces gives a
   collection with every chunk twice and a score that drifts for no visible reason. Deleting a
   collection that does not exist raises — that is the normal first run, not an error.
2. **`None` in metadata.** Chroma takes str, int, float and bool. `None` raises, several
   frames from where the mistake was made.
3. **Duplicate ids.** They overwrite silently. Include the strategy in the id.

### 2.3 Ingest and measure

```
python3 rag/ingest.py naive
/lab:eval naive chunking
```

First run downloads the model. Expect a pause.

| Track | Baseline | Naive |
|---|---|---|
| `support-triage` | 11/12 at 2,303 per answer | **6/12** at 1,331 |
| `vendor-qa` | 12/12 at 2,013 | **8/12** at 1,028 |
| `docgen` | 8/12 at 2,409 | **8/12** at 894 |

Halve the price, lose a third of the answers — and on `docgen`, hold the answers and halve
the price. Do not smooth that inconsistency over. Corpora differ; that is the module's
second lesson arriving early.

### 2.4 Name what just happened

A fixed window cuts where the character count runs out, which is never where the meaning
ends. It splits tables down the middle, separates a heading from the rule underneath it, and
buries the answer in a chunk that is mostly about something else.

Then the sentence to leave hanging:

> The fix is not a better embedding model. It is cutting in better places.

---

## Step 3 — The chunking lab (18 minutes)

### 3.1 Structural

One chunk per markdown section, carrying its **heading path** — the whole trail, `Triage
policy / Escalation / SLA`, not just the nearest heading. The path goes into the chunk text.

That is the cheapest retrieval win available, and worth saying why: it puts the words a
person would actually search for inside the chunk that answers them. A fixed window usually
does not contain them.

Two traps: a `#` inside a fenced code block is not a heading, and a section longer than
`SECTION_MAX` must be split with every piece keeping its heading.

```
python3 rag/ingest.py structural
/lab:eval structural chunking
```

### 3.2 Parent-child

Index small pieces, return the section each came from. Embed the child, store the parent,
return the parent.

**The failure to watch for:** returning the child. Everything still works, the number just
quietly gets worse, and it is invisible in the code unless you know to look. They have paid
to index small pieces and then thrown away the context they bought. The gate catches it; ask
them to predict what it would do to the score before they run it.

```
python3 rag/ingest.py parent_child
/lab:eval parent-child chunking
```

### 3.3 The scoreboard, and the argument

```
/lab:status
```

Four rows now. Let them argue about which strategy is best for a minute or two — then tell
them what the measurement says:

| Track | Winner | Answered | Tokens per answer |
|---|---|---|---|
| `support-triage` | `structural` | 10/12 | **702** |
| `vendor-qa` | `parent_child` | 10/12 | **881** |
| `docgen` | `structural` on cost, `parent_child` on answers | 8/12 · 9/12 | 679 · 780 |

**There is no best chunker.** `naive` loses nearly everywhere, which is the one piece of
received wisdom that survives. Beyond that it depends on the shape of the documents:
prose under clear headings rewards a heading path; table-heavy documents embed badly as whole
sections and do better as small children with big parents.

Nobody could have predicted that from first principles. That is exactly why they were handed
a scoreboard instead of a recommendation — and it is the transferable skill in this module,
more than any chunker.

### 3.4 If someone notices MRR got worse

Someone usually does, and they are right. Chunking splits one strong document match into
several weaker chunk matches, so the first useful result often ranks lower. It matters little
when the agent reads all five.

Use it: **a metric can move the wrong way while the system gets better.** That is why you
watch more than one, and why "the number went up" is not the same as "it improved".

### 3.5 Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_ingest.py"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M2.C2-chunking
```

The gate runs all three strategies over their real corpus and checks the properties each one
claims — headings actually carried, parents actually longer than children, metadata actually
populated. It is not reading their source for keywords.

---

## Step 4 — Metadata and filters (15 minutes)

### 4.1 The question that breaks similarity search

Every track's corpus has a planted time bomb, but **the tracks do not express time the same
way** — check which shape yours is before you teach this:

| Track | Shape | Where the trap is |
|---|---|---|
| `support-triage` | a **superseded document** — two entitlement matrices, one replaced | `data/knowledge/plan-entitlements-2026-01.md` and its successor |
| `docgen` | a **superseded document** — two charter versions | `data/sources/charters/atlas-charter.md` and its successor |
| `vendor-qa` | an **amendment log** — the old wording lives *inside* the current document | `data/contract/MSA-amendments.md`: clause 7.2 was 2 business days, then 3 |

Ask the agent, or have the room ask it:

> What does the **current** version say about &lt;the thing that changed&gt;?

On the superseded-document tracks it is worse than "both versions match" — **measured, the
superseded one ranks first.** On `support-triage` the retired entitlement matrix comes back
at distance 0.653 against the current one's 0.703; on `docgen` the old charter is the top
hit. The answer comes back confident, first-ranked, and out of date.

That is worth saying explicitly, because the intuition in the room will be "similarity search
will prefer the current one". It does not. It has no idea which one is current.

On `vendor-qa` it fails differently and more interestingly. Ask *"what is the Severity 2
resolution time"* and the top hits are `history/findings-M2.md` and `contract/MSA-excerpt.md`
— and that excerpt passage contains **both** terms, the original two business days and the
amended three. Nothing is marked superseded, so no filter saves you. The model has to work
out which applies, and the fact that decides it — the milestone's submission date — is in a
third document. Watch it answer without ever asking "as of when".

Either way, no chunk size fixes it, because what is needed is not in the text. It is
*about* the text.

### 4.2 What metadata is for

Not decoration, and not for humans: **every field is a filter you could retrieve by.** A
field they do not extract now is a question they cannot answer later.

`base_meta()` in their `chunkers.py` is where this lives:

| Field | The question it makes answerable |
|---|---|
| `source` | which file said this — citation |
| `doc_type` | "search only the knowledge base, not the tickets" |
| `period` | "what did the reports say in June" |
| `valid_from` / `valid_to` | "what was in force on the day of the incident" |
| `superseded` | "the **current** policy" |

`valid_from` and `superseded` are the ones they skip and the ones that matter. The gate
checks these against their actual corpus: where a document declares that it supersedes
another, something must come back marked superseded, because a `validity()` that finds
nothing is inert code that looks like working code. On `vendor-qa`, where nothing is
wholesale superseded, the weight falls on the dates instead.

Worth naming for the `vendor-qa` room, and useful everywhere: a flag answers "is this still
true?", while dates answer "what was true *then*?" — and an acceptance decision about a
past submission needs the second one. That distinction is the whole of temporal retrieval,
and it is the thread Module 3 picks up.

### 4.3 Filtered retrieval, and the row that measures it

`search_filtered()` in `retrieve.py`. One Chroma trap worth naming: two keys in one `where`
dict is not AND — multiple conditions need `{"$and": [...]}`.

Re-ingest so the new metadata is stored, then re-run the scoreboard.

**On `support-triage` this is a scored row.** The golden set carries one query in a tier of
its own, `filtered`, reported separately so it never moves the numbers the chunkers are
compared on. Measured, before and after:

```
filtered        0/1     ...   Retrieved a document that contradicts the answer:
                              G16  returned plan-entitlements-2026-01.md, which is superseded
filtered        1/1
```

That query needs a mechanism worth explaining, because it is the only place the module scores
something other than an anchor. The anchor from the *current* matrix is retrieved either way
— so anchor alone would call the unfiltered run a success while the retired matrix sat above
it. The query therefore **forbids** the superseded file: retrieving both versions is not a
partial success, it is contradictory evidence, and the stale one ranks first.

**On `docgen` and `vendor-qa` there is no such row, and say so** rather than letting them hunt
for one. Their corpora do not have the shape for it:

- `docgen`'s two charter versions live in *one file*, so no file can be forbidden. Demonstrate
  it on the chunks instead: with heading-aware chunking the Version 1 section comes back
  `superseded=True` and Version 2 `False`, and `superseded=false` drops exactly the retired
  half of the file.
- `vendor-qa` has nothing superseded at all. The filter cannot help, which is the finding —
  go straight to 4.4.

### 4.3b The trap that is worth more than the lesson

This one was hit while building the module, and it is the best thing in step 4.

A first attempt at `validity()` marks a document superseded whenever the word appears near the
top. On `docgen` that flags **`atlas-charter.md` itself** — the current charter — because it
says *"Superseded: version 1"*, meaning the version it replaced. Filtering to `superseded=false`
then removed the only file holding the current scope. The filter did not return a stale
answer; it made the question unanswerable.

Two rules come out of that, and both transfer:

1. **A mention is not a declaration.** "Supersedes X" and "Superseded: X" mean this document
   is *current*. Only a self-declaration counts.
2. **A flag describes whatever you attach it to.** A per-file flag cannot be right for a file
   that records two versions. Metadata granularity has to match document granularity — which
   is why the fix was to compute it per *section*, not per file.

If someone in the room hits this, do not rescue them quickly. It is the most useful ninety
seconds in the module: a filter that is confidently wrong is worse than no filter, and they
will remember finding that themselves.

### 4.4 The point to land

> Filters are not a refinement of retrieval. For a whole class of question they **are** the
> retrieval, and similarity is just how you rank what is left.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_ingest.py"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M2.C3-metadata
```

---

## Step 5 — Retrieval as a tool (15 minutes)

### 5.1 Why this is earned, not asserted

They wrote a tool as a script in Module 1. So the question has a real answer now: *when does
a script need to become a typed, shareable interface?* When something other than you has to
decide whether to call it.

```
/lab:next
```

Stage `m2s3-mcp` installs `mcp/retrieval_server.py` and a `.mcp.json`.

### 5.2 MCP is a protocol, not a framework

Have them read the bottom half of the file first. Newline-delimited JSON-RPC 2.0 over stdin
and stdout, three methods: `initialize`, `tools/list`, `tools/call`. No SDK. There is nothing
mysterious in it, and that is the point — demystifying MCP is worth more here than using it.

One rule, and it is the failure mode: **anything on stdout that is not a JSON-RPC message
corrupts the stream.** A stray `print()` shows up as a server that failed to start, with no
useful reason. Debug output goes to stderr.

### 5.3 What they write

The tool declarations and the dispatch. Three tools wrapping the three functions they already
have: `search_corpus`, `search_corpus_filtered`, `get_document`.

Two design points, and they are the whole step:

**The description is a skill description under another name.** It is the only thing the model
sees when deciding whether to call the tool. They measured what a vague description costs in
Module 1 — a skill that fired on the 7th request instead of the 1st. Same rule, same cost.
For the filtered tool, the description has to say *when* a filter is right, because the model
will not infer that "current" means `superseded=false`.

**Do not leak the database.** No `where`, no `n_results`, no collection name. If a caller
needs to know Chroma's query syntax, they have not built a tool — they have exported a
dependency. The gate fails this specifically.

And `format_results()`: number each passage and name its source, or the model invents
citations that look right and are not.

### 5.4 Wire it up and watch it get called

Restart the session so `.mcp.json` is read. Then ask a question in plain language and watch
the agent call `search_corpus` on its own.

That moment is the one to point at: they did not tell it to retrieve. It decided to, from a
description they wrote.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_retrieval_tool.py"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M2.C4-tool
```

The gate speaks the protocol to their server the way a client does — handshake, `tools/list`,
real calls. A file that looks correct and never completes a handshake is worth nothing, so it
is not checked by reading.

---

## Step 6 — Agentic retrieval (20 minutes)

### 6.1 Show single-shot failing first

Pick a question with two parts — "has this been seen before, and is the fix released?" — and
ask it with the tool they just built.

What comes back is fluent, well-cited, and answers **one half**. Nobody notices unless they
are looking, which is exactly why this failure is worth 20 minutes: it does not look like a
failure.

### 6.2 The skill

```
/lab:next
```

Stage `m2s4-agentic` installs `.claude/skills/retrieve-and-answer/SKILL.md` with the
procedure skeleton and the steps left to them. Five steps: decompose, retrieve per part,
**assess sufficiency**, answer with citations, declare the gaps.

Step 3 is the one that makes it agentic and the one they will write as a formality. Push on
it. The test is not "did I get plausible passages", it is **"can I point at the sentence that
answers this"**. If they cannot, they have not retrieved it, however relevant the passages
look.

Two constraints to insist on:

- **A retrieval budget.** Two extra rounds, then stop and report. An agent that retrieves
  forever is not thorough, it is stuck, and it burns the context window to get there.
- **Declare what is missing.** The most valuable line in the output and the first one
  dropped. A gap declared is a gap someone fixes; a gap papered over becomes a wrong
  decision downstream.

### 6.3 Measure it against single-shot

Same questions, especially the multi-part ones, and read both answers side by side.

Be straight about what they will see, and be straight about what is *not* known here.

It is certainly **slower and more expensive** — more calls, more context. What it buys has
**not been measured on these corpora**, unlike everything else in this module: the retrieval
numbers came from a harness, and this one needs a real agent loop to judge. So do not promise
an outcome. Ask them to compare the two answers themselves against three things:

1. Does it address every part they asked, or one part fluently?
2. Does every claim carry a source, and does that source actually say it?
3. Does it say what it could not find?

Their comparison is the evidence. If the room finds the agentic version no better on their
track, that is a real result — write it down and tell the facilitator, because it belongs in
the measured notes and currently nothing is there.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_skill.py" --name retrieve-and-answer
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M2.C5-agentic
```

### 6.4 Deliberately not covered

Name these so nobody thinks they were missed: **hybrid search** (lexical and vector combined
— and after step 1 they can see why that is not a silly idea), **reranking** with a
cross-encoder, **contextual retrieval** (a generated summary prefixed to each chunk), and
**semantic chunking** by embedding distance. All real, all cost money or latency, and none of
them changes anything this module teaches.

---

## Step 7 — Debrief, and three questions that stay broken (10 minutes)

### 7.1 The scoreboard as the artifact

```
/lab:status
```

Six or seven rows, and the arc is the deliverable. What they can now do that they could not
two hours ago is not "use ChromaDB" — it is **tell whether a change to retrieval helped.**

The four claims worth repeating, because all four are counter-intuitive and all four are
measured:

1. Chunking buys cost, not accuracy.
2. There is no best chunker; there is only your corpus.
3. A metric can move the wrong way while the system improves.
4. Some questions are not a retrieval problem at all.

### 7.2 Now the cold open for Module 3

Run the three `unreachable` queries. Do not fix them. Do not soften them.

They fail in three distinct ways, and naming the shapes is the whole point:

| Shape | Example | Why retrieval cannot do it |
|---|---|---|
| **Relational** | "which other accounts are exposed to this defect" | the answer is several hops apart, in no single passage |
| **Aggregate** | "how many tickets traced to this vendor case" | the answer is a count, and counting is not similarity |
| **Temporal** | "what changed between these two versions" | the answer is a *difference*, and no chunk contains a difference |

Say it plainly:

> No chunk size fixes these. No embedding model fixes these. They are not retrieval
> problems. They are shape problems — the answer is not in any passage, it is in the
> relationships between passages. That is Module 3.

### 7.3 Package it — plugin v0.2

Two minutes, and do not skip it: they have been building in the project all module, and the
plugin is the thing they keep.

**The skill goes into the plugin.** It is capability — it works the same for anyone:

```
mv .claude/skills/retrieve-and-answer <their-plugin>/skills/retrieve-and-answer
```

Then bump `<their-plugin>/.claude-plugin/plugin.json` to `"version": "0.2.0"` and validate:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_plugin.py"
```

**The MCP server stays in the project, and this is worth thirty seconds of explanation** —
it is the `${CLAUDE_PLUGIN_ROOT}` versus `${CLAUDE_PROJECT_DIR}` distinction from Module 1,
arriving with real stakes. `mcp/retrieval_server.py` needs `.venv`, `chroma/`, and an
ingested corpus. None of those travel. The skill is capability and belongs in the plugin;
the retrieval server is *situation* and belongs to the project it retrieves from.

If someone asks whether a plugin can ship an MCP server: yes, and Module 4 deals with it,
when the question is how to distribute the whole system rather than one skill.

### 7.4 Close

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" complete-module 02
```

Plugin v0.2: a corpus they can search, a number they trust, a tool the agent calls, and a
skill that cites its sources. Tell them to keep the scoreboard — Module 4 re-scores the whole
system, and this is the first honest baseline they have.

---

## If the clock has beaten you

In priority order, protect the top and cut from the bottom:

| Keep at all costs | Step 1 (the floor) and step 3.3 (no best chunker). The module's two ideas |
|---|---|
| Cut to a demo | Step 6 — you drive the agentic skill, they read the diff. It survives being watched |
| Cut to a statement | Step 4 — ask the "current policy" question, show it fail, say what metadata would fix, move on |
| Never cut | The three broken questions in 7.2. Module 3 opens on them and lands flat without this |

If step 0 overruns because of the network, run step 1 while it installs. The baseline has no
dependencies — that is the second reason it goes first.
