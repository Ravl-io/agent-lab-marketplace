#!/usr/bin/env python3
"""Three ways to cut documents up, and the metadata that comes off them.

Chunking is not a preprocessing detail. It decides what can ever be retrieved: a fact split
across two chunks, or buried in a chunk about something else, is unreachable no matter how
good the query gets. Nothing downstream can recover from a bad cut.

You implement three strategies:

    naive         fixed-size character windows. Structure-blind
    structural    one chunk per markdown section, carrying its heading path
    parent_child  index small pieces, return the section they came from

See what one does to a single document:

    python3 rag/chunkers.py structural data/knowledge/<a file>

Stdlib only, and no embedding model appears anywhere in this file. Chunking is a decision
about your documents, made before anything is embedded.
"""

from __future__ import annotations

import os
import re
import sys

# Start here. These four numbers are the whole of naive chunking's "design", which is the
# point being made about it. You will change them later and re-measure.
NAIVE_SIZE = 600
NAIVE_OVERLAP = 80
CHILD_SIZE = 260
SECTION_MAX = 1400          # a section longer than this gets split, keeping its heading

# Which folder a document sits in says what kind of document it is, and that becomes a
# filter in step 2.4. Add any folder your track has that is missing here.
DOC_TYPES = {
    "knowledge": "knowledge", "tickets": "ticket", "db": "reference",
    "contract": "contract", "history": "history", "deliverables": "deliverable",
    "minutes": "minutes", "charters": "charter", "registers": "register",
    "sources": "source", "template": "template", "examples": "example",
}


def project_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


# ---------------------------------------------------------------- metadata
# Metadata is not decoration. Every field here is a filter you could retrieve by later, and
# a field you do not extract now is a question you cannot answer in step 2.4.

def doc_type(rel: str) -> str:
    """'data/knowledge/triage-policy.md' -> 'knowledge'. Use DOC_TYPES."""
    # TODO: walk the path segments and return the first one DOC_TYPES knows.
    #       Fall back to "document" rather than raising — an unknown folder is not an error.
    return "document"


def period(rel: str, text: str) -> str:
    """The YYYY-MM this document is about, from its filename. Empty string if it has none."""
    # TODO: a regex over os.path.basename(rel). Careful: a 4-digit year followed by more
    #       digits is probably not a date.
    return ""


def validity(text: str) -> tuple[str, str, bool]:
    """(valid_from, valid_to, superseded) — when this document's content was in force.

    This is the field that matters most and it is the one people skip. Your track's corpus
    contains near-duplicate pairs on purpose: two entitlement matrices, two charter
    versions, an amended clause. To a similarity search they look identical. Without this
    field, "what is the CURRENT policy" is a question your retriever cannot answer, and it
    will confidently quote the superseded one.

    Look at the first few hundred characters of a real document in your corpus before you
    write this. The phrasings are there — "in force 2026-01-01 to 2026-06-30", "supersedes",
    "effective", "last reviewed".

    Two traps, and both were hit while building this lab:

    1. **A mention of the word is not a declaration.** A document that says
       "Superseded: version 1" is naming what IT replaced, and is current. Match the word
       loosely and you mark the live document as retired — then `superseded=false` hides the
       only file holding the current answer, which is a worse failure than having no filter.
    2. **A flag describes whatever you attach it to.** If one file records two versions of
       something, a per-file flag cannot be right for both halves. Notice it now; what to do
       about it is part of the exercise.
    """
    # TODO: return what you can find. Empty strings are fine; wrong dates are not.
    return "", "", False


def base_meta(rel: str, text: str) -> dict:
    """The metadata every chunk of this document carries, whatever the strategy."""
    valid_from, valid_to, superseded = validity(text)
    return {
        "source": rel,
        "doc_type": doc_type(rel),
        "period": period(rel, text),
        "valid_from": valid_from,
        "valid_to": valid_to,
        "superseded": superseded,
    }


# ---------------------------------------------------------------- strategies
# Every strategy returns a list of dicts shaped like this:
#
#     {"text": "what gets embedded", "meta": {...}}
#
# and parent_child adds one more key:
#
#     {"text": "the child, embedded", "parent": "the section, returned", "meta": {...}}
#
# Keep that shape. rag/ingest.py and the scoreboard both depend on it.

def naive(rel: str, text: str) -> list[dict]:
    """Fixed windows of NAIVE_SIZE characters, overlapping by NAIVE_OVERLAP.

    Cheap, structure-blind, and it will cut a table in half. Implement it exactly as
    described — resist improving it. Its failures are the measurement you need.
    """
    meta = base_meta(rel, text)
    out: list[dict] = []
    # TODO: walk the text in steps of (NAIVE_SIZE - NAIVE_OVERLAP). Skip blank pieces.
    #       Number each chunk in meta["chunk"], and set meta["strategy"] = "naive".
    return out


def sections(text: str) -> list[tuple[str, str]]:
    """Split markdown on headings -> [(heading path, body including its heading line), ...].

    'heading path' means the full trail, not just the nearest heading: a chunk under
    '## Escalation' inside '# Triage policy' should carry 'Triage policy / Escalation'.
    That trail is the cheapest retrieval win available, because it puts the words a person
    would actually search for inside the chunk that answers them.

    One trap: a '#' inside a fenced ``` block is a comment, not a heading.
    """
    # TODO: track a stack of headings by depth so you can build the path.
    return [("", text)]


def structural(rel: str, text: str) -> list[dict]:
    """One chunk per section, each prefixed with its source and heading path.

    Prefix each chunk's text with something like:  [data/knowledge/policy.md / Triage / SLA]
    so the retrieved text says where it came from. Split any section longer than
    SECTION_MAX, and make sure every piece keeps the heading it belongs to.
    """
    meta = base_meta(rel, text)
    out: list[dict] = []
    # TODO: build on sections(). meta["heading"] = the path, meta["strategy"] = "structural".
    return out


def parent_child(rel: str, text: str) -> list[dict]:
    """Index small pieces; return the whole section each one came from.

    The trade-off is explicit, and you will see both halves of it on the scoreboard: a short
    child embeds precisely, and the parent it returns carries the context the child alone
    would lose. You pay for that context in tokens.
    """
    meta = base_meta(rel, text)
    out: list[dict] = []
    # TODO: for each section, cut the body into CHILD_SIZE children. Each child dict gets
    #       "text" = the child and "parent" = the section (prefixed, like structural).
    return out


STRATEGIES = {"naive": naive, "structural": structural, "parent_child": parent_child}


def chunk_corpus(strategy: str, root: str | None = None) -> list[dict]:
    """Every .md and .txt document under data/, cut up by one strategy."""
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
