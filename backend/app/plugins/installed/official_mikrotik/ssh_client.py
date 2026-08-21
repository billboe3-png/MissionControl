"""
MikroTik SSH Client
"""
import asyncio
import logging
from typing import Any

logger = logging.getLogger("plugin.mikrotik.ssh")


class MikroTikSSHClient:
    """Async SSH client for MikroTik RouterOS."""

    def __init__(self, host: str, username: str, password: str, port: int = 22, timeout: int = 30):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout

    async def execute(self, command: str) -> str:
        """Execute a RouterOS command over SSH and return raw output."""
        try:
            import asyncssh
        except ImportError:
            raise RuntimeError("asyncssh is required for MikroTik SSH support")

        async with asyncssh.connect(
            self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            known_hosts=None,
        ) as conn:
            async with conn.create_process() as proc:
                proc.stdin.write(command + "\n")
                await proc.stdin.drain()
                proc.stdin.write_eof()
                stdout, _ = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout
                )
                return stdout

    async def execute_structured(self, command: str) -> list[dict[str, str]]:
        """Execute a command and parse RouterOS key=value output."""
        raw = await self.execute(command)
        return self._parse_key_value_output(raw)

    @staticmethod
    def _parse_key_value_output(raw: str) -> list[dict[str, str]]:
        """Parse RouterOS ':each /command print detail' output."""
        records: list[dict[str, str]] = []
        current: dict[str, str] = {}
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("Flags:"):
                if current:
                    records.append(current)
                    current = {}
                continue
            if line.startswith(" ") and "=" in line:
                key, _, value = line.partition("=")
                current[key.strip()] = value.strip()
        if current:
            records.append(current)
        return records
