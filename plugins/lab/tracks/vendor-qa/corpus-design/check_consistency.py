#!/usr/bin/env python3
"""Cross-check the vendor-qa corpus against itself.

The contract is amended twice and each milestone is judged against a different version of
it. Stating the wrong resolution term in a findings pack is a one-character mistake that
makes the temporal question in Modules 2 and 3 unanswerable, so the dates are checked here
rather than by eye.

    python3 corpus-design/check_consistency.py [--verbose]

Stdlib only. Exit 1 on any contradiction.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "workspace", "data")

A1 = date(2026, 6, 30)          # S2 resolution 2 -> 3 business days
A2 = date(2026, 8, 15)          # clause 5.4, machine-readable API definition

MILESTONES = {
    "M1": {"submitted": date(2026, 3, 6), "issued": date(2026, 3, 18),
           "decided": date(2026, 3, 27), "findings": 2, "open": 0},
    "M2": {"submitted": date(2026, 5, 8), "issued": date(2026, 5, 22),
           "decided": date(2026, 6, 2), "findings": 5, "open": 1},
    "M3": {"submitted": date(2026, 9, 1), "issued": None,
           "decided": None, "findings": 0, "open": 0},
}

problems: list[str] = []
notes: list[str] = []
checked = 0


def ok(cond: bool, label: str, detail: str = "", verbose: bool = False) -> None:
    global checked
    checked += 1
    if cond:
        if verbose:
            print(f"  pass  {label}")
    else:
        problems.append(label + (f" — {detail}" if detail else ""))


def read(rel: str) -> str:
    path = os.path.join(DATA, rel)
    return open(path, encoding="utf-8").read() if os.path.exists(path) else ""


def says(text: str, phrase: str) -> bool:
    return " ".join(phrase.split()).lower() in " ".join(text.split()).lower()


def s2_term(submitted: date) -> int:
    """The Severity 2 resolution term in business days, for a milestone submitted then."""
    return 3 if submitted >= A1 else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    v = ap.parse_args().verbose

    ok(os.path.isdir(DATA), "the data directory exists", DATA, verbose=v)
    if not os.path.isdir(DATA):
        report()
        return 1

    # 1. the amendment log owns the dates; the MSA must point at it and carry 5.4
    amend = read("contract/MSA-amendments.md")
    ok(says(amend, "Amendment 1 — effective 2026-06-30"),
       "the amendment log dates A1", verbose=v)
    ok(says(amend, "Amendment 2 — effective 2026-08-15"),
       "the amendment log dates A2", verbose=v)
    ok(says(amend, "resolved within 2 business days") and
       says(amend, "resolved within 3 business days"),
       "the amendment log records both S2 terms", verbose=v)
    msa = read("contract/MSA-excerpt.md")
    ok(says(msa, "MSA-amendments.md"), "the MSA points at the amendment log", verbose=v)
    ok(says(msa, "5.4"), "the MSA carries clause 5.4", verbose=v)
    ok(says(msa, "machine-readable API definition"),
       "clause 5.4 states the machine-readable requirement", verbose=v)

    # 2. every S2 finding must state the term in force when it was issued
    for ref, info in MILESTONES.items():
        if info["issued"] is None:
            continue
        pack = read(f"history/findings-{ref}.md")
        ok(bool(pack), f"{ref}: findings pack exists", verbose=v)
        expected = s2_term(info["submitted"])
        wrong = s2_term(info["submitted"]) == 2 and 3 or 2
        blocks = re.split(r"^## FINDING ", pack, flags=re.M)[1:]
        for block in blocks:
            fref = block.split()[0]
            sev = re.search(r"\*\*Severity:\*\*\s*(\d)", block)
            if not sev or sev.group(1) != "2":
                continue
            ok(says(block, f"{expected} business days"),
               f"{fref}: S2 term matches the MSA in force at submission",
               f"expected {expected} business days for {ref}", verbose=v)
            ok(not says(block, f"{wrong} business days"),
               f"{fref}: does not quote the other milestone's S2 term", verbose=v)

    # 3. the worked example is a real M2 finding, so it must use M2's term
    example = read("examples/findings-pack-example.md")
    ok(says(example, "2 business days"),
       "the worked example uses the term in force on 2026-05-22", verbose=v)
    ok(not says(example, "3 business days"),
       "the worked example does not quote the post-amendment term",
       "a participant copying it onto M3 would then be right by accident", verbose=v)
    ok(says(example, "term changed on 2026-06-30"),
       "the worked example warns that the term later changed", verbose=v)

    # 4. the acceptance log must agree with the findings packs
    log = read("history/acceptance-log.md")
    for ref, info in MILESTONES.items():
        pack = read(f"history/findings-{ref}.md")
        actual = len(re.findall(r"^## FINDING ", pack, flags=re.M))
        ok(actual == info["findings"], f"{ref}: findings pack has {info['findings']} findings",
           f"found {actual}", verbose=v)
        row = re.search(rf"^\|\s*{ref}\b.*$", log, re.M)
        ok(row is not None, f"{ref}: appears in the acceptance log", verbose=v)
        open_now = len(re.findall(r"\*\*Status:\*\*\s*\*\*Open", pack))
        ok(open_now == info["open"], f"{ref}: open findings count",
           f"pack shows {open_now}, expected {info['open']}", verbose=v)

    # 5. VQ-M2-003 must be open, disputed, and carried into M3 in all three places
    m2 = read("history/findings-M2.md")
    resp = read("history/vendor-response-M2.md")
    ok(says(m2, "VQ-M2-003") and says(m2, "Open"),
       "VQ-M2-003 is open in the M2 pack", verbose=v)
    ok(says(resp, "We do not accept this finding"),
       "the vendor response disputes VQ-M2-003", verbose=v)
    ok(says(log, "VQ-M2-003") and says(log, "4.3"),
       "the acceptance log ties VQ-M2-003 to the escalation clause", verbose=v)

    # 6. the planted coverage gap must stay a gap
    reg = read("requirements-register.md")
    r11 = re.search(r"^\|\s*R-11\b.*$", reg, re.M)
    ok(r11 is not None, "R-11 is in the requirements register", verbose=v)
    if r11:
        ok("AC-" not in r11.group(0),
           "R-11 has no verifying criterion",
           "if an AC covers it, the coverage-gap exercise disappears", verbose=v)
    sow3 = read("contract/SOW-milestone-3.md")
    ok(not says(sow3, "machine-readable"),
       "the M3 SOW criteria do not mention the 5.4 requirement",
       "the gap exists because the SOW predates the amendment", verbose=v)

    # 7. no machine-readable definition may be submitted, or the 5.4 finding evaporates
    deliverables = os.path.join(DATA, "deliverables")
    files = sorted(os.listdir(deliverables)) if os.path.isdir(deliverables) else []
    ok(len(files) >= 4, "there are at least four M3 deliverables", str(files), verbose=v)
    ok(not any(f.endswith((".yaml", ".yml", ".json")) for f in files),
       "no machine-readable API definition is present", str(files), verbose=v)

    # 8. the planted severity-1 evidence must still be findable
    spec = read("deliverables/M3-api-spec.md")
    report_doc = read("deliverables/M3-test-report.md")
    ok("client_secret" in spec, "the credential is still in the specification", verbose=v)
    ok("cardholder" in report_doc, "the production personal data is still in the evidence",
       verbose=v)
    ok(not re.search(r"build\s*[`:]?\s*[\w-]*\d", report_doc, re.I),
       "the test report still has no build identifier",
       "that absence is a finding; if a build id appears, the finding goes", verbose=v)

    # 9. the multi-hop halves must stay in separate documents
    ok(says(reg, "AC-3") and says(reg, "AC-4"),
       "the register holds the requirement-to-criterion mapping", verbose=v)
    for rel in ("history/findings-M1.md", "history/findings-M2.md"):
        pack = read(rel)
        ok(not re.search(r"\bR-\d+\b", pack),
           f"{rel} does not name requirements",
           "if findings map straight to requirements, the multi-hop question collapses",
           verbose=v)

    # 10. every criterion cited in a findings pack must exist in that milestone's SOW
    for ref in ("M1", "M2"):
        pack = read(f"history/findings-{ref}.md")
        sow = read(f"contract/SOW-milestone-{ref[-1]}.md") + read("contract/SOW-milestone-3.md")
        for ac in sorted(set(re.findall(r"AC-\d+(?:\s*\(M\d\))?", pack))):
            ok(says(sow, ac.split("(")[0].strip()),
               f"{ref}: {ac} exists in a statement of work", verbose=v)

    report()
    return 1 if problems else 0


def report() -> None:
    print()
    for n in notes:
        print(f"  ! {n}")
    if problems:
        print(f"CONTRADICTIONS — {len(problems)} of {checked} checks failed:")
        for p in problems:
            print(f"  x {p}")
    else:
        print(f"CONSISTENT — {checked} checks passed")


if __name__ == "__main__":
    sys.exit(main())
