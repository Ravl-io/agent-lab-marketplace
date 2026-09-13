#!/usr/bin/env python3
"""Score a retriever against the golden set.

This is the scoreboard. Every change you make to chunking, metadata or retrieval is measured
here, with the same fifteen queries, so "better" stops being an opinion.

    eval_retrieval.py --retriever rag/baseline_retrieve.py --label "lexical baseline"
    eval_retrieval.py --retriever rag/retrieve.py --label "naive chunking" --k 5
    eval_retrieval.py --retriever rag/retrieve.py --json

Your retriever must expose one function:

    def search(query: str, k: int = 5) -> list[dict]

Each result needs a `source` — the path of the document it came from, relative to the
project root. Anything else it returns is ignored here and used by your skill.

## What is measured, and why it is not recall over filenames

**answered**  the retrieved text contains the query's anchor — the phrase that actually
              answers it. This is the headline.
**context**   how many tokens you put in the window to get there. This is the other half,
              and on a small corpus it is the only half that is hard.
**files**     whether the right document came back. Kept as a diagnostic, not a score.

A lexical search over whole documents answers every scoreable query on a corpus this size —
and spends about 2,200 tokens a query doing it, because it returns five entire documents.
"Did the right file come back" is therefore not a measurement of anything. "Did the answer
come back, and what did it cost" is.

Only `easy` and `hard` count toward the headline. The three `unreachable` queries are
reported separately and are expected to fail: they are what Module 3 is for.

Stdlib only.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys

def flatten(text: str) -> str:
    """Collapse whitespace and drop markdown emphasis.

    Anchors are phrases from prose, and prose in these documents is hard-wrapped and often
    partly bolded. Matching the raw text reports a miss for a phrase that is plainly there.
    """
    return " ".join(re.sub(r"[*_`]", "", text).split()).lower()


SCOREABLE = ("easy", "hard")


def load_golden(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for number, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                rows.append(json.loads(line))
            except ValueError as exc:
                sys.exit(f"{path}:{number} is not valid JSON: {exc}")
    return rows


def load_retriever(path: str):
    if not os.path.exists(path):
        sys.exit(f"no retriever at {path}. Build one that exposes "
                 f"search(query, k) -> list of dicts with a 'source' each.")
    spec = importlib.util.spec_from_file_location("lab_retriever", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                      # noqa: BLE001 - report, do not crash
        sys.exit(f"{path} could not be imported: {type(exc).__name__}: {exc}")
    if not hasattr(module, "search"):
        sys.exit(f"{path} has no search() function. The contract is "
                 f"search(query: str, k: int = 5) -> list[dict].")
    return module


def normalise(results, root: str) -> list[str]:
    """Pull an ordered, de-duplicated list of source paths out of whatever came back."""
    sources = []
    for item in results or []:
        if isinstance(item, dict):
            source = item.get("source") or item.get("path") or item.get("file")
        else:
            source = getattr(item, "source", None)
        if not source:
            continue
        source = os.path.normpath(str(source))
        if os.path.isabs(source):
            source = os.path.relpath(source, root)
        if source not in sources:
            sources.append(source)
    return sources


def score_query(entry: dict, retrieved: list[str], text: str) -> dict:
    """Answered if the anchor is in the retrieved text. Files are a diagnostic only.

    `forbid` is the exception, and it exists because of one specific failure: when a corpus
    holds a superseded document beside its replacement, the anchor from the current version
    is in the retrieved text either way — so an anchor-only check calls it answered while the
    retired version sits ABOVE it in the results. Retrieving both is not a partial success
    here; it is contradictory evidence, and measured, the stale one ranks first. A query that
    names a forbidden source is answered only if that source stayed out.
    """
    want = [os.path.normpath(e) for e in entry.get("expect") or []]
    found = [e for e in want if e in retrieved]
    ranks = [retrieved.index(e) + 1 for e in want if e in retrieved]
    anchor = entry.get("anchor")
    answered = bool(anchor) and flatten(anchor) in flatten(text)
    forbid = [os.path.normpath(e) for e in entry.get("forbid") or []]
    leaked = [e for e in forbid if e in retrieved]
    if leaked:
        answered = False
    return {
        "answered": answered,
        "recall": len(found) / len(want) if want else None,
        "hit": bool(found),
        "rr": 1.0 / min(ranks) if ranks else 0.0,
        "found": found,
        "missed": [e for e in want if e not in retrieved],
        "leaked": leaked,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--retriever", default="rag/retrieve.py")
    ap.add_argument("--golden", default=None)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--label", default=None, help="what changed since the last run")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--no-record", action="store_true",
                    help="do not add a row to the scoreboard")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    # The participant's retrieve.py resolves the project through CLAUDE_PROJECT_DIR or the
    # cwd. This harness may be invoked from anywhere — by the full suite, or by a gate — so
    # --root has to be authoritative before their module is imported, or a working retriever
    # reports nothing found.
    os.environ["CLAUDE_PROJECT_DIR"] = root
    golden_path = args.golden or os.path.join(root, "evals", "retrieval", "golden.jsonl")
    if not os.path.exists(golden_path):
        sys.exit(f"no golden set at {os.path.relpath(golden_path, root)}")

    golden = load_golden(golden_path)
    retriever = load_retriever(os.path.join(root, args.retriever)
                               if not os.path.isabs(args.retriever) else args.retriever)

    rows, failures = [], []
    for entry in golden:
        # A query may name filters. Before the metadata step those change nothing, which is
        # exactly the point: the row scores 0 until the metadata is real and search_filtered
        # honours it.
        filters = entry.get("filters") or {}
        try:
            if filters and hasattr(retriever, "search_filtered"):
                results = retriever.search_filtered(entry["q"], args.k, **filters)
            else:
                results = retriever.search(entry["q"], args.k)
        except Exception as exc:                  # noqa: BLE001
            failures.append(f"{entry['id']}: search() raised {type(exc).__name__}: {exc}")
            results = []
        retrieved = normalise(results, root)
        text = "\n".join(str((r or {}).get("text") or "") for r in (results or [])
                         if isinstance(r, dict))
        chars = len(text)
        scored = score_query(entry, retrieved, text)
        rows.append({"id": entry["id"], "tier": entry.get("tier"), "q": entry["q"],
                     "retrieved": retrieved, "chars": chars,
                     "tokens": round(chars / 4), **scored})

    def summarise(tiers) -> dict:
        chosen = [r for r in rows if r["tier"] in tiers]
        if not chosen:
            return {"queries": 0, "answered": 0, "recall": 0.0, "mrr": 0.0,
                    "files_hit": 0, "mean_tokens": 0, "per_1k_tokens": 0.0,
                    "tokens_per_answer": None}
        scoreable = [r for r in chosen if r["recall"] is not None]
        return {
            "queries": len(chosen),
            "answered": sum(1 for r in chosen if r["answered"]),
            "files_hit": sum(1 for r in chosen if r["hit"]),
            "recall": round(sum(r["recall"] for r in scoreable) / len(scoreable), 3)
                      if scoreable else 0.0,
            "mrr": round(sum(r["rr"] for r in chosen) / len(chosen), 3),
            "mean_tokens": round(sum(r["tokens"] for r in chosen) / len(chosen)),
            # the trade-off in one number: answers bought per thousand tokens spent
            "per_1k_tokens": round(
                sum(1 for r in chosen if r["answered"])
                / max(sum(r["tokens"] for r in chosen) / 1000, 0.001), 1),
            # the same ratio the other way up, which is the one worth saying out loud:
            # "this retriever costs 2,300 tokens for every question it answers"
            "tokens_per_answer": (
                round(sum(r["tokens"] for r in chosen)
                      / sum(1 for r in chosen if r["answered"]))
                if any(r["answered"] for r in chosen) else None),
        }

    headline = summarise(SCOREABLE)
    payload = {
        "label": args.label or "unlabelled",
        "retriever": args.retriever,
        "k": args.k,
        "headline": headline,
        "by_tier": {t: summarise((t,))
                    for t in ("easy", "hard", "filtered", "unreachable")},
        "unreachable_passing": [r["id"] for r in rows
                                if r["tier"] == "unreachable" and r["hit"]],
        "failures": failures,
        "queries": rows,
    }

    if not args.no_record:
        record(root, payload)

    if args.as_json:
        print(json.dumps(payload, indent=2))
    else:
        render(payload)
    return 0


def record(root: str, payload: dict) -> None:
    """Append one row to the scoreboard in .agent-lab/state.json."""
    state_file = os.path.join(root, ".agent-lab", "state.json")
    if not os.path.exists(state_file):
        return
    try:
        with open(state_file) as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        return
    from datetime import datetime, timezone
    head = payload["headline"]
    state.setdefault("eval_history", []).append({
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "label": payload["label"],
        "score": f"{head['answered']}/{head['queries']} answered",
        "answered": head["answered"],
        "mean_tokens": head["mean_tokens"],
        "per_1k_tokens": head["per_1k_tokens"],
        "tokens_per_answer": head.get("tokens_per_answer"),
        "files_hit": head["files_hit"],
        "filtered": (lambda f: f"{f['answered']}/{f['queries']}" if f["queries"] else None)(
            payload["by_tier"]["filtered"]),
        "mrr": head["mrr"],
        "k": payload["k"],
        "retriever": payload["retriever"],
    })
    tmp = state_file + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, state_file)


def render(payload: dict) -> None:
    head = payload["headline"]
    title = f"RETRIEVAL — {payload['label']}"
    print(title)
    print("=" * len(title))
    cost = (f"{head['tokens_per_answer']:,} tokens per answer"
            if head.get("tokens_per_answer") else "no answers to price")
    print(f"\n  {head['answered']}/{head['queries']} answered"
          f"   {head['mean_tokens']:,} tokens per query"
          f"   {cost}"
          f"   MRR {head['mrr']}\n")
    print(f"  {'':12} {'answered':>9}  {'tokens':>7}  {'right file':>10}")
    for tier in ("easy", "hard"):
        t = payload["by_tier"][tier]
        print(f"  {tier:<12} {t['answered']:>4}/{t['queries']:<4} {t['mean_tokens']:>7,}"
              f"  {t['files_hit']:>6}/{t['queries']}")
    f = payload["by_tier"]["filtered"]
    if f["queries"]:
        print(f"  {'filtered':<12} {f['answered']:>4}/{f['queries']:<4} {f['mean_tokens']:>7,}"
              f"  {f['files_hit']:>6}/{f['queries']}   not counted — needs metadata")
    u = payload["by_tier"]["unreachable"]
    print(f"  {'unreachable':<12} {u['answered']:>4}/{u['queries']:<4} {u['mean_tokens']:>7,}"
          f"  {u['files_hit']:>6}/{u['queries']}   not counted — Module 3")

    leaks = [r for r in payload["queries"] if r.get("leaked")]
    if leaks:
        print("\n  Retrieved a document that contradicts the answer:")
        for r in leaks:
            print(f"    {r['id']} [{r['tier']}]  {r['q'][:58]}")
            print(f"           returned {', '.join(r['leaked'])}, which is superseded")

    unanswered = [r for r in payload["queries"]
                  if r["tier"] in SCOREABLE and not r["answered"]]
    if unanswered:
        print(f"\n  Did not retrieve the answer for {len(unanswered)}:")
        for r in unanswered:
            note = "right file, wrong passage" if r["hit"] else "wrong file entirely"
            print(f"    {r['id']} [{r['tier']}]  {r['q'][:58]}")
            print(f"           {note}")
    if payload["unreachable_passing"]:
        print(f"\n  Interesting: {', '.join(payload['unreachable_passing'])} "
              f"retrieved a useful document despite being marked unreachable. "
              f"Retrieving the document is not the same as answering the question — check "
              f"whether it could actually answer it.")
    if payload["failures"]:
        print("\n  search() errored on:")
        for f in payload["failures"]:
            print(f"    {f}")
    print()


if __name__ == "__main__":
    sys.exit(main())
