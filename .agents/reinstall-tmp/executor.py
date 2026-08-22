"""Mission Control Agent - Command execution engine."""

import asyncio
import base64
import logging
import os
import platform
import tempfile
import time
from typing import Any

logger = logging.getLogger("mc-agent")


class CommandExecutor:
    """Executes commands, scripts, and manages file transfers."""

    def __init__(self, timeout: int = 60):
        self.timeout = timeout

    async def execute(
        self,
        command: str,
        command_type: str = "execute",
        timeout: int | None = None,
        file_path: str | None = None,
        file_name: str | None = None,
        file_content_b64: str | None = None,
    ) -> dict[str, Any]:
        """Execute a command and return the result."""
        effective_timeout = timeout or self.timeout
        start_time = time.time()

        try:
            if command_type == "execute":
                result = await self._execute_shell(
                    command, effective_timeout
                )
            elif command_type == "script":
                result = await self._execute_script(
                    command, effective_timeout
                )
            elif command_type == "upload":
                result = await self._handle_upload(
                    file_path, file_name, file_content_b64
                )
            elif command_type == "download":
                result = await self._handle_download(file_path)
            elif command_type == "inventory":
                result = await self._collect_inventory()
            else:
                result = {
                    "success": False,
                    "stderr": f"Unknown command type: {command_type}",
                    "exit_code": 1,
                }

            duration_ms = int((time.time() - start_time) * 1000)
            result["duration_ms"] = duration_ms
            return result

        except asyncio.TimeoutError:
            return {
                "success": False,
                "stderr": f"Command timed out after {effective_timeout}s",
                "exit_code": -1,
                "duration_ms": int(
                    (time.time() - start_time) * 1000
                ),
            }
        except Exception as e:
            return {
                "success": False,
                "stderr": str(e),
                "exit_code": -1,
                "duration_ms": int(
                    (time.time() - start_time) * 1000
                ),
            }

    async def _execute_shell(
        self, command: str, timeout: int
    ) -> dict[str, Any]:
        """Execute a shell command."""
        system = platform.system()
        if system == "Windows":
            shell_cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-Command", command]
        else:
            shell_cmd = ["bash", "-c", command]

        process = await asyncio.create_subprocess_exec(
            *shell_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise

        return {
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "exit_code": process.returncode,
            "success": process.returncode == 0,
        }

    async def _execute_script(
        self, script: str, timeout: int
    ) -> dict[str, Any]:
        """Execute a script by writing to a temp file."""
        system = platform.system()
        suffix = ".ps1" if system == "Windows" else ".sh"

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=suffix,
            delete=False,
            dir=tempfile.gettempdir(),
        ) as tmp:
            tmp.write(script)
            tmp_path = tmp.name

        try:
            if system == "Windows":
                shell_cmd = [
                    "powershell", "-ExecutionPolicy",
                    "Bypass", "-File", tmp_path,
                ]
            else:
                os.chmod(tmp_path, 0o755)
                shell_cmd = ["bash", tmp_path]

            process = await asyncio.create_subprocess_exec(
                *shell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise

            return {
                "stdout": stdout.decode(errors="replace"),
                "stderr": stderr.decode(errors="replace"),
                "exit_code": process.returncode,
                "success": process.returncode == 0,
            }
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    async def _handle_upload(
        self,
        file_path: str | None,
        file_name: str | None,
        file_content_b64: str | None,
    ) -> dict[str, Any]:
        """Handle file upload to the local system."""
        if not file_path or not file_content_b64:
            return {
                "success": False,
                "stderr": "Missing file_path or file_content_b64",
                "exit_code": 1,
            }

        try:
            content = base64.b64decode(file_content_b64)
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(content)

            return {
                "success": True,
                "stdout": f"File written to {file_path} ({len(content)} bytes)",
                "exit_code": 0,
            }
        except Exception as e:
            return {
                "success": False,
                "stderr": f"Upload failed: {e}",
                "exit_code": 1,
            }

    async def _handle_download(
        self, file_path: str | None
    ) -> dict[str, Any]:
        """Handle file download from the local system."""
        if not file_path:
            return {
                "success": False,
                "stderr": "Missing file_path",
                "exit_code": 1,
            }

        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "stderr": f"File not found: {file_path}",
                    "exit_code": 1,
                }

            with open(file_path, "rb") as f:
                content = f.read()

            return {
                "success": True,
                "exit_code": 0,
                "file_content_b64": base64.b64encode(content).decode(),
                "file_name": os.path.basename(file_path),
            }
        except Exception as e:
            return {
                "success": False,
                "stderr": f"Download failed: {e}",
                "exit_code": 1,
            }

    async def _collect_inventory(self) -> dict[str, Any]:
        """Collect and return inventory data."""
        from agent.inventory import InventoryCollector

        collector = InventoryCollector()
        inventory = collector.collect()
        return {
            "success": True,
            "exit_code": 0,
            "stdout": str(inventory),
            "inventory": inventory,
        }
