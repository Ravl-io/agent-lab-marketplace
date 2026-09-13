#!/usr/bin/env python3
"""Chunk the corpus and load it into ChromaDB.

    python3 rag/ingest.py naive
    python3 rag/ingest.py structural
    python3 rag/ingest.py parent_child

One collection per strategy, so re-ingesting one does not destroy the last measurement of
another. The strategy you ingested last becomes the one `rag/retrieve.py` searches, recorded
in `rag/config.json` so nothing has to be passed around.

The first run downloads the embedding model — about 90 MB, all-MiniLM-L6-v2, ONNX. After
that it runs locally: no API key, no network, and no document leaving the machine. Worth
saying out loud, because it is the answer to "can we even do this with our data".
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chunkers import STRATEGIES, chunk_corpus, project_root   # noqa: E402

CHROMA_DIR = "chroma"
CONFIG = "rag/config.json"
BATCH = 200                 # Chroma will embed in one go otherwise, and it will be slow


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("strategy", choices=sorted(STRATEGIES))
    ap.add_argument("--root", default=None)
    args = ap.parse_args()
    root = os.path.abspath(args.root or project_root())

    try:
        import chromadb
    except ImportError:
        sys.exit("chromadb is not installed for this interpreter.\n"
                 "It belongs in the lab's virtual environment — run this module's setup "
                 "step rather than installing it globally.")

    chunks = chunk_corpus(args.strategy, root)
    if not chunks:
        sys.exit(f"no documents found under {os.path.join(root, 'data')} — "
                 f"or your chunker returned nothing, which is more likely right now")

    client = chromadb.PersistentClient(path=os.path.join(root, CHROMA_DIR))
    name = f"corpus_{args.strategy}"

    # TODO 1. Get a clean collection called `name`.
    #         A second ingest must REPLACE, never append. Appending is the single most
    #         common way a scoreboard starts lying to you: the same chunk twice, the old
    #         version still in there, and a number that drifts for no visible reason.
    #         Deleting a collection that does not exist raises — that is the normal case
    #         on a first run, not an error.
    collection = None

    # TODO 2. Turn `chunks` into the three parallel lists Chroma wants.
    #
    #         ids         unique strings. Include the strategy — you have three collections
    #         documents   the text that gets EMBEDDED. For parent_child that is the child
    #         metadatas   chunk["meta"], plus the parent when there is one
    #
    #         Two things Chroma will punish you for:
    #           - a metadata value of None (it accepts str, int, float, bool — not None)
    #           - duplicate ids (they silently overwrite)
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    if not ids:
        sys.exit("nothing to add — TODO 2 is still open")

    for start in range(0, len(ids), BATCH):
        collection.add(ids=ids[start:start + BATCH],
                       documents=documents[start:start + BATCH],
                       metadatas=metadatas[start:start + BATCH])

    config_path = os.path.join(root, CONFIG)
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as fh:
        json.dump({"strategy": args.strategy, "collection": name,
                   "chunks": len(ids), "chroma_dir": CHROMA_DIR}, fh, indent=2)
        fh.write("\n")

    sources = len({m["source"] for m in metadatas})
    mean = sum(len(d) for d in documents) // len(documents)
    print(json.dumps({"strategy": args.strategy, "collection": name,
                      "documents": sources, "chunks": len(ids),
                      "mean_chunk_chars": mean}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
