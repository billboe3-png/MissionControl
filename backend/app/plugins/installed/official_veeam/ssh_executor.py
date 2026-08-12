"""SSH executor abstraction for Veeam host operations.

Production: AgentSshExecutor — dispatches ``veeam:*`` commands to a
linked Mission Control agent via the AgentCommand queue and polls for
completion. Dev/test: DirectSshExecutor — paramiko straight to the Veeam
host, never selected for production configs.
"""

import asyncio
import json
import logging
import time
from contextlib import suppress
from typing import Any, TypedDict

from app.core.config import get_settings

logger = logging.getLogger("plugin.veeam.ssh_executor")


class SshResult(TypedDict):
    success: bool
    output: str
    stderr: str
    exit_code: int
    error: str | None
    duration_ms: int


class AgentSshExecutor:
    """Dispatch veeam:* ops through the AgentCommand queue and poll."""

    def __init__(
        self,
        db: Any,
        agent_id: int,
        target_id: int,
        timeout: int = 120,
        poll_interval: float = 2.0,
        command_repo: Any = None,
        agent_repo: Any = None,
    ) -> None:
        self._db = db
        self._agent_id = agent_id
        self._target_id = target_id
        self.timeout = timeout
        self.poll_interval = poll_interval
        if command_repo is not None:
            self._command_repo = command_repo
        else:
            from app.repositories.agent_repository import AgentCommandRepository
            self._command_repo = AgentCommandRepository
        if agent_repo is not None:
            self._agent_repo = agent_repo
        else:
            from app.repositories.agent_repository import AgentRepository
            self._agent_repo = AgentRepository
        self.transport = "agent"

    async def run(
        self, op: str, params: dict | None = None, timeout: int | None = None,
    ) -> SshResult:
        start = time.monotonic()
        deadline = start + (timeout or self.timeout)

        agent = self._agent_repo.get_by_id(self._db, self._agent_id)
        if agent is None:
            return self._err("Agent not found", start)
        if agent.status != "online":
            return self._err(f"Agent '{getattr(agent, 'name', self._agent_id)}' is offline", start)

        payload = {
            "namespace": "veeam",
            "op": op,
            "params": {
                "target_id": self._target_id,
                **(params or {}),
            },
        }
        cmd = await asyncio.to_thread(
            self._command_repo.create,
            self._db,
            agent_id=self._agent_id,
            command_type="remote_execute",
            command=json.dumps(payload),
            timeout=int(deadline - start),
        )
        command_id = cmd.id

        while True:
            current = await asyncio.to_thread(
                self._command_repo.get_by_id, self._db, command_id
            )
            if current is None:
                return self._err("Command row vanished", start)
            if current.status in ("completed", "failed"):
                duration_ms = int((time.monotonic() - start) * 1000)
                if current.status == "failed" or current.exit_code not in (0, None):
                    return SshResult(
                        success=False,
                        output=current.stdout or "",
                        stderr=current.stderr or "",
                        exit_code=current.exit_code or 1,
                        error=(current.stderr or current.error_message or "Command failed"),
                        duration_ms=duration_ms,
                    )
                return SshResult(
                    success=True,
                    output=current.stdout or "",
                    stderr=current.stderr or "",
                    exit_code=current.exit_code or 0,
                    error=None,
                    duration_ms=duration_ms,
                )
            if time.monotonic() >= deadline:
                return self._err("Timed out waiting for agent", start)
            await asyncio.sleep(self.poll_interval)

    @staticmethod
    def _err(message: str, start: float) -> SshResult:
        return SshResult(
            success=False, output="", stderr="", exit_code=1,
            error=message, duration_ms=int((time.monotonic() - start) * 1000),
        )


