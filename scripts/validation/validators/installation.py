import subprocess
import os
import urllib.request

from validators import BaseValidator


class InstallationValidator(BaseValidator):
    name = "installation"

    def run(self, config: dict):
        self._check("docker_running", lambda: self._check_docker_running(), critical=True)
        self._check("docker_compose", lambda: self._check_docker_compose(), critical=True)
        self._check("postgres_container", lambda: self._check_container("postgres"), critical=True)
        self._check("redis_container", lambda: self._check_container("redis"), critical=True)
        self._check("backend_container", lambda: self._check_container("backend"), critical=True)
        self._check("frontend_container", lambda: self._check_container("frontend"), critical=True)
        self._check("backend_health", lambda: self._check_endpoint(config["api_url"], "/health/live"), critical=True)
        self._check("version_endpoint", lambda: self._check_endpoint(config["api_url"], "/version"), critical=True)
        self._check("required_directories", lambda: self._check_directories(config["project_root"]), critical=True)
        self._check("env_file", lambda: self._check_env_file(config["project_root"]), critical=True)
        self._check("database_migrations", lambda: self._check_migrations(config["project_root"]), critical=True)
        return self.result()

    def _check_docker_running(self):
        proc = subprocess.run(
            ["docker", "info"], capture_output=True, timeout=10
        )
        if proc.returncode != 0:
            raise RuntimeError("Docker is not running")
        return True

    def _check_docker_compose(self):
        proc = subprocess.run(
            ["docker", "compose", "version"], capture_output=True, timeout=10
        )
        if proc.returncode != 0:
            raise RuntimeError("Docker Compose is not available")
        return True

    def _check_container(self, service: str):
        proc = subprocess.run(
            ["docker", "compose", "ps", service, "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Failed to get status for {service}")
        if "Up" not in proc.stdout:
            raise RuntimeError(f"{service} container is not running (status: {proc.stdout.strip()})")
        return True

    def _check_endpoint(self, base_url: str, path: str):
        url = f"{base_url.rstrip('/')}{path}"
        resp = urllib.request.urlopen(url, timeout=5)
        if resp.status != 200:
            raise RuntimeError(f"{path} returned status {resp.status}")
        return True

    def _check_directories(self, project_root: str):
        required = ["backend/app", "frontend/src", ".agents", "docs", "scripts"]
        missing = [d for d in required if not os.path.isdir(os.path.join(project_root, d))]
        if missing:
            raise RuntimeError(f"Missing directories: {', '.join(missing)}")
        return True

    def _check_env_file(self, project_root: str):
        if not os.path.isfile(os.path.join(project_root, ".env")):
            raise RuntimeError(".env file not found")
        return True

    def _check_migrations(self, project_root: str):
        versions_dir = os.path.join(project_root, "backend", "alembic", "versions")
        if not os.path.isdir(versions_dir):
            raise RuntimeError("alembic versions directory not found")
        py_files = [f for f in os.listdir(versions_dir) if f.endswith(".py")]
        if not py_files:
            raise RuntimeError("No migration files found in alembic/versions/")
        return True
