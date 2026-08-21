"""Mission Control Agent - Registration and authentication."""

import hashlib
import logging
import platform
import socket
import uuid

from agent.client import AgentClient
from agent.config import AgentSettings

logger = logging.getLogger("mc-agent")


class RegistrationManager:
    """Handles agent registration with Mission Control server."""

    def __init__(self, client: AgentClient, config: AgentSettings):
        self.client = client
        self.config = config

    def generate_machine_id(self) -> str:
        """Generate a stable machine UUID using hostname + MAC address hash."""
        try:
            mac = uuid.getnode()
            hostname = socket.gethostname()
            raw = f"{hostname}-{mac}"
            return str(uuid.UUID(hashlib.sha256(raw.encode()).hexdigest()[:32]))
        except Exception as e:
            logger.warning("Failed to generate machine_id: %s", e)
            return str(uuid.uuid4())

    def generate_hardware_fingerprint(self) -> dict:
        """Collect CPU, motherboard serial, disk serial for hardware fingerprinting."""
        fingerprint: dict = {}

        try:
            import platform as _platform
            fingerprint["cpu"] = _platform.processor() or "unknown"
        except Exception:
            fingerprint["cpu"] = "unknown"

        try:
            import os
            import subprocess

            system = platform.system()
            if system == "Linux":
                for key, path in (
                    ("board_serial", "/sys/class/dmi/id/board_serial"),
                    ("board_vendor", "/sys/class/dmi/id/board_vendor"),
                    ("board_name", "/sys/class/dmi/id/board_name"),
                ):
                    try:
                        if os.path.exists(path):
                            with open(path) as f:
                                fingerprint[key] = f.read().strip()
                    except Exception:
                        pass

                for key, path in (
                    ("disk_serial", "/sys/block/sda/device/model"),
                    ("disk_vendor", "/sys/block/sda/device/vendor"),
                ):
                    try:
                        if os.path.exists(path):
                            with open(path) as f:
                                fingerprint[key] = f.read().strip()
                    except Exception:
                        pass

            elif system == "Windows":
                try:
                    out = subprocess.check_output(
                        ["wmic", "baseboard", "get", "SerialNumber,Manufacturer,Product"],
                        timeout=10,
                        stderr=subprocess.DEVNULL,
                    ).decode(errors="replace")
                    lines = [l.strip() for l in out.strip().split("\n") if l.strip() and l.strip().upper() not in ("SERIALNUMBER", "MANUFACTURER", "PRODUCT")]
                    if len(lines) >= 3:
                        fingerprint["board_serial"] = lines[0]
                        fingerprint["board_vendor"] = lines[1]
                        fingerprint["board_name"] = lines[2]
                except Exception:
                    pass

                try:
                    out = subprocess.check_output(
                        ["wmic", "diskdrive", "get", "SerialNumber,Model,Manufacturer"],
                        timeout=10,
                        stderr=subprocess.DEVNULL,
                    ).decode(errors="replace")
                    lines = [l.strip() for l in out.strip().split("\n") if l.strip() and l.strip().upper() not in ("SERIALNUMBER", "MODEL", "MANUFACTURER")]
                    if len(lines) >= 3:
                        fingerprint["disk_serial"] = lines[0]
                        fingerprint["disk_model"] = lines[1]
                        fingerprint["disk_vendor"] = lines[2]
                except Exception:
                    pass
            elif system == "Darwin":
                try:
                    out = subprocess.check_output(
                        ["system_profiler", "SPHardwareDataType"],
                        timeout=10,
                        stderr=subprocess.DEVNULL,
                    ).decode()
                    for line in out.strip().split("\n"):
                        if "Serial Number" in line:
                            fingerprint["board_serial"] = line.split(":", 1)[-1].strip()
                        elif "Model Name" in line:
                            fingerprint["board_name"] = line.split(":", 1)[-1].strip()
                        elif "Manufacturer" in line:
                            fingerprint["board_vendor"] = line.split(":", 1)[-1].strip()
                except Exception:
                    pass
        except Exception as e:
            logger.warning("Hardware fingerprint collection failed: %s", e)

        return fingerprint

    def generate_os_fingerprint(self) -> dict:
        """Collect OS details: system, version, kernel, architecture, hostname."""
        import os as _os

        fingerprint: dict = {
            "system": platform.system(),
            "version": platform.version(),
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "hostname": socket.gethostname(),
        }

        try:
            if platform.system() == "Linux" and _os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    for line in f:
                        if "=" in line:
                            key, _, val = line.partition("=")
                            if key.strip() in ("PRETTY_NAME", "VERSION", "ID"):
                                fingerprint[f"os_release_{key.strip().lower()}"] = val.strip().strip('"')
        except Exception:
            pass

        try:
            fingerprint["python_build"] = platform.python_build()
        except Exception:
            pass

        return fingerprint

    async def register(
        self,
        hostname: str,
        os_name: str,
        os_version: str,
        ip_address: str,
        agent_version: str,
    ) -> dict:
        """Register this agent with the Mission Control server."""
        payload = {
            "name": self.config.agent_name or hostname,
            "hostname": hostname,
            "operating_system": os_name,
            "os_version": os_version,
            "ip_address": ip_address,
            "agent_version": agent_version,
            "tags": None,
            "machine_id": self.generate_machine_id(),
            "hardware_fingerprint": self.generate_hardware_fingerprint(),
            "os_fingerprint": self.generate_os_fingerprint(),
        }

        try:
            result = await self.client.post(
                "/api/v1/agents/register", payload
            )
            logger.info(
                "Registered as agent %d (api_key: %s...)",
                result["agent_id"],
                result["api_key"][:12],
            )
            return result
        except Exception as e:
            logger.error("Registration failed: %s", e)
            raise

    async def register_with_token(self, enrollment_token: str) -> dict:
        """Register using an enrollment token."""
        payload = {
            "enrollment_token": enrollment_token,
            "machine_id": self.generate_machine_id(),
            "hardware_fingerprint": self.generate_hardware_fingerprint(),
            "os_fingerprint": self.generate_os_fingerprint(),
            "hostname": socket.gethostname(),
            "agent_name": self.config.agent_name or socket.gethostname(),
        }

        try:
            result = await self.client.post(
                "/api/v1/agents/register", payload
            )
            logger.info(
                "Registered via enrollment token as agent %d (api_key: %s...)",
                result["agent_id"],
                result["api_key"][:12],
            )
            return result
        except Exception as e:
            logger.error("Token-based registration failed: %s", e)
            raise

    async def reregister(self) -> dict:
        """Re-register with same agent_id (for agent replacement)."""
        payload = {
            "machine_id": self.generate_machine_id(),
            "hardware_fingerprint": self.generate_hardware_fingerprint(),
            "os_fingerprint": self.generate_os_fingerprint(),
            "hostname": socket.gethostname(),
            "agent_name": self.config.agent_name or socket.gethostname(),
            "reregister": True,
        }

        try:
            result = await self.client.post(
                "/api/v1/agents/register", payload
            )
            logger.info("Re-registered as agent %d", result["agent_id"])
            return result
        except Exception as e:
            logger.error("Re-registration failed: %s", e)
            raise

    async def validate_enrollment_token(self, token: str) -> dict:
        """Check if an enrollment token is valid before registering."""
        try:
            result = await self.client.post(
                "/api/v1/agents/validate-token",
                {"enrollment_token": token},
            )
            return result
        except Exception as e:
            logger.error("Token validation failed: %s", e)
            raise
