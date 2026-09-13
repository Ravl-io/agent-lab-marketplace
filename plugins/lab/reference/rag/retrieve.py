#!/usr/bin/env python3
"""Search the collection that `rag/ingest.py` built.

    search(query, k=5)                       -> list of results
    search(query, k=5, where={"period": "2026-06"})   -> the same, filtered

Each result carries the fields the eval harness and your skill both rely on:

    source   the document it came from, relative to the project root
    text     what goes in the context window
    score    lower is closer, because Chroma returns a distance
    meta     the chunk's metadata, which is what filters act on

`search_filtered` and `get_document` exist because a skill should ask for what it wants, not
be handed a vector database. That distinction is what makes this a tool rather than a wrapper.
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
    global _COLLECTION
    if _COLLECTION is None:
        import chromadb
        cfg = _config()
        client = chromadb.PersistentClient(
            path=os.path.join(project_root(), cfg.get("chroma_dir", "chroma")))
        _COLLECTION = client.get_collection(cfg["collection"])
    return _COLLECTION


def search(query: str, k: int = 5, where: dict | None = None) -> list[dict]:
    result = collection().query(query_texts=[query], n_results=k,
                                **({"where": where} if where else {}))
    out = []
    for text, meta, distance in zip(result["documents"][0],
                                    result["metadatas"][0],
                                    result["distances"][0]):
        meta = dict(meta or {})
        # parent_child indexes the child but the caller wants the section it came from
        body = meta.pop("parent", None) or text
        out.append({"source": meta.get("source", ""), "text": body,
                    "score": round(float(distance), 4), "meta": meta})
    return out


def search_filtered(query: str, k: int = 5, **filters) -> list[dict]:
    """Search within a slice of the corpus.

    The filters are the reason the metadata exists. `superseded=False` is the difference
    between quoting the policy in force and quoting the one it replaced.
    """
    where = {key: value for key, value in filters.items() if value is not None}
    if len(where) > 1:
        where = {"$and": [{k: v} for k, v in where.items()]}
    return search(query, k, where=where or None)


def get_document(source: str) -> str:
    """The whole document, for when a chunk is not enough."""
    path = os.path.join(project_root(), source)
    if not os.path.exists(path):
        raise FileNotFoundError(source)
    return open(path, encoding="utf-8", errors="replace").read()


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "what are the four classifications"
    for r in search(q):
        print(f"{r['score']:.4f}  {r['source']}  {r['meta'].get('heading', '')}")
        print(f"        {r['text'][:120].replace(chr(10), ' ')}")
