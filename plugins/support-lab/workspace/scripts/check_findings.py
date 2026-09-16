#!/usr/bin/env python3
"""Checks a findings sheet against the done-when rules.  Usage: python3 scripts/check_findings.py tickets/JIRA-4821/findings.md
Exit 0 = passes, 1 = fails (reasons printed). This is the external condition the skill's done-when refers to."""
import re, sys
if len(sys.argv) < 2:
    print(__doc__); sys.exit(2)
text = open(sys.argv[1], encoding="utf-8").read()
problems = []
hyps = re.findall(r"^\s*[-*]?\s*H(\d+)\b(.*)$", text, re.M)
if not hyps:
    problems.append("no hypotheses found (lines starting with H1, H2, ...)")
for n, rest in hyps:
    if "UNVERIFIED" in rest:
        continue
    if re.search(r"(VERIFIED|RULED OUT|PARTIAL|LEADING)", rest) and re.search(r"evidence\s*:", rest, re.I):
        continue
    problems.append(f"H{n}: must be UNVERIFIED, or carry a status with 'evidence:' (a log line, a query result, a config-audit entry)")
for section in ("Observed", "Expected", "Timeline", "Remediation", "Escalation"):
    if not re.search(rf"^#+\s*{section}", text, re.M):
        problems.append(f"missing section: {section}")
if not re.search(r"deploys\.log|deploy", text, re.I):
    problems.append("timeline never mentions the deploy log (ops/deploys.log)")
if not re.search(r"docs/", text):
    problems.append("no documentation page is quoted by path (docs/...)")
if re.search(r"^#+\s*Escalation", text, re.M) and not re.search(r"Escalation[^\n]*\n+\s*(YES|NO)", text):
    problems.append("Escalation section must start with YES or NO")
if problems:
    print("FAIL — findings do not meet done-when:")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("PASS — every hypothesis has evidence or is marked UNVERIFIED; timeline, docs quote, remediation and escalation present.")
