#!/usr/bin/env python3
"""A retriever with no dependencies: lexical scoring over whole documents.

This is the floor. It reads every document under `data/`, scores each against the query by
word overlap with an inverse-document-frequency weighting, and returns the best few. No
embeddings, no chunking, no vector store — about sixty lines of standard library.

Measure it before you build anything:

    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/eval_retrieval.py" \\
        --retriever rag/baseline_retrieve.py --label "lexical baseline"

Two reasons it is worth a scoreboard row of its own:

1. It is the number everything else has to beat. A vector store that scores the same as
   sixty lines of word counting has not earned its dependency.
2. It fails in a different *shape* from embeddings. It cannot match "what do we tell a
   customer" to a document that says "communications policy" — no shared words. Embeddings
   get that and lose elsewhere. Seeing both failure shapes is the point of running this.

The contract is the same one your own retriever will implement:

    search(query: str, k: int = 5) -> list[dict], each with a "source"
"""

from __future__ import annotations

import math
import os
import re
from functools import lru_cache

STOP = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "did", "do", "does", "for",
    "from", "has", "have", "how", "i", "if", "in", "is", "it", "its", "of", "on", "or",
    "our", "so", "that", "the", "their", "them", "then", "there", "they", "this", "to",
    "was", "we", "what", "when", "which", "who", "why", "will", "with", "would", "you",
}


def project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9_\-]+", text.lower())
            if w not in STOP and len(w) > 1]


@lru_cache(maxsize=1)
def corpus() -> list[tuple[str, str, list[str]]]:
    """Every document under data/, as (relative path, full text, words)."""
    root = project_root()
    base = os.path.join(root, "data")
    docs = []
    for dirpath, _dirs, names in os.walk(base):
        for name in sorted(names):
            if not name.endswith((".md", ".txt")):
                continue
            full = os.path.join(dirpath, name)
            try:
                text = open(full, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            docs.append((os.path.relpath(full, root), text, words(text)))
    return docs


@lru_cache(maxsize=1)
def idf() -> dict[str, float]:
    """How rare each word is. Without this, every document matching 'the' scores."""
    docs = corpus()
    total = len(docs) or 1
    seen: dict[str, int] = {}
    for _path, _text, tokens in docs:
        for token in set(tokens):
            seen[token] = seen.get(token, 0) + 1
    return {w: math.log(total / (1 + n)) + 1.0 for w, n in seen.items()}


def search(query: str, k: int = 5) -> list[dict]:
    weights = idf()
    terms = words(query)
    scored = []
    for path, text, tokens in corpus():
        if not tokens:
            continue
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        # length-normalised, so a long document does not win on volume alone
        score = sum(weights.get(t, 0.0) * math.log(1 + counts.get(t, 0)) for t in terms)
        score /= math.sqrt(len(tokens))
        if score > 0:
            # The text is the whole document, because that is genuinely what this puts in
            # the context window. The token cost on the scoreboard is not a penalty; it is
            # the truth about this approach.
            scored.append({"source": path, "score": round(score, 4), "text": text})
    scored.sort(key=lambda r: -r["score"])
    return scored[:k]


if __name__ == "__main__":
    import json
    import sys
    q = " ".join(sys.argv[1:]) or "what are the four classifications"
    print(json.dumps(search(q), indent=2))
