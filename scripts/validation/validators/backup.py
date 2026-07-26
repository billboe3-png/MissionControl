import os
import subprocess

from validators import BaseValidator, CheckResult, Status, ValidatorResult


class BackupValidator(BaseValidator):
    name = "backup"
    description = "Backup infrastructure and tooling checks"

    def run(self, config: dict) -> ValidatorResult:
        result = ValidatorResult(module=self.name)
        cwd = config["project_root"]

        result.add(self._check(
            "pg_dump_available",
            lambda: self._check_pg_dump_available(cwd),
            critical=True,
        ))
        result.add(self._check(
            "pg_dump_test",
            lambda: self._check_pg_dump_test(cwd),
            critical=True,
        ))
        result.add(self._check(
            "redis_bgsave",
            lambda: self._check_redis_bgsave(cwd),
            critical=False,
        ))
        result.add(self._check(
            "redis_lastsave",
            lambda: self._check_redis_lastsave(cwd),
            critical=False,
        ))
        result.add(self._check(
            "config_backup_test",
            lambda: self._check_config_backup(config),
            critical=False,
        ))
        result.add(self._check(
            "backup_dir_writable",
            lambda: self._check_backup_dir_writable(config),
            critical=False,
        ))
        return result

    def _check_pg_dump_available(self, cwd):
        proc = subprocess.run(
            ["docker", "compose", "exec", "-T", "postgres", "pg_dump", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"pg_dump --version failed (rc={proc.returncode}): {proc.stderr.strip()}")
        if "pg_dump" not in proc.stdout:
            raise RuntimeError(f"Unexpected pg_dump output: {proc.stdout.strip()}")
        return CheckResult(
            name="pg_dump_available",
            status=Status.PASS,
            message=proc.stdout.strip(),
        )

    def _check_pg_dump_test(self, cwd):
        proc = subprocess.run(
            ["docker", "compose", "exec", "-T", "postgres",
             "pg_dump", "-U", "missioncontrol", "-d", "mission_control", "--schema-only"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"pg_dump --schema-only failed (rc={proc.returncode}): {proc.stderr.strip()}")
        return True

    def _check_redis_bgsave(self, cwd):
        proc = subprocess.run(
            ["docker", "compose", "exec", "-T", "redis", "redis-cli", "BGSAVE"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"redis-cli BGSAVE failed (rc={proc.returncode}): {proc.stderr.strip()}")
        if "OK" not in proc.stdout:
            raise RuntimeError(f"BGSAVE did not return OK: {proc.stdout.strip()}")
        return "Background saving started"

    def _check_redis_lastsave(self, cwd):
        proc = subprocess.run(
            ["docker", "compose", "exec", "-T", "redis", "redis-cli", "LASTSAVE"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"redis-cli LASTSAVE failed (rc={proc.returncode}): {proc.stderr.strip()}")
        value = proc.stdout.strip()
        if not value.isdigit():
            raise RuntimeError(f"LASTSAVE returned non-numeric value: {value}")
        return CheckResult(
            name="redis_lastsave",
            status=Status.PASS,
            message=f"last save timestamp: {value}",
            metrics={"lastsave": int(value)},
        )

    def _check_config_backup(self, config):
        env_path = os.path.join(config["project_root"], ".env")
        if not os.path.isfile(env_path):
            raise RuntimeError(f".env file not found at {env_path}")
        return True

    def _check_backup_dir_writable(self, config):
        backup_dir = os.path.join(config["project_root"], "backups")
        os.makedirs(backup_dir, exist_ok=True)
        test_file = os.path.join(backup_dir, ".validation_test")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            with open(test_file, "r") as f:
                content = f.read()
            if content != "test":
                raise RuntimeError("Write/read mismatch")
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
        return True
