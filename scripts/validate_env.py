#!/usr/bin/env python3
"""Validate Mission Control environment isolation safety."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REQUIRED_LIVE_VALUES = {
    "COMPOSE_PROJECT_NAME": "missioncontrol-live",
    "ENVIRONMENT": "production",
    "POSTGRES_DB": "missioncontrol_live",
    "POSTGRES_USER": "missioncontrol_live",
    "BACKEND_CORS_ORIGINS": "https://missioncontrol.optihosting.co.za",
}

REQUIRED_DEV_VALUES = {
    "COMPOSE_PROJECT_NAME": "missioncontrol-dev",
    "ENVIRONMENT": "development",
    "POSTGRES_DB": "missioncontrol_dev",
    "POSTGRES_USER": "missioncontrol_dev",
}


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def check(env: str, values: dict[str, str]) -> list[dict]:
    findings = []
    for key, expected in values.items():
        actual = values.get(key, "")
        findings.append(
            {
                "env": env,
                "key": key,
                "expected": expected,
                "actual": actual,
                "pass": actual == expected,
            }
        )
    return findings


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    dev_env_path = root / ".env.dev"
    live_env_path = root / ".env.production"

    dev_env = load_env(dev_env_path)
    live_env = load_env(live_env_path)

    findings = check("DEV", dev_env) + check("LIVE", live_env)

    if not dev_env:
        print("DEV env missing: .env.dev")
    if not live_env:
        print("LIVE env missing: .env.production")

    failed = [f for f in findings if not f["pass"]]
    for f in findings:
        status = "PASS" if f["pass"] else "FAIL"
        print(f"{f['env']} {f['key']}: {status}")
        if not f["pass"]:
            print(f"  expected={f['expected']}")
            print(f"  actual={f['actual']}")

    report = {
        "dev": {
            "env_file": str((root / ".env.dev").exists()),
            "values": dev_env,
            "findings": [f for f in findings if f["env"] == "DEV"],
        },
        "live": {
            "env_file": str((root / ".env.production").exists()),
            "values": live_env,
            "findings": [f for f in findings if f["env"] == "LIVE"],
        },
    }

    report_path = root / "reports" / "env-validation.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2))

    print(f"\nReport: {report_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
