#!/usr/bin/env python3
"""
NPM Audit Security Gate.
Audits npm dependencies and enforces fail-closed vulnerability checking.
Permits only specifically documented accepted risks from docs/security/ACCEPTED_RISKS.md.
"""

import json
import subprocess
import sys
from pathlib import Path

ACCEPTED_ADVISORIES = {
    "GHSA-v3m3-f69x-jf25",  # Quill HTML export XSS (quill 2.0.2 / 2.0.3)
    "GHSA-fx2h-pf6j-xcff",  # Vite server.fs.deny bypass on Windows alternate paths (vite 5.4.21 devDependency)
}


def main() -> int:
    print("=== Running NPM Dependency Security Audit Gate ===")
    root_dir = Path(__file__).resolve().parent.parent

    # Run npm audit --json
    try:
        proc = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        data = json.loads(proc.stdout or "{}")
    except Exception as exc:
        print(f"ERROR: Failed to run npm audit: {exc}", file=sys.stderr)
        return 1

    vulnerabilities = data.get("vulnerabilities", {})
    if not vulnerabilities:
        print("PASS: No npm vulnerabilities detected.")
        return 0

    unaccepted_violations = []
    accepted_found = []

    for name, info in vulnerabilities.items():
        severity = info.get("severity", "unknown").lower()
        via_list = info.get("via", [])

        for via in via_list:
            if isinstance(via, dict):
                adv_url = via.get("url", "")
                adv_id = adv_url.split("/")[-1] if "/" in adv_url else via.get("title", "")
                sev = via.get("severity", severity).lower()

                if adv_id in ACCEPTED_ADVISORIES or any(
                    acc in adv_url for acc in ACCEPTED_ADVISORIES
                ):
                    accepted_found.append((name, adv_id, sev))
                elif sev in ("high", "critical"):
                    unaccepted_violations.append(
                        (name, adv_id or "UNKNOWN", sev, via.get("title", ""))
                    )
            elif isinstance(via, str):
                pass

    if accepted_found:
        print(
            f"INFO: Permitted {len(accepted_found)} accepted risk(s) documented in docs/security/ACCEPTED_RISKS.md:"
        )
        for pkg, adv, sev in accepted_found:
            print(f"  - Package: {pkg} | Advisory: {adv} | Severity: {sev}")

    if unaccepted_violations:
        print(
            f"FAIL: Detected {len(unaccepted_violations)} unaccepted high/critical vulnerability/vulnerabilities:",
            file=sys.stderr,
        )
        for pkg, adv, sev, title in unaccepted_violations:
            print(
                f"  - [FAIL] Package: {pkg} | Severity: {sev.upper()} | Advisory: {adv} | {title}",
                file=sys.stderr,
            )
        return 1

    print("PASS: NPM Security Audit Gate Passed (0 unaccepted high/critical vulnerabilities).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
