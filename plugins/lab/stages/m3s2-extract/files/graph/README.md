# graph/

Your extracted graph. Two files, one JSON object per line.

| File | What it holds |
|---|---|
| `nodes.jsonl` | the things — one per line, with `id`, `type`, `label`, `props`, `source` |
| `edges.jsonl` | the relationships — `src`, `rel`, `dst`, `valid_from`, `valid_to`, `source` |

Both are written by your extraction skill and read by `kg/compile.py`, which validates them
against `ontology/*.yaml` before building `kg.db`. Nothing is compiled until the validation
passes, so the errors it prints are the work list.

## The four things it refuses

| | Why it matters |
|---|---|
| a type the ontology does not declare | the ontology is the contract; a type outside it is unqueryable |
| an edge whose ends are the wrong types | a backwards edge does not error, it answers questions wrongly |
| an edge to a node that does not exist | a dangling edge silently shrinks every traversal through it |
| two nodes with the same `id` | two things claiming one identity — the second wins and takes the first one's edges |

## Two rules that are easy to skip

**Every node carries a `source`.** The file, and the table or section inside it. An answer
nobody can trace to a document is not usable by whoever has to act on it.

**Close a fact; never overwrite it.** When something stops being true, set `valid_to` on its
edge and add a new one. The closed edge is the only thing that can answer what was true at
the time, and "what was true then" is most of what anybody asks about a past decision.
