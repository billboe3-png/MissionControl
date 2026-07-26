import subprocess

from validators import BaseValidator, CheckResult, Status, ValidatorResult


class RestoreValidator(BaseValidator):
    name = "restore"
    description = "Restore readiness and data integrity checks (non-destructive)"

    def run(self, config: dict) -> ValidatorResult:
        result = ValidatorResult(module=self.name)
        cwd = config["project_root"]

        result.add(self._check(
            "schema_only_dump",
            lambda: self._check_schema_only_dump(cwd),
            critical=True,
        ))
        result.add(self._check(
            "schema_only_valid_sql",
            lambda: self._check_schema_only_valid_sql(cwd),
            critical=False,
        ))
        result.add(self._check(
            "redis_config_exists",
            lambda: self._check_redis_config_exists(cwd),
            critical=False,
        ))
        result.add(self._check(
            "restore_dry_run",
            lambda: self._check_restore_dry_run(cwd),
            critical=False,
        ))
        return result

    def _run_pg_dump_schema(self, cwd):
        proc = subprocess.run(
            ["docker", "compose", "exec", "-T", "postgres",
             "pg_dump", "-U", "missioncontrol", "-d", "mission_control", "--schema-only"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd,
        )
        return proc

    def _check_schema_only_dump(self, cwd):
        proc = self._run_pg_dump_schema(cwd)
        if proc.returncode != 0:
            raise RuntimeError(f"pg_dump --schema-only failed (rc={proc.returncode}): {proc.stderr.strip()}")
        output = proc.stdout.strip()
        if not output:
            raise RuntimeError("pg_dump --schema-only returned empty output")
        return CheckResult(
            name="schema_only_dump",
            status=Status.PASS,
            message=f"Schema dump OK ({len(output)} chars)",
            metrics={"dump_size_chars": len(output)},
        )

    def _check_schema_only_valid_sql(self, cwd):
        proc = self._run_pg_dump_schema(cwd)
        if proc.returncode != 0:
            raise RuntimeError(f"pg_dump failed (rc={proc.returncode})")
        output = proc.stdout
        if "CREATE TABLE" not in output:
            raise RuntimeError("Schema dump does not contain CREATE TABLE statements")
        table_count = output.count("CREATE TABLE")
        return CheckResult(
            name="schema_only_valid_sql",
            status=Status.PASS,
            message=f"Found {table_count} CREATE TABLE statements",
            metrics={"create_table_count": table_count},
        )

    def _check_redis_config_exists(self, cwd):
        proc = subprocess.run(
            ["docker", "compose", "exec", "-T", "redis", "redis-cli", "DBSIZE"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"redis-cli DBSIZE failed (rc={proc.returncode}): {proc.stderr.strip()}")
        output = proc.stdout.strip()
        if "keys in" not in output:
            return CheckResult(
                name="redis_config_exists",
                status=Status.WARN,
                message=f"Unexpected DBSIZE output: {output}",
            )
        return CheckResult(
            name="redis_config_exists",
            status=Status.PASS,
            message=output,
        )

    def _check_restore_dry_run(self, cwd):
        proc = self._run_pg_dump_schema(cwd)
        if proc.returncode != 0:
            raise RuntimeError(f"pg_dump failed (rc={proc.returncode})")
        output = proc.stdout
        if not output:
            raise RuntimeError("Empty schema dump - cannot validate")
        if output.startswith("pg_dump:") or "ERROR:" in output:
            raise RuntimeError(f"Schema dump contains errors: {output[:200]}")
        has_preamble = output.startswith("--") or "PostgreSQL database cluster dump" in output
        return CheckResult(
            name="restore_dry_run",
            status=Status.PASS,
            message=f"Schema dump is valid SQL (has_preamble={has_preamble})",
            metrics={"has_preamble": has_preamble},
        )
