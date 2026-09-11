#!/usr/bin/env python3
"""Scan the submitted deliverables for the facts you must not get wrong by eye.

Credentials and production personal data are Severity 1 under the MSA, and they are exactly
what a reviewer skims past at four in the afternoon. A regex does not skim. The rest of the
scan collects the structural facts the acceptance criteria ask about.

    python3 tools/deliverable_scan.py
    python3 tools/deliverable_scan.py --dir data/deliverables
    python3 tools/deliverable_scan.py --selftest
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

def project_root() -> str:
    """Where the data lives — the project, not wherever this script happens to sit.

    This matters the moment the tool moves into a plugin. A path computed from __file__
    resolves to the plugin's own directory, and the data is not there. The project is the
    working directory, and hooks and tools are both given CLAUDE_PROJECT_DIR.
    """
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


ROOT = project_root()

SECRET_PATTERNS = [
    ("client_secret", re.compile(r"client_secret\s*=\s*(\S+)", re.I)),
    ("bearer_token", re.compile(r"bearer\s+[A-Za-z0-9._\-]{12,}", re.I)),
    ("api_key", re.compile(r"api[_-]?key\s*[:=]\s*(\S+)", re.I)),
    ("password", re.compile(r"password\s*[:=]\s*(\S+)", re.I)),
]

PII_PATTERNS = [
    ("email_address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
    ("cardholder_name", re.compile(r'"cardholder"\s*:\s*"([^"]+)"', re.I)),
    ("card_last4", re.compile(r'"card_last4"\s*:\s*"?(\d{4})"?', re.I)),
]

# example.com and friends are reserved for documentation and are not production data
PII_ALLOWLIST = re.compile(r"@(example|test|localhost)\.", re.I)


def scan_dir(rel_dir: str) -> dict:
    base = os.path.join(ROOT, rel_dir)
    if not os.path.isdir(base):
        raise SystemExit(f"no such directory: {rel_dir}")

    files, secrets, pii = [], [], []
    endpoints, error_codes = set(), set()
    build_ids, per_endpoint_limits = [], []

    for name in sorted(os.listdir(base)):
        path = os.path.join(base, name)
        if not os.path.isfile(path) or name.startswith("."):
            continue
        rel = f"{rel_dir}/{name}"
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        files.append({"file": rel, "lines": len(lines)})

        for i, line in enumerate(lines, 1):
            for label, pattern in SECRET_PATTERNS:
                match = pattern.search(line)
                if match:
                    secrets.append({"file": rel, "line": i, "kind": label,
                                    "excerpt": line.strip()[:110]})
            for label, pattern in PII_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                if label == "email_address" and PII_ALLOWLIST.search(match.group(0)):
                    continue
                pii.append({"file": rel, "line": i, "kind": label,
                            "excerpt": line.strip()[:110]})

            endpoint = re.search(r"^###?\s+(GET|POST|PUT|PATCH|DELETE)\s+(\S+)", line)
            if endpoint:
                endpoints.add(f"{endpoint.group(1)} {endpoint.group(2)}")
            for code in re.findall(r"^\|\s*(\d{3})\s*\|", line):
                error_codes.add(code)
            if re.search(r"build\s*[`:]?\s*[\w-]*\d", line, re.I):
                build_ids.append({"file": rel, "line": i, "excerpt": line.strip()[:110]})
            if re.search(r"(rate limit|requests per)", line, re.I) and \
                    re.search(r"\d", line):
                per_endpoint_limits.append({"file": rel, "line": i,
                                            "excerpt": line.strip()[:110]})

    return {
        "directory": rel_dir,
        "files": files,
        "secrets": secrets,
        "personal_data": pii,
        "endpoints": sorted(endpoints),
        "error_codes": sorted(error_codes),
        "build_id_mentions": build_ids,
        "quantified_rate_limits": per_endpoint_limits,
        "summary": {
            "files_scanned": len(files),
            "secrets_found": len(secrets),
            "personal_data_found": len(pii),
            "endpoints_documented": len(endpoints),
            "rate_limits_quantified": bool(per_endpoint_limits),
        },
    }


def selftest() -> int:
    checks, failures = 0, []

    def expect(label: str, ok: bool) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    d = scan_dir("data/deliverables")
    expect("both deliverables scanned", d["summary"]["files_scanned"] == 2)
    expect("the client secret is found", any(s["kind"] == "client_secret"
                                            for s in d["secrets"]))
    expect("production personal data is found",
           any(p["kind"] in ("cardholder_name", "card_last4") for p in d["personal_data"]))
    # the allowlist has to be tested directly: the corpus contains no reserved-domain
    # address, so asserting over the scan results would pass without exercising anything
    expect("reserved documentation domains are allowlisted",
           bool(PII_ALLOWLIST.search("someone@example.com"))
           and not PII_ALLOWLIST.search("m.villanueva@example-merchant.co.uk"))
    expect("endpoints were collected", len(d["endpoints"]) >= 4)
    expect("rate limits are not quantified in the deliverable",
           d["summary"]["rate_limits_quantified"] is False)
    expect("same input, same output", scan_dir("data/deliverables") == d)

    for f in failures:
        print(f"FAIL: {f}", file=sys.stderr)
    print(f"{checks - len(failures)}/{checks} checks passed")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan vendor deliverables for hard facts")
    ap.add_argument("--dir", default="data/deliverables")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    print(json.dumps(scan_dir(args.dir), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
