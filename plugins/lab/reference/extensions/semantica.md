# Optional extension — the same graph, in a real library

**Nothing in the lab needs this.** Module 3 is complete without it. This is here for the
person who finishes and asks the right next question: *would we build this ourselves at work,
or use something off the shelf?*

[Semantica](https://getsemantica.ai) is a pip-installable graph library — MIT licensed, pure
Python wheel, **no database required**. Everything below was measured on 2026-09-13 against
version **0.6.8**, not read off a website.

## What it gives you that your 800 lines do not

| | |
|---|---|
| `CompetencyQuestion` | with `answerable` and `trace_to_elements` — the method Module 3 teaches, as a type, so a question traces to the ontology elements that answer it |
| `BiTemporalFact` | `valid_from`, `valid_until`, `recorded_at`, `superseded_at` — *bi*temporal: when a fact was true, and when you learned it. Yours is one of those two |
| Provenance | W3C PROV-O, with `ProvenanceManager` and an `InMemoryStorage` or `SQLiteStorage` backend |
| Standards | OWL, SHACL, SKOS for ontologies; SPARQL and Datalog for queries; Allen interval algebra for temporal reasoning |
| `EntityResolver` | the decision you made by hand, as a configurable strategy |
| An MCP server | 15 tools, shipped — `add_entity`, `run_reasoning`, `get_causal_chain`, `find_precedents` |

That is a serious list, and every item maps onto something this module taught you to care
about. If you are going to do this work properly at your organisation, look at it.

## What it costs, measured

| | |
|---|---|
| Packages installed | **136** |
| Download | **464 MB** (macOS arm64) |
| On disk | **2.0 GB** |
| Install time | 72 seconds on a fast connection |
| Largest components | `torch` 583 MB, `opencv-python` 119 MB, `transformers` 110 MB, `scipy` 98 MB |

For comparison, Module 3's implementation is **808 lines, 33 KB, and one dependency** —
`pyyaml`, for reading the ontology. Everything else is the Python standard library.

Two platform notes worth knowing before a room of twenty people installs it:

- **Windows needs the Microsoft Visual C++ Redistributable**, a system-level install. Most
  corporate images have it; if yours does not, you cannot fix that from pip.
- **On Linux x86_64, `pip install torch` normally pulls NVIDIA CUDA wheels** — roughly 2 GB
  more — unless you install torch from the CPU-only index first.

## What it is not, yet

Version 0.6.8, twenty-four releases, the latest eight days before this was written. That
shows in the places you would care about. Two findings from actually running it:

**`query_temporal` ignores its query.** The function that looks like the as-of query engine
returns the whole snapshot regardless of what you ask. The library says so in a comment:
*"Basic query execution (simplified) — in a real implementation, this would use a proper
query engine."* It also raises `KeyError` on the dict its own docstring documents, from a log
line doing `query[:50]`.

**The temporal model itself is fine.** `create_temporal_snapshot(graph, timestamp=...)` does
real date filtering, correctly. So the library gives you the temporal *model* and you still
write the query — which is worth knowing before you plan around it.

Neither finding is damning for a 0.6 release. Both are reasons this course does not build its
core on it: a training day that runs four times, days apart, on a locked-down network cannot
absorb a dependency that may change under it.

## Try it yourself

Into the same virtualenv, then copy the comparison script across:

```
pip install semantica
mkdir -p extensions
cp "${CLAUDE_PLUGIN_ROOT}/reference/extensions/semantica_port.py" extensions/
python3 extensions/semantica_port.py --as-of 2026-04-15
```

It reads the `graph/nodes.jsonl` and `graph/edges.jsonl` **you** produced, so your extraction
is the input to both paths — same facts, two implementations. It writes
`graph/semantica.json`, which is the whole point about persistence: Semantica's graph is a
plain dict, so saving it is `json.dump`. No database there either.

Measured on the shipped reference graphs, it reproduces the temporal answers exactly:

| Track | Temporal relation | In force 2026-04-15 | In force today |
|---|---|---|---|
| `support-triage` | `includes_feature` | 16 | **15** — Growth lost bulk export on 2026-06-01 |
| `vendor-qa` | `specifies_term` | 3 | 3 — clause 7.2's term changed, so one closed and one opened |
| `docgen` | `has_version` | 1 | 1 — one charter version in force at a time |

## The question this is actually for

You now have two working implementations of the same graph. One you can read end to end in an
afternoon; one brings standards compliance, bitemporality and a reasoning engine, at 2 GB and
a pre-1.0 version number.

Neither answer is wrong. What matters is that you can now tell **which question you are
answering** — and that is the thing this module was for. If your graph is a few hundred facts
that answer three questions, the 800 lines are probably right. If you need SHACL validation,
PROV-O audit trails and SPARQL because someone will ask you for them, do not write those
yourself.
