#!/usr/bin/env python3
"""Search the collection that `rag/ingest.py` built.

    python3 rag/retrieve.py what is the escalation deadline

Three functions, and the difference between them is the whole design lesson of step 2.5:

    search(query, k)                 similarity, over everything
    search_filtered(query, k, **f)   similarity, over a slice you name
    get_document(source)             the whole file, for when a chunk is not enough

A skill should be able to ask for what it wants. It should never be handed a vector
database and left to work out the query syntax.
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _config() -> dict:
    path = os.path.join(project_root(), "rag", "config.json")
    if not os.path.exists(path):
        raise SystemExit("nothing has been ingested yet — run `python3 rag/ingest.py naive`")
    with open(path) as fh:
        return json.load(fh)


_COLLECTION = None


def collection():
    """Cached, because opening the client costs more than the query does."""
    global _COLLECTION
    if _COLLECTION is None:
        import chromadb
        cfg = _config()
        client = chromadb.PersistentClient(
            path=os.path.join(project_root(), cfg.get("chroma_dir", "chroma")))
        _COLLECTION = client.get_collection(cfg["collection"])
    return _COLLECTION


def search(query: str, k: int = 5, where: dict | None = None) -> list[dict]:
    """Return up to k results, each one shaped exactly like this:

        {"source": "data/knowledge/policy.md",   the file, relative to the project root
         "text":   "...",                         what goes into the context window
         "score":  0.4127,                        Chroma returns a DISTANCE: lower is closer
         "meta":   {...}}                         the chunk's metadata

    Two things to get right, and the scoreboard will catch both:

      1. `source` must be the real relative path. It is how results get attributed.
      2. For parent_child, `text` is the PARENT, not the child you embedded. Returning the
         child is the mistake that makes parent_child look worthless — you would be paying
         to index small pieces and then throwing away the context you bought.
    """
    # TODO: query the collection. collection().query(query_texts=[...], n_results=k) returns
    #       parallel lists under "documents", "metadatas" and "distances", each wrapped in
    #       an outer list because it supports several queries at once.
    return []


def search_filtered(query: str, k: int = 5, **filters) -> list[dict]:
    """Search within a slice of the corpus.

    These filters are the reason the metadata exists. `superseded=False` is the difference
    between quoting the policy in force and quoting the one it replaced.

    Chroma takes a `where` dict. One condition is {"field": value}; more than one has to be
    wrapped as {"$and": [{...}, {...}]} — passing two keys in one dict does not mean AND.
    Drop any filter whose value is None so callers can pass optional arguments.

    The scoreboard has one query that can only be answered through this function — tier
    `filtered`, reported separately from the headline. It stays at 0/1 until the filters are
    really applied, and it is the only row in the module that measures your metadata rather
    than your chunker.
    """
    # TODO: build `where` from filters, then hand off to search().
    return []


def get_document(source: str) -> str:
    """The whole document, for when a chunk is not enough.

    Deliberately not a vector operation. Once retrieval has told you which file matters,
    reading it is just reading a file, and a similarity search is the wrong tool for it.
    """
    path = os.path.join(project_root(), source)
    if not os.path.exists(path):
        raise FileNotFoundError(source)
    return open(path, encoding="utf-8", errors="replace").read()


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "what does the policy say"
    results = search(q)
    if not results:
        print("no results — either nothing is ingested, or search() is still a TODO")
    for r in results:
        print(f"{r['score']:.4f}  {r['source']}  {r['meta'].get('heading', '')}")
        print(f"        {r['text'][:120].replace(chr(10), ' ')}")
