#!/usr/bin/env python3
"""Validate a participant's ontology before they extract a graph against it.

The ontology is a design artifact, so this checks design properties, not spelling: that it
was derived from questions, that it is the right size, that time is modelled where the
questions need it, and that direction was thought about. A bad ontology does not fail
loudly later — it produces a tidy graph that answers the wrong question.

    check_ontology.py              validate ontology/*.yaml in the project
    check_ontology.py --json       machine-readable
"""

from __future__ import annotations

import argparse
import json
import os
import sys

SHAPES = {"multi-hop", "aggregation", "temporal"}
MIN_TYPES, MAX_TYPES = 6, 10
MIN_RELATIONS, MAX_RELATIONS = 8, 12


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    problems: list[str] = []
    notes: list[str] = []

    folder = os.path.join(root, "ontology")
    files = sorted(f for f in os.listdir(folder)
                   if f.endswith((".yaml", ".yml"))) if os.path.isdir(folder) else []
    if not files:
        report({}, ["no ontology/*.yaml yet — step 3.1 is where this comes from"], [],
               args.as_json)
        return 1
    if len(files) > 1:
        notes.append(f"{len(files)} ontology files; only {files[0]} will be compiled")

    path = os.path.join(folder, files[0])
    raw = open(path, encoding="utf-8").read()
    try:
        import yaml
    except ImportError:
        report({}, ["pyyaml is not installed for this interpreter — "
                    "this module's setup step installs it"], [], args.as_json)
        return 1
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        report({}, [f"{files[0]} is not valid YAML: {str(exc)[:200]}"], [], args.as_json)
        return 1

    if "TODO" in raw:
        problems.append(f"{raw.count('TODO')} TODO left in the ontology")

    types = data.get("types") or {}
    relations = data.get("relations") or []
    cqs = data.get("competency_questions") or []

    # --- derived from questions, which is the whole method
    if not cqs:
        problems.append("no competency_questions. The ontology is supposed to be derived "
                        "from the questions you must answer — without them there is no way "
                        "to tell whether a type earns its place")
    else:
        if len(cqs) < 3:
            problems.append(f"{len(cqs)} competency questions; the module starts from the "
                            f"three questions retrieval could not answer")
        shapes = {c.get("shape") for c in cqs}
        missing = SHAPES - shapes
        if missing:
            problems.append(f"no competency question of shape {', '.join(sorted(missing))} "
                            f"— those are the failure classes this module exists for")
        for cq in cqs:
            if not cq.get("q"):
                problems.append(f"a competency question has no `q`: {json.dumps(cq)[:70]}")
            if not cq.get("needs"):
                notes.append(f"{cq.get('id', '?')}: no `needs` — writing down the traversal "
                             f"is how you find out which relations you are missing")

    # --- the right size. Too small answers nothing; too large is a data model, not an ontology
    if not types:
        problems.append("no types declared")
    elif len(types) < MIN_TYPES:
        problems.append(f"{len(types)} types. Fewer than {MIN_TYPES} usually means a "
                        f"competency question has nowhere to land — check each one is "
                        f"traversable")
    elif len(types) > MAX_TYPES:
        problems.append(f"{len(types)} types. More than {MAX_TYPES} in a two-hour module "
                        f"means you are modelling the data rather than the questions. Drop "
                        f"anything no competency question traverses")
    if not relations:
        problems.append("no relations declared — types alone are a taxonomy, not a graph")
    elif not MIN_RELATIONS <= len(relations) <= MAX_RELATIONS:
        problems.append(f"{len(relations)} relations; aim for "
                        f"{MIN_RELATIONS}-{MAX_RELATIONS}")

    # --- every relation has to be a readable sentence between declared types
    seen = set()
    for rel in relations:
        name = rel.get("name")
        if not name:
            problems.append(f"a relation has no name: {json.dumps(rel)[:70]}")
            continue
        if name in seen:
            problems.append(f"relation {name!r} is declared twice")
        seen.add(name)
        for end in ("from", "to"):
            if not rel.get(end):
                problems.append(f"{name}: no `{end}` type — a relation with an open end "
                                f"cannot be validated or traversed")
            elif rel[end] not in types:
                problems.append(f"{name}: `{end}: {rel[end]}` is not a declared type")
        if not rel.get("cardinality"):
            notes.append(f"{name}: no cardinality. It is how the compiler catches two "
                         f"values where there should be one")

    # --- time. The temporal competency question needs at least one temporal relation.
    temporal = [r.get("name") for r in relations if r.get("temporal")]
    if any(c.get("shape") == "temporal" for c in cqs) and not temporal:
        problems.append("a temporal competency question is declared but no relation is "
                        "marked `temporal: true`. Whatever changes over time has to be "
                        "modelled as changing, or the as-of answer is whatever happens to "
                        "be in the row")
    if len(temporal) > len(relations) / 2:
        notes.append(f"{len(temporal)} of {len(relations)} relations are temporal; that is "
                     f"a lot of bookkeeping — check each one really changes")

    # --- a type nothing points at and that points at nothing is decoration
    touched = {r.get("from") for r in relations} | {r.get("to") for r in relations}
    for orphan in sorted(set(types) - touched):
        problems.append(f"type {orphan!r} appears in no relation — it cannot be reached or "
                        f"traversed, so nothing can be asked about it")

    if not data.get("not_modelled"):
        notes.append("no `not_modelled` section. Naming what you left out, and why, is the "
                     "part of this that survives contact with the next question")

    summary = {"file": files[0], "types": len(types), "relations": len(relations),
               "competency_questions": len(cqs), "temporal": temporal}
    report(summary, problems, notes, args.as_json)
    return 1 if problems else 0


def report(summary: dict, problems: list[str], notes: list[str], as_json: bool) -> None:
    if as_json:
        print(json.dumps({"ok": not problems, "problems": problems, "notes": notes,
                          **summary}, indent=2))
        return
    print("ONTOLOGY CHECK")
    print("==============")
    if summary:
        print(f"\n  {summary['file']}: {summary['types']} types, "
              f"{summary['relations']} relations, "
              f"{summary['competency_questions']} competency questions")
        if summary.get("temporal"):
            print(f"  temporal: {', '.join(summary['temporal'])}")
    if problems:
        print("\nNOT READY:")
        for item in problems:
            print(f"  x {item}")
    else:
        print("\nReady — derived from questions, the right size, and time is modelled.")
    if notes:
        print("\nWorth improving (not blocking):")
        for item in notes:
            print(f"  ! {item}")


if __name__ == "__main__":
    sys.exit(main())
