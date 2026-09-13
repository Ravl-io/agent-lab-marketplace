#!/usr/bin/env python3
"""Chunk the corpus and load it into ChromaDB.

    python3 rag/ingest.py naive
    python3 rag/ingest.py structural
    python3 rag/ingest.py parent_child

One collection per strategy, so you can re-ingest and re-measure without losing the last
run. The strategy you ingested last becomes the one `rag/retrieve.py` searches; that is
recorded in `rag/config.json` so nothing has to be passed around.

The first run downloads the embedding model (about 90 MB, all-MiniLM-L6-v2, ONNX). It runs
locally after that — no API key, no network, nothing leaving the machine.
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
BATCH = 200


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
                 "Module 2 installs it into the lab's virtual environment — run the setup "
                 "step for this module rather than installing it globally.")

    chunks = chunk_corpus(args.strategy, root)
    if not chunks:
        sys.exit(f"no documents found under {os.path.join(root, 'data')}")

    client = chromadb.PersistentClient(path=os.path.join(root, CHROMA_DIR))
    name = f"corpus_{args.strategy}"
    try:
        client.delete_collection(name)            # a re-ingest replaces, never appends
    except Exception:                             # noqa: BLE001 - absent is the normal case
        pass
    collection = client.create_collection(name=name)

    ids, documents, metadatas = [], [], []
    for index, chunk in enumerate(chunks):
        meta = dict(chunk["meta"])
        # parent_child embeds the child and returns the parent, so the parent rides along
        if chunk.get("parent"):
            meta["parent"] = chunk["parent"]
        meta = {k: ("" if v is None else v) for k, v in meta.items()}
        ids.append(f"{args.strategy}-{index}")
        documents.append(chunk["text"])
        metadatas.append(meta)

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
