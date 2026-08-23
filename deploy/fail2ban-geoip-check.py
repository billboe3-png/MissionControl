#!/usr/bin/env python3
"""Fail2ban GeoIP pre-check: prints 'ban' or 'ignore' for an IP."""
import sys
import os
from maxminddb import open_database

DB_PATH = os.environ.get("F2B_GEOIP_DB", "/usr/share/GeoIP/GeoLite2-Country.mmdb")
ALLOWED = set((os.environ.get("F2B_ALLOWED_COUNTRIES") or "ZA").split(","))

ip = sys.argv[1] if len(sys.argv) > 1 else None
if not ip:
    print("ignore")
    sys.exit(0)

try:
    with open_database(DB_PATH) as reader:
        result = reader.get(ip)
    cc = ((result or {}).get("country") or {}).get("iso_code")
    print("ban" if cc not in ALLOWED else "ignore")
except Exception:
    # on lookup failure: safer to ban than miss a real attacker
    print("ban")
