#!/usr/bin/env python3
"""
Mission Control RC1 Validation Script

Run from the command line to validate Community Edition RC1:
    python scripts/validate_rc1.py

Sprint 3.12.0 — RC1 Stabilization.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.rc1.certification import generate_rc1_report


def main() -> int:
    print("=" * 70)
    print("  Mission Control Community Edition v1.0 — RC1 Validation")
    print("=" * 70)
    print()

    reports_dir = Path(__file__).parent.parent / "reports"
    result = generate_rc1_report(str(reports_dir))

    print(f"Certified: {'YES' if result['certified'] else 'NO'}")
    print(f"Total Pass: {result['summary']['total_pass']}")
    print(f"Total Fail: {result['summary']['total_fail']}")
    print(f"Total Warn: {result['summary']['total_warn']}")
    print()
    print("Reports generated:")
    for path in result["reports"]:
        print(f"  - {path}")
    print()

    if result["certified"]:
        print("RC1 CERTIFICATION: PASSED")
    else:
        print("RC1 CERTIFICATION: FAILED — fix issues before release")

    return 0 if result["certified"] else 1


if __name__ == "__main__":
    sys.exit(main())