class DirectSshExecutor:
    """Dev/test paramiko executor. Never selected in production."""

    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "",
        password: str = "",
        environment: str | None = None,
    ) -> None:
        env = environment or get_settings().environment
        if env == "production":
            raise RuntimeError("DirectSshExecutor is not allowed in production")
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    @property
    def transport(self) -> str:
        return "direct"

    async def run(
        self, op: str, params: dict | None = None, timeout: int = 120,
    ) -> SshResult:
        if op in ("veeam:db:detect", "veeam:db:query", "veeam:ps"):
            return await self._run_direct(op, params or {}, timeout)
        return self._err(f"Direct executor does not implement {op}")

    async def _run_direct(self, op: str, params: dict, timeout: int) -> SshResult:
        import paramiko
        client = paramiko.SSHClient()
        settings = get_settings()
        if settings.ssh_auto_add_host_keys:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        start = time.monotonic()
        try:
            client.connect(
                self.host, port=self.port, username=self.username,
                password=self.password, timeout=10,
            )
            if op == "veeam:db:detect":
                out = await asyncio.to_thread(
                    self._probe_binaries_and_ports, client,
                )
                return SshResult(
                    success=True, output=json.dumps(out), stderr="",
                    exit_code=0, error=None,
                    duration_ms=int((time.monotonic() - start) * 1000),
                )
            if op == "veeam:db:query":
                out = await asyncio.to_thread(
                    self._run_sql, client, params, timeout,
                )
                return SshResult(
                    success=out["exit_code"] == 0, output=out["output"],
                    stderr=out["stderr"], exit_code=out["exit_code"],
                    error=None if out["exit_code"] == 0 else out["stderr"],
                    duration_ms=int((time.monotonic() - start) * 1000),
                )
            raise ValueError(f"Direct executor does not implement {op}")
        except Exception as exc:
            logger.debug("Direct SSH op failed: %s", exc)
            return SshResult(
                success=False, output="", stderr="", exit_code=1,
                error=str(exc), duration_ms=int((time.monotonic() - start) * 1000),
            )
        finally:
            client.close()

    def _probe_binaries_and_ports(self, client: Any) -> dict:
        psql_path = r"C:\Program Files\PostgreSQL\15\bin\psql.exe"
        sqlcmd_path = r"C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\130\Tools\Binn\SQLCMD.EXE"
        def exists(path: str) -> bool:
            _, out, _ = client.exec_command(
                f'cmd.exe /c "if exist \\"{path}\\" echo FOUND"', timeout=10,
            )
            return "FOUND" in out.read().decode("utf-8", errors="replace")
        def port_open(port: int) -> bool:
            for shell in ("powershell.exe", "pwsh.exe"):
                _, out, _ = client.exec_command(
                    f'{shell} -NoProfile -Command "Test-NetConnection -ComputerName 127.0.0.1 -Port {port} -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded"',
                    timeout=15,
                )
                if "True" in out.read().decode("utf-8", errors="replace"):
                    return True
            return False
        has_psql, has_sqlcmd = exists(psql_path), exists(sqlcmd_path)
        pg_port, ms_port = port_open(5432), port_open(1433)
        if has_psql and pg_port:
            db_type = "postgresql"
        elif has_sqlcmd and ms_port:
            db_type = "mssql"
        elif pg_port:
            db_type = "postgresql"
        elif ms_port:
            db_type = "mssql"
        elif has_psql:
            db_type = "postgresql"
        elif has_sqlcmd:
            db_type = "mssql"
        else:
            db_type = "mssql"
        return {
            "db_type": db_type, "psql_found": has_psql,
            "sqlcmd_found": has_sqlcmd, "pg_port": pg_port, "mssql_port": ms_port,
        }

    def _run_sql(self, client: Any, params: dict, timeout: int) -> dict:
        sql = params.get("sql", "")
        db_type = params.get("db_type", "postgresql")
        sftp = client.open_sftp()
        try:
            with suppress(OSError):
                sftp.mkdir("C:/temp")
            sql_path = "C:/temp/mc_query.sql"
            with sftp.open(sql_path, "w") as f:
                f.write(sql)
        finally:
            sftp.close()
        if db_type == "mssql":
            ps_script = (
                f"& 'C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\130\\Tools\\Binn\\SQLCMD.EXE' "
                f"-S 'localhost\\VEEAMSQL2016' -d VeeamBackup -i '{sql_path}' -s '|' -h -1 -W"
            )
            import base64
            encoded = base64.b64encode(ps_script.encode("utf-16-le")).decode("ascii")
            cmd = f"powershell.exe -NoProfile -NonInteractive -EncodedCommand {encoded}"
        else:
            cmd = (
                f"pwsh.exe -NoProfile -NonInteractive -Command \"& 'C:\\Program Files\\PostgreSQL\\15\\bin\\psql.exe' "
                f"-h 127.0.0.1 -U postgres -d VeeamBackup -t -A -f {sql_path}\""
            )
        _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        exit_code = stdout.channel.recv_exit_status()
        return {"output": out, "stderr": err, "exit_code": exit_code}

    @staticmethod
    def _err(message: str) -> SshResult:
        return SshResult(
            success=False, output="", stderr="", exit_code=1, error=message, duration_ms=0,
        )


def build_ssh_executor(db: Any, server: Any) -> AgentSshExecutor:
    """Build the production executor for a server row."""
    if server.agent_id is None or server.target_id is None:
        raise ValueError(
            "Veeam server requires an agent and remote target for SSH access"
        )
    return AgentSshExecutor(
        db=db, agent_id=server.agent_id, target_id=server.target_id,
        timeout=server.timeout or 120,
    )
