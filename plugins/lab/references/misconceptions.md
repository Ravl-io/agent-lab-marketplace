# Misconceptions to correct on sight

These are the wrong ideas that quietly compound. Correct them whenever they surface, in any
module, whether or not the participant asked. Each one is short on purpose — state the
correction, give the one-line reason, move on.

---

**"More context is better."**
Context is a budget, not a virtue. Relevance beats volume: irrelevant material in the window
competes with the relevant material for the model's attention and costs money and latency.
The whole point of retrieval is putting *less* in the window, more precisely.

**"Embeddings understand meaning."**
They encode distributional similarity — what tends to appear in similar company. Similar is
not the same as relevant, and relevant is not the same as correct. This is why two documents
that use the same vocabulary to say opposite things sit close together.

**"Evals are probabilistic."**
No. **The model is probabilistic. Evals are the measurement system** that accounts for that
variance — that is what running k times against thresholds is for. Getting this backwards
makes evals sound unreliable when they are the only reliable thing you have.

**"A knowledge graph replaces RAG."**
They answer different shapes of question. The graph knows structure, scope and completeness;
the vector store finds the passage that says it in words you can quote. Real systems route to
both. Choosing between them is the mistake.

**"Top-k is the answer set."**
Similarity search returns the k most similar things. It cannot express completeness, so it
structurally cannot answer "all", "how many", or "which ones are missing". Those are
aggregation queries, and no amount of better chunking fixes them.

**"A skill is just a prompt."**
A skill is a *triggerable* procedure: a description that decides when it loads, a body that
is only read when it does, and bundled assets it can point to. The description is the part
the agent sees before loading anything — which is why a bad description means a skill that
never fires, no matter how good its body is.

**"A command and a skill are different things."**
They are the same primitive in the same file format, one frontmatter flag apart. With
`disable-model-invocation: true` only the user can invoke it — that is what people call a
slash command. Without it, the model reads the `description` and decides whether to load it.
The interesting difference is *who decides*, and the description is what lets the model
decide.

**"MCP is required to give an agent tools."**
A shell script that prints JSON is a tool. MCP is how you make a tool surface durable, typed
and shareable across projects and machines. Start with the script; reach for MCP when the
tool outlives the exercise.

**"The hook and the skill do the same job."**
A skill is guidance the model chooses to follow. A hook is enforcement it cannot skip. If it
matters that something *always* happens — an approval gate, a write boundary, a required
format — that is a hook. If it is knowledge about how to do something well, that is a skill.

**"The agent should just be autonomous."**
Autonomy is a ladder, not a switch. The interesting engineering is in the rungs: proposing
with evidence, running its own evals, and applying only behind a gate. The gate is what makes
the useful level shippable inside a real organisation.

**"Chunking is a preprocessing detail."**
Chunking decides what can ever be retrieved. A fact split across two chunks, or buried in a
chunk about something else, is unreachable no matter how good the query. It is a modelling
decision about your documents, not a parameter.

**"The ontology should model the domain."**
It should answer the questions you need answered. An ontology designed from the data grows
without limit and pays for nothing; an ontology designed from competency questions stays small
and earns its maintenance. Start from the questions retrieval got wrong.

**"Citations mean it is grounded."**
A citation proves a source was retrieved, not that the claim follows from it. Groundedness is
a separate measurement from retrieval quality — which is why the lab scores retrieval and
answers separately.
