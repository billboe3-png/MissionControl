"""Explore ERFRF MSSQL schema for Veeam tables."""
import os, sys, paramiko
sys.path.insert(0, "/app")
import asyncpg, asyncio
from app.core.config import get_settings
from app.core.security import CredentialCipher

settings = get_settings()
cipher = CredentialCipher(settings.missioncontrol_secret_key)


async def main():
    conn = await asyncpg.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        database=os.environ.get("POSTGRES_DB", "mission_control"),
        user=os.environ.get("POSTGRES_USER", "mission_control"),
        password=os.environ.get("POSTGRES_PASSWORD", "mission_control"),
    )
    d = dict(await conn.fetchrow(
        "SELECT ssh_host, ssh_username, ssh_port, ssh_password_encrypted "
        "FROM integration_profiles WHERE id = 18"
    ))
    await conn.close()

    ssh_password = cipher.decrypt(d["ssh_password_encrypted"])
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(d["ssh_host"], port=d["ssh_port"], username=d["ssh_username"], password=ssh_password, timeout=10)
    print("SSH OK")

    sqlcmd = "C:\\Program Files\\Microsoft SQL Server\\Client SDK\\ODBC\\130\\Tools\\Binn\\SQLCMD.EXE"
    instance = "localhost\\VEEAMSQL2016"

    def run_sql(query, db="VeeamBackup"):
        # Use SFTP to avoid quoting issues
        sql_path = "C:\\temp\\mc_q.sql"
        sftp = c.open_sftp()
        try: sftp.mkdir("C:\\temp")
        except: pass
        with sftp.open(sql_path, "w") as f: f.write(query)
        sftp.close()
        cmd = f'cmd.exe /c ""{sqlcmd}" -S "{instance}" -d {db} -i "{sql_path}" -h -1 -W"'
        _, stdout, stderr = c.exec_command(cmd, timeout=30)
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()
        return out, err

    # Find all schemas
    out, err = run_sql("SELECT DISTINCT s.name FROM sys.schemas s JOIN sys.tables t ON s.schema_id = t.schema_id ORDER BY s.name")
    print(f"[schemas with tables]\n{out}\n")

    # Find job/session related tables
    out, err = run_sql("SELECT s.name, t.name FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name LIKE '%ession%' OR t.name LIKE '%ob%' ORDER BY s.name, t.name")
    print(f"[job/session tables]\n{out}\n")

    # Find all Backup.Model tables
    out, err = run_sql("SELECT t.name FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE s.name = 'Backup.Model' ORDER BY t.name")
    print(f"[Backup.Model tables]\n{out}\n")

    # Also check for case-insensitive match
    out, err = run_sql("SELECT t.name FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE s.name COLLATE DATABASE_DEFAULT = 'backup' AND t.name COLLATE DATABASE_DEFAULT = 'model'")
    print(f"[backup.model exact]\n{out}\n")

    c.close()

asyncio.run(main())
