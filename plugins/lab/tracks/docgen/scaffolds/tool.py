#!/usr/bin/env python3
"""tools/{{TOOL_NAME}}.py

{{TOOL_PURPOSE}}

Run it:

    {{TOOL_COMMAND}}
    python3 tools/{{TOOL_NAME}}.py --selftest

Two rules for a tool, and they are the reason this is a tool and not a skill:

  1. **Same input, same output.** No judgement, no summarising, no "it depends".
  2. **Structured output.** JSON, because the next thing to read it is a program, not a
     person. Print nothing else to stdout.

The argument handling and the JSON printing are done. What is missing is the part that
matters: getting the facts out, and proving you got them right.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCES = os.path.join(ROOT, "data", "sources")


def add_arguments(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--month", default="2026-08", help="e.g. 2026-08")


def collect(args) -> dict:
    """Return the reportable facts for the month, each with where it came from.

    Your output must contain these keys, because your skill is going to rely on them:
    month, milestones, risks, metrics, sources

    TODO — the extraction. The status updates are the structured source; the sync notes
    carry the reasons; the metrics file is the only place the counts exist.

    Three decisions worth making deliberately rather than by accident:

      * **provenance**: house style says every claim carries a source. A fact without a
        file and line is not traceable, so what does each extracted fact carry with it?
      * **slips**: a date that moved must end up in the report as "old -> new", not just
        the new one. Where do you detect that — here, or later in the writing?
      * **what is wrong with the data**: an unowned project, or a status value outside the
        five house-style values, is worth surfacing rather than silently passing through.
    """
    raise NotImplementedError("TODO: extract the facts")


def selftest() -> int:
    """A tool can be tested. That is most of why it is a tool.

    Add one check per fact you are certain of. When your tool later breaks, these tell you
    *what* broke, which a prompt never can. This is also your first eval — Module 4 is
    largely this idea, scaled up.
    """
    checks, failures = 0, []

    def expect(label: str, ok: bool) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    # TODO — at least three checks. One of them must be this one:
    # expect("same input, same output", collect(...) == collect(...))

    for f in failures:
        print(f"FAIL: {f}", file=sys.stderr)
    print(f"{checks - len(failures)}/{checks} checks passed")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_arguments(ap)
    ap.add_argument("--selftest", action="store_true", help="check the tool against known facts")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    print(json.dumps(collect(args), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
