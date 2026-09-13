#!/usr/bin/env python3
"""Validate a participant's chunkers and ingest before the chunking checkpoint.

Behavioural, not textual: it imports their `rag/chunkers.py`, runs all three strategies over
their real corpus, and checks the properties the module claims each one has. Then, if
something has been ingested, it checks that `rag/retrieve.py` honours its contract — in
particular that parent_child returns the parent and not the child, which is the failure that
makes the strategy look worthless on the scoreboard.

    check_ingest.py               validate what is in the project
    check_ingest.py --json        machine-readable

Exit 0 if the pipeline would produce an honest measurement, 1 if not. Notes do not fail it.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys

REQUIRED_META = ("source", "doc_type", "period", "valid_from", "valid_to", "superseded")


def load(path: str, name: str):
    """Import a participant's file by path, with its own directory importable."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(path))
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check_chunkers(root: str, problems: list[str], notes: list[str]) -> dict:
    path = os.path.join(root, "rag", "chunkers.py")
    if not os.path.exists(path):
        problems.append("rag/chunkers.py does not exist yet")
        return {}
    try:
        mod = load(path, "participant_chunkers")
    except SystemExit as exc:
        problems.append(f"rag/chunkers.py exits on import: {exc}")
        return {}
    except Exception as exc:                                  # noqa: BLE001
        problems.append(f"rag/chunkers.py does not import: {type(exc).__name__}: {exc}")
        return {}

    if not hasattr(mod, "chunk_corpus"):
        problems.append("rag/chunkers.py has no chunk_corpus() — the scoreboard needs it")
        return {}

    counts: dict[str, int] = {}
    for strategy in ("naive", "structural", "parent_child"):
        try:
            chunks = mod.chunk_corpus(strategy, root)
        except Exception as exc:                              # noqa: BLE001
            problems.append(f"{strategy}: raised {type(exc).__name__}: {exc}")
            continue
        counts[strategy] = len(chunks)
        if not chunks:
            problems.append(f"{strategy}: produced no chunks — still a TODO")
            continue

        missing = [k for k in REQUIRED_META if k not in (chunks[0].get("meta") or {})]
        if missing:
            problems.append(f"{strategy}: chunk metadata is missing {', '.join(missing)}")
        if any(not (c.get("text") or "").strip() for c in chunks):
            problems.append(f"{strategy}: some chunks are empty — filter blank pieces out")
        if any((c.get("meta") or {}).get("strategy") not in (None, strategy)
               for c in chunks):
            problems.append(f"{strategy}: chunks are labelled with the wrong strategy")

        sources = {(c.get("meta") or {}).get("source", "") for c in chunks}
        if any(os.path.isabs(s) for s in sources):
            problems.append(f"{strategy}: source is an absolute path — it must be relative "
                            f"to the project root, or results cannot be attributed")

        if strategy == "naive":
            size = getattr(mod, "NAIVE_SIZE", 600)
            longest = max(len(c["text"]) for c in chunks)
            if longest > size * 1.5:
                problems.append(f"naive: a chunk is {longest} chars against NAIVE_SIZE "
                                f"{size} — the windows are not being applied")
            if len(chunks) < 2:
                problems.append("naive: one chunk for the whole corpus is not chunking")

        if strategy == "structural":
            headed = [c for c in chunks if (c.get("meta") or {}).get("heading")]
            if not headed:
                problems.append("structural: no chunk carries a heading — the heading path "
                                "is the entire point of this strategy")
            elif len(headed) < len(chunks) * 0.5:
                notes.append(f"structural: only {len(headed)} of {len(chunks)} chunks carry "
                             f"a heading; check documents that open without one")
            deep = [c for c in headed if " / " in (c["meta"]["heading"] or "")]
            if not deep:
                notes.append("structural: no heading path has more than one level — are you "
                             "keeping the trail, or only the nearest heading?")

        if strategy == "parent_child":
            withparent = [c for c in chunks if c.get("parent")]
            if not withparent:
                problems.append("parent_child: no chunk has a parent — without one this is "
                                "just naive chunking with extra steps")
            else:
                bad = [c for c in withparent if len(c["parent"]) < len(c["text"])]
                if bad:
                    problems.append(f"parent_child: {len(bad)} chunks have a parent shorter "
                                    f"than the child — they are the wrong way round")

    if counts.get("naive") and counts.get("structural"):
        if counts["naive"] == counts["structural"]:
            notes.append("naive and structural produced the same number of chunks, which "
                         "would be a coincidence — check they are really different")
    return counts


def corpus_has_supersede_markers(root: str) -> bool:
    """Does this corpus contain a document that declares itself superseded, or a successor?

    Checked against the documents rather than assumed, because the tracks model time
    differently and a gate that demands the wrong shape fails a correct implementation.
    """
    base = os.path.join(root, "data")
    for dirpath, _dirs, names in os.walk(base):
        for name in names:
            if not name.endswith((".md", ".txt")):
                continue
            try:
                head = open(os.path.join(dirpath, name), encoding="utf-8",
                            errors="replace").read(1200)
            except OSError:
                continue
            if re.search(r"\bsupersed(ed|es)\b", head, re.I):
                return True
    return False


