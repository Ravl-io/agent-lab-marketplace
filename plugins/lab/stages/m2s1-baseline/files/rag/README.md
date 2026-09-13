# rag/

Everything that finds things in `data/`.

| File | What it is |
|---|---|
| `baseline_retrieve.py` | A retriever with no dependencies. Sixty lines of word counting. This is the floor everything else has to beat |
| `chunkers.py` | *You write this.* Three ways to cut documents up |
| `ingest.py` | *You write this.* Loads chunks into the vector store |
| `retrieve.py` | *You write this.* Searches what you ingested |
| `config.json` | Written by `ingest.py`. Records which strategy is live |

Every retriever here implements the same one-function contract, which is why the scoreboard
can compare them:

```python
def search(query: str, k: int = 5) -> list[dict]
```

Each result needs a `source` — the document path, relative to the project root — and a
`text`, which is what would go into the context window. The harness scores the text, because
retrieving the right file is easy and retrieving the right passage cheaply is not.
