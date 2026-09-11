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

DB = os.path.join(ROOT, "data", "db", "support.db")


def add_arguments(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("account_id", nargs="?", help="e.g. acc-1042")
    ap.add_argument("--as-of", default=None,
                    help="date to judge entitlements against. Think about the default.")
    ap.add_argument("--audit-limit", type=int, default=30)


def collect(args) -> dict:
    """Return one dict with everything a triage needs about this account.

    Your output must contain these keys, because your skill is going to rely on them:
    account, sso_domains, users, entitlements, recent_audit, prior_cases

    TODO — the queries. `data/db/schema.md` has the tables and the two queries that matter.

    Three decisions worth making deliberately rather than by accident:

      * **entitlements**: the table has effective_from / effective_to. Answering "is this
        account entitled" without a date answers a different question than a ticket from
        April is asking. What should --as-of default to, and why?
      * **the audit log**: raw rows, or a count grouped by action and error_code, or both?
        Look at your Step 3 trace and see which one you actually kept asking for.
      * **prior cases**: this is the single fact that changes a triage most often. Do not
        leave it out because it was not in the ticket.
    """
    raise NotImplementedError("TODO: build the snapshot")


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
