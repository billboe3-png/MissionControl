"""
Mission Control Production Readiness Assessment

Scores the installation across multiple dimensions and provides
an overall readiness assessment for production deployment.
"""

import os
import subprocess
import sys
from pathlib import Path

DIMENSION_WEIGHTS = {
    "installation": 15,
    "configuration": 10,
    "database": 15,
    "redis": 10,
    "plugins": 10,
    "security": 15,
    "agents": 10,
    "automation": 5,
    "health": 5,
    "performance": 5,
}

TOTAL_WEIGHT = sum(DIMENSION_WEIGHTS.values())


class ReadinessChecker:
    def __init__(self, db=None):
        self.db = db
        self._project_root = Path(__file__).resolve().parents[4]

    def assess_all(self) -> dict:
        return {
            "installation": self.assess_installation(),
            "configuration": self.assess_configuration(),
            "database": self.assess_database(),
            "redis": self.assess_redis(),
            "plugins": self.assess_plugins(),
            "security": self.assess_security(),
            "agents": self.assess_agents(),
            "automation": self.assess_automation(),
            "health": self.assess_health_monitoring(),
            "performance": self.assess_performance(),
        }

    def assess_installation(self) -> dict:
        checks: list[dict] = []

        app_dir = self._project_root / "backend"
        checks.append({"label": "App directory", "pass": app_dir.exists()})

        plugins_dir = self._project_root / "backend" / "plugins"
        checks.append({"label": "Plugins directory", "pass": plugins_dir.exists()})

        env_file = self._project_root / ".env"
        checks.append({"label": ".env file", "pass": env_file.exists()})

        python_ok = sys.version_info >= (3, 12)
        checks.append({"label": "Python 3.12+", "pass": python_ok})

        docker_ok = self._check_docker_available()
        checks.append({"label": "Docker available", "pass": docker_ok})

        passed = sum(1 for c in checks if c["pass"])
        total = len(checks)
        score = int((passed / total) * 100) if total else 0

        return {
            "score": score,
            "status": "PASS" if score >= 80 else ("WARN" if score >= 50 else "FAIL"),
            "message": f"{passed}/{total} installation checks passed",
            "details": checks,
        }

    def assess_configuration(self) -> dict:
        checks: list[dict] = []

        env_file = self._project_root / ".env"
        if env_file.exists():
            try:
                with open(env_file, encoding="utf-8") as f:
                    content = f.read()
                has_secret = "SECRET_KEY" in content and "change-me" not in content.lower().split("secret_key")[1][:50] if "SECRET_KEY" in content else False
                checks.append({"label": "SECRET_KEY configured", "pass": has_secret})
            except OSError:
                checks.append({"label": ".env readable", "pass": False})
        else:
            checks.append({"label": ".env exists", "pass": False})

        checks.append({"label": "Config file present", "pass": env_file.exists()})

        passed = sum(1 for c in checks if c["pass"])
        total = len(checks)
        score = int((passed / total) * 100) if total else 0

        return {
            "score": score,
            "status": "PASS" if score >= 80 else ("WARN" if score >= 50 else "FAIL"),
            "message": f"{passed}/{total} configuration checks passed",
            "details": checks,
        }

    def assess_database(self) -> dict:
        checks: list[dict] = []

        if self.db is not None:
            try:
                from sqlalchemy import text

                self.db.execute(text("SELECT 1"))
                checks.append({"label": "Database connectivity", "pass": True})
            except Exception:
                checks.append({"label": "Database connectivity", "pass": False})

            try:
                from sqlalchemy import text

                result = self.db.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                row = result.fetchone()
                checks.append({"label": "Schema version present", "pass": row is not None})
            except Exception:
                checks.append({"label": "Schema version present", "pass": False})
        else:
            checks.append({"label": "Database session available", "pass": False})

        passed = sum(1 for c in checks if c["pass"])
        total = len(checks)
        score = int((passed / total) * 100) if total else 0

        return {
            "score": score,
            "status": "PASS" if score >= 80 else ("WARN" if score >= 50 else "FAIL"),
            "message": f"{passed}/{total} database checks passed",
            "details": checks,
        }

    def assess_redis(self) -> dict:
        checks: list[dict] = []

        try:
            import redis as redis_lib

            client = redis_lib.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
            client.ping()
            checks.append({"label": "Redis connectivity", "pass": True})
        except ImportError:
            checks.append({"label": "redis package installed", "pass": False})
        except Exception:
            checks.append({"label": "Redis connectivity", "pass": False})

        passed = sum(1 for c in checks if c["pass"])
        total = len(checks)
        score = int((passed / total) * 100) if total else 0

        return {
            "score": score,
            "status": "PASS" if score >= 80 else ("WARN" if score >= 50 else "FAIL"),
            "message": f"{passed}/{total} Redis checks passed",
            "details": checks,
        }

    def assess_plugins(self) -> dict:
        checks: list[dict] = []
        plugins_dir = self._project_root / "backend" / "plugins"

        if not plugins_dir.exists():
            return {
                "score": 100,
                "status": "PASS",
                "message": "No plugins directory — no plugins to assess",
                "details": [{"label": "Plugins directory", "pass": True}],
            }

        manifests = list(plugins_dir.glob("*/manifest.json"))
        checks.append({"label": "Plugin manifests found", "pass": len(manifests) > 0})

        valid = 0
        for manifest_path in manifests:
            try:
                import json

                with open(manifest_path, encoding="utf-8") as f:
                    data = json.load(f)
                if "name" in data and "version" in data:
                    valid += 1
            except Exception:
                continue

        checks.append({"label": f"Valid manifests ({valid}/{len(manifests)})", "pass": valid == len(manifests)})

        passed = sum(1 for c in checks if c["pass"])
        total = len(checks)
        score = int((passed / total) * 100) if total else 0

        return {
            "score": score,
            "status": "PASS" if score >= 80 else ("WARN" if score >= 50 else "FAIL"),
            "message": f"{passed}/{total} plugin checks passed",
            "details": checks,
        }

    def assess_security(self) -> dict:
        checks: list[dict] = []

        env_file = self._project_root / ".env"
        secret_ok = False
        if env_file.exists():
            try:
                with open(env_file, encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("SECRET_KEY="):
                            value = line.split("=", 1)[1].strip().strip("\"'")
                            secret_ok = len(value) >= 16 and "change-me" not in value.lower()
                            break
            except OSError:
                pass
        checks.append({"label": "Strong SECRET_KEY", "pass": secret_ok})

        rate_limit_ok = False
        if env_file.exists():
            try:
                with open(env_file, encoding="utf-8") as f:
                    content = f.read()
                rate_limit_ok = "RATE_LIMIT" in content
            except OSError:
                pass
        checks.append({"label": "Rate limiting configured", "pass": rate_limit_ok})

        tls_ready = os.getenv("TLS_CERT_PATH") or os.getenv("SSL_CERT_FILE") is not None
        if not tls_ready and env_file.exists():
            try:
                with open(env_file, encoding="utf-8") as f:
                    content = f.read()
                tls_ready = "TLS_CERT" in content or "SSL_" in content
            except OSError:
                pass
        checks.append({"label": "TLS readiness", "pass": tls_ready})

        passed = sum(1 for c in checks if c["pass"])
        total = len(checks)
        score = int((passed / total) * 100) if total else 0

        return {
            "score": score,
            "status": "PASS" if score >= 80 else ("WARN" if score >= 50 else "FAIL"),
            "message": f"{passed}/{total} security checks passed",
            "details": checks,
        }

    def assess_agents(self) -> dict:
        checks: list[dict] = []

        if self.db is not None:
            try:
                from sqlalchemy import text

                result = self.db.execute(text("SELECT COUNT(*) FROM agents"))
                count = result.scalar()
                checks.append({"label": "Agents registered", "pass": count is not None and count > 0})
            except Exception:
                checks.append({"label": "Agents queryable", "pass": False})
        else:
            checks.append({"label": "Database session available", "pass": False})

        passed = sum(1 for c in checks if c["pass"])
        total = len(checks)
        score = int((passed / total) * 100) if total else 0

        return {
            "score": score,
            "status": "PASS" if score >= 80 else ("WARN" if score >= 50 else "FAIL"),
            "message": f"{passed}/{total} agent checks passed",
            "details": checks,
        }

    def assess_automation(self) -> dict:
        checks: list[dict] = []

        if self.db is not None:
            try:
                from sqlalchemy import text

                self.db.execute(text("SELECT 1 FROM automation_rules LIMIT 1"))
                checks.append({"label": "Automation rules table", "pass": True})
            except Exception:
                checks.append({"label": "Automation rules table", "pass": False})
        else:
            checks.append({"label": "Database session available", "pass": False})

        passed = sum(1 for c in checks if c["pass"])
        total = len(checks)
        score = int((passed / total) * 100) if total else 0

        return {
            "score": score,
            "status": "PASS" if score >= 80 else ("WARN" if score >= 50 else "FAIL"),
            "message": f"{passed}/{total} automation checks passed",
            "details": checks,
        }

    def assess_health_monitoring(self) -> dict:
        checks: list[dict] = []

        health_endpoint = self._project_root / "backend" / "app" / "api" / "health.py"
        checks.append({"label": "Health endpoint module", "pass": health_endpoint.exists()})

        docker_compose = self._project_root / "docker-compose.yml"
        if not docker_compose.exists():
            docker_compose = self._project_root / "docker-compose.yaml"
        checks.append({"label": "Docker Compose config", "pass": docker_compose.exists()})

        passed = sum(1 for c in checks if c["pass"])
        total = len(checks)
        score = int((passed / total) * 100) if total else 0

        return {
            "score": score,
            "status": "PASS" if score >= 80 else ("WARN" if score >= 50 else "FAIL"),
            "message": f"{passed}/{total} health monitoring checks passed",
            "details": checks,
        }

    def assess_performance(self) -> dict:
        checks: list[dict] = []

        checks.append({"label": "Python executable", "pass": bool(sys.executable)})

        try:
            import importlib

            for mod in ("psutil", "uvloop"):
                importlib.import_module(mod)
            checks.append({"label": "Performance libraries available", "pass": True})
        except ImportError:
            checks.append({"label": "Performance libraries available", "pass": False})

        passed = sum(1 for c in checks if c["pass"])
        total = len(checks)
        score = int((passed / total) * 100) if total else 0

        return {
            "score": score,
            "status": "PASS" if score >= 80 else ("WARN" if score >= 50 else "FAIL"),
            "message": f"{passed}/{total} performance checks passed",
            "details": checks,
        }

    def get_score(self) -> tuple[int, dict]:
        results = self.assess_all()
        weighted_sum = 0.0

        for dimension, weight in DIMENSION_WEIGHTS.items():
            dim_result = results.get(dimension, {})
            dim_score = dim_result.get("score", 0)
            weighted_sum += dim_score * (weight / TOTAL_WEIGHT)

        overall_score = round(weighted_sum)

        issues: list[str] = []
        recommendations: list[str] = []

        for dimension, dim_result in results.items():
            if dim_result.get("status") == "FAIL":
                issues.append(f"{dimension}: {dim_result.get('message', 'Check failed')}")
                recommendations.append(f"Address failing {dimension} checks before production deployment")
            elif dim_result.get("status") == "WARN":
                issues.append(f"{dimension}: {dim_result.get('message', 'Warnings present')}")
                recommendations.append(f"Review warnings in {dimension} dimension")

        production_ready = overall_score >= 80 and not any(
            results[d].get("status") == "FAIL" for d in DIMENSION_WEIGHTS
        )

        return overall_score, {
            "score": overall_score,
            "production_ready": production_ready,
            "dimensions": results,
            "issues": issues,
            "recommendations": recommendations,
        }

    def _check_docker_available(self) -> bool:
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False
