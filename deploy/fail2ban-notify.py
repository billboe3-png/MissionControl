#!/usr/bin/env python3
"""Monitor fail2ban SSH bans and print new bans with IP + country."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

from maxminddb import open_database

DB_PATH = "/usr/share/GeoIP/GeoLite2-Country.mmdb"
STATE_FILE = "/tmp/fail2ban_notified.json"


def load_state() -> set[str]:
    try:
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_state(state: set[str]) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(state), f)


def get_banned_ips() -> list[str]:
    try:
        out = subprocess.check_output(
            ["sudo", "fail2ban-client", "banned", "sshd"],
            text=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        print("fail2ban-client error:", e.output, file=sys.stderr)
        return []
    try:
        data = json.loads(out)
        if isinstance(data, list):
            return [ip for ip in data if ip]
    except json.JSONDecodeError:
        pass
    return []


def country_for(ip: str) -> str:
    try:
        with open_database(DB_PATH) as reader:
            result = reader.get(ip)
        cc = ((result or {}).get("country") or {}).get("iso_code")
        return cc or "Unknown"
    except Exception:
        return "Unknown"


def main() -> int:
    banned = get_banned_ips()
    if not banned:
        return 0

    seen = load_state()
    new = [ip for ip in banned if ip not in seen]
    if not new:
        return 0

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"fail2ban SSH ban @ {now}"]
    for ip in new:
        cc = country_for(ip)
        lines.append(f"{ip} — {cc}")
    print("\n".join(lines))

    seen.update(new)
    save_state(seen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
