"""
Database Bridge for Veeam SSH→SQL Execution.

Supports both PostgreSQL (psql.exe) and MSSQL (sqlcmd.exe) backends.
Auto-detects which database engine the Veeam server uses.
"""

import asyncio
import base64
import logging

import paramiko

logger = logging.getLogger(__name__)

PG_PSQL_PATH = r"C:\Program Files\PostgreSQL\15\bin\psql.exe"
PG_DB_NAME = "VeeamBackup"
SSH_TEMP_DIR = r"C:\temp"
SQLCMD_PATH = r"C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\130\Tools\Binn\SQLCMD.EXE"
MSSQL_INSTANCE = r"localhost\VEEAMSQL2016"
MSSQL_DB_NAME = "VeeamBackup"


def detect_db_type(ssh_host: str, ssh_port: int, ssh_username: str, ssh_password: str) -> str:
    """Detect whether the remote Veeam server uses PostgreSQL or MSSQL.

    Checks file existence + port verification together. Both psql.exe
    and sqlcmd.exe may exist on a server; only the one with a live
    port is the actual Veeam database. Falls back to port-only probing,
    then defaults to MSSQL.
    Returns "postgresql" or "mssql".
    """
    try:
        client = paramiko.SSHClient()
        from app.core.config import get_settings

        if get_settings().ssh_auto_add_host_keys:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        client.connect(ssh_host, port=ssh_port, username=ssh_username, password=ssh_password, timeout=10)
        try:
            # Check which tools exist
            has_psql = False
            has_sqlcmd = False

            _, stdout, _ = client.exec_command(
                f'cmd.exe /c "if exist \\"{PG_PSQL_PATH}\\" echo PG_FOUND"',
                timeout=10,
            )
            if "PG_FOUND" in stdout.read().decode("utf-8", errors="replace"):
                has_psql = True

            _, stdout, _ = client.exec_command(
                f'cmd.exe /c "if exist \\"{SQLCMD_PATH}\\" echo MSSQL_FOUND"',
                timeout=10,
            )
            if "MSSQL_FOUND" in stdout.read().decode("utf-8", errors="replace"):
                has_sqlcmd = True

            # Probe ports to determine which DB is actually running
            pg_port_open = False
            mssql_port_open = False
            for shell in ["powershell.exe", "pwsh.exe"]:
                _, stdout, _ = client.exec_command(
                    f'{shell} -NoProfile -Command "Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded"',
                    timeout=15,
                )
                out = stdout.read().decode("utf-8", errors="replace").strip()
                if out and "True" in out:
                    pg_port_open = True
                    break

            for shell in ["powershell.exe", "pwsh.exe"]:
                _, stdout, _ = client.exec_command(
                    f'{shell} -NoProfile -Command "Test-NetConnection -ComputerName 127.0.0.1 -Port 1433 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded"',
                    timeout=15,
                )
                out = stdout.read().decode("utf-8", errors="replace").strip()
                if out and "True" in out:
                    mssql_port_open = True
                    break

            # Decision: prefer the one with BOTH file + port
            if has_psql and pg_port_open:
                return "postgresql"
            if has_sqlcmd and mssql_port_open:
                return "mssql"

            # Fallback: port alone is strong enough
            if pg_port_open:
                return "postgresql"
            if mssql_port_open:
                return "mssql"

            # File exists but port closed — still prefer that engine
            # (port might be on a non-standard number)
            if has_psql:
                return "postgresql"
            if has_sqlcmd:
                return "mssql"

            return "mssql"
        finally:
            client.close()
    except Exception as exc:
        logger.warning("DB type detection failed for %s: %s, defaulting to postgresql", ssh_host, exc)
        return "postgresql"


def _ssh_connect(ssh_host: str, ssh_port: int, ssh_username: str, ssh_password: str) -> paramiko.SSHClient:
    """Create and return a connected SSH client."""
    client = paramiko.SSHClient()
    from app.core.config import get_settings

    if get_settings().ssh_auto_add_host_keys:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect(ssh_host, port=ssh_port, username=ssh_username, password=ssh_password, timeout=15)
    return client


def _upload_sql(client: paramiko.SSHClient, sql: str) -> str:
    """Upload SQL to a temp file via SFTP, return the remote path."""
    sftp = client.open_sftp()
    try:
        sftp.mkdir(SSH_TEMP_DIR)
    except OSError:
        pass
    sql_path = f"{SSH_TEMP_DIR}/mc_query.sql"
    with sftp.open(sql_path, "w") as f:
        f.write(sql)
    sftp.close()
    return sql_path


