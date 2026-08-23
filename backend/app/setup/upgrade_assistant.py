"""
Mission Control Upgrade Assistant

Detects upgrade readiness by checking database schema,
configuration compatibility, plugin SDK versions, and system requirements.
"""

import contextlib
import shutil
import subprocess
import sys
from pathlib import Path

EXPECTED_SCHEMA_VERSION = "3.0.0"

DEPRECATED_CONFIG_KEYS: dict[str, str] = {}

PLUGIN_DIR_PATTERN = "backend/plugins/*/manifest.json"


class UpgradeAssistant:
    def __init__(self, db=None):
        self.db = db
        self._project_root = Path(__file__).resolve().parents[4]

    def check_all(self) -> dict:
        results = {
            "schema": self.check_schema_version(),
            "config_deprecated": self.check_config_deprecated(),
            "plugin_sdk": self.check_plugin_sdk(),
            "python": self.check_python_version(),
            "docker": self.check_docker_version(),
            "agents": self.check_agent_versions(),
        }

        statuses = [r.get("status", "ok") for r in results.values() if isinstance(r, dict)]
        if "critical" in statuses:
            overall = "critical"
        elif "warning" in statuses:
            overall = "warning"
        else:
            overall = "ok"

        return {"overall_status": overall, "checks": results}

    def check_schema_version(self) -> dict:
        current = "unknown"
        try:
            if self.db is not None:
                from sqlalchemy import text

                result = self.db.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                row = result.fetchone()
                if row:
                    current = row[0]
        except Exception:
            current = "unknown"

        needs_upgrade = current != EXPECTED_SCHEMA_VERSION and current != "unknown"
        status = "ok"
        message = f"Schema is at expected version {EXPECTED_SCHEMA_VERSION}"

        if current == "unknown":
            status = "warning"
            message = "Could not determine current schema version"
        elif needs_upgrade:
            status = "critical"
            message = f"Schema version {current} needs upgrade to {EXPECTED_SCHEMA_VERSION}"

        return {
            "current": current,
            "expected": EXPECTED_SCHEMA_VERSION,
            "needs_upgrade": needs_upgrade,
            "status": status,
            "message": message,
        }

    def check_config_deprecated(self) -> list[dict]:
        deprecated_found: list[dict] = []

        env_path = self._project_root / ".env"
        if not env_path.exists():
            return deprecated_found

        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    key = line.split("=", 1)[0].strip()
                    if key in DEPRECATED_CONFIG_KEYS:
                        deprecated_found.append({
                            "key": key,
                            "message": DEPRECATED_CONFIG_KEYS[key],
                            "status": "warning",
                        })
        except OSError:
            pass

        return deprecated_found

    def check_plugin_sdk(self) -> dict:
        plugins_dir = self._project_root / "backend" / "plugins"
        incompatible: list[dict] = []
        total = 0

        if not plugins_dir.exists():
            return {
                "status": "ok",
                "message": "No plugins directory found",
                "total": 0,
                "incompatible": [],
            }

        for manifest_path in plugins_dir.glob("*/manifest.json"):
            total += 1
            with contextlib.suppress(Exception):
                import json

                with open(manifest_path, encoding="utf-8") as f:
                    manifest = json.load(f)
                sdk_version = manifest.get("sdk_version", "unknown")
                if sdk_version != EXPECTED_SCHEMA_VERSION and sdk_version != "unknown":
                    incompatible.append({
                        "plugin": manifest_path.parent.name,
                        "sdk_version": sdk_version,
                        "required": EXPECTED_SCHEMA_VERSION,
                    })

        status = "ok"
        message = f"All {total} plugins are SDK compatible"
        if incompatible:
            status = "warning"
            message = f"{len(incompatible)} of {total} plugins have incompatible SDK versions"

        return {
            "status": status,
            "message": message,
            "total": total,
            "incompatible": incompatible,
        }

    def check_python_version(self) -> dict:
        version = sys.version_info
        major, minor = version.major, version.minor
        ok = major == 3 and minor >= 12
        return {
            "status": "ok" if ok else "critical",
            "message": f"Python {major}.{minor}.{version.micro} {'meets' if ok else 'does not meet'} requirement of 3.12+",
            "version": f"{major}.{minor}.{version.micro}",
        }

    def check_docker_version(self) -> dict:
        try:
            result = subprocess.run(  # noqa: S603 - static command list, no shell
                [shutil.which("docker") or "docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
            )
            output = result.stdout.strip()
            return {
                "status": "ok",
                "message": f"Docker available: {output}",
                "version_info": output,
            }
        except FileNotFoundError:
            return {
                "status": "warning",
                "message": "Docker is not installed or not in PATH",
                "version_info": None,
            }
        except Exception as exc:
            return {
                "status": "warning",
                "message": f"Could not determine Docker version: {exc}",
                "version_info": None,
            }

    def check_agent_versions(self) -> dict:
        agents: list[dict] = []

        if self.db is not None:
            with contextlib.suppress(Exception):
                from sqlalchemy import text

                result = self.db.execute(text("SELECT name, version FROM agents"))
                for row in result.fetchall():
                    name, version = row[0], row[1]
                    if version and version != EXPECTED_SCHEMA_VERSION:
                        agents.append({"name": name, "version": version})

        status = "ok"
        message = "All agents are up to date"
        if agents:
            status = "warning"
            message = f"{len(agents)} agent(s) are running older versions"

        return {
            "status": status,
            "message": message,
            "outdated_agents": agents,
        }

    def generate_upgrade_plan(self) -> dict:
        checks = self.check_all()
        steps: list[str] = []
        risks: list[str] = []
        estimated_minutes = 5

        schema_check = checks["checks"]["schema"]
        if schema_check.get("needs_upgrade"):
            steps.append(f"Upgrade database schema from {schema_check['current']} to {EXPECTED_SCHEMA_VERSION}")
            risks.append("Database migration may cause brief downtime")
            estimated_minutes += 10

        plugin_check = checks["checks"]["plugin_sdk"]
        if plugin_check.get("incompatible"):
            steps.append("Update incompatible plugins to match SDK version")
            risks.append("Plugin incompatibilities may cause runtime errors")
            estimated_minutes += 5

        deprecated = checks["checks"]["config_deprecated"]
        if deprecated:
            steps.append("Update deprecated configuration keys")
            risks.append("Misconfigured deprecated keys may affect functionality")
            estimated_minutes += 3

        agent_check = checks["checks"]["agents"]
        if agent_check.get("outdated_agents"):
            steps.append("Update outdated agent versions")
            estimated_minutes += 5

        if not steps:
            steps.append("No upgrade steps required — system is current")

        return {
            "steps": steps,
            "risks": risks,
            "estimated_minutes": estimated_minutes,
            "checks_summary": checks,
        }
