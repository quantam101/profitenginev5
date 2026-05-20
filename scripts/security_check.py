from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.security_scanner import scan_repo


def main() -> int:
    findings = scan_repo(".")
    if findings:
        print("Potential secret markers found:")
        for finding in findings:
            print(finding)
        return 1
    print("security-check: no known secret markers found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
