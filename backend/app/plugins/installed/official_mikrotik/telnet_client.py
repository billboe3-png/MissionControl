"""
MikroTik Telnet Client
"""
import asyncio
import contextlib
import logging

logger = logging.getLogger("plugin.mikrotik.telnet")


class MikroTikTelnetClient:
    """Async Telnet client for MikroTik RouterOS."""

    def __init__(self, host: str, username: str, password: str, port: int = 23, timeout: int = 30):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout

    async def _read_until(self, reader: asyncio.StreamReader, expected: bytes) -> bytes:
        return await reader.readuntil(expected)

    async def execute(self, command: str) -> str:
        """Execute a RouterOS command over Telnet and return raw output."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=self.timeout
            )
        except (TimeoutError, OSError) as exc:
            raise RuntimeError(f"Telnet connect failed: {exc}") from exc

        try:
            data = await asyncio.wait_for(
                reader.read(1024), timeout=self.timeout
            )
            if b"login:" in data.lower():
                writer.write((self.username + "\n").encode())
                await writer.drain()
                data = await asyncio.wait_for(
                    reader.read(1024), timeout=self.timeout
                )
            if b"password:" in data.lower():
                writer.write((self.password + "\n").encode())
                await writer.drain()

            await asyncio.sleep(0.2)

            writer.write((command + "\n").encode())
            await writer.drain()

            output = b""
            while True:
                chunk = await asyncio.wait_for(
                    reader.read(4096), timeout=self.timeout
                )
                output += chunk
                if output.count(b"[") > output.count(b"]"):
                    break

            return output.decode("utf-8", errors="replace")
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