def _exec_pg(client: paramiko.SSHClient, sql_path: str, shell: str = "pwsh.exe", use_pg_user: bool = True) -> dict:
    """Execute SQL via psql.exe on the remote server.

    When use_pg_user=True, connects as -U postgres (password auth).
    When use_pg_user=False, omits -U (uses Windows SSPI / current user).
    """
    if use_pg_user:
        psql_cmd = (
            f"& '{PG_PSQL_PATH}' -h 127.0.0.1 -U postgres -d {PG_DB_NAME} "
            f"-t -A -f {sql_path}"
        )
    else:
        psql_cmd = (
            f"& '{PG_PSQL_PATH}' -h 127.0.0.1 -d {PG_DB_NAME} "
            f"-t -A -f {sql_path}"
        )
    cmd = f'{shell} -NoProfile -NonInteractive -Command "{psql_cmd}"'
    _, stdout, stderr = client.exec_command(cmd, timeout=60)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    exit_code = stdout.channel.recv_exit_status()
    return {"success": exit_code == 0, "output": out, "stderr": err, "exit_code": exit_code}


def _exec_mssql(client: paramiko.SSHClient, sql_path: str) -> dict:
    """Execute SQL via sqlcmd.exe on the remote server.

    Uses PowerShell with EncodedCommand to avoid all quoting issues
    with cmd.exe pipe operators and nested quotes.
    """
    # Build the PowerShell script content, then base64 encode it
    ps_script = (
        f"& '{SQLCMD_PATH}' -S '{MSSQL_INSTANCE}' "
        f"-d {MSSQL_DB_NAME} -i '{sql_path}' -s '|' -h -1 -W"
    )
    encoded = base64.b64encode(ps_script.encode("utf-16-le")).decode("ascii")
    ps_exe = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    last_err = ""
    last_out = ""
    for exe in [ps_exe, "powershell.exe"]:
        cmd = f"{exe} -NoProfile -NonInteractive -EncodedCommand {encoded}"
        _, stdout, stderr = client.exec_command(cmd, timeout=60)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        exit_code = stdout.channel.recv_exit_status()
        if exit_code == 0 or out.strip():
            return {"success": exit_code == 0 and bool(out.strip()), "output": out, "stderr": err, "exit_code": exit_code}
        last_err = err
        last_out = out
    return {"success": False, "output": last_out, "stderr": last_err, "exit_code": 1}


async def run_db_query(
    sql: str,
    ssh_host: str,
    ssh_port: int,
    ssh_username: str,
    ssh_password: str,
    db_type: str = "postgresql",
) -> dict:
    """Execute a SQL query on the remote Veeam server via SSH.

    Args:
        sql: The SQL to execute.
        ssh_host: SSH hostname/IP.
        ssh_port: SSH port.
        ssh_username: SSH username.
        ssh_password: SSH password.
        db_type: "postgresql" or "mssql".

    Returns:
        dict with keys: success, output, stderr, exit_code
    """

    def _exec() -> dict:
        client = None
        try:
            client = _ssh_connect(ssh_host, ssh_port, ssh_username, ssh_password)
            sql_path = _upload_sql(client, sql)

            if db_type == "mssql":
                return _exec_mssql(client, sql_path)
            else:
                # Try pwsh.exe first, fall back to powershell.exe
                result = _exec_pg(client, sql_path, "pwsh.exe")
                if not result["success"] and "is not recognized" in result.get("stderr", ""):
                    result = _exec_pg(client, sql_path, "powershell.exe")

                # Retry without -U postgres on auth failure (SSPI/trust servers)
                auth_errors = ("SSPI", "password authentication failed", "pg_hba.conf", "FATAL:")
                if not result["success"] and any(e in result.get("stderr", "") for e in auth_errors):
                    logger.info("PG auth failed, retrying without -U postgres for %s", ssh_host)
                    shell = "powershell.exe" if "is not recognized" in result.get("stderr", "") else "pwsh.exe"
                    result = _exec_pg(client, sql_path, shell, use_pg_user=False)

                return result
        finally:
            if client:
                client.close()

    try:
        loop = asyncio.get_event_loop()
        return await asyncio.wait_for(loop.run_in_executor(None, _exec), timeout=75)
    except Exception as exc:
        logger.exception("Veeam SSH DB execution failed")
        return {"success": False, "error": str(exc), "output": "", "stderr": ""}