def check_metadata_is_real(root: str, mod_counts: dict, problems: list[str],
                           notes: list[str]) -> None:
    """The near-duplicate pairs are planted. If no chunk is superseded, validity() is inert."""
    path = os.path.join(root, "rag", "chunkers.py")
    if not os.path.exists(path) or not mod_counts:
        return
    try:
        mod = sys.modules.get("participant_chunkers") or load(path, "participant_chunkers")
        chunks = mod.chunk_corpus("structural", root)
    except Exception:                                         # noqa: BLE001
        return
    metas = [c.get("meta") or {} for c in chunks]
    if not metas:
        return
    if len({m.get("doc_type") for m in metas}) < 2:
        problems.append("every chunk has the same doc_type — doc_type() is not reading the "
                        "folder, so you cannot filter by document kind in 2.4")
    # Not every corpus expresses time the same way, so this is derived rather than assumed.
    # Two shapes appear across the tracks: a document wholesale superseded by a newer one,
    # and an amendment log where the old wording lives inside the current document. Only the
    # first can set a `superseded` flag, so only require it where the corpus has that shape.
    if corpus_has_supersede_markers(root):
        if not any(m.get("superseded") for m in metas):
            problems.append("no document is marked superseded, but your corpus contains one "
                            "that says it supersedes another — validity() is not finding it, "
                            "and 'what is the CURRENT policy' will quote the old one")
    if not any(m.get("valid_from") for m in metas):
        problems.append("no document has a valid_from date — validity() is returning "
                        "nothing useful")
    if not any(m.get("period") for m in metas):
        notes.append("no document has a period; if your corpus has dated filenames, "
                     "period() is not picking them up")


def check_retrieval(root: str, problems: list[str], notes: list[str]) -> None:
    config = os.path.join(root, "rag", "config.json")
    if not os.path.exists(config):
        notes.append("nothing ingested yet — run `python3 rag/ingest.py naive`")
        return
    try:
        cfg = json.load(open(config))
    except ValueError:
        problems.append("rag/config.json is not valid JSON")
        return
    if not cfg.get("chunks"):
        problems.append("rag/config.json records 0 chunks — the ingest wrote nothing")

    path = os.path.join(root, "rag", "retrieve.py")
    if not os.path.exists(path):
        problems.append("rag/retrieve.py does not exist yet")
        return
    try:
        import chromadb                                       # noqa: F401
    except ImportError:
        notes.append("chromadb is not importable here, so retrieval was not exercised")
        return
    try:
        mod = load(path, "participant_retrieve")
        results = mod.search("what does the policy say", k=3)
    except Exception as exc:                                  # noqa: BLE001
        problems.append(f"rag/retrieve.py search() failed: {type(exc).__name__}: {exc}")
        return

    if not results:
        problems.append("search() returned nothing on a general query — either the "
                        "collection is empty or search() is still a TODO")
        return
    first = results[0]
    for key in ("source", "text", "score"):
        if key not in first:
            problems.append(f"search() results are missing '{key}' — the scoreboard and "
                            f"your skill both read that field")
    if not (first.get("text") or "").strip():
        problems.append("search() returned an empty text — that is what gets scored")
    if os.path.isabs(str(first.get("source", ""))):
        problems.append("search() returns an absolute source path; make it relative")

    if cfg.get("strategy") == "parent_child":
        # Ask the collection the same question directly. What comes back is what was
        # EMBEDDED — the children. If their search() hands back those same strings, the
        # parent is being discarded. Compared by equality, not by length: a small section's
        # parent is legitimately shorter than some other section's longest child, which is
        # what makes the obvious length heuristic wrong.
        try:
            raw = mod.collection().query(query_texts=["what does the policy say"],
                                         n_results=3)
            embedded = list(raw["documents"][0])
            metas = list(raw["metadatas"][0])
        except Exception:                                     # noqa: BLE001
            embedded, metas = [], []
        if embedded and any((m or {}).get("parent") for m in metas):
            returned = [r.get("text") for r in results]
            if returned and all(t in embedded for t in returned):
                problems.append("parent_child is ingested but search() is returning the "
                                "child, not the parent — you are paying to index small "
                                "pieces and then discarding the context you bought")


def report(problems: list[str], notes: list[str], counts: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps({"ok": not problems, "problems": problems,
                          "notes": notes, "chunks": counts}, indent=2))
        return
    print("INGEST CHECK")
    print("============")
    if counts:
        print()
        for strategy, n in counts.items():
            print(f"  {strategy:<14} {n:>5} chunks")
    if problems:
        print("\nNOT READY:")
        for item in problems:
            print(f"  x {item}")
    else:
        print("\nReady — three strategies, real metadata, and an honest retrieval contract.")
    if notes:
        print("\nWorth improving (not blocking):")
        for item in notes:
            print(f"  ! {item}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    # Their chunkers.py and retrieve.py both resolve the project through CLAUDE_PROJECT_DIR
    # or the cwd. The gate may be invoked from anywhere, so make --root authoritative before
    # importing anything of theirs, or a correct pipeline reports "nothing ingested".
    os.environ["CLAUDE_PROJECT_DIR"] = root

    problems: list[str] = []
    notes: list[str] = []
    counts = check_chunkers(root, problems, notes)
    check_metadata_is_real(root, counts, problems, notes)
    check_retrieval(root, problems, notes)
    report(problems, notes, counts, args.as_json)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
