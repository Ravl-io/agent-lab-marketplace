#!/usr/bin/env python3
"""Three ways to cut documents up, and the metadata that comes off them.

Chunking is not a preprocessing detail. It decides what can ever be retrieved: a fact split
across two chunks, or buried in a chunk about something else, is unreachable no matter how
good the query. These three are the ones worth knowing, in the order they are worth trying.

    naive         fixed-size character windows. Structure-blind
    structural    one chunk per markdown section, carrying its heading path
    parent_child  index small pieces, return the section they came from

Run it to see what a strategy does to a document:

    python3 rag/chunkers.py structural data/knowledge/triage-policy.md

Stdlib only. The embedding model never sees this file — chunking is a decision about your
documents, made before anything is embedded.
"""

from __future__ import annotations

import os
import re
import sys

NAIVE_SIZE = 600
NAIVE_OVERLAP = 80
CHILD_SIZE = 260
SECTION_MAX = 1400          # a section longer than this is split, keeping its heading

DOC_TYPES = {
    "knowledge": "knowledge", "tickets": "ticket", "db": "reference",
    "contract": "contract", "history": "history", "deliverables": "deliverable",
    "minutes": "minutes", "charters": "charter", "registers": "register",
    "sources": "source", "template": "template", "examples": "example",
}


def project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


# ---------------------------------------------------------------- metadata

def doc_type(rel: str) -> str:
    for part in rel.split(os.sep):
        if part in DOC_TYPES:
            return DOC_TYPES[part]
    return "document"


def period(rel: str, text: str) -> str:
    """A YYYY-MM in the filename is the period this document is about."""
    match = re.search(r"(\d{4})-(\d{2})(?!\d)", os.path.basename(rel))
    return f"{match.group(1)}-{match.group(2)}" if match else ""


def validity(text: str) -> tuple[str, str, bool]:
    """When a document's content was in force, and whether it has been superseded.

    Without this the near-duplicate pairs in every track — two entitlement matrices, two
    charter versions, an amended clause — are indistinguishable to a similarity search.

    The flag means **this document declares itself out of force**, and nothing weaker. A
    document that says "Superseded: version 1" is naming what IT replaced and is current;
    one that says "Supersedes X" likewise. Matching a bare mention of the word marks the
    live document as retired, and a `superseded=false` filter then hides the only file that
    holds the current answer — measured, that is exactly what happened to the Atlas charter.
    """
    head = text[:900]
    superseded = bool(re.search(
        r"(^|\n)\s*\**superseded\**\s*(\.|\n|$)"          # a standalone declaration
        r"|\bsuperseded\s+by\b"                              # names its replacement
        r"|\bthis\s+\w+\s+(?:was|has been)\s+superseded\b",
        head, re.I))
    span = re.search(r"in force\s+(\d{4}-\d{2}-\d{2})\s*(?:to|–|-|until)\s*(\d{4}-\d{2}-\d{2})",
                     head, re.I)
    if span:
        return span.group(1), span.group(2), True
    single = re.search(r"(?:in force|effective|amended)\s+(?:from\s+)?(\d{4}-\d{2}-\d{2})",
                       head, re.I)
    if single:
        return single.group(1), "", superseded
    reviewed = re.search(r"last reviewed[:\s]+(\d{4}-\d{2}-\d{2})", head, re.I)
    return (reviewed.group(1) if reviewed else ""), "", superseded


def base_meta(rel: str, text: str) -> dict:
    valid_from, valid_to, superseded = validity(text)
    return {
        "source": rel,
        "doc_type": doc_type(rel),
        "period": period(rel, text),
        "valid_from": valid_from,
        "valid_to": valid_to,
        "superseded": superseded,
    }


def section_superseded(heading: str, body: str) -> bool:
    """Is THIS section out of force, whatever the file around it says?

    Metadata has to match the granularity of the thing it describes. A per-file flag on a
    file that records two versions of a charter is worse than no flag: the whole file gets
    marked retired, and filtering to what is in force removes the current version too.
    """
    if re.search(r"\bsupersed(ed|es)\b.*\d{4}-\d{2}-\d{2}", heading or "", re.I):
        return True
    if re.search(r"\bsuperseded\b", heading or "", re.I):
        return True
    return bool(re.search(r"(^|\n)\s*\**superseded\**\s*(\.|\n|$)", body[:300], re.I))


# ---------------------------------------------------------------- strategies

