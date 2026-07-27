"""
Mission Control Installation Report

Generates comprehensive installation reports in Markdown, JSON,
and plain text formats for documentation and troubleshooting.
"""

import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


class InstallationReporter:
    def __init__(self, db=None):
        self.db = db
        self._project_root = Path(__file__).resolve().parents[4]

    def collect_info(self) -> dict:
        info: dict = {}

        info["platform"] = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        }

        info["docker_version"] = self._get_version(["docker", "--version"])
        info["postgresql_version"] = self._get_version(["psql", "--version"])
        info["redis_version"] = self._get_version(["redis-server", "--version"])

        info["mission_control"] = self._get_mc_version()
        info["edition"] = os.getenv("MC_EDITION", "community")

        info["admin_user"] = os.getenv("MC_ADMIN_USER", "admin")
        info["company"] = os.getenv("MC_COMPANY", "")
        info["site"] = os.getenv("MC_SITE", "")

        info["plugins"] = self._get_installed_plugins()
        info["health"] = self._get_health_summary()

        info["configuration"] = self._get_config_summary()

        info["validation"] = self._get_validation_results()

        info["generated_at"] = datetime.now(UTC).isoformat()

        return info

    def generate_markdown(self) -> str:
        info = self.collect_info()
        lines: list[str] = []

        lines.append("# Mission Control Installation Report")
        lines.append("")
        lines.append(f"**Generated:** {info['generated_at']}")
        lines.append("")

        lines.append("## System Information")
        lines.append("")
        sys_info = info["platform"]
        lines.append("| Property | Value |")
        lines.append("|----------|-------|")
        lines.append(f"| Operating System | {sys_info['system']} {sys_info['release']} |")
        lines.append(f"| OS Version | {sys_info['version']} |")
        lines.append(f"| Architecture | {sys_info['machine']} |")
        lines.append(f"| Python | {sys_info['python']} |")
        lines.append(f"| Docker | {info['docker_version'] or 'Not installed'} |")
        lines.append(f"| PostgreSQL | {info['postgresql_version'] or 'Not found'} |")
        lines.append(f"| Redis | {info['redis_version'] or 'Not found'} |")
        lines.append("")

        mc = info["mission_control"]
        lines.append("## Mission Control")
        lines.append("")
        lines.append(f"- **Version:** {mc.get('version', 'unknown')}")
        lines.append(f"- **Edition:** {info['edition']}")
        lines.append(f"- **Python:** {sys.version.split()[0]}")
        lines.append("")

        lines.append("## Organization")
        lines.append("")
        lines.append(f"- **Company:** {info['company'] or '(not set)'}")
        lines.append(f"- **Site:** {info['site'] or '(not set)'}")
        lines.append(f"- **Admin User:** {info['admin_user']}")
        lines.append("")

        lines.append("## Installed Plugins")
        lines.append("")
        plugins = info["plugins"]
        if plugins:
            lines.append("| Plugin | Version | Status |")
            lines.append("|--------|---------|--------|")
            for p in plugins:
                lines.append(f"| {p['name']} | {p.get('version', 'unknown')} | {p.get('status', 'unknown')} |")
        else:
            lines.append("No plugins installed.")
        lines.append("")

        lines.append("## Health Summary")
        lines.append("")
        health = info["health"]
        for key, value in health.items():
            status_icon = "PASS" if value.get("healthy") else "FAIL"
            lines.append(f"- **{key}:** {status_icon} — {value.get('message', '')}")
        lines.append("")

        lines.append("## Configuration Summary")
        lines.append("")
        config = info["configuration"]
        for key, value in config.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

        lines.append("## Validation Results")
        lines.append("")
        validation = info["validation"]
        lines.append("| Check | Status | Message |")
        lines.append("|-------|--------|---------|")
        for v in validation:
            lines.append(f"| {v['check']} | {v['status']} | {v['message']} |")
        lines.append("")

        return "\n".join(lines)

    def generate_json(self) -> str:
        info = self.collect_info()
        return json.dumps(info, indent=2, default=str)

    def generate_text(self) -> str:
        info = self.collect_info()
        lines: list[str] = []

        lines.append("=" * 60)
        lines.append("  Mission Control Installation Report")
        lines.append("=" * 60)
        lines.append(f"  Generated: {info['generated_at']}")
        lines.append("")

        sys_info = info["platform"]
        lines.append("--- System Information ---")
        lines.append(f"  OS:           {sys_info['system']} {sys_info['release']}")
        lines.append(f"  Version:      {sys_info['version']}")
        lines.append(f"  Architecture: {sys_info['machine']}")
        lines.append(f"  Python:       {sys_info['python']}")
        lines.append(f"  Docker:       {info['docker_version'] or 'Not installed'}")
        lines.append(f"  PostgreSQL:   {info['postgresql_version'] or 'Not found'}")
        lines.append(f"  Redis:        {info['redis_version'] or 'Not found'}")
        lines.append("")

        mc = info["mission_control"]
        lines.append("--- Mission Control ---")
        lines.append(f"  Version:  {mc.get('version', 'unknown')}")
        lines.append(f"  Edition:  {info['edition']}")
        lines.append("")

        lines.append("--- Organization ---")
        lines.append(f"  Company:  {info['company'] or '(not set)'}")
        lines.append(f"  Site:     {info['site'] or '(not set)'}")
        lines.append(f"  Admin:    {info['admin_user']}")
        lines.append("")

        lines.append("--- Installed Plugins ---")
        plugins = info["plugins"]
        if plugins:
            for p in plugins:
                lines.append(f"  * {p['name']} v{p.get('version', '?')} [{p.get('status', 'unknown')}]")
        else:
            lines.append("  No plugins installed.")
        lines.append("")

        lines.append("--- Health ---")
        health = info["health"]
        for key, value in health.items():
            marker = "OK" if value.get("healthy") else "FAIL"
            lines.append(f"  [{marker}] {key}: {value.get('message', '')}")
        lines.append("")

        lines.append("--- Validation ---")
        validation = info["validation"]
        for v in validation:
            lines.append(f"  [{v['status']}] {v['check']}: {v['message']}")
        lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def save_reports(self, output_dir: str = "reports/installation") -> dict:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        md_path = out_path / "installation_report.md"
        json_path = out_path / "installation_report.json"
        text_path = out_path / "installation_report.txt"

        md_path.write_text(self.generate_markdown(), encoding="utf-8")
        json_path.write_text(self.generate_json(), encoding="utf-8")
        text_path.write_text(self.generate_text(), encoding="utf-8")

        return {
            "markdown": str(md_path),
            "json": str(json_path),
            "text": str(text_path),
        }

    def _get_version(self, cmd: list[str]) -> str | None:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.stdout.strip().split("\n")[0] if result.returncode == 0 else None
        except Exception:
            return None

    def _get_mc_version(self) -> dict:
        version_file = self._project_root / "backend" / "VERSION"
        if version_file.exists():
            try:
                return {"version": version_file.read_text(encoding="utf-8").strip()}
            except OSError:
                pass

        pyproject = self._project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                for line in pyproject.read_text(encoding="utf-8").splitlines():
                    if line.strip().startswith("version"):
                        version = line.split("=", 1)[1].strip().strip("\"'")
                        return {"version": version}
            except OSError:
                pass

        return {"version": "unknown"}

    def _get_installed_plugins(self) -> list[dict]:
        plugins: list[dict] = []
        plugins_dir = self._project_root / "backend" / "plugins"

        if not plugins_dir.exists():
            return plugins

        for manifest_path in plugins_dir.glob("*/manifest.json"):
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    manifest = json.load(f)
                plugins.append({
                    "name": manifest.get("name", manifest_path.parent.name),
                    "version": manifest.get("version", "unknown"),
                    "status": "loaded",
                })
            except Exception:
                plugins.append({
                    "name": manifest_path.parent.name,
                    "version": "unknown",
                    "status": "error",
                })

        return plugins

    def _get_health_summary(self) -> dict:
        health: dict = {}

        for name, cmd in [
            ("database", ["pg_isready"]),
            ("redis", ["redis-cli", "ping"]),
        ]:
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                healthy = result.returncode == 0
                health[name] = {
                    "healthy": healthy,
                    "message": "Responding" if healthy else "Not responding",
                }
            except Exception:
                health[name] = {
                    "healthy": False,
                    "message": "Check command failed",
                }

        health["docker"] = {
            "healthy": self._get_version(["docker", "info"]) is not None,
            "message": "Docker daemon available" if self._get_version(["docker", "info"]) else "Docker not available",
        }

        return health

    def _get_config_summary(self) -> dict:
        config: dict = {}
        env_file = self._project_root / ".env"

        safe_keys = [
            "MC_EDITION", "MC_COMPANY", "MC_SITE", "MC_ADMIN_USER",
            "MC_PORT", "MC_HOST", "LOG_LEVEL",
        ]

        if env_file.exists():
            try:
                with open(env_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        key = line.split("=", 1)[0].strip()
                        if key in safe_keys:
                            value = line.split("=", 1)[1].strip().strip("\"'")
                            config[key] = value
            except OSError:
                config["_error"] = "Could not read .env file"

        return config

    def _get_validation_results(self) -> list[dict]:
        results: list[dict] = []

        py_ok = sys.version_info >= (3, 12)
        results.append({
            "check": "Python Version",
            "status": "PASS" if py_ok else "FAIL",
            "message": f"Python {sys.version_info.major}.{sys.version_info.minor} {'meets' if py_ok else 'does not meet'} 3.12+ requirement",
        })

        docker_ok = self._get_version(["docker", "--version"]) is not None
        results.append({
            "check": "Docker Available",
            "status": "PASS" if docker_ok else "WARN",
            "message": "Docker is installed" if docker_ok else "Docker not found",
        })

        app_dir = self._project_root / "backend" / "app"
        results.append({
            "check": "App Structure",
            "status": "PASS" if app_dir.exists() else "FAIL",
            "message": "Application directory exists" if app_dir.exists() else "Application directory missing",
        })

        plugins_dir = self._project_root / "backend" / "plugins"
        results.append({
            "check": "Plugins Directory",
            "status": "PASS" if plugins_dir.exists() else "WARN",
            "message": "Plugins directory exists" if plugins_dir.exists() else "No plugins directory",
        })

        if self.db is not None:
            try:
                from sqlalchemy import text

                self.db.execute(text("SELECT 1"))
                results.append({
                    "check": "Database Connectivity",
                    "status": "PASS",
                    "message": "Database connection successful",
                })
            except Exception as exc:
                results.append({
                    "check": "Database Connectivity",
                    "status": "FAIL",
                    "message": f"Database connection failed: {exc}",
                })

        return results