def naive(rel: str, text: str) -> list[dict]:
    """Fixed windows. Cheap, structure-blind, and it will cut a table in half."""
    meta = base_meta(rel, text)
    out, start, index = [], 0, 0
    while start < len(text):
        piece = text[start:start + NAIVE_SIZE]
        if piece.strip():
            out.append({"text": piece, "meta": {**meta, "chunk": index,
                                                "heading": "", "strategy": "naive"}})
            index += 1
        start += NAIVE_SIZE - NAIVE_OVERLAP
    return out


def sections(text: str) -> list[tuple[str, str]]:
    """Split on markdown headings, returning (heading path, body including the heading)."""
    lines = text.splitlines()
    stack: list[str] = []
    blocks: list[tuple[str, list[str]]] = []
    current: list[str] = []
    path = ""
    fenced = False
    for line in lines:
        if line.lstrip().startswith("```"):
            fenced = not fenced
        heading = None if fenced else re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            if current:
                blocks.append((path, current))
            depth = len(heading.group(1))
            stack = stack[: depth - 1] + [heading.group(2).strip()]
            path = " / ".join(stack)
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append((path, current))
    return [(p, "\n".join(b).strip()) for p, b in blocks if "\n".join(b).strip()]


def structural(rel: str, text: str) -> list[dict]:
    """One chunk per section, carrying its heading path.

    The heading path is the cheapest retrieval win available: it puts the words a reader
    would search for into the chunk that answers them, which a fixed window often does not.
    """
    meta = base_meta(rel, text)
    out = []
    for index, (path, body) in enumerate(sections(text)):
        prefix = f"[{rel}{' / ' + path if path else ''}]\n"
        retired = meta["superseded"] or section_superseded(path, body)
        if len(body) <= SECTION_MAX:
            out.append({"text": prefix + body,
                        "meta": {**meta, "chunk": index, "heading": path,
                                 "superseded": retired, "strategy": "structural"}})
            continue
        # a long section is split, but every piece keeps the heading it belongs to
        for part, start in enumerate(range(0, len(body), SECTION_MAX - 200)):
            piece = body[start:start + SECTION_MAX]
            if piece.strip():
                out.append({"text": prefix + piece,
                            "meta": {**meta, "chunk": index * 100 + part,
                                     "heading": path, "superseded": retired,
                                     "strategy": "structural"}})
    return out


def parent_child(rel: str, text: str) -> list[dict]:
    """Index small pieces; return the whole section each came from.

    The trade-off is explicit: a short child embeds precisely, and the parent it returns
    carries the context the child alone would lose. You pay in tokens for that context, and
    the scoreboard will show whether it was worth it.
    """
    meta = base_meta(rel, text)
    out = []
    for index, (path, body) in enumerate(sections(text)):
        prefix = f"[{rel}{' / ' + path if path else ''}]\n"
        parent = prefix + body[:SECTION_MAX]
        retired = meta["superseded"] or section_superseded(path, body)
        for part, start in enumerate(range(0, len(body), CHILD_SIZE)):
            child = body[start:start + CHILD_SIZE]
            if not child.strip():
                continue
            out.append({
                "text": child,                    # what gets embedded
                "parent": parent,                 # what gets returned
                "meta": {**meta, "chunk": index * 100 + part, "heading": path,
                         "superseded": retired, "strategy": "parent_child"},
            })
    return out


STRATEGIES = {"naive": naive, "structural": structural, "parent_child": parent_child}


def chunk_corpus(strategy: str, root: str | None = None) -> list[dict]:
    """Every document under data/, cut up by one strategy."""
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown strategy {strategy!r}; "
                         f"try one of {', '.join(STRATEGIES)}")
    root = root or project_root()
    base = os.path.join(root, "data")
    fn = STRATEGIES[strategy]
    out = []
    for dirpath, _dirs, names in os.walk(base):
        for name in sorted(names):
            if not name.endswith((".md", ".txt")):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            try:
                text = open(full, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            out.extend(fn(rel, text))
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"usage: chunkers.py <{'|'.join(STRATEGIES)}> [file]", file=sys.stderr)
        raise SystemExit(2)
    which = sys.argv[1]
    if len(sys.argv) > 2:
        target = sys.argv[2]
        body = open(target, encoding="utf-8").read()
        chunks = STRATEGIES[which](os.path.relpath(target, project_root()), body)
    else:
        chunks = chunk_corpus(which)
    print(f"{len(chunks)} chunks, {which}")
    for c in chunks[:4]:
        head = c["meta"].get("heading") or "(no heading)"
        print(f"\n--- {c['meta']['source']} :: {head}  [{len(c['text'])} chars]")
        print(c["text"][:260].replace("\n", " ")[:260])
